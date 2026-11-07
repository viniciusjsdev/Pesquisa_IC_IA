"""Read-only, count/ID-only profile for selecting SPEC-013 pilot cases.

This is case preparation, not a gold set. No row values or provider calls.
"""

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "BancoModeloUse"))
from scripts import bootstrap_local  # noqa: E402


QUERIES = {
    "generated_downtime_machine_year": """
        SELECT EXTRACT(YEAR FROM d.start_day)::int AS year, d.machine_id,
               count(*)::int AS rows
        FROM dw.fact_downtime d JOIN dw.source_file s USING (source_file_id)
        WHERE s.table_name = 'paradas_maquinas_geradas'
        GROUP BY 1, 2 ORDER BY rows DESC, year, machine_id LIMIT 12""",
    "finance_observations_by_year": """
        SELECT EXTRACT(YEAR FROM observed_day)::int AS year, count(*)::int AS rows
        FROM dw.fact_financial_observation GROUP BY 1 ORDER BY 1""",
    "downtime_by_year": """
        SELECT EXTRACT(YEAR FROM start_day)::int AS year, count(*)::int AS rows
        FROM dw.fact_downtime GROUP BY 1 ORDER BY 1""",
    "operations_by_year": """
        SELECT EXTRACT(YEAR FROM operation_day)::int AS year, count(*)::int AS rows
        FROM dw.fact_operation GROUP BY 1 ORDER BY 1""",
    "sales_by_year": """
        SELECT EXTRACT(YEAR FROM sale_day)::int AS year, count(*)::int AS rows
        FROM dw.fact_sale GROUP BY 1 ORDER BY 1""",
    "machine_without_2026_facts": """
        SELECT m.machine_id FROM dw.dim_machine m
        WHERE NOT EXISTS (SELECT 1 FROM dw.fact_operation o
                          WHERE o.machine_id = m.machine_id
                            AND o.operation_day >= DATE '2026-01-01'
                            AND o.operation_day < DATE '2027-01-01')
          AND NOT EXISTS (SELECT 1 FROM dw.fact_downtime d
                          WHERE d.machine_id = m.machine_id
                            AND d.start_day >= DATE '2026-01-01'
                            AND d.start_day < DATE '2027-01-01')
        ORDER BY m.machine_id LIMIT 3""",
    "machine_with_2020_downtime": """
        SELECT machine_id, count(*)::int AS rows FROM dw.fact_downtime
        WHERE start_day >= DATE '2020-01-01' AND start_day < DATE '2021-01-01'
        GROUP BY machine_id ORDER BY rows DESC, machine_id LIMIT 3""",
}


def profile() -> dict:
    connection = bootstrap_local.connect("industrial", "db_pesquisa_dw")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            results = {}
            for name, query in QUERIES.items():
                cursor.execute(query)
                names = [column.name for column in cursor.description]
                results[name] = [dict(zip(names, row)) for row in cursor.fetchall()]
        connection.rollback()
        return {"database": "db_pesquisa_dw", "mode": "read_only_counts_and_ids",
                "source_values_exposed": False, "candidate_profile": results}
    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(profile(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.open("x", encoding="utf-8").write(rendered)
    else:
        print(rendered, end="")
