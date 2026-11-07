"""Read-only partition/provenance check for SPEC-013 typed source candidates.

Prints counts and hashes only, never row values or credentials. This verifies
the current isolated cluster; it does not approve semantic joins or activate
the catalog for inference.
"""

import argparse
import hashlib
import json
from pathlib import Path

from psycopg2 import sql

import bootstrap_local


def verify(catalog: dict) -> dict:
    if catalog.get("status") != "candidate_not_enabled":
        raise ValueError("Only the disabled catalog candidate can be checked")
    checks = []
    for domain in ("industrial", "financeiro"):
        domain_map = catalog["domains"][domain]
        if domain_map["schema"] != "public":
            raise ValueError("Typed source schema must be public")
        connection = bootstrap_local.connect(domain)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute("SET LOCAL statement_timeout = '30s'")
                for table_name, source in sorted(domain_map["sources"].items()):
                    if source["kind"] != "typed_table_detail":
                        continue
                    if source.get("enabled") is not False or len(source.get("primary_key", [])) != 1:
                        raise ValueError("Typed source must be disabled with one primary key")
                    pk = source["primary_key"][0]
                    cursor.execute(sql.SQL("""SELECT count(*),
                               count(*) FILTER (WHERE c.table_name IS NULL),
                               count(*) FILTER (WHERE t.{pk} < 1 OR t.{pk} >= %s),
                               count(DISTINCT t.{pk} / %s)
                               FROM {table} AS t LEFT JOIN public.canonical_source_file AS c
                               ON c.table_name = %s AND c.period_index = t.{pk} / %s""").format(
                        pk=sql.Identifier(pk), table=sql.Identifier("public", table_name)),
                        (3 * bootstrap_local.STRIDE, bootstrap_local.STRIDE,
                         table_name, bootstrap_local.STRIDE))
                    rows, missing_source, outside_range, periods = cursor.fetchone()
                    cursor.execute("""SELECT coalesce(sum(row_count), 0), count(*)
                                      FROM public.canonical_source_file WHERE table_name = %s""",
                                   (table_name,))
                    source_rows, source_partitions = cursor.fetchone()
                    checks.append({"domain": domain, "table": table_name,
                                   "rows": rows, "source_rows": source_rows,
                                   "source_partitions": source_partitions,
                                   "observed_periods": periods,
                                   "rows_without_source": missing_source,
                                   "ids_outside_period_range": outside_range,
                                   "matched": rows == source_rows and not missing_source
                                   and not outside_range})
            connection.rollback()
        finally:
            connection.close()
    body = {"catalog_sha256": hashlib.sha256(json.dumps(catalog, sort_keys=True,
             ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest(),
            "id_rule": "source_id + period_index * 1000000",
            "checks": checks}
    return {**body, "all_matched": bool(checks) and all(item["matched"] for item in checks)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(json.loads(args.catalog.read_text(encoding="utf-8")))
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.open("x", encoding="utf-8").write(rendered)
    else:
        print(rendered, end="")
    return 0 if report["all_matched"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
