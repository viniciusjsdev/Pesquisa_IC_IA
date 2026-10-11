"""Live integration checks against independent queries on the local database."""
import json
import unittest
from urllib.request import urlopen

from sqlalchemy import text
from server import engine


class LocalBITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with urlopen('http://127.0.0.1:8501/api/data?refresh=1', timeout=30) as response:
            cls.data = json.load(response)

    def test_inventory_matches_loaded_sources(self):
        self.assertEqual(sum(self.data['inventory']['industrial'].values()), 539140)
        self.assertEqual(sum(self.data['inventory']['financeiro'].values()), 1460)
        for source in self.data['sources']:
            rows = self.data['series'][source['key']]
            self.assertEqual(sum(r['registros'] for r in rows) + source['sem_data'], source['linhas'])

    def test_annual_sales_match_direct_sql(self):
        with engine('financeiro').connect() as conn:
            for year in (2015, 2021, 2025):
                exact = conn.execute(text('SELECT sum(quantidade_vendida * preco_unitario_venda) FROM vendas WHERE extract(year from data_venda) = :year'), {'year': year}).scalar_one()
                actual = sum(r['receita'] for r in self.data['series']['vendas'] if r['mes'].startswith(str(year)))
                self.assertAlmostEqual(actual, float(exact), places=6)

    def test_oee_weighting_matches_direct_average(self):
        rows = [r for r in self.data['series']['equipamentos'] if r['mes'].startswith('2021')]
        actual = sum(r['oee_soma'] for r in rows) / sum(r['oee_n'] for r in rows)
        with engine('industrial').connect() as conn:
            exact = conn.execute(text("SELECT avg(oee) FROM equipamentos WHERE data_registro >= '2021-01-01' AND data_registro < '2022-01-01'")).scalar_one()
        self.assertAlmostEqual(actual, exact, places=10)

    def test_rejection_is_ratio_of_totals(self):
        rows = self.data['series']['qualidade']
        actual = sum(r['rejeitadas'] for r in rows) / sum(r['aprovadas'] + r['rejeitadas'] for r in rows)
        with engine('industrial').connect() as conn:
            exact = conn.execute(text('SELECT sum(unidades_rejeitadas)::numeric / nullif(sum(unidades_aprovadas + unidades_rejeitadas),0) FROM controle_qualidade')).scalar_one()
        self.assertAlmostEqual(actual, float(exact), places=10)

    def test_missing_financial_periods_are_not_fabricated(self):
        for key in ('custos', 'resultados'):
            self.assertFalse(any(r['mes'] >= '2024-01' for r in self.data['series'][key]))
        self.assertTrue(any(r['mes'] == '2026-01' for r in self.data['series']['operacoes']))

    def test_connections_are_read_only(self):
        for domain in ('industrial', 'financeiro'):
            with engine(domain).connect() as conn:
                self.assertEqual(conn.execute(text('SHOW transaction_read_only')).scalar_one(), 'on')


if __name__ == '__main__':
    unittest.main()
