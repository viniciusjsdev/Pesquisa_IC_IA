"""SPEC-012: OpenAI Responses contract, simulated transport and data isolation."""
import io
import json
import os
import sys
import threading
import unittest
from contextlib import nullcontext
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from inference_api import synthetic_data, jobs, models, openai_provider, server, service
from inference_api.auth import Principal

PRINCIPAL = Principal("00000000-0000-0000-0000-000000000001", "Nicoli")
SYNTHETIC = {"provider": "openai", "model_alias": "openai", "evidence_mode": "synthetic_snapshot",
             "system_prompt": 'Responda apenas com a fixture inventada. Cite o ano e indique que os dados são sintéticos.'}


class Stream:
    headers = {"Content-Type": "text/event-stream", "x-request-id": "req_fixture"}

    def __init__(self, result, complete=True):
        self.events = [b"data: " + json.dumps({"type": "response.created"}).encode() + b"\n"]
        if complete:
            self.events.append(b"data: " + json.dumps({"type": "response.completed", "response": result}).encode() + b"\n")

    def __enter__(self): return self
    def __exit__(self, *_): return None
    def __iter__(self): return iter(self.events)


def response(output, **changes):
    return {**{"id": "resp_fixture", "model": openai_provider.MODEL, "status": "completed",
               "usage": {"input_tokens": 30, "output_tokens": 12}, "output": output}, **changes}


def answer(text):
    return {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]}


