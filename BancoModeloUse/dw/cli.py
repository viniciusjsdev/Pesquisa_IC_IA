"""Build and verify the isolated, source-traceable local research warehouse."""

from __future__ import annotations

import argparse
from datetime import date, datetime
from decimal import Decimal
import hashlib
from itertools import zip_longest
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values, Json

from scripts import bootstrap_local as source
from dw.fixed_queries import query

DATABASE = 'db_pesquisa_dw'
VERSION = 1
MIGRATION = Path(__file__).resolve().parent / 'migrations' / '001_init.sql'
REPORT = ROOT / 'reports' / 'dw_validation.json'
STRIDE = source.STRIDE

FACTS = {
    'registros_operacao': ('industrial', 'fact_operation'),
    'paradas_maquinas': ('industrial', 'fact_downtime'),
    'vendas': ('financeiro', 'fact_sale'),
    'resultados_financeiros': ('financeiro', 'fact_financial_observation'),
    'controle_qualidade': ('industrial', 'fact_quality_inspection'),
    'consumo_materiais': ('industrial', 'fact_material_consumption'),
    'materiais_custo_historico': ('financeiro', 'fact_material_price_observation'),
}


def key_parts(mapped_id: int) -> tuple[int, int]:
    period, original = divmod(mapped_id, STRIDE)
    source.require(period in (0, 1, 2) and original > 0, f'Invalid mapped source ID: {mapped_id}')
    return period, original


def outside_label(domain: str, period: int, actual: date | datetime | None) -> bool:
    if actual is None:
        return False
    folder = source.PERIODS[domain][period]
    match = re.search(r'(\d{4})_(\d{4})$', folder)
    source.require(match is not None, f'Folder has no year label: {folder}')
    return not (int(match[1]) <= actual.year <= int(match[2]))


def fingerprint(items: dict) -> str:
    manifest = [(domain, period, table, item['sha256'], len(item['rows']))
                for (domain, period, table), item in sorted(items.items())]
    return hashlib.sha256(json.dumps(manifest, separators=(',', ':')).encode()).hexdigest()


def file_ids(items: dict) -> dict:
    return {key: index for index, key in enumerate(sorted(items), start=1)}


def create_target_if_absent() -> bool:
    conn = source.connect('industrial', 'postgres')
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (DATABASE,))
            if cur.fetchone():
                return False
            cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(DATABASE)))
            return True
    finally:
        conn.close()


def target_state(conn) -> tuple[str, str | None]:
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass('dw.schema_migrations')")
        if cur.fetchone()[0] is not None:
            cur.execute('SELECT version, source_fingerprint FROM dw.schema_migrations')
            rows = cur.fetchall()
            source.require(len(rows) == 1 and rows[0][0] == VERSION,
                           'Unknown or incomplete DW migration; refusing to modify it.')
            return 'loaded', rows[0][1].strip()
        cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")
        table_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM pg_namespace WHERE nspname = 'dw'")
        schema_count = cur.fetchone()[0]
        source.require(table_count == 0 and schema_count == 0,
                       'Target database contains unrecognized objects; refusing to modify it.')
        return 'empty', None


def source_files(cur, items: dict, ids: dict) -> None:
    rows = []
    for key in sorted(items):
        domain, period, table = key
        item = items[key]
        rows.append((ids[key], domain, period, table, item['pk'], f'raw_p{period}',
                     item['path'].relative_to(ROOT).as_posix(), item['sha256'], len(item['rows'])))
    execute_values(cur, 'INSERT INTO dw.source_file VALUES %s', rows)
    execute_values(cur, 'INSERT INTO dw.dim_source_period VALUES %s',
                   [(p, source.PERIODS['industrial'][p], source.PERIODS['financeiro'][p])
                    for p in range(3)])


def day_dimension(cur, report: dict) -> None:
    dates = [date.fromisoformat(extreme[:10])
             for item in report['files'] for bounds in item['dates'].values()
             for extreme in bounds.values()]
    source.require(dates, 'Source date inventory is empty.')
    cur.execute('''INSERT INTO dw.dim_day (day, year, month, day_of_month)
                   SELECT d::date, extract(year FROM d)::integer,
                          extract(month FROM d)::integer, extract(day FROM d)::integer
                   FROM generate_series(%s::date, %s::date, interval '1 day') d''',
                (min(dates), max(dates)))


