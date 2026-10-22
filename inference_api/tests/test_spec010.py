"""SPEC-010 synthetic provider and same-origin browser session regression tests."""
import json
import io
import os
import sys
import threading
import unittest
from http.cookiejar import CookieJar
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from inference_api import groq, models, server, service
from inference_api.auth import Principal

PRINCIPAL = Principal("00000000-0000-0000-0000-000000000001", "Nicoli")
GROQ_INPUT = {"provider": "groq", "model_alias": "groq", "evidence_mode": "synthetic_snapshot",
              "system_prompt": service.SYNTHETIC_PROMPT}


class Stream:
    headers = {"Content-Type": "text/event-stream"}

    def __init__(self, chunks):
        self.chunks = chunks

    def __enter__(self): return self
    def __exit__(self, *_): return None
    def __iter__(self): return iter(self.chunks)


def sse(message="fixture", finish="stop", complete=True):
    chunks = [json.dumps({"model": "fixture-model", "choices": [{"index": 0,
               "delta": {"content": message}, "finish_reason": None}]}).encode() + b"\n"]
    chunks += [json.dumps({"model": "fixture-model", "choices": [{"index": 0,
               "delta": {}, "finish_reason": finish}], "usage": {"prompt_tokens": 9,
               "completion_tokens": 2}}).encode() + b"\n"]
    return [b"data: " + chunk for chunk in chunks] + ([b"data: [DONE]\n"] if complete else [])


