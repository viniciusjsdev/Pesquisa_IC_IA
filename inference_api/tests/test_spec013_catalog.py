"""Structural M0 catalog checks stay separate from semantic approval."""

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from BancoModeloUse.scripts.validate_semantic_catalog import validate  # noqa: E402


EVIDENCE = ROOT / "specs" / "active" / "SPEC-013" / "evidence"
CATALOG = json.loads((EVIDENCE / "m0-semantic-map-candidate-2026-11-01.json").read_text(encoding="utf-8"))
INVENTORY = json.loads((EVIDENCE / "m0-physical-schema-2026-11-01.json").read_text(encoding="utf-8"))
FIXED = ROOT / "BancoModeloUse" / "dw" / "fixed_queries.py"
LINEAGE = ROOT / "BancoModeloUse" / "dw" / "cli.py"


class SemanticCatalogChecks(unittest.TestCase):
    def check(self, catalog=CATALOG, inventory=INVENTORY):
        return validate(catalog, inventory, FIXED, LINEAGE)

    def test_candidate_matches_physical_and_fixed_contract_but_is_not_enabled(self):
        report = self.check()
        self.assertTrue(report["valid_structurally"], report["errors"])
        self.assertFalse(report["eligible_for_activation"])
        self.assertEqual(report["checks"]["sources"], 12)
        self.assertEqual(report["physical_table_counts"],
                         {"dw": 35, "industrial": 39, "financeiro": 19})
        self.assertTrue(all(size < 16384 for size in report["index_bytes_by_domain"].values()))

    def test_unknown_column_and_fixed_output_are_rejected(self):
        catalog = copy.deepcopy(CATALOG)
        catalog["domains"]["industrial"]["sources"]["paradas_maquinas"]["fields"].append("unknown")
        catalog["domains"]["dw"]["sources"]["machine"]["fields"].append("unknown")
        report = self.check(catalog)
        self.assertFalse(report["valid_structurally"])
        self.assertTrue(any("column absent" in error for error in report["errors"]))
        self.assertTrue(any("output fields" in error for error in report["errors"]))

    def test_changed_column_type_is_rejected(self):
        catalog = copy.deepcopy(CATALOG)
        catalog["domains"]["industrial"]["sources"]["registros_operacao"]["field_types"]["quantidade_produzida_real"] = "text"
        report = self.check(catalog)
        self.assertTrue(any("field types differ" in error for error in report["errors"]))

    def test_inventory_tampering_and_source_activation_are_rejected(self):
        inventory = copy.deepcopy(INVENTORY)
        inventory["databases"]["dw"]["tables"].pop("fact_downtime")
        self.assertIn("physical inventory contents differ from their declared SHA-256",
                      self.check(inventory=inventory)["errors"])
        catalog = copy.deepcopy(CATALOG)
        catalog["domains"]["dw"]["sources"]["machine"]["enabled"] = True
        self.assertTrue(any("must stay disabled" in error for error in self.check(catalog)["errors"]))

    def test_unapproved_relation_and_unknown_filter_are_rejected(self):
        catalog = copy.deepcopy(CATALOG)
        source = catalog["domains"]["industrial"]["sources"]["paradas_maquinas_geradas"]
        source["physical_relations"] = ["maquina_id -> maquinas.maquina_id"]
        source["filter_candidates"].append("not_a_column:range")
        report = self.check(catalog)
        self.assertTrue(any("FK not present" in error for error in report["errors"]))
        self.assertTrue(any("filter column absent" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