def load_rows(target_cur, origin, query: str, table: str, columns: tuple[str, ...], transform,
              *, batch_size: int = 5000) -> int:
    identifier = sql.SQL('{}.{}').format(sql.Identifier('dw'), sql.Identifier(table))
    names = sql.SQL(',').join(map(sql.Identifier, columns))
    statement = sql.SQL('INSERT INTO {} ({}) VALUES %s').format(identifier, names).as_string(target_cur.connection)
    count = 0
    with origin.cursor(name=f'dw_{table}') as cursor:
        cursor.itersize = batch_size
        cursor.execute(query)
        while batch := cursor.fetchmany(batch_size):
            values = [transform(row) for row in batch]
            execute_values(target_cur, statement, values, page_size=batch_size)
            count += len(values)
    return count


def compare_rows(target_cur, origin, query: str, table: str, columns: tuple[str, ...], transform,
                 *, batch_size: int = 5000) -> int:
    """Compare every loaded value with the same source projection used by build."""
    target_query = sql.SQL('SELECT {} FROM dw.{} ORDER BY {}').format(
        sql.SQL(',').join(map(sql.Identifier, columns)), sql.Identifier(table), sql.Identifier(columns[0]))
    count = 0
    with origin.cursor(name=f'compare_origin_{table}') as origin_cur, \
            target_cur.connection.cursor(name=f'compare_dw_{table}') as dw_cur:
        origin_cur.itersize = dw_cur.itersize = batch_size
        origin_cur.execute(query)
        dw_cur.execute(target_query)
        for expected, actual in zip_longest((transform(row) for row in origin_cur), dw_cur):
            source.require(expected is not None and actual is not None,
                           f'{table} source/DW row count differs at position {count + 1}.')
            comparable = lambda value: Decimal(str(value)) if isinstance(value, (float, Decimal)) else value
            source.require(tuple(map(comparable, expected)) == tuple(map(comparable, actual)),
                           f'{table} source/DW value differs at ID {expected[0]}.')
            count += 1
    return count


def load_dimensions(cur, origins: dict, ids: dict, loader=load_rows) -> None:
    dimensions = [
        ('produtos', 'dim_product', ('product_id','period_index','source_file_id','original_id','name','unit'),
         'SELECT produto_id,nome_produto,unidade_medida FROM public.produtos ORDER BY produto_id'),
        ('maquinas', 'dim_machine', ('machine_id','period_index','source_file_id','original_id','name','production_line'),
         'SELECT maquina_id,nome_maquina,linha_producao FROM public.maquinas ORDER BY maquina_id'),
        ('materiais', 'dim_material', ('material_id','period_index','source_file_id','original_id','name','unit'),
         'SELECT material_id,nome_material,unidade_medida FROM public.materiais ORDER BY material_id'),
    ]
    for source_table, target_table, columns, query in dimensions:
        def transform(row, table=source_table):
            period, original = key_parts(row[0])
            return (row[0], period, ids['industrial', period, table], original, row[1], row[2])
        loader(cur, origins['industrial'], query, target_table, columns, transform)
    columns = ('material_lot_id','period_index','source_file_id','original_id','material_id','received_on')
    def lot(row):
        period, original = key_parts(row[0])
        return (row[0], period, ids['industrial', period, 'lotes_materiais'], original, row[1], row[2])
    loader(cur, origins['industrial'],
              'SELECT lote_id,material_id,data_recebimento FROM public.lotes_materiais ORDER BY lote_id',
              'dim_material_lot', columns, lot)


