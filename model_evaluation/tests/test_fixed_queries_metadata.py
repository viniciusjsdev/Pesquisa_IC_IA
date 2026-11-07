"""Regression: metadata for one fixed query must not inspect another kind's rows."""

import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "BancoModeloUse"))
from dw import fixed_queries  # noqa: E402


class Cursor:
    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, *_):
        pass

    def fetchall(self):
        return self.rows


class Connection:
    def __init__(self, rows):
        self.rows = rows

    def cursor(self):
        return Cursor(self.rows)


class FixedQueryMetadataTests(unittest.TestCase):
    def test_financial_observation_builds_own_metadata(self):
        row = (1001, date(2021, 1, 31), Decimal("150.25"), Decimal("12.50"))
        result = fixed_queries.query("financial", 2021, None,
                                     connection=Connection([row]), readonly_already=True)
        self.assertEqual(result["coverage"]["rows"], 1)
        self.assertEqual(result["rows"][0]["reported_net_profit"], "12.50")
        self.assertEqual(result["sources"], ["db_financeiro.public.resultados_financeiros"])

    def test_financial_no_observation_is_distinct_from_zero(self):
        result = fixed_queries.query("financial", 2019, None,
                                     connection=Connection([]), readonly_already=True)
        self.assertEqual(result["coverage"]["state"], "no_observation")
        self.assertEqual(result["rows"], [])


if __name__ == "__main__":
    unittest.main()
