"""SPEC-002 local checks: artifact identity, static launch and gateway boundaries."""

from copy import deepcopy
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.error import HTTPError


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runpod" / "serving"))
sys.path.insert(0, str(ROOT / "inference_api" / "src"))

import gateway
import serving
import verify_remote
from inference_api import models, serving_catalog


REVISION = "a" * 40


class ServingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = serving.load_manifest()

    def test_real_catalog_hashes_and_static_command(self):
        result = serving.validate(self.manifest)
        self.assertEqual(result["adapter_count"], 6)
        self.assertEqual(set(result["aliases"]), set(serving.ALIASES) | {"qwen-base"})
        argv = serving.command(self.manifest, ROOT, REVISION)
        self.assertEqual(argv[:3], ["vllm", "serve", self.manifest["base_model"]])
        self.assertEqual(argv[argv.index("--served-model-name") + 1], "qwen-base")
        self.assertEqual(argv[argv.index("--host") + 1], "127.0.0.1")
        self.assertIn("--enable-lora", argv)
        self.assertNotIn("--api-key", argv)
        modules = [json.loads(value) for value in argv[argv.index("--lora-modules") + 1:]]
        self.assertEqual({value["name"] for value in modules}, set(serving.ALIASES))
        self.assertTrue(all(value["base_model_name"] == self.manifest["base_model"]
                            for value in modules))

    def test_preflight_rejects_tampered_hash_missing_path_and_secret(self):
        changed = deepcopy(self.manifest)
        changed["adapters"][0]["weight_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "catalog mismatch"):
            serving.validate(changed)
        with patch.object(serving, "_digest", return_value="0" * 64):
            with self.assertRaisesRegex(ValueError, "Missing or invalid"):
                serving.validate(self.manifest)
        changed = deepcopy(self.manifest)
        changed["adapters"][0]["adapter_dir"] += "-absent"
        with self.assertRaises(ValueError):
            serving.validate(changed)
        changed = deepcopy(self.manifest)
        changed["token"] = "must-not-be-versioned"
        with self.assertRaises(ValueError):
            serving.validate(changed)
        with self.assertRaisesRegex(ValueError, "exact 40-character"):
            serving.command(self.manifest, ROOT, "latest")

    def test_gateway_denies_unlisted_paths_and_requires_bearer(self):
        session = {"manifest_sha256": "f" * 64, "base_revision": REVISION,
                   "session_id": "test-session", "aliases": ["qwen-base"]}
        server = gateway.make_server("t" * 32, session, port=0, upstream_port=1)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            conn = HTTPConnection("127.0.0.1", server.server_address[1], timeout=3)
            conn.request("GET", "/invocations", headers={"Authorization": "Bearer " + "t" * 32})
            response = conn.getresponse()
            self.assertEqual(response.status, 404)
            response.read()
            conn.request("GET", "/v1/models")
            response = conn.getresponse()
            self.assertEqual(response.status, 401)
            response.read()
            conn.request("GET", "/v1/models", headers={"Authorization": "Bearer " + "t" * 32})
            response = conn.getresponse()
            self.assertEqual(response.status, 502)
            response.read()
            conn.request("POST", "/v1/chat/completions",
                         body=b'{"model":"unknown"}',
                         headers={"Authorization": "Bearer " + "t" * 32,
                                  "Content-Type": "application/json"})
            response = conn.getresponse()
            self.assertEqual(response.status, 400)
            response.read()
            conn.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_gateway_forwards_only_authorized_model_list_with_session_identity(self):
        forwarded = {}

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *_):
                return

            def do_GET(self):
                body = b'{"data":[{"id":"qwen-base"}]}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                forwarded["path"] = self.path
                forwarded["authorization"] = self.headers.get("Authorization")
                forwarded["content_type"] = self.headers.get("Content-Type")
                forwarded["body"] = self.rfile.read(int(self.headers["Content-Length"]))
                body = b'{"model":"qwen-base","choices":[{"message":{"content":"OK"}}]}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        session = {"manifest_sha256": serving_catalog.FINGERPRINT,
                   "base_revision": REVISION, "session_id": "session-a",
                   "aliases": ["qwen-base"]}
        server = gateway.make_server("t" * 32, session, port=0,
                                     upstream_port=upstream.server_address[1])
        threads = [Thread(target=item.serve_forever, daemon=True) for item in (upstream, server)]
        for thread in threads:
            thread.start()
        try:
            conn = HTTPConnection("127.0.0.1", server.server_address[1], timeout=3)
            conn.request("GET", "/v1/models", headers={"Authorization": "Bearer " + "t" * 32})
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("X-Inference-Session-ID"), "session-a")
            self.assertEqual(json.loads(response.read())["data"][0]["id"], "qwen-base")
            conn.close()

            payload = {"model": "qwen-base", "messages": [{"role": "user", "content": "OK?"}]}
            body = json.dumps(payload).encode()
            conn = HTTPConnection("127.0.0.1", server.server_address[1], timeout=3)
            conn.request("POST", "/v1/chat/completions", body=body,
                         headers={"Authorization": "Bearer " + "t" * 32,
                                  "Content-Type": "application/json"})
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("X-Inference-Session-ID"), "session-a")
            self.assertEqual(json.loads(response.read())["model"], "qwen-base")
            self.assertEqual(forwarded, {
                "path": "/v1/chat/completions", "authorization": None,
                "content_type": "application/json", "body": body,
            })
            conn.close()
        finally:
            for item in (server, upstream):
                item.shutdown()
                item.server_close()
            for thread in threads:
                thread.join(timeout=3)

    def test_model_client_refuses_redirect_with_bearer_token(self):
        received = {"source": [], "target": []}

        class Target(BaseHTTPRequestHandler):
            def log_message(self, *_):
                return

            def do_GET(self):
                received["target"].append(self.headers.get("Authorization"))
                self.send_response(200)
                self.end_headers()

        target = ThreadingHTTPServer(("127.0.0.1", 0), Target)

        class Source(BaseHTTPRequestHandler):
            def log_message(self, *_):
                return

            def do_GET(self):
                received["source"].append(self.headers.get("Authorization"))
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{target.server_port}/capture")
                self.end_headers()

        source = ThreadingHTTPServer(("127.0.0.1", 0), Source)
        threads = [Thread(target=item.serve_forever, daemon=True) for item in (source, target)]
        for thread in threads:
            thread.start()
        try:
            with patch("inference_api.models.vllm_url", return_value=f"http://127.0.0.1:{source.server_port}"), \
                 patch.dict("os.environ", {"INFERENCE_VLLM_TOKEN": "local-test-token"}):
                with self.assertRaises(HTTPError) as failure:
                    models.available_models()
            self.assertEqual(failure.exception.code, 302)
            self.assertEqual(received["source"], ["Bearer local-test-token"])
            self.assertEqual(received["target"], [])
        finally:
            for item in (source, target):
                item.shutdown()
                item.server_close()
            for thread in threads:
                thread.join(timeout=3)

    def test_provenance_requires_matching_session_and_receipt(self):
        class Headers:
            headers = {
                "X-Inference-Manifest-SHA256": serving_catalog.FINGERPRINT,
                "X-Inference-Base-Revision": REVISION,
                "X-Inference-Session-ID": "session-a",
            }
        identity = serving_catalog.response_identity(Headers())
        self.assertEqual(identity["base_revision"], REVISION)
        base = serving_catalog.provenance("ft-finqa-a", identity, "https://pod.example")
        self.assertEqual(base["adapter_hash"], self.manifest["adapters"][0]["weight_sha256"])
        self.assertEqual(base["adapter_run"], "run_v1_seed42")
        self.assertFalse(base["generation_confirmed"])
        self.assertEqual(serving_catalog.provenance("ft-finqa-a", None, "https://pod.example")
                         ["provenance_status"], "unverified")
        receipt = {"status": "passed", "endpoint": "https://pod.example",
                   **identity, "generations": {"ft-finqa-a": {"confirmed": True}}}
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            with patch.dict("os.environ", {"INFERENCE_SERVING_VERIFICATION": str(path)}):
                self.assertTrue(serving_catalog.generation_confirmed(
                    "https://pod.example", identity, "ft-finqa-a"))
                self.assertFalse(serving_catalog.generation_confirmed(
                    "https://other.example", identity, "ft-finqa-a"))
                self.assertFalse(serving_catalog.generation_confirmed(
                    "https://pod.example", {**identity, "session_id": "changed"}, "ft-finqa-a"))

    def test_api_snapshot_provenance_requires_matching_gateway_headers(self):
        headers = {"X-Inference-Manifest-SHA256": serving_catalog.FINGERPRINT,
                   "X-Inference-Base-Revision": REVISION,
                   "X-Inference-Session-ID": "session-a"}

        class Response:
            def __init__(self, body, identity):
                self.body = json.dumps(body).encode()
                self.headers = identity
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self, *_): return self.body

        def open_request(request, timeout):
            if request.full_url.endswith("/v1/models"):
                return Response({"data": [{"id": "ft-finqa-a"}]}, headers)
            return Response({"model": "ft-finqa-a", "choices": [
                {"message": {"content": "OK"}}]}, headers)

        with patch("inference_api.models.vllm_url", return_value="https://pod.example"), \
             patch("inference_api.models.urlopen", side_effect=open_request):
            listing = models.available_models()
            self.assertTrue(listing["ft-finqa-a"]["available"])
            self.assertFalse(listing["ft-finqa-a"]["generation_confirmed"])
            _, record = models.infer("ft-finqa-a", "P", "Q", {}, 0, 8)
        self.assertEqual(record["base_revision"], REVISION)
        self.assertEqual(record["adapter_run"], "run_v1_seed42")
        self.assertEqual(record["adapter_hash"], self.manifest["adapters"][0]["weight_sha256"])
        self.assertEqual(record["provenance_status"], "session_manifest_checked")
        with patch("inference_api.models.vllm_url", return_value=""):
            self.assertTrue(all(not item["available"] and not item["generation_confirmed"]
                                for item in models.available_models().values()))

    def test_remote_verifier_reports_seven_short_generations_without_remote_call(self):
        identity = {"X-Inference-Manifest-SHA256": serving_catalog.FINGERPRINT,
                    "X-Inference-Base-Revision": REVISION,
                    "X-Inference-Session-ID": "session-a",
                    "X-Inference-VLLM-Version": "test-version"}
        aliases = ["qwen-base", *serving.ALIASES]

        class Response:
            headers = identity
            def __init__(self, body):
                self.body = json.dumps(body).encode()
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self, *_): return self.body

        class Opener:
            def __init__(self):
                self.calls = []
            def open(self, request, timeout):
                self.calls.append(request)
                if request.full_url.endswith("/v1/models"):
                    return Response({"data": [{"id": alias} for alias in aliases]})
                payload = json.loads(request.data)
                self_alias = payload["model"]
                return Response({"model": self_alias, "choices": [
                    {"message": {"content": "OK"}}], "usage": {"total_tokens": 4}})

        opener = Opener()
        with patch("verify_remote.build_opener", return_value=opener), \
             patch("verify_remote.importlib.metadata.version", return_value="test-version"):
            receipt = verify_remote.verify("https://pod.example", REVISION, "t" * 32,
                                           self.manifest)
        self.assertEqual(receipt["status"], "passed")
        self.assertEqual(receipt["vllm_version"], "test-version")
        self.assertEqual(len(opener.calls), 8)
        self.assertEqual(set(receipt["generations"]), set(aliases))
        self.assertTrue(all(value["confirmed"] for value in receipt["generations"].values()))


if __name__ == "__main__":
    unittest.main()