class GroqTests(unittest.TestCase):
    def test_configuration_and_private_modes_fail_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(groq.configuration()["available"])
        for change in ({"evidence_mode": "dw_snapshot", "case_id": "private", "packet_sha256": "a" * 64},
                       {"evidence_mode": "dw_tools", "question": "private"},
                       {"system_prompt": "private"}, {"question": "private"},
                       {"criteria": {"required_caveats": ["private"]}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                service._validate_input({**GROQ_INPUT, **change})

    def test_synthetic_packet_and_tool_choice_never_touch_private_sources(self):
        call = {"id": "call-1", "type": "function", "function": {
            "name": "synthetic_metric", "arguments": '{"year":2020}'}}
        response = {"provider": "groq", "model_id": "fixture-model", "served_model": "fixture-model",
                    "usage": {"prompt_tokens": 9, "completion_tokens": 2}}
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture-key", "GROQ_MODEL": "fixture-model"}), \
             patch("inference_api.service.storage.create_run", side_effect=lambda _a, snap: snap), \
             patch("inference_api.service.evidence_packets.select_packet", side_effect=AssertionError("private packet")), \
             patch("inference_api.service.dw_tools.availability", side_effect=AssertionError("private DW")), \
             patch("inference_api.service.dw_tools.execute", side_effect=AssertionError("private DW")), \
             patch("inference_api.service.groq.chat_turn", side_effect=[
                 ({"role": "assistant", "content": "Fictício"}, response),
                 ({"role": "assistant", "content": None, "tool_calls": [call]}, response),
                 ({"role": "assistant", "content": "Valor inventado: 42"}, response)]) as chat:
            packet = service.execute_run(GROQ_INPUT, PRINCIPAL)
            tools = service.execute_run({**GROQ_INPUT, "evidence_mode": "synthetic_tools"}, PRINCIPAL)
        self.assertEqual((packet["status"], tools["status"]), ("answered_unverified", "answered_unverified"))
        self.assertEqual(packet["schema_version"], 4)
        self.assertEqual(packet["model"]["model_id"], "fixture-model")
        self.assertNotIn("base_revision", packet["model"])
        self.assertEqual(packet["evidence_source"]["kind"], "synthetic_fixture")
        self.assertIn("synthetic fixture", packet["checks"][0]["detail"])
        self.assertNotIn("DW", json.dumps(packet["checks"]))
        self.assertEqual(tools["tool_trace"][0]["raw_request"], call)
        self.assertEqual(tools["tool_trace"][0]["result"]["rows"][0]["value"], 42)
        self.assertEqual(chat.call_args_list[1].kwargs["tools"][0]["function"]["name"], "synthetic_metric")

    def test_stream_success_rate_limit_length_and_partial(self):
        from urllib.error import HTTPError
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture-key", "GROQ_MODEL": "fixture-model"}), \
             patch("inference_api.models.urlopen", return_value=Stream(sse())) as opener:
            message, receipt = groq.chat_turn([{"role": "user", "content": "synthetic"}], .2, None, tools=None)
            self.assertEqual(message["content"], "fixture")
            self.assertEqual(receipt["usage"]["prompt_tokens"], 9)
            self.assertEqual(opener.call_args.args[0].full_url, groq.ENDPOINT)
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture-key", "GROQ_MODEL": "fixture-model"}):
            for response, status in [(Stream(sse(finish="length")), "context_limit"),
                                     (Stream(sse(complete=False)), "stream_incomplete")]:
                with self.subTest(status=status), patch("inference_api.models.urlopen", return_value=response), \
                     self.assertRaises(groq.GroqError) as caught:
                    groq.chat_turn([], .2, None, tools=None)
                self.assertEqual(caught.exception.status, status)
                if status == "context_limit":
                    self.assertEqual(caught.exception.metadata["usage"]["completion_tokens"], 2)
                    self.assertEqual(caught.exception.metadata["finish_reason"], "length")
            error = HTTPError(groq.ENDPOINT, 429, "limit", {"Retry-After": "12"}, None)
            with patch("inference_api.models.urlopen", side_effect=error), self.assertRaises(groq.GroqError) as caught:
                groq.chat_turn([], .2, None, tools=None)
            self.assertEqual((caught.exception.status, caught.exception.retry_after), ("provider_rate_limited", "12"))
            for code, status in [(400, "provider_bad_request"), (401, "provider_auth_error"),
                                 (500, "provider_error")]:
                with self.subTest(code=code), patch("inference_api.models.urlopen",
                      side_effect=HTTPError(groq.ENDPOINT, code, "private upstream detail", {}, None)), \
                     self.assertRaises(groq.GroqError) as caught:
                    groq.chat_turn([], .2, None, tools=None)
                self.assertEqual(caught.exception.status, status)
                self.assertNotIn("private upstream detail", str(caught.exception))
            for body, status in [({"error": {"code": "context_length_exceeded", "message": "private"}}, "context_limit"),
                                 ({"error": {"type": "invalid_request_error", "failed_generation": {"attempted_arguments": "private"}}}, "provider_tool_error")]:
                response = HTTPError(groq.ENDPOINT, 400, "private", {}, io.BytesIO(json.dumps(body).encode()))
                with self.subTest(status=status), patch("inference_api.models.urlopen", side_effect=response), \
                     self.assertRaises(groq.GroqError) as caught:
                    groq.chat_turn([], .2, None, tools=None)
                self.assertEqual(caught.exception.status, status)
                self.assertNotIn("private", str(caught.exception))

    def test_failed_snapshot_keeps_provider_identity_and_retry_metadata(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture-key", "GROQ_MODEL": "fixture-model"}), \
             patch("inference_api.service.storage.create_run", side_effect=lambda _a, snap: snap), \
             patch("inference_api.service.groq.chat_turn", side_effect=groq.GroqError(
                 "provider_rate_limited", "Groq HTTP 429", "12")) as chat:
            run = service.execute_run(GROQ_INPUT, PRINCIPAL)
        chat.assert_called_once()
        self.assertEqual(run["status"], "provider_rate_limited")
        self.assertEqual(run["error"]["retry_after"], "12")
        self.assertEqual(run["provider"], "groq")
        self.assertEqual(run["model"]["model_id"], "fixture-model")
        self.assertIsNone(run["model_output"])
        self.assertNotIn("base_revision", run["model"])
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture-key", "GROQ_MODEL": "fixture-model"}), \
             patch("inference_api.service.storage.create_run", side_effect=lambda _a, snap: snap), \
             patch("inference_api.service.groq.chat_turn", side_effect=groq.GroqError(
                 "context_limit", "Groq finish_reason=length", metadata={
                     "usage": {"prompt_tokens": 9, "completion_tokens": 2},
                     "finish_reason": "length", "served_model": "fixture-model"})):
            truncated = service.execute_run(GROQ_INPUT, PRINCIPAL)
        self.assertEqual(truncated["status"], "context_limit")
        self.assertEqual(truncated["model"]["usage"]["completion_tokens"], 2)
        self.assertEqual(truncated["error"]["finish_reason"], "length")
        self.assertIsNone(truncated["model_output"])

    def test_invalid_tool_and_no_tool_are_failures(self):
        receipt = {"provider": "groq", "model_id": "fixture-model", "served_model": "fixture-model"}
        invalid = {"role": "assistant", "content": None, "tool_calls": [{"id": "bad", "type": "function",
                   "function": {"name": "sql", "arguments": "{}"}}]}
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture-key", "GROQ_MODEL": "fixture-model"}), \
             patch("inference_api.service.storage.create_run", side_effect=lambda _a, snap: snap), \
             patch("inference_api.service.groq.chat_turn", side_effect=[
                 (invalid, receipt), ({"role": "assistant", "content": "Sem consulta"}, receipt)]):
            tool_run = service.execute_run({**GROQ_INPUT, "evidence_mode": "synthetic_tools"}, PRINCIPAL)
            no_evidence = service.execute_run({**GROQ_INPUT, "evidence_mode": "synthetic_tools"}, PRINCIPAL)
        self.assertEqual(tool_run["status"], "tool_error")
        self.assertEqual(no_evidence["status"], "insufficient_evidence")


