"""Small localhost HTTP adapter around the versioned inference contract."""
import hmac
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from . import models, service, storage
from .config import api_token

WEB = Path(__file__).resolve().parents[2] / "web" / "index.html"


class Handler(BaseHTTPRequestHandler):
    def _authorized(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        return hmac.compare_digest(supplied, "Bearer " + api_token())

    def _send(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 < size <= 65536:
            raise ValueError("JSON body must contain 1 to 65536 bytes")
        data = json.loads(self.rfile.read(size))
        if not isinstance(data, dict):
            raise ValueError("JSON object required")
        return data

    def _dispatch(self, method: str) -> None:
        path = urlparse(self.path).path
        if method == "GET" and path == "/":
            body = WEB.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(body)
            return
        if not path.startswith("/api/"):
            self._send(404, {"error": "not_found"})
            return
        if not self._authorized():
            self._send(401, {"error": "unauthorized"})
            return
        try:
            if method == "GET" and path == "/api/models":
                self._send(200, models.available_models())
            elif method == "GET" and path == "/api/prompts":
                self._send(200, storage.list_prompts())
            elif method == "POST" and path == "/api/prompts":
                data = self._body()
                result = storage.create_prompt(data.get("name"), data.get("author"),
                                               data.get("system_prompt"),
                                               data.get("expected_revision"))
                self._send(201, result)
            elif method == "GET" and path == "/api/runs":
                self._send(200, storage.list_runs())
            elif method == "POST" and path == "/api/runs":
                self._send(201, service.execute_run(self._body()))
            elif method == "GET" and path.startswith("/api/runs/"):
                run_id = str(UUID(path.removeprefix("/api/runs/")))
                result = storage.get_run(run_id)
                self._send(200 if result else 404, result or {"error": "not_found"})
            elif method == "POST" and path.startswith("/api/runs/") and path.endswith("/feedback"):
                run_id = str(UUID(path[len("/api/runs/"):-len("/feedback")]))
                data = self._body()
                result = storage.add_feedback(run_id, data.get("author"), data.get("text"))
                self._send(201, result)
            else:
                self._send(404, {"error": "not_found"})
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})
        except Exception as exc:
            print(f"HTTP operation failed: {type(exc).__name__}")
            self._send(503, {"error": "service_unavailable", "type": type(exc).__name__})

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")


def serve() -> None:
    api_token()
    storage.list_prompts()  # Fail startup if the application database is unavailable.
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Inference API listening at http://127.0.0.1:8765")
    server.serve_forever()