def load_facts(cur, origins: dict, ids: dict, loader=load_rows) -> dict[str, int]:
    totals = {}
    def meta(domain, table, mapped_id):
        period, original = key_parts(mapped_id)
        return ids[domain, period, table], period, original

    table = 'registros_operacao'
    columns = ('operation_id','source_file_id','period_index','original_id','operation_day','order_id',
               'machine_id','product_id','started_at','ended_at','quantity_reported','energy_kwh',
               'setup_minutes','order_dates_inverted','interval_invalid','outside_source_label')
    def operation(r):
        file_id, period, original = meta('industrial', table, r[0])
        start, end = r[4], r[5]
        return (r[0], file_id, period, original, start.date() if start else None, r[1], r[2], r[3],
                start, end, r[6], r[7], r[8], bool(r[9]), bool(start and end and end < start),
                outside_label('industrial', period, start))
    totals[table] = loader(cur, origins['industrial'],
        '''SELECT r.registro_id,r.ordem_producao_id,r.maquina_id,o.produto_id,r.hora_inicio,r.hora_fim,
                  r.quantidade_produzida_real,r.consumo_energia_kwh,r.tempo_setup_real_min,
                  (o.data_inicio_real > o.data_fim_real)
           FROM public.registros_operacao r JOIN public.ordens_producao o
             ON o.ordem_producao_id=r.ordem_producao_id ORDER BY r.registro_id''',
        'fact_operation', columns, operation)

    table = 'paradas_maquinas'
    columns = ('downtime_id','source_file_id','period_index','original_id','start_day','machine_id',
               'started_at','ended_at','duration_minutes','interval_invalid','outside_source_label')
    def downtime(r):
        file_id, period, original = meta('industrial', table, r[0])
        start, end = r[2], r[3]
        invalid = bool(start and end and end < start)
        duration = Decimal(str((end - start).total_seconds())) / 60 if start and end and not invalid else None
        return (r[0], file_id, period, original, start.date() if start else None, r[1], start, end,
                duration, invalid, outside_label('industrial', period, start))
    totals[table] = loader(cur, origins['industrial'],
        'SELECT parada_id,maquina_id,hora_inicio_parada,hora_fim_parada FROM public.paradas_maquinas ORDER BY parada_id',
        'fact_downtime', columns, downtime)

    table = 'vendas'
    columns = ('sale_id','source_file_id','period_index','original_id','sale_day','product_id',
               'quantity_sold','unit_price','observed_sales_value','outside_source_label')
    def sale(r):
        file_id, period, original = meta('financeiro', table, r[0])
        value = r[3] * r[2] if r[2] is not None and r[3] is not None else None
        return (r[0], file_id, period, original, r[1], r[4], r[2], r[3], value,
                outside_label('financeiro', period, r[1]))
    totals[table] = loader(cur, origins['financeiro'],
        'SELECT venda_id,data_venda,quantidade_vendida,preco_unitario_venda,produto_id FROM public.vendas ORDER BY venda_id',
        'fact_sale', columns, sale)

    table = 'resultados_financeiros'
    columns = ('observation_id','source_file_id','period_index','original_id','observed_day',
               'reported_revenue','reported_net_profit','source_float','outside_source_label')
    def financial(r):
        file_id, period, original = meta('financeiro', table, r[0])
        return (r[0], file_id, period, original, r[1].date() if r[1] else None,
                r[2], r[3], True, outside_label('financeiro', period, r[1]))
    totals[table] = loader(cur, origins['financeiro'],
        'SELECT id,data_registro,receita_total,lucro_liquido FROM public.resultados_financeiros ORDER BY id',
        'fact_financial_observation', columns, financial)

    table = 'controle_qualidade'
    columns = ('inspection_id','source_file_id','period_index','original_id','inspection_day',
               'production_lot_id','order_id','product_id','approved_units','rejected_units',
               'lot_quantity','inspected_exceeds_lot','outside_source_label')
    def quality(r):
        file_id, period, original = meta('industrial', table, r[0])
        inspected = (r[5] or 0) + (r[6] or 0)
        return (r[0], file_id, period, original, r[4].date() if r[4] else None, r[1], r[2],
                r[3], r[5], r[6], r[7], bool(r[7] is not None and inspected > r[7]),
                outside_label('industrial', period, r[4]))
    totals[table] = loader(cur, origins['industrial'],
        '''SELECT c.controle_id,c.lote_producao_id,l.ordem_producao_id,o.produto_id,c.data_inspecao,
                  c.unidades_aprovadas,c.unidades_rejeitadas,l.quantidade_total
           FROM public.controle_qualidade c JOIN public.lotes_producao l USING (lote_producao_id)
           JOIN public.ordens_producao o USING (ordem_producao_id) ORDER BY c.controle_id''',
        'fact_quality_inspection', columns, quality)

    table = 'consumo_materiais'
    columns = ('consumption_id','source_file_id','period_index','original_id','registered_day',
               'operation_id','material_id','material_lot_id','quantity_consumed','outside_source_label')
    def consumption(r):
        file_id, period, original = meta('industrial', table, r[0])
        return (r[0], file_id, period, original, r[5].date() if r[5] else None,
                r[1], r[2], r[3], r[4], outside_label('industrial', period, r[5]))
    totals[table] = loader(cur, origins['industrial'],
        'SELECT consumo_id,registro_id,material_id,lote_material_id,quantidade_consumida,data_registro FROM public.consumo_materiais ORDER BY consumo_id',
        'fact_material_consumption', columns, consumption)

    table = 'materiais_custo_historico'
    columns = ('price_observation_id','source_file_id','period_index','original_id','purchase_day',
               'material_id','material_lot_id','unit_price','outside_source_label')
    def price(r):
        file_id, period, original = meta('financeiro', table, r[0])
        return (r[0], file_id, period, original, r[4], r[1], r[2], r[3],
                outside_label('financeiro', period, r[4]))
    totals[table] = loader(cur, origins['financeiro'],
        'SELECT custo_material_id,material_id,lote_material_id,custo_unitario,data_compra FROM public.materiais_custo_historico ORDER BY custo_material_id',
        'fact_material_price_observation', columns, price)
    return totals


