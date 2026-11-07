"""Transport and idempotency checks without paid serving or a live database."""
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from contextlib import closing
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from time import monotonic, sleep

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inference_api" / "src"))
sys.path.insert(0, str(ROOT / "runpod" / "serving"))

import gateway
from inference_api import auth, config, jobs, limits, models, server, storage
from inference_api.auth import Principal
import psycopg2
from uuid import uuid4


class StreamingTests(unittest.TestCase):
    def test_gateway_exposes_first_event_before_model_finishes(self):
        first_sent = threading.Event()
        release = threading.Event()

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                self.wfile.write(b'data: {"first":true}\n\n')
                self.wfile.flush()
                first_sent.set()
                release.wait(3)
                self.wfile.write(b'data: [DONE]\n\n')
                self.wfile.flush()

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        session = {"manifest_sha256": "a" * 64, "base_revision": "b" * 40,
                   "session_id": "session", "aliases": ["qwen-base"]}
        proxy = gateway.make_server("t" * 32, session, port=0,
                                    upstream_port=upstream.server_address[1])
        threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (upstream, proxy)]
        for thread in threads: thread.start()
        try:
            conn = HTTPConnection("127.0.0.1", proxy.server_address[1], timeout=2)
            body = json.dumps({"model": "qwen-base", "stream": True}).encode()
            conn.request("POST", "/v1/chat/completions", body=body,
                         headers={"Authorization": "Bearer " + "t" * 32,
                                  "Content-Type": "application/json"})
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("X-Inference-Session-ID"), "session")
            self.assertTrue(first_sent.wait(1))
            self.assertEqual(response.readline(), b'data: {"first":true}\n')
            self.assertFalse(release.is_set())
            release.set()
            self.assertIn(b'[DONE]', response.read())
            conn.close()
        finally:
            release.set()
            for server in (proxy, upstream): server.shutdown(); server.server_close()
            for thread in threads: thread.join(timeout=3)

    def test_client_assembles_tool_deltas_and_rejects_incomplete_stream(self):
        class Response:
            headers = {"Content-Type": "text/event-stream"}
            def __init__(self, lines): self.lines = lines
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def __iter__(self): return iter(self.lines)

        def event(delta, finish=None):
            return ("data: " + json.dumps({"model": "qwen-base", "choices": [
                {"index": 0, "delta": delta, "finish_reason": finish}]}) + "\n\n").encode()

        complete = [
            event({"tool_calls": [{"index": 0, "id": "call-1", "type": "function",
                                   "function": {"name": "financial", "arguments": "{\"year\":"}}]}),
            event({"tool_calls": [{"index": 0, "function": {"arguments": "2020}"}}]}, "tool_calls"),
            b"data: [DONE]\n\n",
        ]
        identity = {"manifest_sha256": "a" * 64, "base_revision": "b" * 40,
                    "session_id": "session"}
        with patch("inference_api.models.vllm_url", return_value="https://example.invalid"), \
             patch("inference_api.models.available_models", return_value={
                 "qwen-base": {"available": True, "session_id": "session"}}), \
             patch("inference_api.models.serving_catalog.response_identity", return_value=identity), \
             patch("inference_api.models.urlopen", return_value=Response(complete)):
            message, record = models.chat_turn("qwen-base", [{"role": "user", "content": "Q"}],
                                               0, None, tools=[], session_id="session")
        self.assertEqual(message["tool_calls"][0]["function"]["arguments"], '{"year":2020}')
        self.assertEqual(record["raw_response_format"], "sse")
        with patch("inference_api.models.vllm_url", return_value="https://example.invalid"), \
             patch("inference_api.models.available_models", return_value={
                 "qwen-base": {"available": True, "session_id": "session"}}), \
             patch("inference_api.models.serving_catalog.response_identity", return_value=identity), \
             patch("inference_api.models.urlopen", return_value=Response(complete[:-1])):
            with self.assertRaises(models.ModelResponseError) as caught:
                models.chat_turn("qwen-base", [{"role": "user", "content": "Q"}],
                                 0, None, tools=[], session_id="session")
        self.assertIn("incomplete", str(caught.exception).lower())
        exhausted = [event({"content": "unfinished"}, "length"), b"data: [DONE]\n\n"]
        with patch("inference_api.models.vllm_url", return_value="https://example.invalid"), \
             patch("inference_api.models.available_models", return_value={
                 "qwen-base": {"available": True, "session_id": "session"}}), \
             patch("inference_api.models.serving_catalog.response_identity", return_value=identity), \
             patch("inference_api.models.urlopen", return_value=Response(exhausted)):
            with self.assertRaises(models.ModelResponseError) as caught:
                models.chat_turn("qwen-base", [{"role": "user", "content": "Q"}],
                                 0, None, tools=None, session_id="session")
        self.assertEqual(caught.exception.serving["raw_response"]["choices"][0]["finish_reason"], "length")


class JobTests(unittest.TestCase):
    def test_duplicate_request_does_not_launch_second_model_call(self):
        principal = Principal("00000000-0000-0000-0000-000000000001", "Nicoli")
        key = "00000000-0000-0000-0000-000000000002"
        receipt = {"id": "00000000-0000-0000-0000-000000000003", "status": "accepted"}
        calls = []

        class ImmediateThread:
            def __init__(self, *, target, args, **_): self.target, self.args = target, args
            def start(self): self.target(*self.args)

        @contextmanager
        def reserve(_id):
            yield

        with patch("inference_api.jobs.service.prepare", return_value={}), \
             patch("inference_api.jobs.storage.create_job", side_effect=[(receipt, True), (receipt, False)]), \
             patch("inference_api.jobs.Thread", ImmediateThread), \
             patch("inference_api.jobs.limits.reserve", reserve), \
             patch("inference_api.jobs.service.execute_run", return_value={"id": "run-1"}) as execute, \
             patch("inference_api.jobs.storage.update_job", side_effect=lambda *args, **kw: calls.append((args, kw))):
            self.assertEqual(jobs.submit({}, principal, key), receipt)
            self.assertEqual(jobs.submit({}, principal, key), receipt)
        self.assertEqual(execute.call_count, 1)
        self.assertEqual([item[0][2] for item in calls], ["running", "completed"])


