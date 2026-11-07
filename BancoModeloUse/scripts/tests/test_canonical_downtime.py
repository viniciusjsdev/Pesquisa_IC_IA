"""Offline checks for the canonical downtime union; no database access."""

import csv
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import sys
import unittest


DATA_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DATA_ROOT))
from scripts import canonical_ingest as ingest  # noqa: E402
from dw.fixed_queries import query  # noqa: E402


class CanonicalDowntimeTests(unittest.TestCase):
    def test_generated_events_have_provenance_and_disjoint_ids(self):
        manifest = json.loads(ingest.MANIFEST.read_text(encoding='utf-8'))
        ids = {}
        counts = {}
        machines_by_period = {}
        for item in manifest:
            path = ingest.ROOT / item['caminho']
            if path.stem != 'maquinas':
                continue
            with path.open(encoding='utf-8-sig', newline='') as handle:
                machines_by_period[ingest.period_for(path)] = {
                    int(row['maquina_id']) for row in csv.DictReader(handle)
                }
        for name in ('paradas_maquinas', 'paradas_maquinas_geradas'):
            count = 0
            for item in manifest:
                path = ingest.ROOT / item['caminho']
                if path.stem != name:
                    continue
                period = ingest.period_for(path)
                with path.open(encoding='utf-8-sig', newline='') as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(len(rows), int(item['linhas']))
                for row in rows:
                    mapped_id = period * ingest.STRIDE + int(row['parada_id'])
                    self.assertNotIn(mapped_id, ids)
                    ids[mapped_id] = item['caminho']
                    if name == 'paradas_maquinas_geradas':
                        self.assertIn(int(row['maquina_id']),
                                      machines_by_period[period])
                count += len(rows)
            counts[name] = count
        self.assertEqual(counts, {'paradas_maquinas': 1200,
                                  'paradas_maquinas_geradas': 90})
        self.assertEqual(len(ids), 1290)

    def test_generated_projection_preserves_id_duration_and_origin(self):
        row = ingest.generated_downtime_row(
            (900132, 3, datetime(2015, 2, 12, 10),
             datetime(2015, 2, 12, 12, 30)),
            42, 0, 'dados_complementares_datamind/gerados/periodo_2015_2016/paradas_maquinas_geradas.csv')
        self.assertEqual(row[:6], (900132, 42, 0, 900132,
                                   datetime(2015, 2, 12).date(), 3))
        self.assertEqual(row[8:], (Decimal('150'), False, False))

    def test_machine_query_reports_only_loaded_downtime_sources(self):
        class Cursor:
            calls = 0
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def execute(self, statement, params=None):
                self.calls += 1
            def fetchall(self):
                if self.calls == 1:
                    return [(3, 1, 10, 2, Decimal('150'))]
                return [('paradas_maquinas',), ('paradas_maquinas_geradas',)]
        class Connection:
            def cursor(self):
                return Cursor()
        result = query('machine', 2020, 3, connection=Connection(), readonly_already=True)
        self.assertEqual(result['rows'][0]['downtime_rows'], 2)
        self.assertIn('db_industrial.public.paradas_maquinas_geradas', result['sources'])
        self.assertIn('synthetic', result['interpretation'])

    def test_generated_loader_appends_each_period_with_its_source_file(self):
        captured = []
        class SourceCursor:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def execute(self, statement, params):
                self.period = params[0] // ingest.STRIDE
            def fetchall(self):
                year = (2015, 2017, 2021)[self.period]
                return [(self.period * ingest.STRIDE + 900001, 3,
                         datetime(year, 1, 2, 10), datetime(year, 1, 2, 11))]
        class Origin:
            def cursor(self):
                return SourceCursor()
        class TargetCursor:
            def execute(self, statement):
                pass
            def fetchone(self):
                return (len(captured),)
        parts = [{'caminho': f'gerados/periodo_{a}_{b}/paradas_maquinas_geradas.csv',
                  'period': period, 'linhas': 1}
                 for period, (a, b) in enumerate(((2015, 2016), (2017, 2020),
                                                   (2021, 2025)))]
        ids = {('industrial', period, 'paradas_maquinas_geradas'): 20 + period
               for period in range(3)}
        def collect(cur, statement, values, page_size):
            captured.extend(values)
        total = ingest.load_generated_downtime(
            TargetCursor(), Origin(), parts, ids, collect)
        self.assertEqual(total, 3)
        self.assertEqual([(row[1], row[2], row[3]) for row in captured],
                         [(20, 0, 900001), (21, 1, 900001), (22, 2, 900001)])
        self.assertTrue(all(row[8] == Decimal('60') for row in captured))


if __name__ == '__main__':
    unittest.main()
