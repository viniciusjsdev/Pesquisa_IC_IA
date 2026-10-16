"""Session gate, static boundary and frozen BI payload for SPEC-008."""

import http.client
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import re
from threading import Thread
import unittest
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inference_api import config, server  # noqa: E402


class BiHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join(timeout=2)

    def request(self, path, *, bearer=False):
        connection = http.client.HTTPConnection("127.0.0.1", self.http.server_port)
        headers = {"Authorization": "Bearer fixture"} if bearer else {}
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        status, body, cache = response.status, response.read(), response.getheader("Cache-Control")
        connection.close()
        return status, body, cache

    def test_snapshot_requires_session_and_is_not_static(self):
        principal = type("Principal", (), {"id": "fixture", "username": "Nicoli"})()
        with patch.object(server.auth, "authenticate", side_effect=lambda header: principal if header == "Bearer fixture" else None):
            denied = self.request("/api/bi/snapshot")
            allowed = self.request("/api/bi/snapshot", bearer=True)
            static = self.request("/private/bi_snapshot.json")
        self.assertEqual(denied[0], 401)
        self.assertEqual(allowed[0], 200)
        self.assertEqual(allowed[2], "no-store")
        self.assertEqual(static[0], 404)
        self.assertIn("snapshot_at", json.loads(allowed[1]))

    def test_private_json_is_exact_reference_payload(self):
        fixture = Path(__file__).resolve().parents[2] / "specs/active/SPEC-008/references/BI_Pesquisa_Offline.reference.html"
        html = fixture.read_text(encoding="utf-8")
        match = re.search(r'<script id="embedded-data" type="application/json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(match)
        self.assertEqual(server.BI_SNAPSHOT.read_bytes(), match.group(1).encode("utf-8"))


class DockerConfigTests(unittest.TestCase):
    def test_host_and_docker_allowlists_are_exact(self):
        values = {"INDUSTRIAL_DB_HOST": "127.0.0.1", "INDUSTRIAL_DB_PORT": "5544",
                  "INDUSTRIAL_DB_NAME": "db_industrial", "INDUSTRIAL_DB_USER": "fixture",
                  "INDUSTRIAL_DB_PASSWORD": "fixture", "INFERENCE_RUNTIME_MODE": "host"}
        with patch.dict(config.os.environ, values):
            self.assertEqual(config.db_params("INDUSTRIAL")["host"], "127.0.0.1")
        values.update({"INDUSTRIAL_DB_HOST": "db", "INDUSTRIAL_DB_PORT": "5432", "INFERENCE_RUNTIME_MODE": "docker"})
        with patch.dict(config.os.environ, values):
            self.assertEqual(config.db_params("INDUSTRIAL")["port"], 5432)
            config.os.environ["INDUSTRIAL_DB_HOST"] = "other-service"
            with self.assertRaises(ValueError):
                config.db_params("INDUSTRIAL")


if __name__ == "__main__":
    unittest.main()
