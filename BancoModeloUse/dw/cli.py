"""Build and verify the isolated, source-traceable local research warehouse."""

from __future__ import annotations

import argparse
from datetime import date, datetime
from decimal import Decimal
import hashlib
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


def load_dimensions(cur, origins: dict, ids: dict) -> None:
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
        load_rows(cur, origins['industrial'], query, target_table, columns, transform)
    columns = ('material_lot_id','period_index','source_file_id','original_id','material_id','received_on')
    def lot(row):
        period, original = key_parts(row[0])
        return (row[0], period, ids['industrial', period, 'lotes_materiais'], original, row[1], row[2])
    load_rows(cur, origins['industrial'],
              'SELECT lote_id,material_id,data_recebimento FROM public.lotes_materiais ORDER BY lote_id',
              'dim_material_lot', columns, lot)


def load_facts(cur, origins: dict, ids: dict) -> dict[str, int]:
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
    totals[table] = load_rows(cur, origins['industrial'],
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
    totals[table] = load_rows(cur, origins['industrial'],
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
    totals[table] = load_rows(cur, origins['financeiro'],
        'SELECT venda_id,data_venda,quantidade_vendida,preco_unitario_venda,produto_id FROM public.vendas ORDER BY venda_id',
        'fact_sale', columns, sale)

    table = 'resultados_financeiros'
    columns = ('observation_id','source_file_id','period_index','original_id','observed_day',
               'reported_revenue','reported_net_profit','source_float','outside_source_label')
    def financial(r):
        file_id, period, original = meta('financeiro', table, r[0])
        return (r[0], file_id, period, original, r[1].date() if r[1] else None,
                r[2], r[3], True, outside_label('financeiro', period, r[1]))
    totals[table] = load_rows(cur, origins['financeiro'],
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
    totals[table] = load_rows(cur, origins['industrial'],
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
    totals[table] = load_rows(cur, origins['industrial'],
        'SELECT consumo_id,registro_id,material_id,lote_material_id,quantidade_consumida,data_registro FROM public.consumo_materiais ORDER BY consumo_id',
        'fact_material_consumption', columns, consumption)

    table = 'materiais_custo_historico'
    columns = ('price_observation_id','source_file_id','period_index','original_id','purchase_day',
               'material_id','material_lot_id','unit_price','outside_source_label')
    def price(r):
        file_id, period, original = meta('financeiro', table, r[0])
        return (r[0], file_id, period, original, r[4], r[1], r[2], r[3],
                outside_label('financeiro', period, r[4]))
    totals[table] = load_rows(cur, origins['financeiro'],
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
                  'lineage_samples': {}, 'reconciliation': {}}
        with target:
            with target.cursor() as cur:
                cur.execute('SET TRANSACTION READ ONLY')
                cur.execute('SELECT count(*) FROM dw.source_file')
                source.require(cur.fetchone()[0] == len(items), 'Source manifest count mismatch.')
                cur.execute('SELECT domain,period_index,table_name,sha256,row_count,source_path FROM dw.source_file')
                stored_files = {(d,p,t): (sha.strip(), count, path) for d,p,t,sha,count,path in cur.fetchall()}
                expected_files = {key: (item['sha256'], len(item['rows']), item['path'].relative_to(ROOT).as_posix())
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


def query(kind: str, year: int, identifier: int | None) -> dict:
    source.require(2015 <= year <= 2026, 'Year outside available study range.')
    statements = {
        'machine': ('''SELECT m.machine_id,
                              (SELECT count(*) FROM dw.fact_operation o WHERE o.machine_id=m.machine_id
                                AND o.operation_day >= %s AND o.operation_day < %s),
                              (SELECT sum(o.quantity_reported) FROM dw.fact_operation o WHERE o.machine_id=m.machine_id
                                AND o.operation_day >= %s AND o.operation_day < %s),
                              (SELECT count(*) FROM dw.fact_downtime d WHERE d.machine_id=m.machine_id
                                AND d.start_day >= %s AND d.start_day < %s),
                              (SELECT sum(d.duration_minutes) FROM dw.fact_downtime d WHERE d.machine_id=m.machine_id
                                AND d.start_day >= %s AND d.start_day < %s)
                       FROM dw.dim_machine m WHERE (%s IS NULL OR m.machine_id=%s) ORDER BY m.machine_id''',
                    ('machine_id','operation_rows','reported_operation_quantity','downtime_rows','downtime_minutes')),
        'product': ('''SELECT p.product_id,
                              (SELECT count(*) FROM dw.fact_operation o WHERE o.product_id=p.product_id
                                AND o.operation_day >= %s AND o.operation_day < %s),
                              (SELECT sum(o.quantity_reported) FROM dw.fact_operation o WHERE o.product_id=p.product_id
                                AND o.operation_day >= %s AND o.operation_day < %s),
                              (SELECT count(*) FROM dw.fact_sale s WHERE s.product_id=p.product_id
                                AND s.sale_day >= %s AND s.sale_day < %s),
                              (SELECT sum(s.observed_sales_value) FROM dw.fact_sale s WHERE s.product_id=p.product_id
                                AND s.sale_day >= %s AND s.sale_day < %s)
                       FROM dw.dim_product p WHERE (%s IS NULL OR p.product_id=%s)
                       ORDER BY p.product_id''',
                    ('product_id','operation_rows','reported_operation_quantity','sale_rows','observed_sales_value')),
        'financial': ('''SELECT observation_id,observed_day,reported_revenue,reported_net_profit
                       FROM dw.fact_financial_observation WHERE observed_day >= %s AND observed_day < %s
                       ORDER BY observed_day,observation_id''',
                      ('observation_id','observed_day','reported_revenue','reported_net_profit')),
        'quality': ('''SELECT product_id,count(*),sum(approved_units),sum(rejected_units),
                            count(*) FILTER (WHERE inspected_exceeds_lot)
                     FROM dw.fact_quality_inspection WHERE inspection_day >= %s AND inspection_day < %s
                       AND (%s IS NULL OR product_id=%s) GROUP BY product_id ORDER BY product_id''',
                    ('product_id','inspection_rows','approved_reported','rejected_reported','exceeds_lot_rows')),
        'material': ('''SELECT m.material_id,
                             (SELECT count(*) FROM dw.fact_material_consumption c WHERE c.material_id=m.material_id
                               AND c.registered_day >= %s AND c.registered_day < %s),
                             (SELECT sum(c.quantity_consumed) FROM dw.fact_material_consumption c
                               WHERE c.material_id=m.material_id AND c.registered_day >= %s AND c.registered_day < %s),
                             (SELECT count(*) FROM dw.fact_material_price_observation p WHERE p.material_id=m.material_id
                               AND p.purchase_day >= %s AND p.purchase_day < %s),
                             (SELECT min(p.unit_price) FROM dw.fact_material_price_observation p
                               WHERE p.material_id=m.material_id AND p.purchase_day >= %s AND p.purchase_day < %s),
                             (SELECT max(p.unit_price) FROM dw.fact_material_price_observation p
                               WHERE p.material_id=m.material_id AND p.purchase_day >= %s AND p.purchase_day < %s)
                      FROM dw.dim_material m WHERE (%s IS NULL OR m.material_id=%s) ORDER BY m.material_id''',
                     ('material_id','consumption_rows','quantity_consumed','price_observation_rows',
                      'min_observed_unit_price','max_observed_unit_price')),
    }
    source.require(kind in statements, f'Unknown fixed query: {kind}')
    start, end = date(year, 1, 1), date(year + 1, 1, 1)
    if kind == 'machine':
        params = (start,end,start,end,start,end,start,end,identifier,identifier)
    elif kind == 'product':
        params = (start,end,start,end,start,end,start,end,identifier,identifier)
    elif kind == 'material':
        params = (start,end,start,end,start,end,start,end,start,end,identifier,identifier)
    elif kind == 'quality':
        params = (start,end,identifier,identifier)
    else:
        params = (start,end)
    conn = source.connect('industrial', DATABASE)
    try:
        with conn, conn.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            cur.execute(statements[kind][0], params)
            rows = [dict(zip(statements[kind][1], row)) for row in cur.fetchall()]
    finally:
        conn.close()
    def normalize(value):
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        return value
    if kind in ('machine', 'product', 'material'):
        relevant = {'machine': ('operation_rows','downtime_rows'), 'product': ('operation_rows','sale_rows'),
                    'material': ('consumption_rows','price_observation_rows')}[kind]
        rows = [row for row in rows if any(row[field] for field in relevant)]
    coverage = {'rows': len(rows), 'state': 'observed' if rows else 'no_observation'}
    if kind == 'financial':
        coverage['observed_months'] = len({row['observed_day'].strftime('%Y-%m') for row in rows if row['observed_day']})
        first_day = min((row['observed_day'] for row in rows if row['observed_day']), default=None)
        last_day = max((row['observed_day'] for row in rows if row['observed_day']), default=None)
        coverage['first_day'] = first_day.isoformat() if first_day else None
        coverage['last_day'] = last_day.isoformat() if last_day else None
    metadata = {
        'machine': ('machine/year', ['db_industrial.public.registros_operacao','db_industrial.public.paradas_maquinas'],
                    {'operation_rows':'count(registro_id)', 'reported_operation_quantity':'sum(quantidade_produzida_real)',
                     'downtime_rows':'count(parada_id)', 'downtime_minutes':'sum(hora_fim_parada - hora_inicio_parada) / 60 seconds'},
                    {'reported_operation_quantity':'reported units', 'downtime_minutes':'minutes'}),
        'product': ('source product/year', ['db_industrial.public.registros_operacao','db_financeiro.public.vendas'],
                    {'operation_rows':'count(registro_id)', 'reported_operation_quantity':'sum(quantidade_produzida_real)',
                     'sale_rows':'count(venda_id)', 'observed_sales_value':'sum(quantidade_vendida * preco_unitario_venda)'},
                    {'reported_operation_quantity':'reported units', 'observed_sales_value':'source monetary units'}),
        'financial': ('one financial source row', ['db_financeiro.public.resultados_financeiros'],
                      {'reported_revenue':'source receita_total, no annual summation',
                       'reported_net_profit':'source lucro_liquido, no annual summation'},
                      {'reported_revenue':'source monetary units', 'reported_net_profit':'source monetary units'}),
        'quality': ('source product/year', ['db_industrial.public.controle_qualidade'],
                    {'inspection_rows':'count(controle_id)', 'approved_reported':'sum(unidades_aprovadas)',
                     'rejected_reported':'sum(unidades_rejeitadas)'},
                    {'approved_reported':'inspected units', 'rejected_reported':'inspected units'}),
        'material': ('source material/year', ['db_industrial.public.consumo_materiais',
                    'db_financeiro.public.materiais_custo_historico'],
                    {'consumption_rows':'count(consumo_id)', 'quantity_consumed':'sum(quantidade_consumida)',
                     'price_observation_rows':'count(custo_material_id)',
                     'min_observed_unit_price':'min(custo_unitario)', 'max_observed_unit_price':'max(custo_unitario)'},
                    {'quantity_consumed':'material source unit', 'min_observed_unit_price':'source monetary unit per material unit',
                     'max_observed_unit_price':'source monetary unit per material unit'}),
    }
    grain, sources, formulas, units = metadata[kind]
    return {'query': kind, 'year': year, 'grain': grain, 'sources': sources, 'formula': formulas,
            'units': units, 'coverage': coverage,
            'rows': [{key: normalize(value) for key, value in row.items()} for row in rows],
            'interpretation': {
                'machine':'Operation quantities may repeat production stages; downtime is assigned to start day. Association only.',
                'product':'Sales value is from observed sales, not accounting revenue. Operation quantities may repeat stages. Association only.',
                'financial':'Observed dated rows and month coverage only; no complete annual revenue is inferred.',
                'quality':'Inspections may repeat lots and disagree with lot quantities; these are reported units, not unique output.',
                'material':'Price observations share material and lot keys but have no rule assigning a price to each consumption. No realized cost is calculated.'
            }[kind]}


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
            cur.execute(sql.SQL('''SELECT f.original_id,f.period_index,s.domain,s.table_name,s.pk_column,
                          s.raw_schema,s.source_path,s.sha256
                      FROM dw.{} f JOIN dw.source_file s USING (source_file_id) WHERE f.{}=%s''').format(
                          sql.Identifier(fact), sql.Identifier(pk)), (mapped_id,))
            row = cur.fetchone()
            source.require(row is not None, 'Fact ID not found.')
            result = {'mapped_id': mapped_id, 'original_id': row[0], 'period_index': row[1],
                    'source_database': f'db_{row[2]}', 'source_table': row[3], 'source_pk_column': row[4],
                    'raw_schema': row[5], 'source_csv': row[6], 'source_sha256': row[7].strip()}
            origin = source.connect(row[2])
            try:
                with origin, origin.cursor() as origin_cur:
                    origin_cur.execute('SET TRANSACTION READ ONLY')
                    for label, schema, key in [('raw_record', row[5], row[0]),
                                               ('typed_record', 'public', mapped_id)]:
                        predicate = sql.SQL('{}::integer=%s').format(sql.Identifier(row[4])) if label == 'raw_record' else \
                                    sql.SQL('{}=%s').format(sql.Identifier(row[4]))
                        origin_cur.execute(sql.SQL('SELECT * FROM {}.{} WHERE {}').format(
                            sql.Identifier(schema), sql.Identifier(row[3]), predicate), (key,))
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
    t = sub.add_parser('trace', help='Return raw/public lineage of one fact ID')
    t.add_argument('fact', choices=tuple(target for _, target in FACTS.values()))
    t.add_argument('id', type=int)
    args = parser.parse_args()
    if args.command == 'build':
        result = build()
    elif args.command == 'verify':
        result = verify()
    elif args.command == 'query':
        result = query(args.kind, args.year, args.id)
    else:
        result = trace(args.fact, args.id)
    if args.command in ('build','verify'):
        REPORT.parent.mkdir(exist_ok=True)
        REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
