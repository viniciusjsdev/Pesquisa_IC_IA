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
              "system_prompt": 'Responda apenas com a fixture inventada. Cite o ano e indique que os dados são sintéticos.'}


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
                       {"system_prompt": "private"}, {"question": "private"},
                       {"criteria": {"required_caveats": ["private"]}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                service._validate_input({**GROQ_INPUT, **change})

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

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

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass


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
            data = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
            req = Request(base + path, data=data,
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
                # The rejected origin and logout handlers intentionally do not consume request bodies.
                # An empty POST prevents Windows from resetting a socket with unread payload bytes.
                self.assertEqual(request("/api/login", body=b"",
                                         headers={"Origin": "https://evil.example", "X-Browser-Session": "1"})[0], 403)
                self.assertEqual(request("/api/logout", body=b"", headers={"Origin": "https://evil.example"})[0], 403)
                self.assertEqual(request("/api/me")[0], 200)
                active.clear()  # Simulate server-side expiry of the stored session.
                self.assertEqual(request("/api/me")[0], 401)
                self.assertEqual(request("/api/login", body={"username": "Nicoli", "password": "fixture"}, headers=origin)[0], 200)
                self.assertEqual(request("/api/logout", body=b"", headers={"Origin": base})[0], 200)
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
