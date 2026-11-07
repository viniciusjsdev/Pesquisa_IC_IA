"""Verify artifact integrity of a human case-content review receipt.

This verifies hashes, paths and enumerated case IDs. It cannot authenticate
the human decision or turn content approval into a scientific score.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
CASE_HEADING = re.compile(r"^## ([A-Za-z][A-Za-z0-9_-]*) · ", re.MULTILINE)
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _read_verified_artifact(artifact: dict) -> tuple[Path, bytes]:
    if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
        raise ValueError("invalid_artifact_record")
    expected = artifact.get("sha256")
    if not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise ValueError("invalid_artifact_sha256")
    path = (ROOT / artifact["path"]).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("artifact_missing_or_outside_workspace")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("artifact_hash_mismatch: " + artifact["path"])
    return path, data


def verify(receipt_path: Path) -> dict:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema_version") != 1 or not isinstance(receipt.get("review_source"), dict):
        raise ValueError("invalid_review_receipt")
    if (not isinstance(receipt.get("reviewer"), str) or not receipt["reviewer"] or
            not isinstance(receipt.get("preparer"), str) or not receipt["preparer"] or
            receipt["reviewer"] == receipt["preparer"] or
            not isinstance(receipt["review_source"].get("reply_verbatim"), str) or
            not receipt["review_source"]["reply_verbatim"]):
        raise ValueError("review_provenance_incomplete")
    decisions = receipt.get("case_decisions")
    if not isinstance(decisions, list) or not decisions:
        raise ValueError("missing_case_decisions")
    ids = [item.get("case_id") for item in decisions if isinstance(item, dict)]
    if (len(ids) != len(decisions) or
            not all(isinstance(item, str) and item for item in ids) or
            len(set(ids)) != len(ids) or
            not all(item.get("decision") == "approved_content" for item in decisions)):
        raise ValueError("invalid_case_decisions")
    _, reviewed_bytes = _read_verified_artifact(receipt["reviewed_artifact"])
    headings = CASE_HEADING.findall(reviewed_bytes.decode("utf-8"))
    if sorted(headings) != sorted(ids):
        raise ValueError("reviewed_packet_case_ids_mismatch")
    references = receipt.get("reference_artifacts")
    if not isinstance(references, list) or not references:
        raise ValueError("missing_reference_artifacts")
    paths = []
    for artifact in references:
        path, _ = _read_verified_artifact(artifact)
        paths.append(path)
    if len(set(paths)) != len(paths):
        raise ValueError("duplicate_reference_artifact")
    return {"artifact_integrity_valid": True, "reviewed_case_ids": ids,
            "reference_artifacts_verified": len(paths),
            "human_identity_independently_verified": False,
            "scoring_status": receipt.get("scoring_eligibility")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.receipt), ensure_ascii=False, indent=2))