@unittest.skipUnless(os.getenv("INFERENCE_IDENTITY_DB_TEST") == "1",
                     "Set INFERENCE_IDENTITY_DB_TEST=1 for isolated PostgreSQL integration")
class JobDatabaseTests(unittest.TestCase):
    def test_migration_idempotency_ownership_and_restart_reconciliation(self):
        dbname = "runjob_test_" + uuid4().hex[:12]
        base = config.db_params("FINANCEIRO")
        params = {**base, "dbname": dbname}
        admin = psycopg2.connect(**base)
        admin.autocommit = True
        try:
            with admin.cursor() as cursor: cursor.execute("CREATE DATABASE " + dbname)
            owner, other = str(uuid4()), str(uuid4())
            with closing(psycopg2.connect(**params)) as connection, connection:
                with connection.cursor() as cursor:
                    cursor.execute(storage.SCHEMA)
                    cursor.execute(storage.MIGRATION.read_text(encoding="utf-8"))
                    cursor.execute(storage.CRITERIA_MIGRATION.read_text(encoding="utf-8"))
                    cursor.execute("""INSERT INTO researchers
                        (id, username, password_salt, password_digest)
                        VALUES (%s, 'Nicoli', %s, %s), (%s, 'Vinicius', %s, %s)""",
                        (owner, b"salt", b"digest", other, b"salt", b"digest"))
            pg_dump = shutil.which("pg_dump") or r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe"
            with tempfile.TemporaryDirectory() as temp, \
                 patch.object(storage, "app_db_params", return_value=params):
                backup = Path(temp) / "before-jobs.dump"
                storage.migrate_run_jobs(backup, pg_dump)
                self.assertGreater(backup.stat().st_size, 0)
                key = str(uuid4())
                first, created = storage.create_job(owner, key, {"question": "Q"})
                self.assertTrue(created)
                again, created = storage.create_job(owner, key, {"question": "Q"})
                self.assertFalse(created)
                self.assertEqual(first["id"], again["id"])
                with self.assertRaises(ValueError):
                    storage.create_job(owner, key, {"question": "changed"})
                with self.assertRaises(limits.BusyError):
                    storage.create_job(other, str(uuid4()), {"question": "other"})
                self.assertIsNone(storage.get_job(first["id"], other))
                self.assertIsNone(storage.get_job_by_key(key, other))
                storage.update_job(first["id"], "accepted", "running")
                storage.interrupt_unfinished_jobs()
                self.assertEqual(storage.get_job(first["id"], owner)["status"], "interrupted")
                second, created = storage.create_job(other, str(uuid4()), {"question": "other"})
                self.assertTrue(created)
                self.assertEqual(second["status"], "accepted")
                storage.update_job(second["id"], "accepted", "busy")
                principal = Principal(owner, "Nicoli")
                class QuietHandler(server.Handler):
                    def log_message(self, *_): pass
                http = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
                thread = threading.Thread(target=http.serve_forever, daemon=True)
                thread.start()
                executions = []
                def fake_run(_payload, actor, *, prepared=None):
                    executions.append(actor.id)
                    return storage.create_run(actor.username, {"status": "test"})
                def request(path, body=None):
                    data = json.dumps(body).encode() if body is not None else None
                    req = Request(f"http://127.0.0.1:{http.server_address[1]}{path}",
                                  data=data, headers={"Authorization": "Bearer fixture",
                                                      "Content-Type": "application/json"},
                                  method="POST" if body is not None else "GET")
                    try:
                        with urlopen(req, timeout=5) as response:
                            return response.status, json.load(response)
                    except HTTPError as exc:
                        return exc.code, json.load(exc)
                try:
                    with patch.object(limits, "app_db_params", return_value=params), \
                         patch.object(auth, "authenticate", return_value=principal), \
                         patch.object(jobs.service, "prepare", return_value={}), \
                         patch.object(jobs.service, "execute_run", side_effect=fake_run):
                        body = {"request_key": str(uuid4()), "question": "HTTP fixture"}
                        code, submitted = request("/api/run-jobs", body)
                        self.assertEqual(code, 202)
                        self.assertEqual(request("/api/run-jobs", body)[1]["id"], submitted["id"])
                        deadline = monotonic() + 5
                        while monotonic() < deadline:
                            code, receipt = request("/api/run-jobs/" + submitted["id"])
                            if receipt["status"] == "completed": break
                            sleep(0.05)
                        self.assertEqual(code, 200)
                        self.assertEqual(receipt["status"], "completed")
                        self.assertEqual(request("/api/runs/" + receipt["run_id"])[1]["snapshot"]["status"], "test")
                        self.assertEqual(request("/api/run-jobs/by-key/" + body["request_key"])[1]["id"], submitted["id"])
                        self.assertEqual(executions, [owner])
                finally:
                    http.shutdown(); http.server_close(); thread.join(timeout=3)
                with closing(psycopg2.connect(**params)) as connection, connection:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT version FROM inference_schema_migrations ORDER BY version")
                        self.assertEqual([row[0] for row in cursor.fetchall()], [1, 2, 3])
        finally:
            with admin.cursor() as cursor: cursor.execute("DROP DATABASE IF EXISTS " + dbname)
            admin.close()


if __name__ == "__main__": unittest.main()
