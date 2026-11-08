"""SPEC-009: explicit Bancada modes, packet integrity and model-selected DW tools."""
import base64
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inference_api" / "src"))
sys.path.insert(0, str(ROOT))

from inference_api import dw_tools, evidence_packets, models, service
from inference_api.identity.auth import Principal
from model_evaluation import export
from model_evaluation.tests.test_export import fixture_case, fixture_report, fixture_query

PRINCIPAL = Principal("00000000-0000-0000-0000-000000000001", "Nicoli")
BASE = {"model_alias": "qwen-base", "system_prompt": "Use dados.", "criteria": {
    "schema_version": 1, "require_evidence": True, "require_period": True,
    "required_units": [], "require_cited_ids": False, "required_caveats": []}}
DW = {"available": True, "database": "db_pesquisa_dw", "schema_version": 1,
      "query_contract_version": 1, "source_fingerprint": "a" * 64,
      "query_code_sha256": "b" * 64}
RESULT = fixture_query("product", 2020, 1000001)


def turn(message):
    return message, {"session_id": "session-1", "served_model": "qwen-base",
                     "raw_response": {"choices": [{"message": message}]},
                     "base_revision": "a" * 40, "provenance_status": "session_manifest_checked"}


class ModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "packets"
        self.root.mkdir()
        code = Path(self.temp.name) / "code.py"
        code.write_text("fixed query fixture", encoding="utf-8")
        packet = export.build_packets([fixture_case()], verify_fn=fixture_report,
                                      query_fn=fixture_query, query_code_path=code)["integrated-1"]
        (self.root / "integrated-1.json").write_bytes(packet)
        self.packet = json.loads(packet)
        self.packet_bytes = packet

    def run_saved(self, payload, **patches):
        with patch("inference_api.executions.service.storage.create_run", side_effect=lambda _a, s: s), \
             patch("inference_api.executions.service.config.vllm_url", return_value="https://model.example"):
            return service.execute_run(payload, PRINCIPAL)

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    def test_private_packet_hash_bytes_and_tamper(self):
        with patch("inference_api.evidence.evidence_packets.packet_directory", return_value=self.root):
            listing = evidence_packets.list_packets()
            self.assertEqual(listing[0]["sha256"], self.packet["sha256"])
            selected, raw = evidence_packets.select_packet("integrated-1", self.packet["sha256"])
            self.assertEqual(raw, self.packet_bytes)
            self.assertEqual(selected["body"]["question"], fixture_case()["question"])
            with self.assertRaises(ValueError):
                evidence_packets.select_packet("integrated-1", "0" * 64)
            path = self.root / "integrated-1.json"
            path.write_bytes(raw + b" ")
            with self.assertRaises(ValueError):
                evidence_packets.list_packets()

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    def test_strict_tool_arguments(self):
        for name, args in [("financial", {"year": 2020, "id": 1}), ("machine", {"year": 2020}),
                           ("machine", {"year": True, "id": 1}), ("machine", {"year": 2020, "id": -1}),
                           ("sql", {"year": 2020})]:
            with self.subTest(name=name, args=args), self.assertRaises(ValueError):
                dw_tools.validate_call(name, args)
        self.assertEqual(dw_tools.validate_call("financial", {"year": 2020}), {"year": 2020})

    def test_chat_turn_sends_auto_choice_and_checks_session(self):
        sent = []
        class Response:
            headers = {"Content-Type": "text/event-stream"}
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def __iter__(self):
                yield b'data: {"model":"qwen-base","choices":[{"index":0,"delta":{"role":"assistant","content":"A"},"finish_reason":null}]}\n'
                yield b'data: {"model":"qwen-base","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n'
                yield b'data: [DONE]\n'
        def open_request(request, timeout):
            sent.append(json.loads(request.data))
            return Response()
        identity = {"manifest_sha256": "a" * 64, "base_revision": "b" * 40, "session_id": "s"}
        with patch("inference_api.model_service.models.vllm_url", return_value="https://model.example"), \
             patch("inference_api.model_service.models.available_models", return_value={"qwen-base": {"available": True, "session_id": "s"}}), \
             patch("inference_api.model_service.models.urlopen", side_effect=open_request), \
             patch("inference_api.model_service.models.serving_catalog.response_identity", return_value=identity):
            _, record = models.chat_turn("qwen-base", [{"role": "user", "content": "Q"}], 0, None,
                                         tools=dw_tools.catalog(), session_id="s")
            self.assertEqual(record["session_id"], "s")
            self.assertEqual(sent[0]["tool_choice"], "auto")
            self.assertIs(sent[0]["parallel_tool_calls"], False)
            self.assertNotIn("max_tokens", sent[0])
            self.assertTrue(sent[0]["stream"])
            self.assertEqual(record["raw_response_format"], "sse")
            models.chat_turn("qwen-base", [{"role": "user", "content": "Q"}], 0, 2048,
                             tools=None, session_id="s")
            self.assertEqual(sent[1]["max_tokens"], 2048)
            with self.assertRaises(models.ModelResponseError):
                models.chat_turn("qwen-base", [], 0, 64, tools=None, session_id="other")


if __name__ == "__main__":
    unittest.main()