def build() -> dict:
    items = source.inventory()
    digest = fingerprint(items)
    source_report = source.verify(items)  # full, read-only raw/public reconciliation before any DW write
    created = create_target_if_absent()
    target = source.connect('industrial', DATABASE)
    try:
        state, previous = target_state(target)
        target.commit()
        if state == 'loaded':
            source.require(previous == digest, 'DW source fingerprint differs; refusing automatic replacement.')
            result = verify(items=items, source_report=source_report, target=target)
            result['build_status'] = 'already_current'
            return result
        origins = {domain: source.connect(domain) for domain in ('industrial', 'financeiro')}
        try:
            for conn in origins.values():
                with conn.cursor() as cur:
                    cur.execute('SET TRANSACTION READ ONLY')
            ids = file_ids(items)
            with target:
                with target.cursor() as cur:
                    cur.execute(MIGRATION.read_text(encoding='utf-8'))
                    source_files(cur, items, ids)
                    day_dimension(cur, source_report)
                    load_dimensions(cur, origins, ids)
                    totals = load_facts(cur, origins, ids)
                    for table, (domain, _) in FACTS.items():
                        expected = source_report['databases'][domain]['tables'][table]
                        source.require(totals[table] == expected,
                                       f'Fact count mismatch during build: {table}: {totals[table]} != {expected}')
                    cur.execute('INSERT INTO dw.schema_migrations (version,source_fingerprint,source_checks) VALUES (%s,%s,%s)',
                                (VERSION, digest, Json({'files': len(items), 'source_rows':
                                    {d: source_report['databases'][d]['rows'] for d in origins}})))
                    cur.execute('ANALYZE')
        finally:
            for conn in origins.values():
                conn.close()
        result = verify(items=items, source_report=source_report, target=target)
        result['build_status'] = 'created' if created else 'loaded_empty_target'
        return result
    finally:
        target.close()


