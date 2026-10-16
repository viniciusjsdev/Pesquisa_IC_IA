import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from jsonschema import Draft202012Validator

from model_evaluation import export as subject


SCHEMAS = Path(subject.__file__).parent / "schemas"


def fixture_case(case_id="integrated-1"):
    return {"case_id": case_id, "question": "Há vendas e resultado financeiro em 2020?",
            "domain": "integrado", "queries": [
                {"query": "product", "year": 2020, "id": 1000001},
                {"query": "financial", "year": 2020}]}


def fixture_report():
    return {"database": "db_pesquisa_dw", "schema_version": 1,
            "source_fingerprint": "a" * 64, "source_files": 75,
            "quality_flags": {"fact_sale.outside_source_label": 3}}


def fixture_query(kind, year, identifier):
    common = {"query": kind, "year": year, "grain": "source product/year" if kind == "product" else "one financial source row",
              "sources": ["db_financeiro.public.vendas" if kind == "product" else
                          "db_financeiro.public.resultados_financeiros"],
              "formula": {"observed_sales_value": "sum(quantity * price)"} if kind == "product" else {},
              "units": {"observed_sales_value": "source monetary units"} if kind == "product" else {},
              "interpretation": "Association only; sales are not accounting revenue." if kind == "product"
                                else "No complete annual revenue is inferred."}
    rows = [{"product_id": identifier, "operation_rows": 6168,
             "reported_operation_quantity": 611785, "sale_rows": 1,
             "observed_sales_value": "53161.6"}] if kind == "product" else []
    coverage = {"rows": len(rows), "state": "observed" if rows else "no_observation"}
    if kind == "financial":
        coverage.update({"observed_months": 0, "first_day": None, "last_day": None})
    return {**common, "rows": rows, "coverage": coverage}


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.code = self.root / "query.py"
        self.code.write_text("fixed query v1", encoding="utf-8")

    def packets(self, cases=None, report=None, query=None):
        return subject.build_packets(cases or [fixture_case()],
                                     verify_fn=lambda: report or fixture_report(),
                                     query_fn=query or fixture_query,
                                     query_code_path=self.code)

    def test_schema_hash_and_no_observation(self):
        cases = [fixture_case()]
        manifest = {"schema_version": 1, "cases": cases}
        manifest_schema = json.loads((SCHEMAS / "cases_manifest.schema.json").read_text(encoding="utf-8"))
        packet_schema = json.loads((SCHEMAS / "evidence_packet.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(manifest_schema)
        Draft202012Validator.check_schema(packet_schema)
        Draft202012Validator(manifest_schema).validate(manifest)
        payload = self.packets(cases)["integrated-1"]
        packet = json.loads(payload)
        Draft202012Validator(packet_schema).validate(packet)
        self.assertEqual(payload, subject.canonical(packet))
        self.assertEqual(packet["sha256"], hashlib.sha256(subject.canonical(packet["body"])).hexdigest())
        self.assertEqual(packet["body"]["evidence_items"][1]["coverage"]["state"], "no_observation")
        self.assertEqual(packet["body"]["quality_summary"],
                         {"scope": "global_dw_load", "flags": fixture_report()["quality_flags"]})
        self.assertIn("Association only", packet["body"]["evidence_items"][0]["interpretation"])
        self.assertNotIn("gold_set", payload.decode())
        self.assertNotIn("expected_answer", payload.decode())
        self.assertNotIn("rubric", payload.decode())
        self.assertNotIn("password", payload.decode())
        self.assertNotIn("127.0.0.1", payload.decode())

    def test_schema_rejects_tampered_filters_coverage_and_row(self):
        schema = json.loads((SCHEMAS / "evidence_packet.schema.json").read_text(encoding="utf-8"))
        original = json.loads(self.packets()["integrated-1"])
        tampered = copy.deepcopy(original)
        item = tampered["body"]["evidence_items"][0]
        item["filters"] = {"sql": "SELECT secret", "password": "exposed"}
        item["coverage"] = {"rows": 999, "state": "no_observation", "unexpected": True}
        item["rows"] = [{"unexpected": "accepted"}]
        self.assertGreater(len(list(Draft202012Validator(schema).iter_errors(tampered))), 0)
        for change in (lambda x: x["body"]["evidence_items"][0]["filters"].update({"query": "machine"}),
                       lambda x: x["body"]["evidence_items"][1]["coverage"].update({"rows": 1}),
                       lambda x: x["body"]["evidence_items"][0]["rows"][0].update({"gold_set": "leak"})):
            with self.subTest(change=change):
                candidate = copy.deepcopy(original)
                change(candidate)
                self.assertGreater(len(list(Draft202012Validator(schema).iter_errors(candidate))), 0)

    def test_schema_accepts_all_five_fixed_query_shapes(self):
        schema = json.loads((SCHEMAS / "evidence_packet.schema.json").read_text(encoding="utf-8"))
        case = fixture_case()
        case["queries"] = [{"query": kind, "year": 2020, "id": 1000001}
                           for kind in ("machine", "product", "quality", "material")]
        case["queries"].append({"query": "financial", "year": 2020})
        rows = {
            "machine": {"machine_id": 1000001, "operation_rows": 1,
                        "reported_operation_quantity": 10, "downtime_rows": 1, "downtime_minutes": "2.0"},
            "quality": {"product_id": 1000001, "inspection_rows": 1,
                        "approved_reported": 8, "rejected_reported": 2, "exceeds_lot_rows": 0},
            "material": {"material_id": 1000001, "consumption_rows": 1,
                         "quantity_consumed": "3.2", "price_observation_rows": 1,
                         "min_observed_unit_price": "5.0", "max_observed_unit_price": "5.0"}
        }
        def query(kind, year, identifier):
            result = fixture_query(kind, year, identifier)
            if kind in rows:
                result["rows"] = [rows[kind]]
                result["coverage"] = {"rows": 1, "state": "observed"}
            return result
        packet = json.loads(self.packets([case], query=query)[case["case_id"]])
        Draft202012Validator(schema).validate(packet)

    def test_packet_byte_verifier_rejects_semantic_tampering(self):
        payload = self.packets()["integrated-1"]
        self.assertEqual(subject.verify_packet_bytes(payload, expected_case_id="integrated-1")["body"]["case_id"],
                         "integrated-1")
        original = json.loads(payload)
        altered_year = copy.deepcopy(original)
        altered_year["body"]["evidence_items"][0]["filters"]["year"] = 2021
        altered_year["sha256"] = hashlib.sha256(subject.canonical(altered_year["body"])).hexdigest()
        with self.assertRaisesRegex(subject.ExportError, "Filtros"):
            subject.verify_packet_bytes(subject.canonical(altered_year))
        altered_checksum = copy.deepcopy(original)
        altered_checksum["sha256"] = "0" * 64
        with self.assertRaisesRegex(subject.ExportError, "Checksum"):
            subject.verify_packet_bytes(subject.canonical(altered_checksum))
        with self.assertRaisesRegex(subject.ExportError, "canônico"):
            subject.verify_packet_bytes(json.dumps(original, ensure_ascii=False).encode("utf-8"))

    def test_repeat_reuses_bytes_without_rewrite_and_divergence_preserves_original(self):
        packet = self.packets()
        output = self.root / "packets"
        first = subject.publish_packets(packet, output)
        original = (output / "integrated-1.json").read_bytes()
        stat = (output / "integrated-1.json").stat().st_mtime_ns
        second = subject.publish_packets(self.packets(), output)
        self.assertEqual(first[0]["status"], "created")
        self.assertEqual(second[0]["status"], "reused")
        self.assertEqual((output / "integrated-1.json").stat().st_mtime_ns, stat)
        changed = fixture_case()
        changed["question"] = "Outra pergunta"
        with self.assertRaisesRegex(subject.ExportError, "diverge"):
            subject.publish_packets(self.packets([changed]), output)
        self.assertEqual((output / "integrated-1.json").read_bytes(), original)

    def test_invalid_manifest_fails_before_verify_or_query(self):
        for mutation in (lambda c: c["queries"][0].update({"query": "free_sql"}),
                         lambda c: c["queries"][0].update({"year": 2027}),
                         lambda c: c["queries"][0].pop("id"),
                         lambda c: c["queries"][0].update({"sql": "SELECT 1"}),
                         lambda c: c.update({"expected_answer": "yes"})):
            with self.subTest(mutation=mutation):
                case = fixture_case()
                mutation(case)
                with self.assertRaises(subject.ExportError):
                    subject.build_packets([case], verify_fn=lambda: self.fail("DB verification called"),
                                          query_fn=lambda *_: self.fail("DB query called"),
                                          query_code_path=self.code)
        with self.assertRaisesRegex(subject.ExportError, "duplicado"):
            subject.validate_manifest({"schema_version": 1, "cases": [fixture_case(), fixture_case()]})

    def test_invalid_unicode_question_fails_before_database_access(self):
        case = fixture_case()
        case["question"] = "Pergunta com surrogate " + chr(0xD800)
        with self.assertRaisesRegex(subject.ExportError, "Unicode inválido"):
            subject.build_packets([case], verify_fn=lambda: self.fail("DB verification called"),
                                  query_fn=lambda *_: self.fail("DB query called"),
                                  query_code_path=self.code)

    def test_limits_fail_before_publication(self):
        with self.assertRaisesRegex(subject.ExportError, "linhas"):
            self.packets(query=lambda kind, year, identifier:
                         {**fixture_query(kind, year, identifier),
                          "rows": [{}] * 201, "coverage": {"rows": 201, "state": "observed"}})
        def large_query(kind, year, identifier):
            result = fixture_query(kind, year, identifier)
            result["interpretation"] = "x" * subject.MAX_BYTES
            return result
        with self.assertRaisesRegex(subject.ExportError, "bytes"):
            self.packets(query=large_query)
        self.assertFalse((self.root / "packets").exists())

    def test_three_domains_and_code_fingerprint_change(self):
        cases = [fixture_case("integrated"), fixture_case("financial"), fixture_case("industrial")]
        cases[1].update({"domain": "financeiro", "queries": [{"query": "financial", "year": 2020}]})
        cases[2].update({"domain": "industrial", "queries": [{"query": "product", "year": 2020, "id": 1000001}]})
        packets = self.packets(cases)
        self.assertEqual(set(packets), {"integrated", "financial", "industrial"})
        self.code.write_text("fixed query v2", encoding="utf-8")
        self.assertNotEqual(packets["integrated"], self.packets(cases)["integrated"])
        report = copy.deepcopy(fixture_report())
        report["source_fingerprint"] = "b" * 64
        self.assertNotEqual(packets["integrated"], self.packets(cases, report=report)["integrated"])

    def test_partial_or_conflicting_existing_file_blocks_entire_batch(self):
        output = self.root / "packets"
        output.mkdir()
        (output / "financial.json").write_bytes(b"{")
        cases = [fixture_case("integrated"), fixture_case("financial")]
        with self.assertRaisesRegex(subject.ExportError, "diverge"):
            subject.publish_packets(self.packets(cases), output)
        self.assertFalse((output / "integrated.json").exists())
        self.assertEqual((output / "financial.json").read_bytes(), b"{")


if __name__ == "__main__":
    unittest.main()
