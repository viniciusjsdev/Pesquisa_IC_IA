"""Read-only typed detail service; no provider or database is used here."""

import copy
import json
import sys
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inference_api" / "src"))
from inference_api.agent_harness.typed_detail import DetailRejected, execute  # noqa: E402


CATALOG_PATH = ROOT / "specs" / "active" / "SPEC-013" / "evidence" / "m0-semantic-map-candidate-2026-11-01.json"
CATALOG = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def promoted_catalog():
    catalog = copy.deepcopy(CATALOG)
    catalog["status"] = "approved_for_local_query"
    catalog["domains"]["industrial"]["sources"]["paradas_maquinas"]["enabled"] = True
    return catalog


PLAN = {"fonte_id": "paradas_maquinas", "campos": ["parada_id", "maquina_id", "hora_inicio_parada"],
        "filtros": {"parada_id": 1}, "limite": 2, "grao": "parada_id/source_period"}


class FakeConnection:
    def __init__(self, *, rows=None, files=None, database="db_industrial", field_types=None):
        self.rows = rows if rows is not None else [(1, 20, datetime(2015, 1, 1, 8))]
        self.files = files if files is not None else [(0, "period0/paradas.csv", "a" * 64)]
        self.database = database
        self.field_types = field_types if field_types is not None else list(
            CATALOG["domains"]["industrial"]["sources"]["paradas_maquinas"]["field_types"].items())
        self.calls = []
        self.fetches = 0
        self.closed = False
        self.rolled_back = False

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, statement, params=None):
        self.calls.append((statement, params))

    def fetchall(self):
        self.fetches += 1
        return {1: self.field_types, 2: self.files}.get(self.fetches, self.rows)

    def fetchone(self):
        return (self.database,)

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class TypedDetailTests(unittest.TestCase):
    def test_readonly_parameterized_detail_has_row_provenance(self):
        connection = FakeConnection()
        result = execute("industrial", "paradas_maquinas", PLAN,
                         promoted_catalog(), lambda: connection)
        self.assertEqual(result["coverage"], {"state": "observed", "rows": 1})
        self.assertEqual(result["rows"][0]["provenance"]["source_file_sha256"], "a" * 64)
        self.assertEqual(result["rows"][0]["values"]["hora_inicio_parada"], "2015-01-01T08:00:00")
        self.assertEqual(connection.calls[0][0], "SET TRANSACTION READ ONLY")
        self.assertEqual(connection.calls[-1][1], (1, 3))
        self.assertTrue(connection.rolled_back and connection.closed)

    def test_disabled_source_bad_field_and_no_filter_fail_before_connection(self):
        def forbidden():
            raise AssertionError("database must not be opened")
        with self.assertRaisesRegex(DetailRejected, "catalog_not_approved"):
            execute("industrial", "paradas_maquinas", PLAN, CATALOG, forbidden)
        catalog = promoted_catalog()
        for changes, reason in [({"campos": ["secret"]}, "fields_outside_catalog"),
                                ({"filtros": {}}, "filters_outside_catalog"),
                                ({"filtros": {"maquina_id": "1"}}, "invalid_id_filter")]:
            with self.subTest(changes=changes), self.assertRaisesRegex(DetailRejected, reason):
                execute("industrial", "paradas_maquinas", {**PLAN, **changes}, catalog, forbidden)

    def test_more_rows_than_plan_and_missing_source_fail_closed(self):
        catalog = promoted_catalog()
        extra = FakeConnection(rows=[(1, 20, datetime(2015, 1, 1)),
                                     (2, 21, datetime(2015, 1, 2)),
                                     (3, 22, datetime(2015, 1, 3))])
        with self.assertRaisesRegex(DetailRejected, "row_limit_exceeded"):
            execute("industrial", "paradas_maquinas", PLAN, catalog, lambda: extra)
        self.assertTrue(extra.rolled_back and extra.closed)
        missing = FakeConnection(files=[])
        with self.assertRaisesRegex(DetailRejected, "source_files_unavailable"):
            execute("industrial", "paradas_maquinas", PLAN, catalog, lambda: missing)

    def test_range_and_result_byte_limits(self):
        catalog = promoted_catalog()
        range_plan = {**PLAN, "filtros": {"hora_inicio_parada": {
            "from": "2015-01-01T00:00:00", "to": "2015-02-01T00:00:00"}}}
        connection = FakeConnection()
        execute("industrial", "paradas_maquinas", range_plan, catalog, lambda: connection)
        self.assertEqual(connection.calls[-1][1][-1], 3)
        with self.assertRaisesRegex(DetailRejected, "invalid_range_filter"):
            execute("industrial", "paradas_maquinas", {**range_plan,
                "filtros": {"hora_inicio_parada": {"from": "2015-02-01", "to": "2015-01-01"}}},
                catalog, lambda: FakeConnection())
        with self.assertRaisesRegex(DetailRejected, "result_byte_limit_exceeded"):
            execute("industrial", "paradas_maquinas", PLAN, catalog,
                    lambda: FakeConnection(), max_bytes=1)

    def test_database_and_physical_type_drift_fail_before_data_select(self):
        catalog = promoted_catalog()
        for connection, reason in [
            (FakeConnection(database="db_financeiro"), "source_database_mismatch"),
            (FakeConnection(field_types=[("parada_id", "text")]), "source_schema_mismatch"),
        ]:
            with self.subTest(reason=reason), self.assertRaisesRegex(DetailRejected, reason):
                execute("industrial", "paradas_maquinas", PLAN, catalog,
                        lambda connection=connection: connection)
            self.assertTrue(connection.rolled_back and connection.closed)
            self.assertFalse(any("ORDER BY" in str(statement) for statement, _ in connection.calls))


if __name__ == "__main__":
    unittest.main()
