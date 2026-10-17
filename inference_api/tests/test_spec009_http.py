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

    def test_auth_packet_listing_and_both_post_modes(self):
        calls = [{"role": "assistant", "content": "Pacote respondido"},
                 {"role": "assistant", "tool_calls": [{"id": "call-1", "type": "function",
                     "function": {"name": "product", "arguments": '{"year":2020,"id":1000001}'}}]},
                 {"role": "assistant", "content": "Tool respondida"}]
        saved = []
        def create_run(author, snapshot):
            saved.append(snapshot)
            return {"id": str(len(saved)), "author": author, "created_at": "2026-10-16T00:00:00Z", "snapshot": snapshot}
        with patch("inference_api.server.auth.authenticate", side_effect=lambda header: fixture.PRINCIPAL if header else None), \
             patch("inference_api.server.limits.reserve", return_value=nullcontext()), \
             patch("inference_api.server.storage.create_run", side_effect=create_run), \
             patch("inference_api.evidence_packets.packet_directory", return_value=self.root), \
             patch("inference_api.server.dw_tools.availability", return_value=fixture.DW), \
             patch("inference_api.service.dw_tools.availability", return_value=fixture.DW), \
             patch("inference_api.service.dw_tools.execute", return_value=fixture.RESULT), \
             patch("inference_api.service.models.chat_turn", side_effect=[fixture.turn(item) for item in calls]):
            self.assertEqual(self.request("GET", "/api/bench/evidence-packets", authorized=False)[0], 401)
            code, packets = self.request("GET", "/api/bench/evidence-packets")
            self.assertEqual(code, 200)
            self.assertEqual(packets[0]["sha256"], self.packet["sha256"])
            self.assertEqual(self.request("POST", "/api/runs", {**fixture.BASE, "question": "Q"})[0], 400)
            code, snapshot = self.request("POST", "/api/runs", {**fixture.BASE, "evidence_mode": "dw_snapshot",
                        "case_id": "integrated-1", "packet_sha256": self.packet["sha256"]})
            self.assertEqual(code, 201)
            self.assertEqual(snapshot["snapshot"]["status"], "answered_unverified")
            code, live = self.request("POST", "/api/runs", {**fixture.BASE, "evidence_mode": "dw_tools", "question": "Q"})
            self.assertEqual(code, 201)
            self.assertEqual(live["snapshot"]["tool_trace"][0]["name"], "product")
            self.assertEqual(live["snapshot"]["status"], "answered_unverified")
            self.assertEqual(len(saved), 2)
