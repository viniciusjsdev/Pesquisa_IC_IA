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
from inference_api.auth import Principal
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
        with patch("inference_api.service.storage.create_run", side_effect=lambda _a, s: s), \
             patch("inference_api.service.config.vllm_url", return_value="https://model.example"):
            return service.execute_run(payload, PRINCIPAL)

    def test_mode_and_cross_mode_rejected_before_dependencies(self):
        for change in ({}, {"evidence_mode": "bad"},
                       {"evidence_mode": "dw_tools", "question": "Q", "scope": "financeiro"},
                       {"evidence_mode": "dw_snapshot", "case_id": "x", "packet_sha256": "a" * 64, "question": "Q"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                service._validate_input({**BASE, **change})
        self.assertEqual(service._validate_input({**BASE, "evidence_mode": "dw_tools", "question": "Q"})[0], "dw_tools")

    def test_private_packet_hash_bytes_and_tamper(self):
        with patch("inference_api.evidence_packets.packet_directory", return_value=self.root):
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

    def test_snapshot_uses_exact_packet_question_and_json(self):
        with patch("inference_api.evidence_packets.packet_directory", return_value=self.root), \
             patch("inference_api.service.models.chat_turn", return_value=turn({"role": "assistant", "content": "Resposta"})) as chat:
            run = self.run_saved({**BASE, "evidence_mode": "dw_snapshot",
                                  "case_id": "integrated-1", "packet_sha256": self.packet["sha256"]})
        self.assertEqual(run["schema_version"], 3)
        self.assertEqual(run["status"], "answered_unverified")
        self.assertEqual(run["question_request"]["question"], fixture_case()["question"])
        self.assertEqual(base64.b64decode(run["packet"]["bytes_b64"]), self.packet_bytes)
        self.assertEqual(run["evidence_json_sent"].encode(), self.packet_bytes)
        self.assertIn(self.packet_bytes.decode(), chat.call_args.args[1][1]["content"])
        self.assertIsNone(chat.call_args.kwargs["tools"])

    def test_model_chooses_tool_and_result_is_returned(self):
        call = {"id": "call-1", "type": "function", "function": {
            "name": "product", "arguments": '{"year":2020,"id":1000001}'}}
        with patch("inference_api.service.dw_tools.availability", return_value=DW), \
             patch("inference_api.service.dw_tools.execute", return_value=RESULT) as query, \
             patch("inference_api.service.models.chat_turn", side_effect=[
                 turn({"role": "assistant", "content": None, "tool_calls": [call]}),
                 turn({"role": "assistant", "content": "Resposta sustentada"})]) as chat:
            run = self.run_saved({**BASE, "evidence_mode": "dw_tools", "question": "Pergunta livre"})
        self.assertEqual(run["status"], "answered_unverified")
        query.assert_called_once_with("product", {"year": 2020, "id": 1000001},
                                      expected_fingerprint="a" * 64)
        self.assertEqual(run["tool_trace"][0]["raw_request"], call)
        self.assertEqual(run["tool_trace"][0]["result"], RESULT)
        self.assertEqual(chat.call_args_list[0].kwargs["tools"], dw_tools.catalog())
        self.assertEqual(chat.call_args_list[1].args[1][-1]["role"], "tool")
        self.assertEqual(chat.call_args_list[1].kwargs["session_id"], "session-1")

    def test_tool_protocol_and_no_evidence_fail_closed(self):
        for message, expected in [({"role": "assistant", "content": "Sem consulta"}, "insufficient_evidence"),
                                  ({"role": "assistant", "tool_calls": [{"id": "x", "type": "function", "function": {"name": "DELETE", "arguments": "{}"}}]}, "tool_error"),
                                  ({"role": "assistant", "tool_calls": []}, "tool_protocol_error")]:
            with self.subTest(message=message), \
                 patch("inference_api.service.dw_tools.availability", return_value=DW), \
                 patch("inference_api.service.dw_tools.execute") as query, \
                 patch("inference_api.service.models.chat_turn", return_value=turn(message)):
                run = self.run_saved({**BASE, "evidence_mode": "dw_tools", "question": "Q"})
            self.assertEqual(run["status"], expected)
            query.assert_not_called()

    def test_dw_unavailable_does_not_call_model(self):
        with patch("inference_api.service.dw_tools.availability", return_value={"available": False, "reason": "DW unavailable"}), \
             patch("inference_api.service.models.chat_turn") as chat:
            run = self.run_saved({**BASE, "evidence_mode": "dw_tools", "question": "Q"})
        self.assertEqual(run["status"], "dw_unavailable")
        chat.assert_not_called()

    def test_post_validation_query_and_limit_failures_are_distinct(self):
        call = {"id": "call-1", "type": "function", "function": {
            "name": "product", "arguments": '{"year":2020,"id":1000001}'}}
        tool_turn = turn({"role": "assistant", "content": None, "tool_calls": [call]})
        for effect, status, stage in [
            (dw_tools.DWFingerprintError("changed"), "query_error", "query"),
            (dw_tools.DWResultLimitError("too large"), "tool_limit_error", "limit"),
            (RuntimeError("database offline"), "query_error", "query"),
        ]:
            with self.subTest(effect=type(effect).__name__), \
                 patch("inference_api.service.dw_tools.availability", return_value=DW), \
                 patch("inference_api.service.dw_tools.execute", side_effect=effect), \
                 patch("inference_api.service.models.chat_turn", return_value=tool_turn):
                run = self.run_saved({**BASE, "evidence_mode": "dw_tools", "question": "Q"})
            self.assertEqual((run["status"], run["error"]["stage"]), (status, stage))
            self.assertEqual(run["tool_trace"][0]["status"], "failed")
            self.assertEqual(run["tool_trace"][0]["validated_arguments"], {"year": 2020, "id": 1000001})

    def test_cumulative_budget_and_call_turn_limit(self):
        calls = [{"id": f"call-{index}", "type": "function", "function": {
            "name": "product", "arguments": '{"year":2020,"id":1000001}'}}
            for index in range(1, 7)]
        turns = [turn({"role": "assistant", "content": None, "tool_calls": [call]}) for call in calls]
        with patch("inference_api.service.dw_tools.availability", return_value=DW), \
             patch("inference_api.service.dw_tools.execute", return_value=RESULT) as query, \
             patch("inference_api.service.models.chat_turn", side_effect=turns):
            run = self.run_saved({**BASE, "evidence_mode": "dw_tools", "question": "Q"})
        self.assertEqual(run["status"], "tool_protocol_error")
        self.assertEqual(query.call_count, 5)
        self.assertEqual(len(run["model_turns"]), 6)
        with patch("inference_api.service.dw_tools.availability", return_value=DW), \
             patch("inference_api.service.dw_tools.execute", return_value=RESULT), \
             patch("inference_api.service.models.chat_turn", return_value=turns[0]), \
             patch("inference_api.service.dw_tools.MAX_BYTES", 1):
            limited = self.run_saved({**BASE, "evidence_mode": "dw_tools", "question": "Q"})
        self.assertEqual((limited["status"], limited["error"]["stage"]), ("tool_limit_error", "limit"))
        self.assertEqual(limited["tool_trace"][0]["status"], "failed")

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
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self): return json.dumps({"model": "qwen-base", "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "A"}}]}).encode()
        def open_request(request, timeout):
            sent.append(json.loads(request.data))
            return Response()
        identity = {"manifest_sha256": "a" * 64, "base_revision": "b" * 40, "session_id": "s"}
        with patch("inference_api.models.vllm_url", return_value="https://model.example"), \
             patch("inference_api.models.available_models", return_value={"qwen-base": {"available": True, "session_id": "s"}}), \
             patch("inference_api.models.urlopen", side_effect=open_request), \
             patch("inference_api.models.serving_catalog.response_identity", return_value=identity):
            _, record = models.chat_turn("qwen-base", [{"role": "user", "content": "Q"}], 0, 64,
                                         tools=dw_tools.catalog(), session_id="s")
            self.assertEqual(record["session_id"], "s")
            self.assertEqual(sent[0]["tool_choice"], "auto")
            self.assertIs(sent[0]["parallel_tool_calls"], False)
            with self.assertRaises(models.ModelResponseError):
                models.chat_turn("qwen-base", [], 0, 64, tools=None, session_id="other")


if __name__ == "__main__":
    unittest.main()
