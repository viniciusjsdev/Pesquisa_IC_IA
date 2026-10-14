"""Check identifier and temporal rules that would silently corrupt warehouse joins."""

from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cli


class WarehouseContractTests(unittest.TestCase):
    def test_source_ids_keep_period_partition(self):
        self.assertEqual(cli.key_parts(1), (0, 1))
        self.assertEqual(cli.key_parts(1_000_001), (1, 1))
        self.assertEqual(cli.key_parts(2_000_001), (2, 1))
        for invalid in (0, 1_000_000, 3_000_001):
            with self.subTest(invalid=invalid), self.assertRaises(RuntimeError):
                cli.key_parts(invalid)

    def test_actual_date_is_checked_against_source_label(self):
        self.assertFalse(cli.outside_label('industrial', 0, date(2017, 1, 1)))
        self.assertTrue(cli.outside_label('industrial', 2, date(2026, 1, 1)))
        self.assertFalse(cli.outside_label('financeiro', 0, date(2016, 12, 31)))

    def test_fingerprint_changes_when_a_source_file_changes(self):
        original = {('industrial', 0, 'produtos'): {'sha256': 'a' * 64, 'rows': [{}]}}
        changed = {('industrial', 0, 'produtos'): {'sha256': 'b' * 64, 'rows': [{}]}}
        self.assertEqual(cli.fingerprint(original), cli.fingerprint(dict(original)))
        self.assertNotEqual(cli.fingerprint(original), cli.fingerprint(changed))


if __name__ == '__main__':
    unittest.main()
