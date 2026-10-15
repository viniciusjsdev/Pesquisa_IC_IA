"""Explicit, short generation check for every alias on an authorized endpoint."""

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from serving import MANIFEST, REPO, load_manifest, validate


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def _url(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or
            parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
        raise ValueError("Endpoint must be an HTTPS origin without credentials or query")
    return value.rstrip("/")


def _call(opener, url: str, token: str, body: dict | None = None) -> tuple[dict, dict]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Authorization": "Bearer " + token}
    if data is not None:
        headers["Content-Type"] = "application/json"
    with opener.open(Request(url, data=data, headers=headers,
                             method="POST" if data is not None else "GET"), timeout=120) as response:
        raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Endpoint response exceeds 2 MiB")
        identity = {name: response.headers.get(header) for name, header in {
            "manifest_sha256": "X-Inference-Manifest-SHA256",
            "base_revision": "X-Inference-Base-Revision",
            "session_id": "X-Inference-Session-ID",
            "vllm_version": "X-Inference-VLLM-Version",
        }.items()}
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError("Endpoint returned a non-object JSON response")
    return result, identity


def verify(endpoint: str, base_revision: str, token: str, manifest: dict,
           root: Path = REPO) -> dict:
    from serving import REVISION
    if not REVISION.fullmatch(base_revision):
        raise ValueError("An exact base commit is required")
    if len(token) < 32:
        raise ValueError("INFERENCE_VLLM_TOKEN is missing or too short")
    summary = validate(manifest, root)
    endpoint = _url(endpoint)
    opener = build_opener(NoRedirect())
    models, identity = _call(opener, endpoint + "/v1/models", token)
    if (identity["manifest_sha256"] != summary["manifest_sha256"] or
            identity["base_revision"] != base_revision or not identity["session_id"]):
        raise ValueError("Endpoint session does not match the validated manifest and base revision")
    installed_version = importlib.metadata.version("vllm")
    if identity["vllm_version"] != installed_version:
        raise ValueError("Gateway vLLM version differs from the verifier environment")
    served = {item["id"] for item in models.get("data", []) if isinstance(item, dict) and
              isinstance(item.get("id"), str)}
    aliases = summary["aliases"]
    if set(aliases) != served:
        raise ValueError("Endpoint aliases differ from the seven expected aliases")
    generations = {}
    for alias in aliases:
        result, current = _call(opener, endpoint + "/v1/chat/completions", token, {
            "model": alias,
            "messages": [{"role": "user", "content": "Responda apenas OK."}],
            "temperature": 0,
            "max_tokens": 8,
            "stream": False,
        })
        content = result.get("choices", [{}])[0].get("message", {}).get("content")
        ok = (current == identity and result.get("model") == alias and
              isinstance(content, str) and bool(content.strip()))
        generations[alias] = {"confirmed": ok, "served_model": result.get("model"),
                              "usage": result.get("usage")}
    receipt = {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "manifest_sha256": summary["manifest_sha256"],
        "base_revision": base_revision,
        "session_id": identity["session_id"],
        "vllm_version": installed_version,
        "aliases_returned": sorted(served),
        "artifact_hashes": {item["alias"]: {"weight_sha256": item["weight_sha256"],
                                            "config_sha256": item["config_sha256"]}
                            for item in manifest["adapters"]},
        "generations": generations,
        "status": "passed" if all(item["confirmed"] for item in generations.values()) else "failed",
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--base-revision", required=True)
    parser.add_argument("--checkout", type=Path, default=REPO)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = verify(args.endpoint, args.base_revision,
                         os.environ.get("INFERENCE_VLLM_TOKEN", ""),
                         load_manifest(args.manifest), args.checkout)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
        print(json.dumps({"status": receipt["status"], "session_id": receipt["session_id"],
                          "aliases_confirmed": sum(item["confirmed"] for item in
                                                   receipt["generations"].values()),
                          "receipt": str(args.output)}))
        return 0 if receipt["status"] == "passed" else 1
    except Exception as exc:
        print(f"Remote verification failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
