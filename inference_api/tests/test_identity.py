"""Identity and global lock tests against an isolated disposable application DB."""
import json
import os
import sys
import threading
import unittest
from contextlib import ExitStack, closing
from http.server import ThreadingHTTPServer
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import psycopg2
from inference_api import auth, budget, config, limits, server, storage


class BudgetTests(unittest.TestCase):
    def test_without_read_key_keeps_balance_unconfirmed(self):
        with patch.dict(os.environ, {}, clear=True):
            result = budget.status()
        self.assertEqual(result["session_ceiling_usd"], 10.0)
        self.assertIsNone(result["runpod_balance_usd"])
        self.assertEqual(result["runpod_status"], "not_configured")
        self.assertIsNone(result["checked_at"])
        self.assertIsNotNone(result["status_checked_at"])

    def test_confirmed_balance_is_read_only(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self): return b'{"data":{"myself":{"clientBalance":7.5,"currentSpendPerHr":0.4}}}'
        with patch.dict(os.environ, {"RUNPOD_BALANCE_READ_KEY": "test-only"}), \
             patch("inference_api.budget._open", return_value=Response()) as open_url:
            result = budget.status()
        self.assertEqual(result["runpod_balance_usd"], 7.5)
        self.assertEqual(result["runpod_status"], "confirmed_read")
        self.assertIsNotNone(result["checked_at"])
        self.assertEqual(result["runpod_source"], "RunPod GraphQL myself.clientBalance")
        self.assertIn("myself", json.loads(open_url.call_args.args[0].data)["query"])

    def test_balance_key_is_not_sent_to_redirect_target(self):
        reached = []
        class Target(BaseHTTPRequestHandler):
            def do_POST(self):
                reached.append(self.headers.get("Authorization"))
                self.send_response(200); self.end_headers()
            def log_message(self, *_): pass
        target = ThreadingHTTPServer(("127.0.0.1", 0), Target)
        class Redirect(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(307)
                self.send_header("Location", f"http://127.0.0.1:{target.server_address[1]}/")
                self.end_headers()
            def log_message(self, *_): pass
        redirect = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
        threads = [threading.Thread(target=s.serve_forever, daemon=True)
                   for s in (target, redirect)]
        for thread in threads: thread.start()
        try:
            with patch.dict(os.environ, {"RUNPOD_BALANCE_READ_KEY": "test-only"}), \
                 patch.object(budget, "GRAPHQL",
                              f"http://127.0.0.1:{redirect.server_address[1]}/"):
                result = budget.status()
            self.assertEqual(result["runpod_status"], "read_failed")
            self.assertIsNotNone(result["checked_at"])
            self.assertEqual(reached, [])
        finally:
            for s in (redirect, target): s.shutdown(); s.server_close()
            for thread in threads: thread.join(timeout=5)


class LoginGateTests(unittest.TestCase):
    def test_concurrency_and_rate_are_bounded_without_ip_headers(self):
        gate = auth.LoginGate(max_attempts=2, window_seconds=60,
                              max_concurrent=1)
        with gate.attempt():
            with self.assertRaises(auth.LoginBusy):
                with gate.attempt():
                    pass
        with gate.attempt():
            pass
        with self.assertRaises(auth.LoginBusy):
            with gate.attempt():
                pass


@unittest.skipUnless(os.getenv("INFERENCE_IDENTITY_DB_TEST") == "1",
                     "Set INFERENCE_IDENTITY_DB_TEST=1 for isolated PostgreSQL integration")
class MigrationTests(unittest.TestCase):
    def test_down_preserves_preexisting_records(self):
        dbname = "identity_rollback_" + uuid4().hex[:12]
        base = config.db_params("FINANCEIRO")
        params = {**base, "dbname": dbname}
        admin = psycopg2.connect(**base)
        admin.autocommit = True
        try:
            with admin.cursor() as cursor:
                cursor.execute("CREATE DATABASE " + dbname)
            with closing(psycopg2.connect(**params)) as connection, connection:
                with connection.cursor() as cursor:
                    cursor.execute(storage.SCHEMA)
                    cursor.execute("""INSERT INTO prompt_revisions
                        (id, name, revision, author, system_prompt)
                        VALUES (%s, 'before-identity', 1, 'historical', 'kept')""",
                                   (str(uuid4()),))
                    cursor.execute(storage.MIGRATION.read_text(encoding="utf-8"))
                    cursor.execute((storage.MIGRATION.parent /
                                    "001_identity_down.sql").read_text(encoding="utf-8"))
                    cursor.execute("SELECT count(*) FROM prompt_revisions WHERE name = 'before-identity'")
                    self.assertEqual(cursor.fetchone()[0], 1)
                    for table in ("runs", "feedback"):
                        cursor.execute("SELECT to_regclass(%s)", ("public." + table,))
                        self.assertIsNotNone(cursor.fetchone()[0])
                    cursor.execute("SELECT to_regclass('public.researchers')")
                    self.assertIsNone(cursor.fetchone()[0])
        finally:
            with admin.cursor() as cursor:
                cursor.execute("DROP DATABASE IF EXISTS " + dbname)
            admin.close()


@unittest.skipUnless(os.getenv("INFERENCE_IDENTITY_DB_TEST") == "1",
                     "Set INFERENCE_IDENTITY_DB_TEST=1 for isolated PostgreSQL integration")
class IdentityDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dbname = "identity_test_" + uuid4().hex[:12]
        base = config.db_params("FINANCEIRO")
        cls.params = {**base, "dbname": cls.dbname}
        admin = psycopg2.connect(**base)
        admin.autocommit = True
        with admin.cursor() as cursor:
            cursor.execute("CREATE DATABASE " + cls.dbname)
        admin.close()
        cls.patches = ExitStack()
        for module in (auth, limits, storage):
            cls.patches.enter_context(patch.object(module, "app_db_params",
                                                   return_value=cls.params))
        with psycopg2.connect(**cls.params) as connection:
            with connection.cursor() as cursor:
                cursor.execute(storage.SCHEMA)
                cursor.execute(storage.MIGRATION.read_text(encoding="utf-8"))
        auth.set_password("Nicoli", "test-only-one")
        auth.set_password("Vinicius", "test-only-two")
        cls.logs = []
        class CapturedHandler(server.Handler):
            def log_message(self, fmt, *args):
                cls.logs.append(fmt % args)
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), CapturedHandler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.http.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join(timeout=5)
        cls.patches.close()
        base = config.db_params("FINANCEIRO")
        admin = psycopg2.connect(**base)
        admin.autocommit = True
        with admin.cursor() as cursor:
            cursor.execute("DROP DATABASE " + cls.dbname)
        admin.close()

    def request(self, path, token=None, body=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request(self.base_url + path,
                          data=json.dumps(body).encode() if body is not None else None,
                          headers=headers,
                          method="POST" if body is not None else "GET")
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def login(self, username, password):
        status, result = self.request("/api/login", body={"username": username,
                                                          "password": password})
        self.assertEqual(status, 200)
        return result["token"]

    def test_two_sessions_author_and_revocation(self):
        nicoli = self.login("Nicoli", "test-only-one")
        vinicius = self.login("Vinicius", "test-only-two")
        with psycopg2.connect(**self.params) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT password_salt, password_digest FROM researchers WHERE username = 'Nicoli'")
                salt, digest = cursor.fetchone()
                self.assertNotIn(b"test-only-one", bytes(salt) + bytes(digest))
                cursor.execute("SELECT token_salt, token_digest FROM researcher_sessions")
                self.assertTrue(all(nicoli.encode() not in bytes(s) + bytes(d)
                                    for s, d in cursor.fetchall()))
        self.assertEqual(self.request("/api/me", nicoli)[1]["username"], "Nicoli")
        self.assertEqual(self.request("/api/me", vinicius)[1]["username"], "Vinicius")
        status, _ = self.request("/api/prompts", body={"name": "x"})
        self.assertEqual(status, 401)
        status, prompt = self.request("/api/prompts", nicoli, {
            "name": "identity-test", "author": "Vinicius",
            "system_prompt": "Test prompt", "expected_revision": 0})
        self.assertEqual(status, 201)
        self.assertEqual(prompt["author"], "Nicoli")
        status, run = self.request("/api/runs", vinicius, {
            "author": "Nicoli", "question": "test", "model_alias": "qwen-base",
            "system_prompt": "test", "scope": "invalid", "year": 2020})
        self.assertEqual(status, 201)
        self.assertEqual(run["author"], "Vinicius")
        self.assertTrue(run["snapshot"]["identity"]["author_verified"])
        self.assertNotIn(nicoli, json.dumps(run["snapshot"]))
        self.assertNotIn(vinicius, json.dumps(run["snapshot"]))
        self.assertFalse(any(nicoli in line or vinicius in line
                             for line in self.logs))
        auth.revoke("Nicoli")
        self.assertEqual(self.request("/api/prompts", nicoli)[0], 401)
        self.assertEqual(self.request("/api/me", vinicius)[0], 200)

    def test_second_run_rejected_while_first_holds_global_lock(self):
        first = self.login("Vinicius", "test-only-two")
        second = self.login("Nicoli", "test-only-one")
        entered = threading.Event()
        release = threading.Event()
        outcomes = []
        def fake_run(_payload, principal):
            entered.set()
            release.wait(timeout=5)
            return storage.create_run(principal.username,
                                      {"identity": {"principal_id": principal.id,
                                                    "author_verified": True},
                                       "model": {"alias": "test"}, "status": "test"})
        with patch("inference_api.server.service.execute_run", side_effect=fake_run):
            thread = threading.Thread(target=lambda: outcomes.append(
                self.request("/api/runs", first, {"question": "one"})))
            thread.start()
            self.assertTrue(entered.wait(timeout=5))
            try:
                status, body = self.request("/api/runs", second, {"question": "two"})
                self.assertEqual(status, 429)
                self.assertIn("Another inference", body["error"])
            finally:
                release.set()
                thread.join(timeout=5)
        self.assertEqual(outcomes[0][0], 201)
        self.assertEqual(outcomes[0][1]["author"], "Vinicius")

    def test_z_failed_attempts_do_not_lock_account(self):
        auth.set_password("Nicoli", "test-only-one")
        with patch.object(auth, "LOGIN_GATE", auth.LoginGate()):
            for _ in range(5):
                self.assertEqual(self.request("/api/login", body={
                    "username": "Nicoli", "password": "wrong"})[0], 401)
            self.assertEqual(self.request("/api/login", body={
                "username": "Nicoli", "password": "test-only-one"})[0], 200)

    def test_login_rate_returns_429_before_password_check(self):
        with patch.object(auth, "LOGIN_GATE", auth.LoginGate(max_attempts=2)):
            for _ in range(2):
                self.assertEqual(self.request("/api/login", body={
                    "username": "unknown", "password": "wrong"})[0], 401)
            self.assertEqual(self.request("/api/login", body={
                "username": "unknown", "password": "wrong"})[0], 429)

    def test_short_password_is_rejected(self):
        with self.assertRaises(ValueError):
            auth.set_password("Nicoli", "short")


if __name__ == "__main__":
    unittest.main()
