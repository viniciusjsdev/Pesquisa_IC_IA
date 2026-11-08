"""The real-data pilot must fail before a durable job or provider call."""

import json
import os
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch
from uuid import uuid4


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from inference_api import server, service  # noqa: E402
from inference_api.agent_harness import real_pilot  # noqa: E402
from inference_api.agent_harness.real_pilot import PROTOCOL_PROMPT  # noqa: E402
from inference_api.identity.auth import Principal  # noqa: E402


class PilotHttpGateTests(unittest.TestCase):
    def test_real_pilot_spaces_groq_calls_without_retry(self):
        envelope = {"role": "analista_pergunta"}
        contract = {"task": "teste", "schema": {"type": "object"}}
        with patch.object(real_pilot, "require_external_approval"), \
             patch.object(real_pilot.groq, "chat_turn", return_value=(
                 {"content": "{}"}, {"served_model": "qwen/qwen3.8-27b"})) as chat, \
             patch.object(real_pilot.time, "monotonic", side_effect=[0, 0, 20]), \
             patch.object(real_pilot.time, "sleep") as sleep:
            call = real_pilot.make_groq_model_call("qwen/qwen3.8-27b", PROTOCOL_PROMPT)
            call("analista_pergunta", envelope, contract)
            call("analista_pergunta", envelope, contract)
            self.assertEqual(chat.call_count, 2)
            sleep.assert_called_once_with(real_pilot.PILOT_MIN_CALL_SPACING_SECONDS)

    def test_real_data_gate_binds_exact_reviewed_bytes(self):
        with patch.dict(os.environ, {"INFERENCE_SPEC013_GROQ_REAL_DATA": "1"}):
            real_pilot.require_external_approval()
            with TemporaryDirectory() as temporary:
                changed = Path(temporary) / "changed-review.md"
                changed.write_bytes(real_pilot.REVIEW_PATH.read_bytes() + b"\nnew scope")
                with patch.object(real_pilot, "REVIEW_PATH", changed):
                    with self.assertRaisesRegex(ValueError, "does not match"):
                        real_pilot.require_external_approval()

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    def test_persistence_failure_keeps_private_trace(self):
        run_id = str(uuid4())
        snapshot = {"harness_result": {"run_id": run_id, "trace": [{"role": "analista_pergunta"}]}}
        with TemporaryDirectory() as temporary, patch.object(real_pilot, "ROOT", Path(temporary)):
            target = real_pilot.preserve_failed_persistence(snapshot, OSError("db unavailable"))
            saved = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "persistence_uncertain")
            self.assertEqual(saved["error_type"], "OSError")
            self.assertEqual(saved["snapshot"], snapshot)
            self.assertNotIn("db unavailable", target.read_text(encoding="utf-8"))

    def test_authenticated_submission_is_blocked_before_job_creation(self):
        class Quiet(server.Handler):
            def log_message(self, *_):
                pass

        http = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        body = {"provider": "groq", "evidence_mode": "agent_harness_pilot",
                "model_alias": "groq_harness_pilot", "question": "Pergunta de teste",
                "system_prompt": PROTOCOL_PROMPT, "request_key": str(uuid4())}
        request = Request(f"http://127.0.0.1:{http.server_port}/api/run-jobs",
                          data=json.dumps(body).encode("utf-8"), method="POST",
                          headers={"Content-Type": "application/json",
                                   "Authorization": "Bearer fixture"})
        try:
            with patch.dict(os.environ, {"INFERENCE_SPEC013_GROQ_REAL_DATA": "0"}), \
                 patch("inference_api.api.server.auth.authenticate",
                       return_value=Principal(str(uuid4()), "Researcher")), \
                 patch("inference_api.persistence.storage.create_job",
                       side_effect=AssertionError("job created")), \
                 patch("inference_api.model_service.groq.chat_turn",
                       side_effect=AssertionError("provider called")):
                with self.assertRaises(HTTPError) as raised:
                    urlopen(request, timeout=5)
                self.assertEqual(raised.exception.code, 400)
                self.assertIn("legacy_execution_mode_retired", json.load(raised.exception)["error"])
        finally:
            http.shutdown()
            http.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
