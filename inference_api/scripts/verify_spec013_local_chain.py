"""Run three real local reads through five roles with a scripted model fixture.

This is an orchestration smoke, not model inference or scientific evaluation.
The disk catalog stays disabled; an in-memory copy is used for this check.
"""

import argparse
import copy
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inference_api/src"))
from inference_api.agent_harness import run  # noqa: E402
from inference_api.agent_harness.catalog_runtime import compile_maps  # noqa: E402
from inference_api.agent_harness import local_queries  # noqa: E402
from inference_api.agent_harness import real_pilot  # noqa: E402


CATALOG_PATH = ROOT / "specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json"
QUESTION = ("Em 2021, qual agregado de parada da máquina 2000002 está na DW, "
            "quais paradas geradas da mesma máquina/período aparecem no industrial "
            "e quais observações financeiras existem, sem atribuir relação causal?")
ROUTE = {1: ("dw", "machine"),
         2: ("industrial", "paradas_maquinas_geradas"),
         3: ("financeiro", "resultados_financeiros")}
PLANS = {
    "machine": {"fonte_id": "machine",
                "campos": ["machine_id", "downtime_rows", "downtime_minutes"],
                "filtros": {"year": 2021, "id": 2000002}, "limite": 1,
                "grao": "machine_id/year"},
    "paradas_maquinas_geradas": {
        "fonte_id": "paradas_maquinas_geradas",
        "campos": ["parada_id", "maquina_id", "hora_inicio_parada", "hora_fim_parada", "origem"],
        "filtros": {"maquina_id": 2000002,
                    "hora_inicio_parada": {"from": "2021-01-01T00:00:00",
                                           "to": "2022-01-01T00:00:00"}},
        "limite": 20, "grao": "parada_id/source_period"},
    "resultados_financeiros": {
        "fonte_id": "resultados_financeiros",
        "campos": ["id", "data_registro", "lucro_liquido"],
        "filtros": {"data_registro": {"from": "2021-01-01", "to": "2022-01-01"}},
        "limite": 20, "grao": "id/observation_date/source_period"},
}


def scripted_model(role: str, envelope: dict, contract: dict) -> tuple[str, dict]:
    round_no = envelope["round"]
    inputs = envelope["input"]
    if role == "analista_pergunta":
        answer = {"tratavel": True,
                  "necessidade": {"entidade": "máquina 2000002",
                                  "medida": "paradas e observações financeiras",
                                  "periodo": "2021",
                                  "grao": "máquina/ano, parada/evento e observação/data"},
                  "dominios": ["dw"], "lacunas": []}
    elif role == "selecionador_fontes":
        source_id = ROUTE[round_no][1]
        answer = {"decisao": "consultar", "justificativa": "Rota do smoke.",
                  "fonte_id": source_id, "dominio_adicional": None,
                  "map_refs": [source_id]}
    elif role == "especialista_consulta":
        answer = {"plano": PLANS[ROUTE[round_no][1]],
                  "justificativa": "Plano tipado do smoke.",
                  "evidence_refs": [f"result_{n:02d}" for n in range(1, round_no)]}
    elif role == "revisor_evidencias":
        next_domain = ROUTE[round_no + 1][0] if round_no < 3 else None
        answer = {"decisao": "precisa_aprofundar" if next_domain else "suficiente",
                  "evidencias_utilizadas": [f"result_{n:02d}" for n in range(1, round_no + 1)],
                  "justificativa": "Verificação da cadeia local, sem juízo de qualidade.",
                  "lacuna": "Falta a próxima fonte do smoke." if next_domain else None,
                  "proximo_dado_necessario": ROUTE[round_no + 1][1] if next_domain else None,
                  "dominio_sugerido": next_domain}
    elif role == "redator_resposta":
        answer = {"resposta": "Smoke local concluído; resposta científica não avaliada.",
                  "evidencias_utilizadas": ["result_01", "result_02", "result_03"],
                  "calculos": [], "ressalvas": ["Transporte de modelo simulado."]}
    else:
        raise RuntimeError("Unexpected role: " + role)
    return json.dumps(answer, ensure_ascii=False), {"provider": "local_fixture",
                                                   "model_id": "scripted_same_candidate"}


def verify(*, approved_catalog: bool = False) -> dict:
    original = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if original.get("status") != "candidate_not_enabled":
        raise RuntimeError("Disk catalog must stay disabled")
    if approved_catalog:
        catalog, maps = real_pilot.context()
    else:
        catalog = copy.deepcopy(original)
        catalog["status"] = "approved_for_local_query"
        allowed = {source_id for _, source_id in ROUTE.values()}
        for domain in catalog["domains"].values():
            for source_id, source in domain["sources"].items():
                source["enabled"] = source_id in allowed
        maps = compile_maps(catalog)
    result = run(QUESTION, maps, scripted_model,
                 lambda plan: local_queries.execute(plan, catalog),
                 limits=real_pilot.PILOT_LIMITS,
                 protocol="local_readonly_pilot")
    if result["status"] != "answered_unverified" or result["queries"] != 3 or [
            item["source_id"] for item in result["evidence"]] != [
                "machine", "paradas_maquinas_geradas", "resultados_financeiros"]:
        raise RuntimeError("Local chain did not complete: " + str(result["final_state"]))
    if [len(item["rows"]) for item in result["evidence"]] != [1, 13, 13]:
        raise RuntimeError("Real source row counts changed")
    return {"mode": ("approved_catalog_local_scripted_model" if approved_catalog else
                     "local_read_only_with_scripted_model_and_in_memory_catalog"),
            "catalog_file_unchanged": True, "provider_called": False,
            "model_calls": result["model_calls"], "queries": result["queries"],
            "roles": [event["role"] for event in result["trace"]],
            "source_ids": [item["source_id"] for item in result["evidence"]],
            "source_rows": [len(item["rows"]) for item in result["evidence"]],
            "max_model_input_bytes": max(len(json.dumps(event["input"],
                                                    ensure_ascii=False,
                                                    separators=(",", ":")).encode("utf-8"))
                                         for event in result["trace"]
                                         if event["role"] not in {"map_projection", "data_query"}),
            "status": result["status"], "scientific_score": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--approved-catalog", action="store_true")
    args = parser.parse_args()
    report = verify(approved_catalog=args.approved_catalog)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.open("x", encoding="utf-8").write(rendered)
    else:
        print(rendered, end="")