def verify(*, items=None, source_report=None, target=None) -> dict:
    items = items or source.inventory()
    source_report = source_report or source.verify(items)
    close_target = target is None
    target = target or source.connect('industrial', DATABASE)
    try:
        state, previous = target_state(target)
        source.require(state == 'loaded' and previous == fingerprint(items),
                       'DW absent, incomplete or based on different source files.')
        target.commit()
        result = {'database': DATABASE, 'schema_version': VERSION, 'source_fingerprint': previous,
                  'source_files': len(items), 'source_rows': source_report['databases'],
                  'facts': {}, 'dimensions': {}, 'quality_flags': {}, 'quality_examples': {},
                  'lineage_samples': {}, 'reconciliation': {}, 'content_reconciliation': {}}
        with target:
            with target.cursor() as cur:
                cur.execute('SET TRANSACTION READ ONLY')
                cur.execute('SELECT count(*) FROM dw.source_file')
                source.require(cur.fetchone()[0] == len(items), 'Source manifest count mismatch.')
                cur.execute('SELECT source_file_id,domain,period_index,table_name,pk_column,raw_schema,sha256,row_count,source_path FROM dw.source_file')
                stored_files = {(d,p,t): (file_id, pk, raw, sha.strip(), count, path)
                                for file_id,d,p,t,pk,raw,sha,count,path in cur.fetchall()}
                ids = file_ids(items)
                expected_files = {key: (ids[key], item['pk'], f'raw_p{key[1]}', item['sha256'],
                                        len(item['rows']), item['path'].relative_to(ROOT).as_posix())
                                  for key, item in items.items()}
                source.require(stored_files == expected_files, 'DW source manifest differs from current CSV inventory.')
                for table, (domain, fact) in FACTS.items():
                    cur.execute(sql.SQL('SELECT count(*) FROM dw.{}').format(sql.Identifier(fact)))
                    count = cur.fetchone()[0]
                    expected = source_report['databases'][domain]['tables'][table]
                    source.require(count == expected, f'{fact} count mismatch: {count} != {expected}')
                    result['facts'][fact] = count
                    cur.execute(sql.SQL('''SELECT count(*) FROM dw.{} f JOIN dw.source_file s USING (source_file_id)
                        WHERE s.domain <> %s OR s.table_name <> %s OR s.period_index <> f.period_index
                           OR f.original_id <> f.{} %% %s''').format(sql.Identifier(fact),
                           sql.Identifier({'fact_operation':'operation_id','fact_downtime':'downtime_id',
                             'fact_sale':'sale_id','fact_financial_observation':'observation_id',
                             'fact_quality_inspection':'inspection_id','fact_material_consumption':'consumption_id',
                             'fact_material_price_observation':'price_observation_id'}[fact])),
                        (domain, table, STRIDE))
                    source.require(cur.fetchone()[0] == 0, f'{fact} lineage mismatch.')
                    fact_pk = {'fact_operation':'operation_id','fact_downtime':'downtime_id',
                        'fact_sale':'sale_id','fact_financial_observation':'observation_id',
                        'fact_quality_inspection':'inspection_id','fact_material_consumption':'consumption_id',
                        'fact_material_price_observation':'price_observation_id'}[fact]
                    samples = []
                    for direction in ('ASC', 'DESC'):
                        cur.execute(sql.SQL('''SELECT f.{}, f.original_id, s.period_index, s.raw_schema, s.pk_column
                            FROM dw.{} f JOIN dw.source_file s USING (source_file_id)
                            ORDER BY f.{} {} LIMIT 1''').format(sql.Identifier(fact_pk), sql.Identifier(fact),
                                sql.Identifier(fact_pk), sql.SQL(direction)))
                        mapped, original, period, raw_schema, pk_column = cur.fetchone()
                        origin = source.connect(domain)
                        try:
                            with origin, origin.cursor() as origin_cur:
                                origin_cur.execute('SET TRANSACTION READ ONLY')
                                origin_cur.execute(sql.SQL('SELECT 1 FROM public.{} WHERE {}=%s').format(
                                    sql.Identifier(table), sql.Identifier(pk_column)), (mapped,))
                                source.require(origin_cur.fetchone() is not None, f'{fact} typed lineage sample missing.')
                                origin_cur.execute(sql.SQL('SELECT 1 FROM {}.{} WHERE {}::integer=%s').format(
                                    sql.Identifier(raw_schema), sql.Identifier(table), sql.Identifier(pk_column)),
                                    (original,))
                                source.require(origin_cur.fetchone() is not None, f'{fact} raw lineage sample missing.')
                        finally:
                            origin.close()
                        samples.append({'mapped_id': mapped, 'original_id': original, 'period_index': period})
                    result['lineage_samples'][fact] = samples
                for table, domain, source_table in [('dim_product','industrial','produtos'),
                    ('dim_machine','industrial','maquinas'), ('dim_material','industrial','materiais'),
                    ('dim_material_lot','industrial','lotes_materiais')]:
                    cur.execute(sql.SQL('SELECT count(*) FROM dw.{}').format(sql.Identifier(table)))
                    count = cur.fetchone()[0]
                    expected = source_report['databases'][domain]['tables'][source_table]
                    source.require(count == expected, f'{table} count mismatch.')
                    result['dimensions'][table] = count
                cur.execute('SELECT period_index,industrial_folder,financeiro_folder FROM dw.dim_source_period ORDER BY period_index')
                source.require(cur.fetchall() == [(p, source.PERIODS['industrial'][p],
                            source.PERIODS['financeiro'][p]) for p in range(3)],
                            'dim_source_period content mismatch.')
                dates = [date.fromisoformat(extreme[:10]) for item in source_report['files']
                         for bounds in item['dates'].values() for extreme in bounds.values()]
                source.require(bool(dates), 'Source date inventory is empty.')
                cur.execute('''SELECT count(*), min(day), max(day),
                            count(*) FILTER (WHERE year <> extract(year FROM day)::integer
                              OR month <> extract(month FROM day)::integer
                              OR day_of_month <> extract(day FROM day)::integer)
                            FROM dw.dim_day''')
                days_count, first_day, last_day, invalid_days = cur.fetchone()
                source.require(first_day == min(dates) and last_day == max(dates)
                    and days_count == (max(dates) - min(dates)).days + 1 and invalid_days == 0,
                    'dim_day content mismatch.')
                origins = {domain: source.connect(domain) for domain in ('industrial', 'financeiro')}
                try:
                    for origin in origins.values():
                        with origin.cursor() as origin_cur:
                            origin_cur.execute('SET TRANSACTION READ ONLY')
                    load_dimensions(cur, origins, ids, loader=compare_rows)
                    compared = load_facts(cur, origins, ids, loader=compare_rows)
                    source.require(all(compared[table] == result['facts'][fact]
                                       for table, (_, fact) in FACTS.items()),
                                   'Full fact comparison count mismatch.')
                    result['content_reconciliation'] = {'mode': 'full_source_projection_row_comparison',
                        'dimensions': {name: result['dimensions'][name] for name in result['dimensions']},
                        'facts': {fact: result['facts'][fact] for _, fact in FACTS.values()},
                        'source_periods': 3, 'days': days_count}
                finally:
                    for origin in origins.values():
                        origin.close()
                checks = [
                    ('operation_quantity', 'SELECT sum(quantity_reported) FROM dw.fact_operation',
                     'industrial', 'SELECT sum(quantidade_produzida_real) FROM public.registros_operacao'),
                    ('sale_quantity', 'SELECT sum(quantity_sold) FROM dw.fact_sale',
                     'financeiro', 'SELECT sum(quantidade_vendida) FROM public.vendas'),
                    ('observed_sales_value', 'SELECT sum(observed_sales_value) FROM dw.fact_sale',
                     'financeiro', 'SELECT sum(quantidade_vendida * preco_unitario_venda) FROM public.vendas'),
                ]
                for name, dw_query, domain, origin_query in checks:
                    cur.execute(dw_query)
                    dw_value = cur.fetchone()[0]
                    origin = source.connect(domain)
                    try:
                        with origin, origin.cursor() as source_cur:
                            source_cur.execute('SET TRANSACTION READ ONLY')
                            source_cur.execute(origin_query)
                            source_value = source_cur.fetchone()[0]
                    finally:
                        origin.close()
                    source.require(dw_value == source_value, f'{name} aggregate mismatch.')
                    result['reconciliation'][name] = str(dw_value)
                for fact, flags in [('fact_operation', ('order_dates_inverted','interval_invalid','outside_source_label')),
                                    ('fact_downtime', ('interval_invalid','outside_source_label')),
                                    ('fact_sale', ('outside_source_label',)),
                                    ('fact_financial_observation', ('source_float','outside_source_label')),
                                    ('fact_quality_inspection', ('inspected_exceeds_lot','outside_source_label')),
                                    ('fact_material_consumption', ('outside_source_label',)),
                                    ('fact_material_price_observation', ('outside_source_label',))]:
                    for flag in flags:
                        cur.execute(sql.SQL('SELECT count(*) FROM dw.{} WHERE {}').format(
                            sql.Identifier(fact), sql.Identifier(flag)))
                        result['quality_flags'][f'{fact}.{flag}'] = cur.fetchone()[0]
                        fact_pk = {'fact_operation':'operation_id','fact_downtime':'downtime_id',
                            'fact_sale':'sale_id','fact_financial_observation':'observation_id',
                            'fact_quality_inspection':'inspection_id','fact_material_consumption':'consumption_id',
                            'fact_material_price_observation':'price_observation_id'}[fact]
                        cur.execute(sql.SQL('SELECT {} FROM dw.{} WHERE {} ORDER BY {} LIMIT 5').format(
                            sql.Identifier(fact_pk), sql.Identifier(fact), sql.Identifier(flag), sql.Identifier(fact_pk)))
                        result['quality_examples'][f'{fact}.{flag}'] = [row[0] for row in cur.fetchall()]
        return result
    finally:
        if close_target:
            target.close()



