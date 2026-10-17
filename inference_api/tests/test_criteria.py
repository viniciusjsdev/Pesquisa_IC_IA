"""SPEC-004 declarative criteria and immutable run contracts."""
import copy
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from contextlib import closing
from dataclasses import asdict
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inference_api import config, criteria, server, service, storage
from inference_api.auth import Principal

PRINCIPAL = Principal("00000000-0000-0000-0000-000000000001", "Nicoli")


class CriteriaTests(unittest.TestCase):
    def test_schema_rejects_executable_shape_and_limits(self):
        for value in ({**criteria.DEFAULT, "sql": "SELECT * FROM runs"},
                      {**criteria.DEFAULT, "script": "alert(1)"},
                      {**criteria.DEFAULT, "required_units": ["x" * 81]},
                      {**criteria.DEFAULT, "required_caveats": ["x"] * 9},
                      {**criteria.DEFAULT, "require_period": "true"}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                criteria.validate(value)

    def test_caveats_are_literal_and_never_executed(self):
        config = criteria.validate({**criteria.DEFAULT, "required_caveats": ["limitação"]})
        result = service._checks([{"year": 2020, "coverage": {"state": "observed"},
                                   "units": {"amount": "BRL"}}], "SQL e limitação", config)
        self.assertEqual(next(item for item in result if item["check"] == "criteria_caveat_literal")["result"], "passed")
        self.assertEqual(next(item for item in result if item["check"] == "numerical_truth")["result"], "not_checked")

    def test_saved_revision_snapshot_remains_exact_after_later_edit(self):
        saved = {"revision": 1, "system_prompt": "P", "config": copy.deepcopy(criteria.DEFAULT)}
        with patch("inference_api.service.storage.get_criteria", return_value=saved):
            first = service._criteria({"criteria_revision_id": "00000000-0000-0000-0000-000000000002"})
        saved["config"]["required_caveats"].append("novo")
        self.assertEqual(first["revision"], 1)
        self.assertEqual(first["config"], criteria.DEFAULT)
        self.assertEqual(first["revision_id"], "00000000-0000-0000-0000-000000000002")


@unittest.skipUnless(os.getenv("INFERENCE_IDENTITY_DB_TEST") == "1",
                     "Set INFERENCE_IDENTITY_DB_TEST=1 for isolated PostgreSQL integration")
class CriteriaDatabaseTests(unittest.TestCase):
    def test_migration_revision_conflict_and_down_preserve_old_records(self):
        dbname = "criteria_test_" + uuid4().hex[:12]
        base = config.db_params("FINANCEIRO")
        params = {**base, "dbname": dbname}
        pg_dump = shutil.which("pg_dump") or r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe"
        admin = psycopg2.connect(**base)
        admin.autocommit = True
        try:
            with admin.cursor() as cursor:
                cursor.execute("CREATE DATABASE " + dbname)
            with closing(psycopg2.connect(**params)) as connection, connection:
                with connection.cursor() as cursor:
                    cursor.execute(storage.SCHEMA)
                    cursor.execute(storage.MIGRATION.read_text(encoding="utf-8"))
                    cursor.execute("""INSERT INTO prompt_revisions
                        (id, name, revision, author, system_prompt)
                        VALUES (%s, 'historical', 1, 'declared', 'kept')""", (str(uuid4()),))
            with tempfile.TemporaryDirectory() as temp, \
                 patch.object(storage, "app_db_params", return_value=params):
                backup = Path(temp) / "before-criteria.dump"
                storage.migrate_criteria(backup, pg_dump)
                self.assertGreater(backup.stat().st_size, 0)
                first = storage.create_criteria("checks", "Nicoli", criteria.DEFAULT, 0)
                second_config = {**criteria.DEFAULT, "required_caveats": ["limite"]}
                second = storage.create_criteria("checks", "Vinicius", second_config, 1)
                self.assertEqual(storage.get_criteria(first["id"])["config"], criteria.DEFAULT)
                self.assertEqual(storage.get_criteria(second["id"])["revision"], 2)
                with self.assertRaises(storage.RevisionConflict) as caught:
                    storage.create_criteria("checks", "Nicoli", criteria.DEFAULT, 1)
                self.assertEqual(caught.exception.current["id"], second["id"])
                self.assertEqual(len(storage.list_criteria()), 2)
                class QuietHandler(server.Handler):
                    def log_message(self, *_): pass
                http = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
                thread = threading.Thread(target=http.serve_forever, daemon=True)
                thread.start()
                def request(body=None, route="/api/criteria"):
                    call = Request(f"http://127.0.0.1:{http.server_address[1]}{route}",
                                   data=json.dumps(body).encode() if body is not None else None,
                                   headers={"Authorization": "Bearer test-only",
                                            "Content-Type": "application/json"},
                                   method="POST" if body is not None else "GET")
                    try:
                        with urlopen(call, timeout=5) as received:
                            return received.status, json.load(received)
                    except HTTPError as error:
                        return error.code, json.load(error)
                try:
                    with patch.object(server.auth, "authenticate", return_value=PRINCIPAL):
                        self.assertEqual(len(request()[1]), 2)
                        status, conflict = request({"name": "checks", "author": "Vinicius",
                                                    "config": criteria.DEFAULT, "expected_revision": 1})
                        self.assertEqual(status, 409)
                        self.assertEqual(conflict["current"]["revision"], 2)
                        status, created = request({"name": "checks", "author": "Vinicius",
                                                   "config": criteria.DEFAULT, "expected_revision": 2})
                        self.assertEqual(status, 201)
                        self.assertEqual(created["author"], "Nicoli")
                        status, prompt = request({"name": "prompt-check", "system_prompt": "original",
                                                  "expected_revision": 0}, "/api/prompts")
                        self.assertEqual(status, 201)
                        self.assertEqual(prompt["author"], "Nicoli")
                        status, conflict = request({"name": "prompt-check", "system_prompt": "draft",
                                                    "expected_revision": 0}, "/api/prompts")
                        self.assertEqual(status, 409)
                        self.assertEqual(conflict["current"]["system_prompt"], "original")
                finally:
                    http.shutdown(); http.server_close(); thread.join(timeout=5)
            with closing(psycopg2.connect(**params)) as connection, connection:
                with connection.cursor() as cursor:
                    cursor.execute((storage.CRITERIA_MIGRATION.parent /
                                    "002_criteria_down.sql").read_text(encoding="utf-8"))
                    cursor.execute("SELECT system_prompt FROM prompt_revisions WHERE name = 'historical'")
                    self.assertEqual(cursor.fetchone()[0], "kept")
                    cursor.execute("SELECT to_regclass('public.verification_criteria_revisions')")
                    self.assertIsNone(cursor.fetchone()[0])
        finally:
            with admin.cursor() as cursor:
                cursor.execute("DROP DATABASE IF EXISTS " + dbname)
            admin.close()


if __name__ == "__main__":
    unittest.main()
