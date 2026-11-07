"""Load the exact 12-source catalog approved for local-only SPEC-013 reads."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from . import local_queries


ROOT = Path(__file__).resolve().parents[4]
APPROVED_PATH = ROOT / "specs/active/SPEC-013/catalog/pilot_local_v1.json"
RECEIPT_PATH = ROOT / "specs/active/SPEC-013/evidence/m0-semantic-local-approval-2026-11-02.json"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load() -> dict:
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    if (receipt.get("approved_scope") != "local_readonly_pilot_all_12_sources_without_cross_database_joins" or
            receipt.get("review_source", {}).get("reply_verbatim") !=
            "Aprovo o contrato detalhado para uso local" or
            receipt.get("external_provider_transmission_approved") is not False or
            receipt.get("scientific_scoring_approved") is not False or
            receipt.get("catalog_candidate_sha256") != _digest(local_queries.CATALOG_PATH) or
            receipt.get("data_contract_sha256") != _digest(local_queries.DATA_CONTRACT_PATH)):
        raise local_queries.LocalQueryRejected("semantic_approval_receipt_invalid")
    candidate = json.loads(local_queries.CATALOG_PATH.read_text(encoding="utf-8"))
    if candidate.get("status") != "candidate_not_enabled" or any(
            source.get("enabled") is not False for domain in candidate["domains"].values()
            for source in domain["sources"].values()):
        raise local_queries.LocalQueryRejected("candidate_catalog_changed")
    expected = copy.deepcopy(candidate)
    expected["status"] = "approved_for_local_query"
    for domain in expected["domains"].values():
        for source in domain["sources"].values():
            source["enabled"] = True
    approved = json.loads(APPROVED_PATH.read_text(encoding="utf-8"))
    if approved != expected or sum(len(domain["sources"]) for domain in approved["domains"].values()) != 12:
        raise local_queries.LocalQueryRejected("approved_catalog_differs_from_reviewed_candidate")
    local_queries._validate_catalog_base(approved)
    return approved
