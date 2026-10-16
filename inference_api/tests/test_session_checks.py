"""SPEC-005 gates without RunPod, ngrok or real HTTP generation."""

import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inference_api"))

import session_checks


class SessionChecksTests(unittest.TestCase):
    def test_default_preflight_has_no_external_http_and_reports_each_gate(self):
        with patch.object(session_checks, "_git", return_value={"head": "abc"}), \
             patch.object(session_checks, "_source", return_value={"rows_in_existing_load": 1}), \
             patch.object(session_checks, "_app", return_value={"schema_versions": [1, 2]}), \
             patch.object(session_checks, "_artifacts", return_value={"adapter_count": 6}), \
             patch.object(session_checks, "_serving_config", return_value={"network_call": False}), \
             patch.object(session_checks, "_limits", return_value={"global_concurrent_inferences": 1}), \
             patch.object(session_checks, "build_opener", side_effect=AssertionError("external HTTP")):
            result = session_checks.preflight()
        self.assertEqual(result["state"], "CONFIRMED")
        self.assertEqual(len(result["checks"]), 7)
        self.assertEqual(result["remote_generation"], "not_run")
        self.assertEqual(result["ngrok_http"], "not_run")

    def test_missing_identity_hash_and_protected_config_block_preflight(self):
        with patch.object(session_checks, "_git", return_value={"head": "abc"}), \
             patch.object(session_checks, "_source", return_value={"rows_in_existing_load": 1}), \
             patch.object(session_checks, "_app", side_effect=ValueError("identity missing")), \
             patch.object(session_checks, "_artifacts", side_effect=ValueError("hash mismatch")), \
             patch.object(session_checks, "_serving_config", side_effect=ValueError("URL missing")), \
             patch.object(session_checks, "_limits", return_value={}):
            result = session_checks.preflight()
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual({item["component"] for item in result["checks"]
                          if item["state"] == "BLOCKED"},
                         {"db_inference_app", "adapters", "serving_configuration"})
        self.assertNotIn("hash mismatch", json.dumps(result))

    def test_rehearsal_requires_explicit_execution_and_safe_origin(self):
        with patch.object(sys, "argv", ["session_checks.py", "rehearsal"]), \
             patch.object(session_checks, "AppClient", side_effect=AssertionError("HTTP")), \
             self.assertRaises(SystemExit) as stopped:
            session_checks.main()
        self.assertEqual(stopped.exception.code, 2)
        for origin in ("http://example.org", "http://127.0.0.1:5544",
                       "https://user:secret@example.org", "https://example.org/path"):
            with self.assertRaises(ValueError):
                session_checks.AppClient(origin)

    def test_rehearsal_stops_before_http_when_preflight_is_blocked(self):
        output = ROOT / "inference_api" / ".local" / "spec005-never-created.json"
        with patch.object(sys, "argv", ["session_checks.py", "rehearsal", "--execute",
                                        "--app-origin", "https://session.example",
                                        "--aliases", "qwen-base", "ft-finqa-a",
                                        "--output", str(output)]), \
             patch.object(session_checks, "preflight", return_value={"state": "BLOCKED"}), \
             patch.object(session_checks, "AppClient", side_effect=AssertionError("HTTP")), \
             patch.object(session_checks, "getpass", side_effect=AssertionError("password")):
            self.assertEqual(session_checks.main(), 2)
        self.assertFalse(output.exists())

    def test_https_rehearsal_requires_matching_fresh_tunnel_report(self):
        local = ROOT / "inference_api" / ".local"
        local.mkdir(exist_ok=True)
        with NamedTemporaryFile(mode="w", suffix=".json", prefix="spec005-tunnel-test-",
                                dir=local, delete=False, encoding="utf-8") as stream:
            path = Path(stream.name)
            json.dump({"kind": "ngrok_http_probe", "state": "CONFIRMED",
                       "origin": "https://session.example",
                       "checked_at": datetime.now(timezone.utc).isoformat()}, stream)
        try:
            session_checks._tunnel_report(path, "https://session.example")
            with self.assertRaises(ValueError):
                session_checks._tunnel_report(path, "https://other.example")
        finally:
            path.unlink()

    def test_tunnel_probe_checks_app_only_and_requires_manual_forwarding_readback(self):
        class Response:
            def __init__(self, status):
                self.status = status
            def read(self, _limit):
                return b""
            def close(self):
                return None

        class Opener:
            def __init__(self):
                self.paths = []
            def open(self, request, timeout):
                self.paths.append(request.full_url)
                return Response({"/": 200, "/api/me": 401, "/api/runs": 401,
                                 "/api/models": 401, "/v1/models": 404}[
                                     request.full_url.removeprefix("https://session.example")])

        opener = Opener()
        with patch.object(session_checks, "build_opener", return_value=opener):
            result = session_checks.tunnel_probe("https://session.example")
        self.assertEqual(result["state"], "CONFIRMED")
        self.assertEqual(len(opener.paths), 5)
        self.assertEqual(result["tunnel_target_readback"], "manual_required")
        with self.assertRaises(ValueError):
            session_checks.tunnel_probe("http://127.0.0.1:8765")

    def test_lost_login_response_is_uncertain_without_exposing_credentials(self):
        class LostLoginApp:
            origin = "https://session.example"

            def call(self, method, path, token="", body=None):
                if path == "/api/me":
                    return 401, {}
                if path == "/api/login":
                    raise TimeoutError("response lost after login POST")
                raise AssertionError(path)

        journal = []
        result = session_checks.rehearsal(
            LostLoginApp(), ["qwen-base", "ft-finqa-a"], 2020,
            {"Nicoli": "hidden", "Vinicius": "hidden"},
            journal=lambda data: journal.append(json.loads(json.dumps(data))))
        self.assertEqual(result["state"], "UNCERTAIN")
        self.assertEqual(result["pending"], {"component": "Nicoli_login", "author": "Nicoli"})
        self.assertEqual(journal[-1]["pending"], result["pending"])
        self.assertNotIn("hidden", json.dumps(result))

    def test_lost_post_response_is_uncertain_and_journals_exact_revision(self):
        class LostResponseApp:
            origin = "https://session.example"
            def call(self, method, path, token="", body=None):
                if path == "/api/me":
                    return (200, {"username": token}) if token else (401, {})
                if path == "/api/login":
                    return 200, {"token": body["username"]}
                if path == "/api/logout":
                    return 200, {}
                if path == "/api/models":
                    return 200, {alias: {"available": True, "generation_confirmed": True}
                                 for alias in ("qwen-base", "ft-finqa-a")}
                if path == "/api/prompts":
                    raise TimeoutError("response lost after POST")
                raise AssertionError(path)

        journal = []
        result = session_checks.rehearsal(
            LostResponseApp(), ["qwen-base", "ft-finqa-a"], 2020,
            {"Nicoli": "hidden", "Vinicius": "hidden"},
            journal=lambda data: journal.append(json.loads(json.dumps(data))))
        self.assertEqual(result["state"], "UNCERTAIN")
        self.assertEqual(result["pending"]["component"], "Nicoli_prompt_revision")
        self.assertEqual(result["pending"]["expected_revision"], 0)
        self.assertTrue(journal[-1]["pending"])
        self.assertNotIn("hidden", json.dumps(result))

    def test_rehearsal_checks_three_routes_two_aliases_revisions_and_authors(self):
        class FakeApp:
            origin = "https://session.example"

            def __init__(self):
                self.calls = []
                self.prompt_revision = 0
                self.criteria_revision = 0
                self.runs = {}

            def call(self, method, path, token="", body=None):
                self.calls.append((method, path, token))
                if path == "/api/me":
                    return (200, {"username": token}) if token else (401, {"error": "unauthorized"})
                if path == "/api/login":
                    return 200, {"token": body["username"]}
                if path == "/api/logout":
                    return 200, {"status": "logged_out"}
                if path == "/api/models":
                    return 200, {alias: {"available": True, "generation_confirmed": True}
                                 for alias in ("qwen-base", "ft-finqa-a")}
                if path == "/api/prompts":
                    self.prompt_revision += 1
                    return 201, {"id": f"p{self.prompt_revision}",
                                 "revision": self.prompt_revision}
                if path == "/api/criteria":
                    self.criteria_revision += 1
                    return 201, {"id": f"c{self.criteria_revision}",
                                 "revision": self.criteria_revision}
                if path == "/api/runs" and body["model_alias"] == "unknown-alias":
                    return 400, {"error": "Unknown model alias"}
                if path == "/api/runs":
                    run_id = f"r{len(self.runs) + 1}"
                    route_error = body["year"] == 2014
                    tools = session_checks.orchestrator.TOOLS_BY_SCOPE[body["scope"]]
                    self.runs[run_id] = {"id": run_id, "author": token,
                                         "snapshot": {"identity": {"author_verified": True},
                                                      "status": "route_error" if route_error else "answered_unverified",
                                                      "question_request": {"scope": body["scope"],
                                                                           "year": body["year"]},
                                                      "prompt": {"revision_id": body.get("prompt_revision_id")},
                                                      "verification_criteria": {
                                                          "revision_id": body.get("criteria_revision_id")},
                                                      "model": {"alias": body["model_alias"],
                                                                "generation_confirmed": True,
                                                                "provenance_status": "session_manifest_checked"},
                                                      "evidence_bundle": {"items": [
                                                          {"tool": tool, "record_count": 2}
                                                          for tool in tools]},
                                                      "checks": [{"result": "passed"}]}}
                    return 201, {"id": run_id}
                if path.startswith("/api/runs/"):
                    return 200, self.runs[path.rsplit("/", 1)[1]]
                raise AssertionError(path)

        app = FakeApp()
        checkpoints = []
        report = session_checks.rehearsal(app, ["qwen-base", "ft-finqa-a"], 2020,
                                          {"Nicoli": "hidden", "Vinicius": "hidden"},
                                          journal=lambda data: checkpoints.append(
                                              len(data["created_run_ids"])))
        self.assertEqual(report["state"], "CONFIRMED")
        self.assertEqual(len(report["runs"]), 7)
        self.assertEqual(len(report["revisions"]), 2)
        self.assertEqual(set(run["snapshot"]["question_request"]["scope"]
                             for run in report["runs"] if run["snapshot"]["status"] == "answered_unverified"),
                         {"financeiro", "industrial", "integrado"})
        self.assertEqual(checkpoints[-1], 7)
        self.assertEqual(sum(1 for method, path, _ in app.calls
                             if method == "POST" and path == "/api/runs"), 8)
        self.assertNotIn("hidden", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
