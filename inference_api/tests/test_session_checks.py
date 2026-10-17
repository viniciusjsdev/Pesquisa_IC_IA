"""Local session preflight after SPEC-009; no paid or external generation."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inference_api"))
import session_checks


class SessionChecksTests(unittest.TestCase):
    def test_preflight_reads_dw_and_never_opens_external_http(self):
        with patch.object(session_checks, "_git", return_value={"head": "abc"}), \
             patch.object(session_checks, "_dw", return_value={"database": "db_pesquisa_dw", "transaction_read_only": True}), \
             patch.object(session_checks, "_app", return_value={"schema_versions": [1, 2]}), \
             patch.object(session_checks, "_artifacts", return_value={"adapter_count": 6}), \
             patch.object(session_checks, "_serving_config", return_value={"network_call": False}), \
             patch.object(session_checks, "_limits", return_value={"global_concurrent_inferences": 1}), \
             patch.object(session_checks, "build_opener", side_effect=AssertionError("external HTTP")):
            result = session_checks.preflight()
        self.assertEqual(result["state"], "CONFIRMED")
        self.assertEqual(len(result["checks"]), 6)
        self.assertEqual(result["checks"][1]["component"], "db_pesquisa_dw")
        self.assertEqual(result["remote_generation"], "not_run")

    def test_preflight_failure_does_not_leak_connection_details(self):
        with patch.object(session_checks, "_git", return_value={"head": "abc"}), \
             patch.object(session_checks, "_dw", side_effect=RuntimeError("secret-host")), \
             patch.object(session_checks, "_app", return_value={}), \
             patch.object(session_checks, "_artifacts", return_value={}), \
             patch.object(session_checks, "_serving_config", return_value={}), \
             patch.object(session_checks, "_limits", return_value={}):
            result = session_checks.preflight()
        self.assertEqual(result["state"], "BLOCKED")
        self.assertNotIn("secret-host", json.dumps(result))

    def test_legacy_rehearsal_command_is_retired(self):
        with patch.object(sys, "argv", ["session_checks.py", "rehearsal"]), \
             self.assertRaises(SystemExit) as stopped:
            session_checks.main()
        self.assertEqual(stopped.exception.code, 2)

    def test_tunnel_probe_only_checks_app_routes(self):
        class Response:
            def __init__(self, status): self.status = status
            def read(self, _limit): return b""
            def close(self): pass
        class Opener:
            def __init__(self): self.paths = []
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
            session_checks.tunnel_probe("http://other.example")


if __name__ == "__main__":
    unittest.main()