CONTRIBUTOR_FACTS = {
    'machine': (('fact_operation', 'operation_id', 'machine_id', 'operation_day'),
                ('fact_downtime', 'downtime_id', 'machine_id', 'start_day')),
    'product': (('fact_operation', 'operation_id', 'product_id', 'operation_day'),
                ('fact_sale', 'sale_id', 'product_id', 'sale_day')),
    'quality': (('fact_quality_inspection', 'inspection_id', 'product_id', 'inspection_day'),),
    'material': (('fact_material_consumption', 'consumption_id', 'material_id', 'registered_day'),
                 ('fact_material_price_observation', 'price_observation_id', 'material_id', 'purchase_day')),
}


def contributors(kind: str, year: int, identifier: int, *, fact: str | None = None,
                 after: int = 0, limit: int = 100) -> dict:
    """Page through exact fact IDs contributing to one fixed aggregate row."""
    source.require(kind in CONTRIBUTOR_FACTS, 'Unknown aggregate query.')
    source.require(2015 <= year <= 2026 and isinstance(identifier, int) and identifier > 0,
                   'Invalid aggregate year or dimension ID.')
    source.require(isinstance(after, int) and after >= 0 and 1 <= limit <= 1000,
                   'Invalid contributor pagination.')
    specs = CONTRIBUTOR_FACTS[kind]
    source.require(fact is None or fact in {item[0] for item in specs},
                   'Fact does not contribute to this aggregate.')
    source.require(fact is not None or after == 0, 'Select a fact when continuing pagination.')
    start, end = date(year, 1, 1), date(year + 1, 1, 1)
    selected = [item for item in specs if fact is None or item[0] == fact]
    conn = source.connect('industrial', DATABASE)
    try:
        with conn, conn.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            pages = []
            for table, pk, dimension, day in selected:
                predicate = sql.SQL('{}=%s AND {} >= %s AND {} < %s').format(
                    sql.Identifier(dimension), sql.Identifier(day), sql.Identifier(day))
                cur.execute(sql.SQL('SELECT count(*) FROM dw.{} WHERE {}').format(
                    sql.Identifier(table), predicate), (identifier, start, end))
                total = cur.fetchone()[0]
                cur.execute(sql.SQL('''SELECT {} FROM dw.{} WHERE {} AND {} > %s
                        ORDER BY {} LIMIT %s''').format(sql.Identifier(pk), sql.Identifier(table),
                        predicate, sql.Identifier(pk), sql.Identifier(pk)),
                        (identifier, start, end, after, limit + 1))
                ids = [row[0] for row in cur.fetchall()]
                has_more = len(ids) > limit
                ids = ids[:limit]
                pages.append({'fact': table, 'total': total, 'ids': ids,
                              'next_after': ids[-1] if has_more else None})
    finally:
        conn.close()
    return {'query': kind, 'year': year, 'dimension_id': identifier,
            'after': after, 'limit': limit, 'contributors': pages}


