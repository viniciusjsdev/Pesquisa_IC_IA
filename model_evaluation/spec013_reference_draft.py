"""Prepare a private, read-only DW reference packet for six draft pilot cases.

The output contains source values and belongs only in ignored `.local/`.
It is not a reviewed gold set and must never be supplied to agent prompts.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "BancoModeloUse"))
from dw import fixed_queries  # noqa: E402
from scripts import bootstrap_local  # noqa: E402


CATALOG_PATH = ROOT / "specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json"
QUERIES = {
    "machine_2021_2000002": ("machine", 2021, 2000002),
    "machine_2026_1": ("machine", 2026, 1),
    "machine_2020_1000002": ("machine", 2020, 1000002),
    "financial_2021": ("financial", 2021, None),
    "financial_2019": ("financial", 2019, None),
    "financial_2020": ("financial", 2020, None),
}


def prepare(output: Path) -> dict:
    output = output.resolve()
    local_root = (ROOT / "model_evaluation/.local").resolve()
    if not output.is_relative_to(local_root):
        raise ValueError("Reference values must stay under ignored model_evaluation/.local")
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if catalog["status"] != "candidate_not_enabled":
        raise ValueError("Expected disabled pilot catalog")
    connection = bootstrap_local.connect("industrial", "db_pesquisa_dw")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SELECT version, source_fingerprint FROM dw.schema_migrations")
            migrations = cursor.fetchall()
            if len(migrations) != 1 or migrations[0][1] != catalog["dw_source_fingerprint"]:
                raise ValueError("DW fingerprint differs from the pilot catalog")
            version, fingerprint = migrations[0]
        results = {name: fixed_queries.query(kind, year, identifier,
                    connection=connection, readonly_already=True)
                   for name, (kind, year, identifier) in QUERIES.items()}
        connection.rollback()
    finally:
        connection.close()
    packet = {"status": "draft_not_reviewed", "mode": "local_read_only",
              "schema_version": version, "dw_source_fingerprint": fingerprint,
              "query_code_sha256": hashlib.sha256((ROOT / "BancoModeloUse/dw/fixed_queries.py").read_bytes()).hexdigest(),
              "catalog_sha256": hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(),
              "reference_queries": results}
    rendered = json.dumps(packet, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(rendered)
    return {"file": str(output), "sha256": hashlib.sha256(rendered).hexdigest(),
            "bytes": len(rendered), "source_rows": {name: item["coverage"]["rows"]
                                               for name, item in results.items()},
            "status": "draft_not_reviewed", "provider_called": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output), ensure_ascii=False, indent=2))
