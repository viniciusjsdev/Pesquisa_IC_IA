"""SPEC-011 local diagnostics; no model, database or external request is used."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inference_api" / "src"))
sys.path.insert(0, str(ROOT / "runpod" / "serving"))

from inference_api import models
import diagnose_finqa


MESSAGES = [
    {"role": "system", "content": "Use apenas a evidência."},
    {"role": "user", "content": "Qual é a variação?\n\nEvidência JSON exata:\n{\"valor\": 10}"},
]


def event(alias, content=None, finish=None, usage=None):
    choice = [] if content is None and finish is None else [
        {"index": 0, "delta": {"content": content} if content is not None else {},
         "finish_reason": finish}]
    return ("data: " + json.dumps({"model": alias, "choices": choice, "usage": usage}) + "\n\n").encode()


class DiagnosticsTests(unittest.TestCase):
    def test_preserved_pair_requires_identical_messages(self):
        entries = [{"source_run_id": alias, "body": {"model": alias, "messages": MESSAGES,
                                                       "temperature": 0.2}}
                   for alias in ("ft-finqa-a", "ft-finqa-b")]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "pair.json"
            path.write_text(json.dumps(entries), encoding="utf-8")
            messages, provenance = diagnose_finqa.load_case(path)
            self.assertEqual(messages, MESSAGES)
            self.assertEqual(len(provenance["source_sha256"]), 64)
            entries[1]["body"]["messages"] = [{"role": "user", "content": "different"}]
            path.write_text(json.dumps(entries), encoding="utf-8")
            with self.assertRaises(ValueError):
                diagnose_finqa.load_case(path)

    def test_matrix_changes_declared_factors_and_caps_all_calls(self):
        plan = diagnose_finqa.conditions(MESSAGES, "<chat-rendered>")
        self.assertEqual([item["id"] for item in plan], [
            "C1_chat_02", "C2_chat_00", "C3_chat_serialized_00",
            "C4_finqa_format_00", "C5_finqa_format_32"])
        self.assertEqual(plan[0]["input"], plan[1]["input"])
        self.assertEqual(plan[0]["max_tokens"], plan[1]["max_tokens"])
        self.assertEqual(plan[1]["temperature"], plan[2]["temperature"])
        self.assertEqual(plan[2]["max_tokens"], plan[3]["max_tokens"])
        self.assertEqual(plan[3]["input"], plan[4]["input"])
        self.assertTrue(all(item["max_tokens"] <= 128 for item in plan))
        payload = diagnose_finqa.request_body("ft-finqa-a", plan[3])
        self.assertIn("### Instruction:", payload["prompt"])
        self.assertNotIn("messages", payload)
        self.assertEqual(payload["top_p"], 0.9)
        self.assertEqual(payload["stop"], [])
        self.assertEqual(payload["repetition_penalty"], 1.0)

    def test_raw_stream_keeps_repetition_and_length_as_incomplete(self):
        alias = "ft-finqa-a"
        repeated = "context phrase " * 40
        raw = [event(alias, repeated[:150]), event(alias, repeated[150:], "length"),
               event(alias, usage={"prompt_tokens": 945, "completion_tokens": 3151,
                                   "total_tokens": 4096}), b"data: [DONE]\n\n"]
        response, body = models._read_chat_stream(io.BytesIO(b"".join(raw)), "local", alias, {})
        self.assertEqual(response["choices"][0]["message"]["content"], repeated)
        self.assertEqual(response["choices"][0]["finish_reason"], "length")
        self.assertEqual(response["usage"]["total_tokens"], 4096)
        self.assertEqual(body, b"".join(raw))
        summary = diagnose_finqa.classify(response)
        self.assertFalse(summary["complete"])
        self.assertGreater(summary["max_repeat_of_80_char_block"], 1)

    def test_short_fragment_stops_but_is_only_transport_complete(self):
        alias = "ft-finqa-b"
        raw = [event(alias, "53161.6 , 611785 , 1 .", "stop"), b"data: [DONE]\n\n"]
        response, _ = models._read_chat_stream(io.BytesIO(b"".join(raw)), "local", alias, {})
        summary = diagnose_finqa.classify(response)
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["response_chars"], 22)
        self.assertEqual(summary["tool_call_count"], 0)
        self.assertNotIn("accuracy", summary)

    def test_live_gateway_identity_must_match_receipt(self):
        aliases = ("qwen-base", "ft-finqa-a", "ft-finqa-b")
        manifest = {"base_alias": aliases[0], "adapters": [{"alias": a} for a in aliases[1:]]}
        receipt = {"manifest_sha256": "a" * 64, "base_revision": "b" * 40,
                   "session_id": "session-1", "vllm_version": "test"}
        listing = {"data": [{"id": a, "max_model_len": 4096} for a in aliases]}
        with patch("diagnose_finqa._call", return_value=(listing, dict(receipt))):
            live = diagnose_finqa.live_identity(receipt, manifest, "t" * 32)
        self.assertEqual(live["identity"], receipt)
        self.assertEqual(live["reported_max_model_len"]["ft-finqa-a"], 4096)
        with patch("diagnose_finqa._call", return_value=(listing,
                                                          {**receipt, "session_id": "old"})):
            with self.assertRaisesRegex(ValueError, "Live gateway identity"):
                diagnose_finqa.live_identity(receipt, manifest, "t" * 32)

    def test_http_failure_leaves_attempt_and_partial_summary(self):
        receipt = {"manifest_sha256": "a" * 64, "base_revision": "b" * 40,
                   "session_id": "session-1", "vllm_version": "test"}
        manifest = {"base_alias": "qwen-base", "adapters": []}
        plan = [diagnose_finqa.conditions(MESSAGES, "<rendered>")[0]]
        failure = HTTPError("http://127.0.0.1:8002/v1/chat/completions", 400,
                            "bad request", {}, io.BytesIO(b'{"error":"context"}'))
        with tempfile.TemporaryDirectory() as folder, \
             patch("diagnose_finqa.command", return_value=["--max-model-len", "4096"]), \
             patch("diagnose_finqa.live_identity", return_value={"identity": receipt}), \
             patch("diagnose_finqa.urlopen", side_effect=failure):
            output = Path(folder)
            result = diagnose_finqa.run_matrix(plan, manifest, receipt, {"source_sha256": "c" * 64},
                                               output, 30, "t" * 32)
            attempt = json.loads((output / "C1_chat_02-qwen-base.json").read_text())
            saved = json.loads((output / "summary.json").read_text())
        self.assertEqual(result["status"], "partial_failed")
        self.assertEqual(saved["completed_calls"], 1)
        self.assertEqual(attempt["status"], "failed")
        self.assertEqual(attempt["error"]["http_status"], 400)
        self.assertIn("gateway_before", attempt)


if __name__ == "__main__":
    unittest.main()