def trace(fact: str, mapped_id: int) -> dict:
    allowed = {target: key for key, (_, target) in FACTS.items()}
    source.require(fact in allowed, 'Unknown fact table.')
    pk = {'fact_operation':'operation_id','fact_downtime':'downtime_id','fact_sale':'sale_id',
          'fact_financial_observation':'observation_id','fact_quality_inspection':'inspection_id',
          'fact_material_consumption':'consumption_id','fact_material_price_observation':'price_observation_id'}[fact]
    conn = source.connect('industrial', DATABASE)
    try:
        with conn, conn.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            cur.execute(sql.SQL('''SELECT f.*,s.domain,s.table_name,s.pk_column,
                          s.raw_schema,s.source_path,s.sha256
                      FROM dw.{} f JOIN dw.source_file s USING (source_file_id) WHERE f.{}=%s''').format(
                          sql.Identifier(fact), sql.Identifier(pk)), (mapped_id,))
            row = cur.fetchone()
            source.require(row is not None, 'Fact ID not found.')
            record = {column.name: value.isoformat() if isinstance(value, (date, datetime))
                      else str(value) if isinstance(value, Decimal) else value
                      for column, value in zip(cur.description, row)}
            domain = record.pop('domain')
            source_table = record.pop('table_name')
            pk_column = record.pop('pk_column')
            raw_schema = record.pop('raw_schema')
            source_path = record.pop('source_path')
            source_sha256 = record.pop('sha256').strip()
            result = {'mapped_id': mapped_id, 'original_id': record['original_id'],
                    'period_index': record['period_index'], 'source_database': f'db_{domain}',
                    'source_table': source_table, 'source_pk_column': pk_column,
                    'raw_schema': raw_schema, 'source_csv': source_path,
                    'source_sha256': source_sha256, 'dw_record': record}
            origin = source.connect(domain)
            try:
                with origin, origin.cursor() as origin_cur:
                    origin_cur.execute('SET TRANSACTION READ ONLY')
                    for label, schema, key in [('raw_record', raw_schema, record['original_id']),
                                               ('typed_record', 'public', mapped_id)]:
                        predicate = sql.SQL('{}::integer=%s').format(sql.Identifier(pk_column)) if label == 'raw_record' else \
                                    sql.SQL('{}=%s').format(sql.Identifier(pk_column))
                        origin_cur.execute(sql.SQL('SELECT * FROM {}.{} WHERE {}').format(
                            sql.Identifier(schema), sql.Identifier(source_table), predicate), (key,))
                        values = origin_cur.fetchone()
                        source.require(values is not None, f'{label} missing for mapped fact {mapped_id}.')
                        result[label] = {column.name: value.isoformat() if isinstance(value, (date, datetime))
                                         else str(value) if isinstance(value, Decimal) else value
                                         for column, value in zip(origin_cur.description, values)}
            finally:
                origin.close()
            return result
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('build', help='Validate existing sources, then create/load an isolated DW once')
    sub.add_parser('verify', help='Read-only reconciliation of existing source and DW loads')
    q = sub.add_parser('query', help='Run a fixed, read-only analytical query')
    q.add_argument('kind', choices=('machine','product','financial','quality','material'))
    q.add_argument('--year', type=int, required=True)
    q.add_argument('--id', type=int)
    c = sub.add_parser('contributors', help='Page through fact IDs behind one aggregate row')
    c.add_argument('kind', choices=tuple(CONTRIBUTOR_FACTS))
    c.add_argument('--year', type=int, required=True)
    c.add_argument('--id', type=int, required=True)
    c.add_argument('--fact', choices=tuple(target for _, target in FACTS.values()))
    c.add_argument('--after', type=int, default=0)
    c.add_argument('--limit', type=int, default=100)
    t = sub.add_parser('trace', help='Return DW/raw/public lineage of one fact ID')
    t.add_argument('fact', choices=tuple(target for _, target in FACTS.values()))
    t.add_argument('id', type=int)
    args = parser.parse_args()
    if args.command == 'build':
        result = build()
    elif args.command == 'verify':
        result = verify()
    elif args.command == 'query':
        result = query(args.kind, args.year, args.id)
    elif args.command == 'contributors':
        result = contributors(args.kind, args.year, args.id, fact=args.fact,
                              after=args.after, limit=args.limit)
    else:
        result = trace(args.fact, args.id)
    if args.command in ('build','verify'):
        REPORT.parent.mkdir(exist_ok=True)
        REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
