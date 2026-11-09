"""Small localhost HTTP adapter around the versioned inference contract."""
import json
import mimetypes
import os
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from inference_api import auth, budget, dw_tools, evidence_packets, jobs, limits, models, service, storage
from inference_api.observability import reconciliation, receipts

ROOT = Path(__file__).resolve().parents[3]
WEB = ROOT / "frontend" / "dist"
BI_SNAPSHOT = ROOT / "private" / "bi_snapshot.json"


class Handler(BaseHTTPRequestHandler):
    def _static(self, path: str) -> None:
        relative = "index.html" if path == "/" else path.lstrip("/")
        target = (WEB / relative).resolve()
        if not target.is_relative_to(WEB.resolve()) or not target.is_file():
            self._send(404, {"error": "not_found"})
            return
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store" if target.name == "index.html" else "public, max-age=31536000, immutable")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; object-src 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def _send(self, status: int, payload: dict | list, extra_headers: dict | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
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

    def _browser_origin(self) -> str | None:
        """Accept cookie writes only from this public HTTPS or loopback origin."""
        origin = self.headers.get("Origin", "")
        host = self.headers.get("Host", "")
        if not host or any(c in host for c in " /\\@"):
            return None
        if origin == f"https://{host}":
            return origin
        if host.split(":")[0] in {"localhost", "127.0.0.1"} and origin == f"http://{host}":
            return origin
        return None

    def _cookie_token(self) -> str:
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            return cookie["inference_session"].value if "inference_session" in cookie else ""
        except Exception:
            return ""

    @staticmethod
    def _session_cookie(token: str, secure: bool) -> str:
        value = f"inference_session={token}; Path=/api; HttpOnly; SameSite=Strict; Max-Age={auth.SESSION_HOURS * 3600}"
        return value + ("; Secure" if secure else "")

    def _dispatch(self, method: str) -> None:
        path = urlparse(self.path).path
        if method == "GET" and path == "/health":
            self._send(200, {"status": "up"})
            return
        if method == "GET" and not path.startswith("/api/"):
            self._static(path)
            return
        if not path.startswith("/api/"):
            self._send(404, {"error": "not_found"})
            return
        try:
            if method == "POST" and path == "/api/login":
                browser = self.headers.get("X-Browser-Session") == "1"
                origin = self._browser_origin() if browser else None
                if browser and origin is None:
                    self._send(403, {"error": "invalid_origin"})
                    return
                data = self._body()
                result = auth.login(data.get("username"), data.get("password"))
                if browser and result:
                    token = result.pop("token")
                    self._send(200, result, {"Set-Cookie": self._session_cookie(token, origin.startswith("https:"))})
                else:
                    self._send(200 if result else 401, result or {"error": "invalid_credentials"})
                return
            bearer = self.headers.get("Authorization", "")
            cookie_token = self._cookie_token() if not bearer else ""
            if cookie_token and method == "POST" and self._browser_origin() is None:
                self._send(403, {"error": "invalid_origin"})
                return
            credential = bearer or ("Bearer " + cookie_token if cookie_token else "")
            principal = auth.authenticate(credential)
            if principal is None:
                self._send(401, {"error": "unauthorized"})
                return
            if method == "GET" and path == "/api/me":
                self._send(200, {"id": principal.id, "username": principal.username})
            elif method == "GET" and path == "/api/bi/snapshot":
                self._send(200, json.loads(BI_SNAPSHOT.read_text(encoding="utf-8")))
            elif method == "GET" and path == "/api/budget":
                self._send(200, budget.status())
            elif method == "POST" and path == "/api/logout":
                auth.logout(credential)
                cleared = "inference_session=; Path=/api; HttpOnly; SameSite=Strict; Max-Age=0"
                if self._browser_origin() and self._browser_origin().startswith("https:"):
                    cleared += "; Secure"
                self._send(200, {"status": "logged_out"}, {"Set-Cookie": cleared} if cookie_token else None)
            elif method == "GET" and path == "/api/models":
                from inference_api.model_service.registry import public_profiles
                self._send(200, public_profiles())
            elif method == "GET" and path == "/api/bench/scenarios":
                from inference_api.agent_harness import approved_catalog
                self._send(200, {"scenarios": ["fixed_evidence", "data_access"],
                                 "catalog_version": approved_catalog.load()["version"]})
            elif method == "GET" and path == "/api/bench/evidence-packets":
                self._send(200, evidence_packets.list_packets())
            elif method == "GET" and path == "/api/bench/dw-tools":
                self._send(200, dw_tools.availability())
            elif method == "GET" and path == "/api/prompts":
                self._send(200, storage.list_prompts())
            elif method == "POST" and path == "/api/prompts":
                data = self._body()
                result = storage.create_prompt(data.get("name"), principal.username,
                                               data.get("system_prompt"),
                                               data.get("expected_revision"))
                self._send(201, result)
            elif method == "GET" and path == "/api/criteria":
                self._send(200, storage.list_criteria())
            elif method == "POST" and path == "/api/criteria":
                data = self._body()
                result = storage.create_criteria(data.get("name"), principal.username,
                                                 data.get("config"),
                                                 data.get("expected_revision"))
                self._send(201, result)
            elif method == "GET" and path == "/api/runs":
                self._send(200, storage.list_runs())
            elif method == "POST" and path == "/api/run-jobs":
                data = self._body()
                request_key = data.pop("request_key", None)
                self._send(202, jobs.submit(data, principal, request_key))
            elif method == "GET" and path.startswith("/api/run-jobs/by-key/"):
                key = str(UUID(path.removeprefix("/api/run-jobs/by-key/")))
                job = storage.get_job_by_key(key, principal.id)
                self._send(200 if job else 404, job or {"error": "not_found"})
            elif method == "GET" and path.startswith("/api/run-jobs/"):
                job_id = str(UUID(path.removeprefix("/api/run-jobs/")))
                job = storage.get_job(job_id, principal.id)
                self._send(200 if job else 404, job or {"error": "not_found"})
            elif method == "POST" and path == "/api/runs":
                data = self._body()
                service._validate_input(data)
                with limits.reserve(principal.id):
                    self._send(201, service.execute_run(data, principal))
            elif method=='POST' and path.startswith('/api/runs/') and path.endswith('/observability/reconcile'):
                run_id=str(UUID(path[len('/api/runs/'):-len('/observability/reconcile')]))
                if int(self.headers.get('Content-Length','0')):
                    if self._body():raise ValueError('reconciliation_body_forbidden')
                self._send(200,{'observability_current':reconciliation.reconcile(run_id,principal)})
            elif method == "GET" and path.startswith("/api/runs/"):
                run_id = str(UUID(path.removeprefix("/api/runs/")))
                result = storage.get_run(run_id,principal_id=principal.id)
                self._send(200 if result else 404, result or {"error": "not_found"})
            elif method == "POST" and path.startswith("/api/runs/") and path.endswith("/feedback"):
                run_id = str(UUID(path[len("/api/runs/"):-len("/feedback")]))
                data = self._body()
                result = storage.add_feedback(run_id, principal.username, data.get("text"))
                self._send(201, result)
            else:
                self._send(404, {"error": "not_found"})
        except reconciliation.NotFound as exc:
            self._send(404,{'error':str(exc)})
        except reconciliation.Forbidden as exc:
            self._send(403,{'error':str(exc)})
        except receipts.ReconciliationBusy:
            self._send(409,{'error':'reconciliation_in_progress'})
        except (auth.LoginBusy, limits.BusyError, limits.QuotaError) as exc:
            self._send(429, {"error": str(exc)})
        except storage.RevisionConflict as exc:
            self._send(409, {"error": str(exc), "kind": exc.kind, "current": exc.current})
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
    mode = os.getenv("INFERENCE_RUNTIME_MODE", "host")
    if mode not in {"host", "docker"}:
        raise ValueError("INFERENCE_RUNTIME_MODE must be host or docker")
    if mode == "host":
        storage.list_prompts()  # Preserve fail-fast behavior for direct local execution.
    storage.interrupt_unfinished_jobs()
    host = "0.0.0.0" if mode == "docker" else "127.0.0.1"
    server = ThreadingHTTPServer((host, 8765), Handler)
    print(f"Inference API listening at http://{host}:8765")
    server.serve_forever()