class OpenAITests(unittest.TestCase):
    def test_output_limit_omitted_only_when_explicitly_requested(self):
        messages = [{"role": "system", "content": "fixture"},
                    {"role": "user", "content": "fixture"}]
        for omit in (False, True):
            with self.subTest(omit=omit), \
                 patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fixture-secret"}), \
                 patch("inference_api.models.urlopen", return_value=Stream(response([answer("ok")]))) as opener:
                _, metadata = openai_provider.Conversation().chat_turn(
                    messages, 0, None, tools=None, omit_output_token_limit=omit)
                payload = json.loads(opener.call_args.args[0].data)
                if omit:
                    self.assertNotIn("max_output_tokens", payload)
                    self.assertIsNone(metadata["max_output_tokens"])
                else:
                    self.assertEqual(payload["max_output_tokens"], 4096)
        with patch("inference_api.models.urlopen") as opener:
            with self.assertRaises(ValueError):
                openai_provider.Conversation().chat_turn(
                    messages, 0, 100, tools=None, omit_output_token_limit=True)
            opener.assert_not_called()

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    def test_responses_stream_stateless_tool_choice_and_no_secret_in_receipt(self):
        call = {"type": "function_call", "call_id": "call_fixture", "name": "synthetic_metric",
                "arguments": '{"year":2020}'}
        reasoning = {"type": "reasoning", "id": "rs_fixture", "encrypted_content": "opaque_fixture"}
        conversation = openai_provider.Conversation()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fixture-secret"}), \
             patch("inference_api.models.urlopen", side_effect=[Stream(response([reasoning, call])),
                                                         Stream(response([answer("Valor inventado: 42")]))]) as opener:
            messages = [{"role": "system", "content": "Fixture only"},
                        {"role": "user", "content": "Qual o valor?"}]
            first, receipt = conversation.chat_turn(messages, .2, None, tools=synthetic_data.catalog())
            self.assertEqual(first["tool_calls"][0]["function"]["name"], "synthetic_metric")
            self.assertEqual(receipt["request_id"], "req_fixture")
            self.assertEqual(receipt["usage"]["output_tokens"], 12)
            messages += [first, {"role": "tool", "tool_call_id": "call_fixture", "content": '{"value":42}'}]
            second, _ = conversation.chat_turn(messages, .2, None, tools=synthetic_data.catalog())
            self.assertIn("42", second["content"])
        request1 = json.loads(opener.call_args_list[0].args[0].data)
        request2 = json.loads(opener.call_args_list[1].args[0].data)
        self.assertEqual(opener.call_args_list[0].args[0].full_url, openai_provider.ENDPOINT)
        self.assertFalse(request1["store"])
        self.assertTrue(request1["stream"])
        self.assertEqual(request1["reasoning"]["effort"], "medium")
        self.assertNotIn("temperature", request1)
        self.assertEqual(request1["tools"][0]["name"], "synthetic_metric")
        self.assertEqual(request1["tool_choice"], "auto")
        self.assertFalse(request1["parallel_tool_calls"])
        self.assertEqual(request2["input"][-1], {"type": "function_call_output",
                         "call_id": "call_fixture", "output": '{"value":42}'})
        self.assertIn(reasoning, request2["input"])
        self.assertNotIn("secret", json.dumps(receipt))

    def test_model_mismatch_and_request_ids_remain_in_sanitized_failure(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fixture-secret"}), \
             patch("inference_api.models.urlopen", return_value=Stream(response(
                 [answer("wrong model")], model="other-model"))), \
             self.assertRaises(openai_provider.OpenAIError) as caught:
            openai_provider.Conversation().chat_turn([{"role": "system", "content": "x"},
                {"role": "user", "content": "x"}], .2, None, tools=None)
        self.assertEqual(caught.exception.status, "provider_model_mismatch")
        self.assertEqual(caught.exception.metadata["served_model"], "other-model")
        self.assertEqual(caught.exception.metadata["response_id"], "resp_fixture")
        self.assertEqual(caught.exception.metadata["request_id"], "req_fixture")
    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    def test_http_errors_partial_and_context_limit_are_sanitized(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fixture-secret"}):
            for code, status in [(401, "provider_auth_error"), (403, "provider_auth_error"),
                                 (429, "provider_rate_limited"), (500, "provider_error")]:
                error = HTTPError(openai_provider.ENDPOINT, code, "private secret",
                                  {"Retry-After": "12", "x-request-id": "req_http"}, io.BytesIO())
                with self.subTest(code=code), patch("inference_api.models.urlopen", side_effect=error), \
                     self.assertRaises(openai_provider.OpenAIError) as caught:
                    openai_provider.Conversation().chat_turn([{"role": "system", "content": "x"},
                        {"role": "user", "content": "x"}], .2, None, tools=None)
                self.assertEqual(caught.exception.status, status)
                self.assertEqual(caught.exception.metadata["request_id"], "req_http")
                self.assertNotIn("private", str(caught.exception))
            with patch("inference_api.models.urlopen", return_value=Stream(response([answer("partial")]), False)), \
                 self.assertRaises(openai_provider.OpenAIError) as caught:
                openai_provider.Conversation().chat_turn([{"role": "system", "content": "x"},
                    {"role": "user", "content": "x"}], .2, None, tools=None)
            self.assertEqual(caught.exception.status, "stream_incomplete")
            incomplete = response([], status="incomplete", incomplete_details={"reason": "max_output_tokens"})
            with patch("inference_api.models.urlopen", return_value=Stream(incomplete)), \
                 self.assertRaises(openai_provider.OpenAIError) as caught:
                openai_provider.Conversation().chat_turn([{"role": "system", "content": "x"},
                    {"role": "user", "content": "x"}], .2, None, tools=None)
            self.assertEqual(caught.exception.status, "context_limit")
            exhausted = HTTPError(openai_provider.ENDPOINT, 429, "private",
                                  {}, io.BytesIO(json.dumps({"error": {
                                      "code": "credit_balance_exhausted", "message": "private"}}).encode()))
            with patch("inference_api.models.urlopen", side_effect=exhausted), \
                 self.assertRaises(openai_provider.OpenAIError) as caught:
                openai_provider.Conversation().chat_turn([{"role": "system", "content": "x"},
                    {"role": "user", "content": "x"}], .2, None, tools=None)
            self.assertEqual(caught.exception.status, "provider_quota_exhausted")
            self.assertNotIn("private", str(caught.exception))
            for event, status in [
                ({"type": "response.incomplete", "response": {
                    "incomplete_details": {"reason": "max_output_tokens"}}}, "context_limit"),
                ({"type": "response.failed", "response": {"error": {
                    "code": "credit_balance_exhausted", "message": "private"}}}, "provider_quota_exhausted")]:
                with self.subTest(event=event["type"]), self.assertRaises(openai_provider.OpenAIError) as caught:
                    openai_provider._read_stream([b"data: " + json.dumps(event).encode() + b"\n"])
                self.assertEqual(caught.exception.status, status)
                self.assertNotIn("private", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
