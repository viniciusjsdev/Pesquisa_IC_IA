import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
"""Retained synthetic-data and provider checks; old engine tests archived by SPEC-015."""
import json, os, unittest
from unittest.mock import patch
from inference_api.agent_harness.synthetic_demo import fixture_query
from inference_api import groq


class HarnessTests(unittest.TestCase):
    def test_synthetic_fixture_applies_plan_filters(self):
        industrial = {"fonte_id": "dw_paradas", "campos": ["minutos_parada"],
                      "filtros": {"linha": "L1", "ano": 2020}}
        financial = {"fonte_id": "fin_resultado", "campos": ["data", "lucro_liquido"],
                     "filtros": {"data": {"from": "2020-01-01", "to": "2021-01-01"}}}
        self.assertEqual(fixture_query(industrial)["rows"][0]["minutos_parada"], 45)
        self.assertEqual(fixture_query(financial)["rows"][0]["lucro_liquido"], 1200)
        self.assertEqual(fixture_query({**industrial, "filtros": {"ano": 2019}})["coverage"]["state"],
                         "no_observation")
        self.assertEqual(fixture_query({**financial, "filtros": {"data": {"from": "2021-01-01", "to": "2022-01-01"}}})["rows"], [])
        with self.assertRaisesRegex(ValueError, "unsupported_synthetic_filter"):
            fixture_query({**industrial, "filtros": {"sql": "SELECT *"}})

    def test_groq_harness_transport_sends_qwen_not_general_groq_model(self):
        requested = []
        model_id = "qwen/qwen3.8-27b"
        first = {"model": model_id, "choices": [{"index": 0, "delta": {"content": "{}"},
                                                   "finish_reason": None}]}
        last = {"model": model_id, "choices": [{"index": 0, "delta": {},
                                                  "finish_reason": "stop"}], "usage": {"total_tokens": 5}}

        class Stream:
            headers = {"Content-Type": "text/event-stream"}
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def __iter__(self):
                return iter([b"data: " + json.dumps(item).encode() + b"\n" for item in (first, last)] +
                            [b"data: [DONE]\n"])

        def urlopen(request, timeout):
            requested.append(json.loads(request.data))
            return Stream()

        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture-key",
                                  "GROQ_MODEL": "openai/gpt-oss-120b",
                                  "GROQ_HARNESS_MODEL": model_id}), \
             patch("inference_api.model_service.groq.models.urlopen", side_effect=urlopen):
            message, metadata = groq.chat_turn([{"role": "user", "content": "fixture"}],
                                               0, 900, tools=None, harness_model=model_id)
        self.assertEqual(requested[0]["model"], model_id)
        self.assertEqual(message["content"], "{}")
        self.assertEqual(metadata["served_model"], model_id)

if __name__=="__main__": unittest.main()
