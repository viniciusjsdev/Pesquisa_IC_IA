"""Bind the nine reviewed SPEC-013 questions to private reference contracts.

This is an offline preparation step. It never calls a model or a database,
never enables the semantic catalog, and keeps gold values under .local/.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re

from model_evaluation.verify_human_review_receipt import ROOT, verify


RECEIPT = ROOT / "specs/active/SPEC-013/evidence/m3-human-case-content-approval-2026-11-01.json"
CATALOG = ROOT / "specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json"
FIXED_QUERIES = ROOT / "BancoModeloUse/dw/fixed_queries.py"
APPROVED_CATALOG = ROOT / "specs/active/SPEC-013/catalog/pilot_local_v1.json"
CASE_IDS = ("I1", "I2", "I3", "F1", "F2", "F3", "X1", "X2", "X3")
SECTION = re.compile(r"^## (I[123]|F[123]|X[123]) · [^\n]+\n(.*?)(?=^## |\Z)", re.M | re.S)
QUESTION = re.compile(r"\*\*Pergunta:\*\*\s*“(.*?)”", re.S)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


STEPS = {
    "machine_2021_2000002": ("machine", {"year": 2021, "id": 2000002}),
    "machine_2026_1": ("machine", {"year": 2026, "id": 1}),
    "machine_2020_1000002": ("machine", {"year": 2020, "id": 1000002}),
    "financial_2021": ("financial", {"year": 2021}),
    "financial_2019": ("financial", {"year": 2019}),
    "financial_2020": ("financial", {"year": 2020}),
    "generated_stops_2021_machine_2000002": (
        "paradas_maquinas_geradas",
        {"fonte_id": "paradas_maquinas_geradas",
         "campos": ["parada_id", "maquina_id", "hora_inicio_parada", "hora_fim_parada", "origem"],
         "filtros": {"maquina_id": 2000002,
                     "hora_inicio_parada": {"from": "2021-01-01T00:00:00",
                                            "to": "2022-01-01T00:00:00"}},
         "limite": 20, "grao": "parada_id/source_period"}),
    "sales_2021": (
        "vendas",
        {"fonte_id": "vendas",
         "campos": ["venda_id", "produto_id", "quantidade_vendida",
                    "preco_unitario_venda", "data_venda"],
         "filtros": {"data_venda": {"from": "2021-01-01", "to": "2022-01-01"}},
         "limite": 20, "grao": "venda_id/source_period"}),
}

CASE_STEPS = {
    "I1": ("machine_2021_2000002",),
    "I2": ("machine_2026_1",),
    "I3": ("machine_2021_2000002", "generated_stops_2021_machine_2000002"),
    "F1": ("financial_2021",),
    "F2": ("financial_2019",),
    "F3": ("sales_2021", "financial_2021"),
    "X1": ("machine_2021_2000002", "financial_2021"),
    "X2": ("machine_2020_1000002", "financial_2020"),
    "X3": ("machine_2021_2000002", "generated_stops_2021_machine_2000002",
           "financial_2021"),
}

CASE_CHECKS = {
    "I1": ["downtime_minutes_exact", "unit_minutes"],
    "I2": ["no_observation_not_zero"],
    "I3": ["downtime_rows_exact", "generated_stop_ids_and_provenance",
           "generated_ids_subset_of_dw_contributors"],
    "F1": ["financial_rows_exact", "observed_months_exact", "first_last_day_exact",
           "not_complete_annual_total"],
    "F2": ["no_observation_not_zero"],
    "F3": ["sales_rows_exact", "financial_rows_exact",
           "observed_sale_value_not_accounting_revenue"],
    "X1": ["downtime_minutes_exact", "financial_rows_exact", "no_causal_attribution"],
    "X2": ["downtime_minutes_exact", "financial_no_observation",
           "no_profit_trend_without_observations"],
    "X3": ["downtime_rows_exact", "generated_stop_ids_and_provenance",
           "financial_rows_exact", "no_causal_attribution"],
}


def materialize(*, approved_local_catalog: bool = False) -> dict:
    integrity = verify(RECEIPT)
    if integrity["reviewed_case_ids"] != list(CASE_IDS):
        raise ValueError("reviewed_case_ids_differ_from_pilot")
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    packet = (ROOT / receipt["reviewed_artifact"]["path"]).read_text(encoding="utf-8")
    sections = dict(SECTION.findall(packet))
    if set(sections) != set(CASE_IDS):
        raise ValueError("reviewed_case_sections_differ")
    dw = json.loads((ROOT / receipt["reference_artifacts"][0]["path"]).read_text(encoding="utf-8"))
    detail = json.loads((ROOT / receipt["reference_artifacts"][1]["path"]).read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if (catalog.get("status") != "candidate_not_enabled" or
            file_digest(CATALOG) != dw.get("catalog_sha256") or
            file_digest(CATALOG) != detail.get("catalog_sha256") or
            file_digest(FIXED_QUERIES) != dw.get("query_code_sha256") or
            catalog.get("dw_source_fingerprint") != dw.get("dw_source_fingerprint")):
        raise ValueError("reference_catalog_or_code_drift")
    maps = None
    map_hashes = None
    if approved_local_catalog:
        import sys
        sys.path.insert(0, str(ROOT / "inference_api/src"))
        from inference_api.agent_harness.approved_catalog import load
        from inference_api.agent_harness.catalog_runtime import compile_maps
        maps = compile_maps(load())
        map_hashes = {domain: digest(domain_map)
                      for domain, domain_map in maps.items()}
    references = {**dw["reference_queries"],
                  **{key: detail[key] for key in
                     ("generated_stops_2021_machine_2000002", "sales_2021")}}
    if set(references) != set(STEPS):
        raise ValueError("reference_step_set_differ")
    generated = {row["values"]["parada_id"] for row in
                 references["generated_stops_2021_machine_2000002"]["rows"]}
    contributors = detail["downtime_contributors_2021_machine_2000002"]
    contributing = {fact_id for page in contributors["contributors"]
                    for fact_id in page["ids"] if page["fact"] == "fact_downtime"}
    if not generated or not generated <= contributing or any(
            page["next_after"] is not None for page in contributors["contributors"]):
        raise ValueError("generated_stop_lineage_unverified")
    cases = []
    for case_id in CASE_IDS:
        match = QUESTION.search(sections[case_id])
        if match is None:
            raise ValueError("case_question_missing: " + case_id)
        question = " ".join(match.group(1).split())
        steps = []
        for ref_key in CASE_STEPS[case_id]:
            source_id, plan = STEPS[ref_key]
            result = references[ref_key]
            if maps is not None:
                matches = [source for domain in maps.values()
                           for candidate, source in domain["sources"].items()
                           if candidate == source_id]
                if len(matches) != 1:
                    raise ValueError("approved_source_missing: " + source_id)
                source = matches[0]
                selected_fields = (plan["campos"] if isinstance(plan, dict) and
                                   "campos" in plan else source["fields"])
                filters = plan.get("filtros", {}) if "fonte_id" in plan else plan
                allowed_filters = {item.split(":", 1)[0]
                                   for item in source.get("filters", source.get("filter_candidates", []))}
                if (source.get("enabled") is not True or
                        ("grao" in plan and source["grain"] != plan["grao"]) or
                        not set(selected_fields) <= set(source["fields"]) or
                        not set(filters) <= allowed_filters):
                    raise ValueError("approved_source_contract_mismatch: " + source_id)
            if (result["coverage"]["rows"] != len(result["rows"]) or
                    result["coverage"]["state"] !=
                    ("observed" if result["rows"] else "no_observation")):
                raise ValueError("reference_coverage_inconsistent: " + ref_key)
            if source_id in {"machine", "financial"}:
                if result["query"] != source_id or result["year"] != plan["year"]:
                    raise ValueError("dw_reference_plan_mismatch: " + ref_key)
                if source_id == "machine" and any(
                        row["machine_id"] != plan["id"] for row in result["rows"]):
                    raise ValueError("dw_reference_id_mismatch: " + ref_key)
            elif result["origin"]["table"] != source_id:
                raise ValueError("typed_reference_plan_mismatch: " + ref_key)
            elif source_id == "paradas_maquinas_geradas" and any(
                    row["values"]["maquina_id"] != plan["filtros"]["maquina_id"] or
                    not plan["filtros"]["hora_inicio_parada"]["from"] <=
                    row["values"]["hora_inicio_parada"] <
                    plan["filtros"]["hora_inicio_parada"]["to"]
                    for row in result["rows"]):
                raise ValueError("typed_reference_filter_mismatch: " + ref_key)
            elif source_id == "vendas" and any(
                    not plan["filtros"]["data_venda"]["from"] <=
                    row["values"]["data_venda"] < plan["filtros"]["data_venda"]["to"]
                    for row in result["rows"]):
                raise ValueError("typed_reference_filter_mismatch: " + ref_key)
            steps.append({"source_id": source_id, "plan": plan,
                          "reference_key": ref_key, "reference_sha256": digest(result),
                          "coverage": result["coverage"],
                          "units": result.get("units", {}),
                          "formula": result.get("formula", {
                              "observed_sales_value": "quantidade_vendida * preco_unitario_venda"
                          } if source_id == "vendas" else {})})
        route = [step["source_id"] for step in steps]
        cases.append({"case_id": case_id, "status": "content_approved_pending_execution",
                      "question": question, "question_sha256": digest(question),
                      "reviewed_section_sha256": hashlib.sha256(
                          sections[case_id].encode("utf-8")).hexdigest(),
                      "steps": steps,
                      "accepted_routes": [list(p) for p in dict.fromkeys(
                          itertools.permutations(route))],
                      "expected_evidence_states": {
                          step["source_id"]: step["coverage"]["state"] for step in steps},
                      "checks": CASE_CHECKS[case_id], "numeric_tolerance": "0",
                      "review": {"reviewer": receipt["reviewer"],
                                 "reply_source": receipt["review_source"]["question_item_id"],
                                 "packet_sha256": receipt["reviewed_artifact"]["sha256"]}})
        if map_hashes is not None:
            cases[-1]["map_sha256"] = map_hashes
            cases[-1]["required_evidence_sources"] = list(route)
            cases[-1]["prepared_by"] = receipt["preparer"]
    return {"schema_version": 1, "spec_id": "SPEC-013",
            "status": ("approved_map_bound_pending_case_review" if maps is not None else
                       "content_approved_pending_execution"),
            "catalog_enabled": maps is not None, "provider_called": False,
            "review_receipt_sha256": file_digest(RECEIPT),
            "reviewed_packet_sha256": receipt["reviewed_artifact"]["sha256"],
            "catalog_sha256": file_digest(APPROVED_CATALOG if maps is not None else CATALOG),
            **({"map_sha256": map_hashes,
                "catalog_candidate_sha256": file_digest(CATALOG)}
               if maps is not None else {}),
            "dw_source_fingerprint": dw["dw_source_fingerprint"],
            "dw_query_code_sha256": file_digest(FIXED_QUERIES),
            "reference_artifacts": receipt["reference_artifacts"],
            "lineage_reference_sha256": digest(contributors),
            "generated_ids_confirmed_in_dw": len(generated),
            "cases": cases}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--approved-local-catalog", action="store_true",
                        help="Vincula os mapas aprovados, ainda sem habilitar score")
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "model_evaluation/.local").resolve()):
        raise SystemExit("Gold case manifests must stay under model_evaluation/.local")
    document = materialize(approved_local_catalog=args.approved_local_catalog)
    rendered = canonical(document)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(rendered)
    print(json.dumps({"path": str(target), "sha256": hashlib.sha256(rendered).hexdigest(),
                      "case_ids": [case["case_id"] for case in document["cases"]],
                      "status": document["status"], "provider_called": False},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
