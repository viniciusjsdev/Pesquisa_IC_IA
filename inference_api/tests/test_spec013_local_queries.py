"""Fail-closed local query and protocol boundaries, without opening a DB."""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inference_api/src"))
from inference_api.agent_harness import real_pilot  # noqa: E402
from inference_api.agent_harness import local_queries  # noqa: E402
from inference_api.agent_harness.catalog_runtime import compile_maps  # noqa: E402
from inference_api.agent_harness import approved_catalog  # noqa: E402
from inference_api.agent_harness import real_pilot  # noqa: E402
from inference_api import models, service  # noqa: E402
from inference_api.identity.auth import Principal  # noqa: E402


CATALOG = json.loads((ROOT / "specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json")
                     .read_text(encoding="utf-8"))
PLAN = {"fonte_id": "machine", "campos": ["machine_id", "downtime_minutes"],
        "filtros": {"year": 2021, "id": 2000002},
        "limite": 1, "grao": "machine_id/year"}


def promoted():
    catalog = copy.deepcopy(CATALOG)
    catalog["status"] = "approved_for_local_query"
    catalog["domains"]["dw"]["sources"]["machine"]["enabled"] = True
    return catalog




class LocalQueryBoundaryTests(unittest.TestCase):
    def test_dw_filter_validation_returns_specific_rejection(self):
        with patch.object(local_queries.dw_tools, "validate_call",
                          side_effect=ValueError("invalid backend argument")):
            with self.assertRaisesRegex(local_queries.LocalQueryRejected,
                                        "filters_outside_catalog"):
                local_queries._fixed_query(PLAN, {}, {}, 1000)

    def test_real_provider_gate_requires_new_receipt_and_local_switch(self):
        payload = {"provider": "groq", "evidence_mode": "agent_harness_pilot",
                   "model_alias": "groq_harness_pilot", "question": "Pergunta piloto",
                   "system_prompt": real_pilot.PROTOCOL_PROMPT}
        with self.assertRaisesRegex(ValueError, "legacy_execution_mode_retired"):
            service._validate_input(payload)
        with patch.dict("os.environ", {"INFERENCE_SPEC013_GROQ_REAL_DATA": "0"}):
            with self.assertRaisesRegex(ValueError, "gate is disabled"):
                real_pilot.require_external_approval()
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict("os.environ", {"INFERENCE_SPEC013_GROQ_REAL_DATA": "1"}), \
                 patch.object(real_pilot, "RECEIPT_PATH", Path(folder) / "missing.json"):
                with self.assertRaisesRegex(ValueError, "approval receipt is unavailable"):
                    real_pilot.require_external_approval()
        with self.assertRaises(ValueError):
            service._validate_input({**payload, "provider": "openai"})
        with self.assertRaises(ValueError):
            service._validate_input({**payload, "system_prompt": "Alterado"})
        with patch.dict("os.environ", {"INFERENCE_SPEC013_GROQ_REAL_DATA": "0"}):
            pilot = models.available_models()["groq_harness_pilot"]
        self.assertEqual(pilot["kind"], "real_agent_harness_pilot")
        self.assertFalse(pilot["available"])

    def test_approved_catalog_is_exact_reviewed_candidate_and_receipt(self):
        approved = approved_catalog.load()
        self.assertEqual(approved["status"], "approved_for_local_query")
        self.assertEqual(sum(len(domain["sources"]) for domain in approved["domains"].values()),
                         12)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "receipt.json"
            receipt = json.loads(approved_catalog.RECEIPT_PATH.read_text(encoding="utf-8"))
            receipt["data_contract_sha256"] = "0" * 64
            path.write_text(json.dumps(receipt), encoding="utf-8")
            with patch.object(approved_catalog, "RECEIPT_PATH", path):
                with self.assertRaisesRegex(local_queries.LocalQueryRejected,
                                            "semantic_approval_receipt_invalid"):
                    approved_catalog.load()

    def test_disk_catalog_remains_disabled_before_connection(self):
        with patch.object(local_queries, "_connect", side_effect=AssertionError("DB opened")):
            with self.assertRaisesRegex(local_queries.LocalQueryRejected,
                                        "catalog_not_approved_for_local_query"):
                local_queries.execute(PLAN, CATALOG)

    def test_invalid_plan_and_unapproved_source_fail_before_connection(self):
        catalog = promoted()
        bad = [
            ({**PLAN, "fonte_id": "product"}, "source_not_enabled"),
            ({**PLAN, "grao": "annual_total"}, "plan_source_or_grain_mismatch"),
            ({**PLAN, "campos": ["sql"]}, "fields_outside_catalog"),
            ({**PLAN, "campos": [{}]}, "fields_outside_catalog"),
            ({**PLAN, "limite": 21}, "row_limit_invalid"),
            ({**PLAN, "filtros": "SELECT *"}, "filters_outside_catalog"),
            ({**PLAN, "filtros": {**PLAN["filtros"], "join": "financeiro"}},
             "relation_not_approved"),
        ]
        with patch.object(local_queries, "_connect", side_effect=AssertionError("DB opened")):
            for plan, reason in bad:
                with self.subTest(reason=reason), self.assertRaisesRegex(
                        local_queries.LocalQueryRejected, reason):
                    local_queries.execute(plan, catalog)

if __name__=="__main__": unittest.main()
