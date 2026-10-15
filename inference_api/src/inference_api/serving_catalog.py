"""Candidate aliases and conditional provenance from a validated serving session."""

import hashlib
import json
import os
from pathlib import Path
import re

from .config import ROOT


MANIFEST_PATH = ROOT / "runpod" / "serving" / "manifest.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
BASE = MANIFEST["base_model"]
FINGERPRINT = hashlib.sha256(json.dumps(
    MANIFEST, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
).encode("utf-8")).hexdigest()
MODELS = {MANIFEST["base_alias"]: {"battery": "base", "kind": "base"}}
for _adapter in MANIFEST["adapters"]:
    MODELS[_adapter["alias"]] = {
        "battery": _adapter["battery"], "kind": "adapter",
        "run": _adapter["run"], "weight_sha256": _adapter["weight_sha256"],
    }

IDENTITY_HEADERS = {
    "manifest_sha256": "X-Inference-Manifest-SHA256",
    "base_revision": "X-Inference-Base-Revision",
    "session_id": "X-Inference-Session-ID",
}


def response_identity(response) -> dict | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    identity = {key: headers.get(header) for key, header in IDENTITY_HEADERS.items()}
    if (identity["manifest_sha256"] != FINGERPRINT or
            not isinstance(identity["base_revision"], str) or
            not re.fullmatch(r"[0-9a-f]{40}", identity["base_revision"]) or
            not identity["session_id"]):
        return None
    return identity


def generation_confirmed(endpoint: str, identity: dict | None, alias: str) -> bool:
    path = os.getenv("INFERENCE_SERVING_VERIFICATION", "").strip()
    if not path or identity is None:
        return False
    try:
        receipt = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(receipt.get("status") == "passed" and receipt.get("endpoint") == endpoint and
                all(receipt.get(key) == identity[key] for key in IDENTITY_HEADERS) and
                receipt.get("generations", {}).get(alias, {}).get("confirmed") is True)


def provenance(alias: str, identity: dict | None, endpoint: str) -> dict:
    result = {
        "base_revision": None, "adapter_run": None, "adapter_hash": None,
        "provenance_status": "unverified", "generation_confirmed": False,
        "session_id": None,
    }
    if identity is None:
        return result
    item = MODELS[alias]
    result.update({
        "base_revision": identity["base_revision"],
        "adapter_run": item.get("run"),
        "adapter_hash": item.get("weight_sha256"),
        "provenance_status": "session_manifest_checked",
        "generation_confirmed": generation_confirmed(endpoint, identity, alias),
        "session_id": identity["session_id"],
    })
    return result
