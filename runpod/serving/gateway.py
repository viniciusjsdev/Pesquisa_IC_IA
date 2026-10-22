"""Minimal bearer-authenticated allowlist in front of loopback-only vLLM."""

from hmac import compare_digest
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json


MAX_REQUEST = 2 * 1024 * 1024
MAX_RESPONSE = 8 * 1024 * 1024
IDENTITY_HEADERS = {
    "manifest_sha256": "X-Inference-Manifest-SHA256",
    "base_revision": "X-Inference-Base-Revision",
    "session_id": "X-Inference-Session-ID",
}


def make_server(token: str, session: dict, *, port: int = 8000,
                upstream_port: int = 8002) -> ThreadingHTTPServer:
    if len(token) < 32:
        raise ValueError("Gateway token is missing or too short")
    if not all(session.get(key) for key in IDENTITY_HEADERS):
        raise ValueError("Gateway session identity is incomplete")

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_args):
            # Prompts, tokens and request URLs must not enter a shared Pod log.
            return

        def _reply(self, status: int, body: bytes) -> None:
            self.close_connection = True
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)

        def _handle(self) -> None:
            if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) > 1:
                self._reply(400, b'{"error":"unsupported transfer framing"}')
                return
            permitted = ((self.command == "GET" and self.path == "/v1/models") or
                         (self.command == "POST" and self.path == "/v1/chat/completions"))
            if not permitted:
                self._reply(404, b'{"error":"not found"}')
                return
            supplied = self.headers.get("Authorization", "")
            if not compare_digest(supplied, "Bearer " + token):
                self._reply(401, b'{"error":"unauthorized"}')
                return
            body = None
            if self.command == "POST":
                size = self.headers.get("Content-Length", "")
                if not size.isdecimal() or not 0 < int(size) <= MAX_REQUEST:
                    self._reply(413, b'{"error":"invalid request size"}')
                    return
                if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                    self._reply(415, b'{"error":"json required"}')
                    return
                body = self.rfile.read(int(size))
                try:
                    request_payload = json.loads(body)
                    if not isinstance(request_payload, dict):
                        raise ValueError("JSON object required")
                except (ValueError, UnicodeDecodeError):
                    self._reply(400, b'{"error":"invalid json"}')
                    return
                if request_payload.get("model") not in session.get("aliases", ()):
                    self._reply(400, b'{"error":"unknown model alias"}')
                    return
            connection = HTTPConnection("127.0.0.1", upstream_port, timeout=610)
            headers_sent = False
            try:
                connection.request(self.command, self.path, body=body,
                                   headers={"Content-Type": "application/json"})
                response = connection.getresponse()
                if (self.command == "POST" and request_payload.get("stream") is True
                        and response.status == 200):
                    if response.getheader("Content-Type", "").split(";")[0].strip() != "text/event-stream":
                        self._reply(502, b'{"error":"upstream did not stream"}')
                        return
                    self.close_connection = True
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Transfer-Encoding", "chunked")
                    self.send_header("Cache-Control", "no-store, no-transform")
                    self.send_header("Connection", "close")
                    for key, header in IDENTITY_HEADERS.items():
                        self.send_header(header, session[key])
                    if session.get("vllm_version"):
                        self.send_header("X-Inference-VLLM-Version", session["vllm_version"])
                    self.end_headers()
                    headers_sent = True
                    total = 0
                    for line in iter(response.readline, b""):
                        total += len(line)
                        if total > MAX_RESPONSE:
                            return  # Truncated chunked response fails closed in the client.
                        self.wfile.write(f"{len(line):X}\r\n".encode("ascii") + line + b"\r\n")
                        self.wfile.flush()
                    self.wfile.write(b"0\r\n\r\n")
                    self.wfile.flush()
                    return
                payload = response.read(MAX_RESPONSE + 1)
                if len(payload) > MAX_RESPONSE:
                    self._reply(502, b'{"error":"upstream response too large"}')
                    return
                self.close_connection = True
                self.send_response(response.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "close")
                for key, header in IDENTITY_HEADERS.items():
                    self.send_header(header, session[key])
                if session.get("vllm_version"):
                    self.send_header("X-Inference-VLLM-Version", session["vllm_version"])
                self.end_headers()
                self.wfile.write(payload)
            except OSError:
                if not headers_sent:
                    self._reply(502, b'{"error":"model unavailable"}')
            finally:
                connection.close()

        def do_GET(self):
            self._handle()

        def do_POST(self):
            self._handle()

        def do_HEAD(self):
            self._reply(404, b'{"error":"not found"}')

    return ThreadingHTTPServer(("0.0.0.0" if port == 8000 else "127.0.0.1", port), Handler)