class CookieHttpTests(unittest.TestCase):
    def test_refresh_logout_csrf_expiration_and_legacy_bearer(self):
        active = set()
        def login(*_):
            active.add("fixture-token")
            return {"username": "Nicoli", "token": "fixture-token", "expires_in_seconds": 3600}
        def authenticate(header):
            return PRINCIPAL if header == "Bearer fixture-token" and "fixture-token" in active else None
        def logout(header):
            if header == "Bearer fixture-token": active.discard("fixture-token")
        class Quiet(server.Handler):
            def log_message(self, *_): pass
        http = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{http.server_port}"
        client = build_opener(HTTPCookieProcessor(CookieJar()))
        def request(path, *, body=None, headers=None, opener=client):
            req = Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                          headers=headers or {}, method="POST" if body is not None else "GET")
            try:
                with opener.open(req, timeout=3) as response:
                    return response.status, json.load(response), response.headers
            except HTTPError as exc:
                return exc.code, json.load(exc), exc.headers
        try:
            with patch("inference_api.server.auth.login", side_effect=login), \
                 patch("inference_api.server.auth.authenticate", side_effect=authenticate), \
                 patch("inference_api.server.auth.logout", side_effect=logout):
                origin = {"Origin": base, "X-Browser-Session": "1"}
                status, payload, headers = request("/api/login", body={"username": "Nicoli", "password": "fixture"}, headers=origin)
                self.assertEqual(status, 200)
                self.assertNotIn("token", payload)
                self.assertIn("HttpOnly", headers["Set-Cookie"])
                self.assertIn("SameSite=Strict", headers["Set-Cookie"])
                self.assertEqual(request("/api/me")[0], 200)  # New request with persisted cookie.
                self.assertEqual(request("/api/login", body={"username": "Nicoli", "password": "fixture"},
                                         headers={"Origin": "https://evil.example", "X-Browser-Session": "1"})[0], 403)
                self.assertEqual(request("/api/logout", body={}, headers={"Origin": "https://evil.example"})[0], 403)
                self.assertEqual(request("/api/me")[0], 200)
                active.clear()  # Simulate server-side expiry of the stored session.
                self.assertEqual(request("/api/me")[0], 401)
                self.assertEqual(request("/api/login", body={"username": "Nicoli", "password": "fixture"}, headers=origin)[0], 200)
                self.assertEqual(request("/api/logout", body={}, headers={"Origin": base})[0], 200)
                self.assertEqual(request("/api/me")[0], 401)
                secure_status, secure_payload, secure_headers = request(
                    "/api/login", body={"username": "Nicoli", "password": "fixture"},
                    headers={"Origin": "https://public.example", "Host": "public.example", "X-Browser-Session": "1"})
                self.assertEqual(secure_status, 200)
                self.assertNotIn("token", secure_payload)
                self.assertIn("Secure", secure_headers["Set-Cookie"])
                status, payload, headers = request("/api/login", body={"username": "Nicoli", "password": "fixture"})
                self.assertEqual(status, 200)
                self.assertEqual(payload["token"], "fixture-token")
                self.assertIsNone(headers.get("Set-Cookie"))
                self.assertEqual(request("/api/me", headers={"Authorization": "Bearer fixture-token"})[0], 200)
                active.clear()
                self.assertEqual(request("/api/me", headers={"Authorization": "Bearer fixture-token"})[0], 401)
        finally:
            http.shutdown(); http.server_close(); thread.join(timeout=3)


if __name__ == "__main__": unittest.main()
