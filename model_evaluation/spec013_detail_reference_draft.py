"""Prepare private typed detail and lineage references for pilot questions.

Uses in-memory approval only for local read-only preparation. No model sees
these results; the official catalog remains disabled.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "BancoModeloUse"))
sys.path.insert(0, str(ROOT / "inference_api/src"))
from dw import cli as dw_cli  # noqa: E402
from inference_api.agent_harness.typed_detail import execute  # noqa: E402
from scripts import bootstrap_local  # noqa: E402


CATALOG_PATH = ROOT / "specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json"


def prepare(output: Path) -> dict:
    output = output.resolve()
    if not output.is_relative_to((ROOT / "model_evaluation/.local").resolve()):
        raise ValueError("Reference values must stay under ignored model_evaluation/.local")
    original = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if original["status"] != "candidate_not_enabled":
        raise ValueError("Expected disabled pilot catalog")
    catalog = copy.deepcopy(original)
    catalog["status"] = "approved_for_local_query"
    catalog["domains"]["industrial"]["sources"]["paradas_maquinas_geradas"]["enabled"] = True
    catalog["domains"]["financeiro"]["sources"]["vendas"]["enabled"] = True
    stops = execute("industrial", "paradas_maquinas_geradas", {
        "fonte_id": "paradas_maquinas_geradas",
        "campos": ["parada_id", "maquina_id", "hora_inicio_parada", "hora_fim_parada", "origem"],
        "filtros": {"maquina_id": 2000002,
                    "hora_inicio_parada": {"from": "2021-01-01T00:00:00",
                                           "to": "2022-01-01T00:00:00"}},
        "limite": 20, "grao": catalog["domains"]["industrial"]["sources"]["paradas_maquinas_geradas"]["grain"]},
        catalog, lambda: bootstrap_local.connect("industrial"),
        max_rows=20, max_bytes=32768)
    sales = execute("financeiro", "vendas", {
        "fonte_id": "vendas",
        "campos": ["venda_id", "produto_id", "quantidade_vendida",
                   "preco_unitario_venda", "data_venda"],
        "filtros": {"data_venda": {"from": "2021-01-01", "to": "2022-01-01"}},
        "limite": 20, "grao": catalog["domains"]["financeiro"]["sources"]["vendas"]["grain"]},
        catalog, lambda: bootstrap_local.connect("financeiro"),
        max_rows=20, max_bytes=32768)
    contributors = dw_cli.contributors("machine", 2021, 2000002,
                                       fact="fact_downtime", limit=100)
    if any(page["next_after"] is not None for page in contributors["contributors"]):
        raise ValueError("Contributor list requires pagination before draft is complete")
    generated_ids = {row["values"]["parada_id"] for row in stops["rows"]}
    contributor_ids = {item for page in contributors["contributors"] for item in page["ids"]}
    if not generated_ids <= contributor_ids:
        raise ValueError("Generated stop IDs missing from DW contributors")
    packet = {"status": "draft_not_reviewed", "catalog_enabled_on_disk": False,
              "catalog_sha256": hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(),
              "generated_stops_2021_machine_2000002": stops,
              "sales_2021": sales,
              "downtime_contributors_2021_machine_2000002": contributors}
    rendered = json.dumps(packet, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(rendered)
    return {"file": str(output), "sha256": hashlib.sha256(rendered).hexdigest(),
            "bytes": len(rendered), "generated_stop_rows": stops["coverage"]["rows"],
            "sales_rows": sales["coverage"]["rows"],
            "downtime_contributor_ids": sum(len(page["ids"]) for page in contributors["contributors"]),
            "generated_ids_confirmed_in_dw": len(generated_ids),
            "provider_called": False, "status": "draft_not_reviewed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output), ensure_ascii=False, indent=2))
