"""Activate the exact human-reviewed v4 case contracts for post-run scoring.

The reviewed v4 remains immutable. This command only writes a new private
manifest after the receipt and every reference binding are verified. It never
calls a model, sends data, or scores a run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from model_evaluation.materialize_spec013_pilot_cases import (
    CASE_IDS, ROOT, canonical, materialize,
)


RECEIPT = ROOT / "specs/active/SPEC-013/evidence/m3-executable-case-approval-2026-11-02.json"
PRIVATE_ROOT = (ROOT / "model_evaluation/.local").resolve()
APPROVED_V4_SHA256 = "27214d0acc5424f11bf9c27e3f4c5ee0be1d977dc169524fceb3a8900fa2018a"
APPROVAL_QUESTION_ID = "call_dde320b417a0400d9bf90d1843e27c35/0"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def activate() -> dict:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    artifact = receipt.get("reviewed_artifact", {})
    reviewed = (ROOT / artifact.get("path", "")).resolve()
    if (reviewed != PRIVATE_ROOT / "spec013-pilot-case-contracts-2026-11-02-v4.json" or
            not reviewed.is_file() or sha(reviewed) != APPROVED_V4_SHA256 or
            artifact.get("sha256") != APPROVED_V4_SHA256 or
            receipt.get("spec_id") != "SPEC-013" or
            receipt.get("decision") != "approved_for_technical_activation" or
            receipt.get("reviewer") == receipt.get("preparer") or
            not receipt.get("reviewer") or not receipt.get("preparer") or
            receipt.get("review_source", {}).get("reply_verbatim") !=
            "Aprovo a v4 dos nove casos" or
            receipt.get("review_source", {}).get("question_item_id") != APPROVAL_QUESTION_ID):
        raise ValueError("executable_case_approval_invalid")
    decisions = receipt.get("case_decisions")
    if (not isinstance(decisions, list) or len(decisions) != len(CASE_IDS) or
            [item.get("case_id") for item in decisions] != list(CASE_IDS) or
            any(item.get("decision") != "approved" for item in decisions)):
        raise ValueError("case_decisions_do_not_match_review")
    frozen = json.loads(reviewed.read_text(encoding="utf-8"))
    if canonical(materialize(approved_local_catalog=True)) != reviewed.read_bytes():
        raise ValueError("case_reference_or_map_drift")
    if (frozen.get("status") != "approved_map_bound_pending_case_review" or
            [case.get("case_id") for case in frozen.get("cases", [])] != list(CASE_IDS) or
            any(case.get("prepared_by") != receipt["preparer"] or
                case.get("status") != "content_approved_pending_execution"
                for case in frozen["cases"])):
        raise ValueError("reviewed_case_contract_invalid")
    receipt_sha = sha(RECEIPT)
    frozen["status"] = "approved_for_scoring_pending_run_review"
    frozen["executable_case_approval_sha256"] = receipt_sha
    frozen["reviewed_v4_sha256"] = sha(reviewed)
    for case in frozen["cases"]:
        case["status"] = "approved"
        case["review"].update({"reviewer": receipt["reviewer"],
                               "reviewed_at": receipt["review_date_local"],
                               "evidence_receipt": receipt_sha,
                               "reply_source": receipt["review_source"]["question_item_id"]})
    return frozen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to(PRIVATE_ROOT):
        raise SystemExit("Approved case manifests must stay under model_evaluation/.local")
    rendered = canonical(activate())
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(rendered)
    print(json.dumps({"path": str(target),
                      "sha256": hashlib.sha256(rendered).hexdigest(),
                      "case_ids": list(CASE_IDS),
                      "status": "approved_for_scoring_pending_run_review",
                      "provider_called": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
