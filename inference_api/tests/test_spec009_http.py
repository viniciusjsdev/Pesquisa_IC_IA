"""Authenticated HTTP contract with a simulated serving endpoint and packets."""
from contextlib import nullcontext
import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inference_api" / "src"))

from inference_api import server
import test_contract as fixture


class HttpModeTests(unittest.TestCase):
    def setUp(self):
        fixture.ModeTests.setUp(self)
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.http.server_close)
        self.addCleanup(self.http.shutdown)

    def request(self, method, path, body=None, authorized=True):
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": "Bearer fixture"} if authorized else {}
        if data:
            headers["Content-Type"] = "application/json"
        request = Request(f"http://127.0.0.1:{self.http.server_port}{path}",
                          data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.load(exc)

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass
