"""Read-only local smoke of six pilot query paths; no model or provider calls.

The disabled catalog is copied and enabled only in memory for this explicit
technical check. This does not activate the Bancada harness or approve meaning.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inference_api/src"))
from inference_api.agent_harness import local_queries  # noqa: E402


CATALOG_PATH = ROOT / "specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json"
PLANS = [
    {"fonte_id": "machine", "campos": ["machine_id", "downtime_rows", "downtime_minutes"],
     "filtros": {"year": 2021, "id": 2000002}, "limite": 1, "grao": "machine_id/year"},
    {"fonte_id": "financial", "campos": ["observation_id", "observed_day", "reported_net_profit"],
     "filtros": {"year": 2021}, "limite": 20, "grao": "observation_id/date"},
    {"fonte_id": "contributors", "campos": ["fact", "total", "ids", "next_after"],
     "filtros": {"kind": "machine", "year": 2021, "id": 2000002,
                 "fact": "fact_downtime", "after": 0},
     "limite": 20, "grao": "aggregate_row/fact_id"},
    {"fonte_id": "trace", "campos": local_queries.LINEAGE_FIELDS["trace"],
     "filtros": {"fact": "fact_downtime", "id": 2900057},
     "limite": 1, "grao": "fact_id/source_row"},
    {"fonte_id": "paradas_maquinas_geradas",
     "campos": ["parada_id", "maquina_id", "hora_inicio_parada", "hora_fim_parada", "origem"],
     "filtros": {"maquina_id": 2000002,
                 "hora_inicio_parada": {"from": "2021-01-01T00:00:00",
                                        "to": "2022-01-01T00:00:00"}},
     "limite": 20, "grao": "parada_id/source_period"},
    {"fonte_id": "vendas",
     "campos": ["venda_id", "quantidade_vendida", "preco_unitario_venda", "data_venda"],
     "filtros": {"data_venda": {"from": "2021-01-01", "to": "2022-01-01"}},
     "limite": 20, "grao": "venda_id/source_period"},
]


def verify() -> dict:
    original = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if original.get("status") != "candidate_not_enabled":
        raise RuntimeError("Expected disabled catalog on disk")
    try:
        local_queries.execute(PLANS[0], original)
    except local_queries.LocalQueryRejected as exc:
        if str(exc) != "catalog_not_approved_for_local_query":
            raise
    else:
        raise RuntimeError("Disabled catalog was accepted")
    catalog = copy.deepcopy(original)
    catalog["status"] = "approved_for_local_query"
    for domain in catalog["domains"].values():
        for source_id, source in domain["sources"].items():
            if source_id in {plan["fonte_id"] for plan in PLANS}:
                source["enabled"] = True
    outputs = []
    for plan in PLANS:
        result = local_queries.execute(plan, catalog)
        if result["coverage"]["rows"] != len(result["rows"]):
            raise RuntimeError("Result coverage mismatch")
        outputs.append({"source_id": plan["fonte_id"],
                        "rows": len(result["rows"]),
                        "result_bytes": len(json.dumps(result, sort_keys=True,
                                                        ensure_ascii=False).encode("utf-8"))})
    if [item["rows"] for item in outputs] != [1, 13, 1, 1, 13, 11]:
        raise RuntimeError("Pilot source row count changed")
    return {"mode": "local_read_only_with_in_memory_catalog_override",
            "catalog_file_unchanged": True, "provider_called": False,
            "reader_role": "spec013_reader",
            "catalog_file_sha256": hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(),
            "sources": outputs}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify()
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.open("x", encoding="utf-8").write(rendered)
    else:
        print(rendered, end="")
