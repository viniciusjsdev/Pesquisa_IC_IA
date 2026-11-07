"""Explicit local-only smoke for five SPEC-013 typed sources; no model calls.

An in-memory copy of the approved pilot *scope* is promoted solely for this
read-only check. The catalog file and Bancada mode remain disabled. Only counts
and provenance booleans are written; row values never leave the process.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

import psycopg2
from psycopg2 import sql


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "BancoModeloUse"))
sys.path.insert(0, str(ROOT / "inference_api" / "src"))
from scripts import bootstrap_local  # noqa: E402
from inference_api.agent_harness.typed_detail import execute  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reader-credentials", type=Path,
                        help="Ignored JSON created by provision_spec013_reader.py")
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    if catalog.get("status") != "candidate_not_enabled":
        raise SystemExit("Expected disabled candidate catalog")
    reader = (json.loads(args.reader_credentials.read_text(encoding="utf-8"))
              if args.reader_credentials else None)
    if reader is not None and reader.get("user") != "spec013_reader":
        raise SystemExit("Expected the dedicated SPEC-013 reader role")
    def connect(domain):
        return (psycopg2.connect(**reader, dbname=catalog["domains"][domain]["database"])
                if reader is not None else bootstrap_local.connect(domain))
    report = []
    for domain in ("industrial", "financeiro"):
        for source_id, source in sorted(catalog["domains"][domain]["sources"].items()):
            if source["kind"] != "typed_table_detail":
                continue
            pk = source["primary_key"][0]
            connection = connect(domain)
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute(sql.SQL("SELECT min({}) FROM {}").format(
                        sql.Identifier(pk), sql.Identifier("public", source_id)))
                    row_id = cursor.fetchone()[0]
                connection.rollback()
            finally:
                connection.close()
            if type(row_id) is not int or row_id <= 0:
                raise RuntimeError(f"No sample row for {domain}.{source_id}")
            test_catalog = copy.deepcopy(catalog)
            test_catalog["status"] = "approved_for_local_query"
            test_catalog["domains"][domain]["sources"][source_id]["enabled"] = True
            plan = {"fonte_id": source_id, "campos": [pk],
                    "filtros": {pk: row_id}, "limite": 1, "grao": source["grain"]}
            result = execute(domain, source_id, plan, test_catalog,
                             lambda domain=domain: connect(domain))
            if result["coverage"]["rows"] != 1:
                raise RuntimeError(f"Unexpected row count for {domain}.{source_id}")
            origin = result["rows"][0]["provenance"]
            valid = origin["table"] == source_id and len(origin["source_file_sha256"]) == 64
            if not valid:
                raise RuntimeError(f"Provenance missing for {domain}.{source_id}")
            report.append({"domain": domain, "table": source_id,
                           "rows": 1, "period_index": origin["period_index"],
                           "source_file_recorded": valid})
    document = {"mode": "local_read_only_test_with_in_memory_catalog_override",
                "catalog_file_unchanged": True,
                "provider_called": False,
                "reader_role": reader["user"] if reader is not None else "local_admin",
                "catalog_sha256": hashlib.sha256(json.dumps(catalog, sort_keys=True,
                    ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest(),
                "sources": report}
    rendered = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.open("x", encoding="utf-8").write(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
