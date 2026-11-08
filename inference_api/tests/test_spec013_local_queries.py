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
from inference_api.agent_harness import real_pilot, HarnessError, Limits, run  # noqa: E402
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

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

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

    def test_real_maps_require_explicit_protocol_and_approved_catalog(self):
        with self.assertRaisesRegex(local_queries.LocalQueryRejected,
                                    "catalog_not_approved_for_local_query"):
            compile_maps(CATALOG)
        maps = compile_maps(promoted())
        with self.assertRaisesRegex(HarnessError, "real_or_invalid_domain_map_blocked"):
            run("Pergunta local", maps, lambda *_: (_ for _ in ()).throw(
                AssertionError("model called")), lambda *_: {}, protocol="synthetic_fixture_m1")

    def test_unapproved_relation_returns_to_selector_without_sql(self):
        catalog = promoted()
        catalog["domains"]["dw"]["sources"]["product"]["enabled"] = True
        maps = compile_maps(catalog)
        first = {"fonte_id": "machine", "campos": ["machine_id"],
                 "filtros": {"year": 2021, "id": 2000002, "join": "financeiro"},
                 "limite": 1, "grao": "machine_id/year"}
        second = {"fonte_id": "product", "campos": ["product_id"],
                  "filtros": {"year": 2021, "id": 2000001},
                  "limite": 1, "grao": "product_id/year"}
        outputs = iter([
            ("analista_pergunta", {"tratavel": True,
              "necessidade": {"entidade": "produto", "medida": "contagem",
                              "periodo": "2021", "grao": "produto/ano"},
              "dominios": ["dw"], "lacunas": []}),
            ("selecionador_fontes", {"decisao": "consultar", "justificativa": "fixture",
                                     "fonte_id": "machine", "dominio_adicional": None,
                                     "map_refs": ["machine"]}),
            ("especialista_consulta", {"plano": first, "justificativa": "fixture",
                                     "evidence_refs": []}),
            ("selecionador_fontes", {"decisao": "consultar", "justificativa": "alternativa",
                                     "fonte_id": "product", "dominio_adicional": None,
                                     "map_refs": ["product"]}),
            ("especialista_consulta", {"plano": second, "justificativa": "fixture",
                                     "evidence_refs": []}),
            ("revisor_evidencias", {"decisao": "suficiente",
                                    "evidencias_utilizadas": ["result_01"],
                                    "justificativa": "fixture", "lacuna": None,
                                    "proximo_dado_necessario": None,
                                    "dominio_sugerido": None}),
            ("redator_resposta", {"resposta": "Fixture.",
                                   "evidencias_utilizadas": ["result_01"],
                                   "calculos": [], "ressalvas": []}),
        ])
        selector_feedback = []
        def model(role, envelope, _contract):
            if role == "selecionador_fontes":
                selector_feedback.append(envelope["input"].get("correction_feedback"))
            expected, output = next(outputs)
            self.assertEqual(role, expected)
            return json.dumps(output), {"provider": "fixture", "model_id": "same"}
        def query(plan):
            if "join" in plan["filtros"]:
                raise local_queries.LocalQueryRejected("relation_not_approved")
            return {"rows": [{"product_id": 2000001}],
                    "coverage": {"state": "observed", "rows": 1},
                    "units": {}, "origin": {"database": "fixture"}}
        result = run("Pergunta local", maps, model, query,
                     limits=Limits(calls=20, queries=2),
                     protocol="local_readonly_pilot")
        self.assertEqual(result["status"], "answered_unverified")
        self.assertEqual(result["queries"], 1)
        self.assertEqual([item["source_id"] for item in result["evidence"]], ["product"])
        self.assertIsNone(selector_feedback[0])
        self.assertEqual(selector_feedback[1]["error_code"], "relation_not_approved")
        self.assertEqual([event["error"] for event in result["trace"]
                          if event["role"] == "data_query" and event["status"] == "rejected"],
                         ["relation_not_approved"])


if __name__ == "__main__":
    unittest.main()
