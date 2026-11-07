"""Local, read-only V2 packet source with a narrow known-load readback.

This is deliberately not the V1 CSV-to-DW verifier: it checks the migration,
provenance rows and downtime split on the existing local load. The packet
labels that narrower scope instead of claiming complete source reconciliation.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "inference_api/src"))

from inference_api.agent_harness.approved_catalog import load  # noqa: E402
from inference_api.agent_harness.local_queries import _dw_connection  # noqa: E402
from BancoModeloUse.dw import fixed_queries  # noqa: E402


def _connection():
    return _dw_connection(load(), 10000)


def verify() -> dict:
    """Confirm only the reviewed V2 identity and critical provenance counts."""
    catalog = load()
    with closing(_dw_connection(catalog, 10000)) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM dw.source_file")
            source_files = cur.fetchone()[0]
            cur.execute("""SELECT s.table_name, count(*) FROM dw.fact_downtime f
                           JOIN dw.source_file s USING (source_file_id)
                           GROUP BY s.table_name""")
            downtime = dict(cur.fetchall())
        conn.rollback()
    if source_files != 167 or downtime != {"paradas_maquinas": 1200,
                                          "paradas_maquinas_geradas": 90}:
        raise ValueError("DW V2 provenance or downtime counts changed")
    return {"database": "db_pesquisa_dw", "schema_version": 2,
            "source_fingerprint": catalog["dw_source_fingerprint"],
            "source_files": source_files, "quality_flags": {}}


def query(kind: str, year: int, identifier: int | None) -> dict:
    with closing(_connection()) as conn:
        try:
            return fixed_queries.query(kind, year, identifier, connection=conn,
                                       readonly_already=True)
        finally:
            conn.rollback()
