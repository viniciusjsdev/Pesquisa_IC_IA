"""Local, read-only BI. Run with the BancoModeloUse virtual environment."""
from datetime import datetime, timezone
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
import logging
from pathlib import Path
import sys
import threading
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sqlalchemy import create_engine, text
from infrastructure.config.database_config import get_all_database_configs, get_database_url

SOURCES = {
    'vendas': ('financeiro', 'vendas', 'data_venda', 'Vendas',
              'Receita = soma de quantidade_vendida × preco_unitario_venda. Somente vendas presentes na base.'),
    'resultados': ('financeiro', 'resultados_financeiros', 'data_registro', 'Resultados financeiros',
                   'Valores reportados nos CSVs. Receita reportada e receita das vendas são fontes distintas, ainda não conciliadas.'),
    'custos': ('financeiro', 'custos_producao', 'data_registro', 'Custos de produção',
              'Custo unitário agregado = soma de custo_total / soma de unidades_produzidas, na própria tabela de custos.'),
    'operacoes': ('industrial', 'registros_operacao', 'hora_inicio', 'Registros de operação',
                  'Volume = soma de quantidade_produzida_real por operação; não equivale necessariamente a produtos acabados únicos.'),
    'equipamentos': ('industrial', 'equipamentos', 'data_registro', 'Indicadores de equipamentos',
                    'OEE, disponibilidade, performance e qualidade: médias simples das observações fornecidas, exibidas em %. OEE não é recalculado.'),
    'qualidade': ('industrial', 'controle_qualidade', 'data_inspecao', 'Inspeções de qualidade',
                  'Rejeição = unidades_rejeitadas / (unidades_aprovadas + unidades_rejeitadas). Unidades inspecionadas podem incluir reinspeções.'),
    'paradas': ('industrial', 'paradas_maquinas', 'hora_inicio_parada', 'Paradas de máquinas',
                'Horas = soma das durações dos eventos, atribuídas ao mês de início; sobreposições não são deduplicadas.'),
}
AGGREGATES = {
    'vendas': 'count(*) AS registros, sum(quantidade_vendida) AS quantidade, sum(quantidade_vendida * preco_unitario_venda) AS receita',
    'resultados': 'count(*) AS registros, sum(receita_total) AS receita_reportada, sum(lucro_liquido) AS lucro_liquido, sum(despesas_operacionais) AS despesas_operacionais',
    'custos': 'count(*) AS registros, sum(custo_total) AS custo_total, sum(unidades_produzidas) AS unidades, sum(materia_prima) AS materia_prima, sum(mao_obra_direta) AS mao_obra, sum(custos_indiretos) AS indiretos',
    'operacoes': 'count(*) AS registros, sum(quantidade_produzida_real) AS volume, sum(consumo_energia_kwh) AS energia',
    'equipamentos': 'count(*) AS registros, sum(oee) AS oee_soma, count(oee) AS oee_n, sum(disponibilidade) AS disponibilidade_soma, count(disponibilidade) AS disponibilidade_n, sum(performance) AS performance_soma, count(performance) AS performance_n, sum(qualidade) AS qualidade_soma, count(qualidade) AS qualidade_n',
    'qualidade': 'count(*) AS registros, sum(unidades_aprovadas) AS aprovadas, sum(unidades_rejeitadas) AS rejeitadas',
    'paradas': 'count(*) AS registros, sum(extract(epoch FROM (hora_fim_parada - hora_inicio_parada)) / 3600) AS horas',
}
# Fixed identifiers only: the HTTP API never accepts SQL or database credentials.
TABLES = {
    'industrial': 'consumo_materiais controle_qualidade equipamentos fornecedores lotes_materiais lotes_producao maquinas materiais ordens_producao paradas_maquinas processos_industriais produtos registros_operacao roteiros_producao'.split(),
    'financeiro': 'contas_contabeis custo_mao_obra_historico custos_indiretos_rateio custos_operacionais_variaveis custos_padrao custos_producao kpis_gerenciais lancamentos_financeiros materiais_custo_historico resultados_financeiros vendas'.split(),
}
ENGINES = {}
CACHE = None
CACHE_TIME = 0
LOCK = threading.Lock()


def engine(domain):
    if domain not in ENGINES:
        config = get_all_database_configs()[domain]
        if config['host'] not in ('127.0.0.1', 'localhost'):
            raise RuntimeError('BI requires a local database')
        ENGINES[domain] = create_engine(get_database_url(config), pool_pre_ping=True,
            connect_args={'connect_timeout': 5,
                          'options': '-c default_transaction_read_only=on -c statement_timeout=20000'})
    return ENGINES[domain]


def collect():
    payload = {'series': {}, 'sources': [], 'inventory': {}, 'snapshot_at': None,
               'synthetic': True, 'dw_used': False}
    for domain in TABLES:
        with engine(domain).connect() as conn, conn.begin():
            conn.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
            counts = {}
            for table in TABLES[domain]:
                counts[table] = conn.execute(text(f'SELECT count(*) FROM public.{table}')).scalar_one()
            payload['inventory'][domain] = counts
            for key, (source_domain, table, date_field, label, definition) in SOURCES.items():
                if source_domain != domain:
                    continue
                query = f"SELECT to_char(date_trunc('month', {date_field}), 'YYYY-MM') AS mes, {AGGREGATES[key]} FROM public.{table} WHERE {date_field} IS NOT NULL GROUP BY 1 ORDER BY 1"
                payload['series'][key] = [dict(row) for row in conn.execute(text(query)).mappings()]
                coverage = conn.execute(text(f"SELECT count(*) AS linhas, min({date_field})::text AS inicio, max({date_field})::text AS fim, count(*) FILTER (WHERE {date_field} IS NULL) AS sem_data FROM public.{table}")).mappings().one()
                payload['sources'].append(dict(key=key, domain=domain, table=table, date_field=date_field,
                                                label=label, definition=definition, **coverage))
    payload['snapshot_at'] = datetime.now(timezone.utc).isoformat()
    return payload


def snapshot(force=False):
    global CACHE, CACHE_TIME
    with LOCK:
        if CACHE is None or force or time.monotonic() - CACHE_TIME > 60:
            fresh = collect()
            CACHE = fresh
            CACHE_TIME = time.monotonic()
        return CACHE


def encode(value):
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(type(value).__name__)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path)
        try:
            if path.path == '/api/data':
                result = snapshot(force=path.query == 'refresh=1')
                content = json.dumps(result, default=encode, ensure_ascii=False, allow_nan=False).encode('utf-8')
                self.reply(200, 'application/json; charset=utf-8', content)
            elif path.path in ('/', '/index.html'):
                self.reply(200, 'text/html; charset=utf-8', Path(__file__).with_name('index.html').read_bytes())
            elif path.path == '/health':
                self.reply(200, 'application/json', b'{"status":"ok"}')
            else:
                self.reply(404, 'text/plain', b'Not found')
        except Exception as exc:
            # Connection exceptions can contain credentials/DSNs; never return their text.
            logging.error('BI request failed (%s)', type(exc).__name__)
            message = {'error': 'Não foi possível consultar o banco local. Confira se o PostgreSQL está iniciado e tente atualizar.'}
            self.reply(503, 'application/json; charset=utf-8', json.dumps(message, ensure_ascii=False).encode('utf-8'))

    def reply(self, status, mime, content):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8501)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'BI da pesquisa: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        for db_engine in ENGINES.values():
            db_engine.dispose()
