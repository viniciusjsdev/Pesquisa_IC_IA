"""Small localhost HTTP adapter around the versioned inference contract."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from . import auth, budget, limits, models, service, storage

WEB = Path(__file__).resolve().parents[2] / "web" / "index.html"


class Handler(BaseHTTPRequestHandler):
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
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(body)
            return
        if not path.startswith("/api/"):
            self._send(404, {"error": "not_found"})
            return
        try:
            if method == "POST" and path == "/api/login":
                data = self._body()
                result = auth.login(data.get("username"), data.get("password"))
                self._send(200 if result else 401, result or {"error": "invalid_credentials"})
                return
            principal = auth.authenticate(self.headers.get("Authorization", ""))
            if principal is None:
                self._send(401, {"error": "unauthorized"})
                return
            if method == "GET" and path == "/api/me":
                self._send(200, {"id": principal.id, "username": principal.username})
            elif method == "GET" and path == "/api/budget":
                self._send(200, budget.status())
            elif method == "POST" and path == "/api/logout":
                auth.logout(self.headers.get("Authorization", ""))
                self._send(200, {"status": "logged_out"})
            elif method == "GET" and path == "/api/models":
                self._send(200, models.available_models())
            elif method == "GET" and path == "/api/prompts":
                self._send(200, storage.list_prompts())
            elif method == "POST" and path == "/api/prompts":
                data = self._body()
                result = storage.create_prompt(data.get("name"), principal.username,
                                               data.get("system_prompt"),
                                               data.get("expected_revision"))
                self._send(201, result)
            elif method == "GET" and path == "/api/runs":
                self._send(200, storage.list_runs())
            elif method == "POST" and path == "/api/runs":
                data = self._body()
                with limits.reserve(principal.id):
                    self._send(201, service.execute_run(data, principal))
            elif method == "GET" and path.startswith("/api/runs/"):
                run_id = str(UUID(path.removeprefix("/api/runs/")))
                result = storage.get_run(run_id)
                self._send(200 if result else 404, result or {"error": "not_found"})
            elif method == "POST" and path.startswith("/api/runs/") and path.endswith("/feedback"):
                run_id = str(UUID(path[len("/api/runs/"):-len("/feedback")]))
                data = self._body()
                result = storage.add_feedback(run_id, principal.username, data.get("text"))
                self._send(201, result)
            else:
                self._send(404, {"error": "not_found"})
        except (auth.LoginBusy, limits.BusyError, limits.QuotaError) as exc:
            self._send(429, {"error": str(exc)})
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
    storage.list_prompts()  # Fail startup if the application database is unavailable.
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Inference API listening at http://127.0.0.1:8765")
    server.serve_forever()
