"""Check identifier and temporal rules that would silently corrupt warehouse joins."""

from datetime import date
from decimal import Decimal
import os
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

    def test_full_row_comparison_rejects_changed_values_and_missing_rows(self):
        class Rows:
            def __init__(self, values):
                self.values = values
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def execute(self, query):
                pass
            def __iter__(self):
                return iter(self.values)
        class Origin:
            def cursor(self, name):
                return Rows([(1000001, Decimal('12.50'), date(2020, 1, 1))])
        class Target:
            def __init__(self, values):
                self.values = values
            def cursor(self, name):
                return Rows(self.values)
        class Cursor:
            def __init__(self, values):
                self.connection = Target(values)
        columns = ('id', 'value', 'day')
        loader = lambda values: cli.compare_rows(Cursor(values), Origin(), 'SELECT fixture',
            'fact_sale', columns, lambda row: row)
        self.assertEqual(loader([(1000001, Decimal('12.50'), date(2020, 1, 1))]), 1)
        for changed in ([(1000001, Decimal('13.50'), date(2020, 1, 1))],
                        [(1000001, Decimal('12.50'), date(2020, 1, 2))], []):
            with self.subTest(changed=changed), self.assertRaises(RuntimeError):
                loader(changed)

    def test_contributor_contract_rejects_unrelated_fact_before_database(self):
        with self.assertRaises(RuntimeError):
            cli.contributors('quality', 2020, 1000001, fact='fact_sale')
        with self.assertRaises(RuntimeError):
            cli.contributors('product', 2020, 1000001, after=1)


@unittest.skipUnless(os.environ.get('DW_LOCAL_INTEGRATION') == '1',
                     'Set DW_LOCAL_INTEGRATION=1 for read-only existing-load verification')
class ExistingLoadReadOnlyTests(unittest.TestCase):
    def test_loaded_migration_grain_and_foreign_keys(self):
        conn = cli.source.connect('industrial', cli.DATABASE)
        try:
            with conn, conn.cursor() as cur:
                cur.execute('SET TRANSACTION READ ONLY')
                state, digest = cli.target_state(conn)
                self.assertEqual((state, digest), ('loaded', cli.fingerprint(cli.source.inventory())))
                for _, fact in cli.FACTS.values():
                    with self.subTest(fact=fact):
                        cur.execute('''SELECT count(*), count(DISTINCT source_file_id::text || ':' || original_id::text)
                                       FROM dw.{}'''.format(fact))
                        total, grain = cur.fetchone()
                        self.assertEqual(total, grain)
                cur.execute('''SELECT count(*) FROM pg_constraint c
                    JOIN pg_class t ON t.oid=c.conrelid JOIN pg_namespace n ON n.oid=t.relnamespace
                    WHERE n.nspname='dw' AND c.contype='f' AND t.relname LIKE 'fact_%' ''')
                self.assertGreaterEqual(cur.fetchone()[0], 7)
        finally:
            conn.close()

    def test_different_source_fingerprint_is_refused_without_write(self):
        items = cli.source.inventory()
        key = next(iter(items))
        changed = {**items, key: {**items[key], 'sha256': '0' * 64}}
        conn = cli.source.connect('industrial', cli.DATABASE)
        try:
            with self.assertRaises(RuntimeError):
                cli.verify(items=changed, source_report={'databases': {}}, target=conn)
        finally:
            conn.close()

    def test_full_content_and_metadata_reconciliation(self):
        report = cli.verify()
        self.assertEqual(report['content_reconciliation']['mode'],
                         'full_source_projection_row_comparison')
        self.assertEqual(report['content_reconciliation']['facts'], report['facts'])
        self.assertEqual(report['content_reconciliation']['source_periods'], 3)

    def test_query_contributors_and_trace_follow_the_same_grain(self):
        expected = {'machine': ('machine_id', ('fact_operation', 'fact_downtime')),
                    'product': ('product_id', ('fact_operation', 'fact_sale')),
                    'quality': ('product_id', ('fact_quality_inspection',)),
                    'material': ('material_id', ('fact_material_consumption',
                                               'fact_material_price_observation'))}
        for kind, (key, facts) in expected.items():
            with self.subTest(kind=kind):
                row = cli.query(kind, 2020, 1000001)['rows'][0]
                self.assertEqual(row[key], 1000001)
                pages = cli.contributors(kind, 2020, row[key], limit=2)['contributors']
                self.assertEqual(tuple(page['fact'] for page in pages), facts)
                for page in pages:
                    self.assertEqual(page['ids'], sorted(page['ids']))
                    if page['ids']:
                        record = cli.trace(page['fact'], page['ids'][0])
                        self.assertEqual(record['dw_record'][key], row[key])
                        self.assertIn('raw_record', record)
                        self.assertIn('typed_record', record)
                if pages[0]['next_after'] is not None:
                    continued = cli.contributors(kind, 2020, row[key], fact=facts[0],
                                                 after=pages[0]['next_after'], limit=2)
                    self.assertGreater(continued['contributors'][0]['ids'][0], pages[0]['ids'][-1])

    def test_financial_rows_are_not_annualized(self):
        result = cli.query('financial', 2020, None)
        self.assertEqual(result['coverage']['state'], 'no_observation')
        self.assertEqual(result['coverage']['observed_months'], 0)
        self.assertEqual(result['rows'], [])


if __name__ == '__main__':
    unittest.main()
