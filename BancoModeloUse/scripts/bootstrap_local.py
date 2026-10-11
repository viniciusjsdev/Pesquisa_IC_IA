"""Lossless CSV ingestion into the isolated cluster, with deterministic ID mapping."""
import argparse
import csv
import hashlib
import importlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import psycopg2
from psycopg2 import sql
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from infrastructure.config.database_config import get_all_database_configs

STRIDE = 1_000_000
PERIODS = {
    'industrial': ['dados_industriais_automotivo_eletronica_2015_2017',
                   'dados_industriais_automotivo_eletronica_2017_2020',
                   'dados_industriais_automotivo_eletronics_2021_2025'],
    'financeiro': ['dados_financeiros_2015_2016', 'dados_financeiros_2017_2020',
                   'dados_financeiros_2021_2025'],
}
MODULES = {'industrial': ['cadastros', 'producao', 'equipamentos', 'qualidade'],
           'financeiro': ['custos', 'contabil', 'vendas', 'kpis']}
CROSS = {'vendas': {'produto_id': ('produtos', 'produto_id')},
         'materiais_custo_historico': {'material_id': ('materiais', 'material_id'),
                                      'lote_material_id': ('lotes_materiais', 'lote_id')}}
DIALECT = postgresql.dialect()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def metadata(domain):
    for module in MODULES[domain]:
        importlib.import_module(f'core.models.{domain}.{module}')
    return importlib.import_module(f'infrastructure.database.connections.{domain}_connection').Base.metadata


def inventory():
    result = {}
    for domain, folders in PERIODS.items():
        meta = metadata(domain)
        for period, folder in enumerate(folders):
            for path in sorted((ROOT / 'dados_simulados' / folder).glob('*.csv')):
                name = 'processos_industriais' if path.stem == 'processo_industrial' else path.stem
                table = meta.tables[name]
                with path.open(encoding='utf-8-sig', newline='') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    fields = reader.fieldnames
                require(rows and len(fields) == len(set(fields)), f'Empty/invalid CSV: {path.name}')
                require(set(fields) <= set(table.c.keys()), f'Unmapped columns: {path.name}')
                pk = list(table.primary_key.columns)[0].name
                ids = [int(r[pk]) for r in rows]
                require(len(ids) == len(set(ids)), f'Duplicate IDs within {folder}/{path.name}')
                require(min(ids) > 0 and max(ids) < STRIDE, f'ID outside supported range: {path.name}')
                result[domain, period, name] = dict(path=path, fields=fields, rows=rows,
                    pk=pk, ids=set(ids), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    require(len(result) == 75, 'Expected all 75 source CSV files; review inventory before changing this contract.')
    for (domain, period, name), item in result.items():
        refs = {fk.parent.name: (domain, fk.column.table.name, fk.column.name)
                for fk in metadata(domain).tables[name].foreign_keys}
        if domain == 'financeiro':
            refs.update({key: ('industrial', *value) for key, value in CROSS.get(name, {}).items()})
        for field, (target_domain, target_table, target_field) in refs.items():
            target = result[target_domain, period, target_table]
            valid = {r[target_field] for r in target['rows']}
            missing = {r[field] for r in item['rows'] if r.get(field) and r[field] not in valid}
            require(not missing, f'Orphan references: {domain}/{period}/{name}.{field}')
    return result


def connect(domain, database=None):
    config = get_all_database_configs()[domain]
    require((ROOT / '.env.local').exists(), 'Start local_postgres.py first.')
    require(config['host'] == '127.0.0.1' and int(config['port']) == 5544,
            'This command only operates on the isolated local cluster at 127.0.0.1:5544.')
    conn = psycopg2.connect(host=config['host'], port=config['port'], user=config['user'],
                            password=config['password'], dbname=database or config['database'])
    with conn.cursor() as cur:
        cur.execute('SHOW data_directory')
        require(Path(cur.fetchone()[0]).resolve() == (ROOT / '.local/postgres').resolve(),
                'Unexpected PostgreSQL data directory; refusing to proceed.')
    conn.commit()
    return conn


def selection(table, item, period):
    remap = {c.name for c in table.primary_key.columns} | {f.parent.name for f in table.foreign_keys}
    if table.name in CROSS:
        remap |= set(CROSS[table.name])
    expressions = []
    for col in table.columns:
        typ = col.type.compile(dialect=DIALECT)
        if col.name not in item['fields']:
            expressions.append(sql.SQL('NULL::{}').format(sql.SQL(typ)))
        else:
            value = sql.SQL("NULLIF({}, '')::{}").format(sql.Identifier(col.name), sql.SQL(typ))
            if col.name in remap:
                value = sql.SQL('({} + {})').format(value, sql.Literal(period * STRIDE))
            expressions.append(value)
    return sql.SQL('SELECT {} FROM {}.{}').format(sql.SQL(',').join(expressions),
        sql.Identifier(f'raw_p{period}'), sql.Identifier(table.name))


def create_databases():
    conn = connect('industrial', 'postgres')
    conn.autocommit = True
    with conn.cursor() as cur:
        for domain in MODULES:
            config = get_all_database_configs()[domain]
            cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (config['database'],))
            if cur.fetchone() is None:
                cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(config['database'])))
    conn.close()
    # Refuse existing objects before changing ANY target database.
    for domain in MODULES:
        conn = connect(domain)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")
            require(cur.fetchone()[0] == 0, f'{domain} already has tables. Use --verify; no existing data was overwritten.')
        conn.close()


def load(domain, items):
    meta = metadata(domain)
    conn = connect(domain)
    try:
        with conn, conn.cursor() as cur:
            for table in meta.sorted_tables:
                cur.execute(str(CreateTable(table).compile(dialect=DIALECT)))
            for period in range(3):
                cur.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(f'raw_p{period}')))
                for table in meta.sorted_tables:
                    item = items.get((domain, period, table.name))
                    if item is None:
                        continue
                    raw = sql.SQL('{}.{}').format(sql.Identifier(f'raw_p{period}'), sql.Identifier(table.name))
                    columns = sql.SQL(',').join(sql.SQL('{} text').format(sql.Identifier(c)) for c in item['fields'])
                    cur.execute(sql.SQL('CREATE TABLE {} ({})').format(raw, columns))
                    with item['path'].open(encoding='utf-8-sig', newline='') as f:
                        cur.copy_expert(sql.SQL('COPY {} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)').format(raw).as_string(conn), f)
                    cur.execute(sql.SQL('INSERT INTO {} ({}) {}').format(sql.Identifier(table.name),
                        sql.SQL(',').join(map(sql.Identifier, table.c.keys())), selection(table, item, period)))
            for table in meta.sorted_tables:
                for index in table.indexes:
                    cur.execute(str(CreateIndex(index).compile(dialect=DIALECT)))
                pk = list(table.primary_key.columns)[0].name
                cur.execute('SELECT pg_get_serial_sequence(%s,%s)', (table.name, pk))
                sequence = cur.fetchone()[0]
                if sequence:
                    cur.execute(sql.SQL('SELECT max({}) FROM {}').format(sql.Identifier(pk), sql.Identifier(table.name)))
                    maximum = cur.fetchone()[0]
                    cur.execute('SELECT setval(%s,%s,%s)', (sequence, maximum or 1, maximum is not None))
            cur.execute('ANALYZE')
    finally:
        conn.close()
    print(f'{domain}: committed successfully', flush=True)


def verify(items):
    report = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'id_rule': 'source_id + period_index * 1000000 (indices 0, 1, 2)',
              'files': [], 'databases': {}}
    for domain in MODULES:
        conn = connect(domain)
        totals = {}
        with conn, conn.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            for table in metadata(domain).sorted_tables:
                expected = sum(len(item['rows']) for (d, _, name), item in items.items()
                               if d == domain and name == table.name)
                cur.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table.name)))
                actual = cur.fetchone()[0]
                require(actual == expected, f'Count mismatch: {domain}.{table.name}: {actual} != {expected}')
                totals[table.name] = actual
            for (d, period, name), item in items.items():
                if d != domain:
                    continue
                table = metadata(domain).tables[name]
                cur.execute(sql.SQL('SELECT {} FROM {}.{} ORDER BY {}::integer').format(
                    sql.SQL(',').join(map(sql.Identifier, item['fields'])), sql.Identifier(f'raw_p{period}'),
                    sql.Identifier(name), sql.Identifier(item['pk'])))
                stored = [tuple('' if v is None else v for v in row) for row in cur.fetchall()]
                source = [tuple(r[c] for c in item['fields']) for r in sorted(item['rows'], key=lambda r: int(r[item['pk']]))]
                require(stored == source, f'Raw content mismatch: {item["path"].name}')
                public = sql.SQL('SELECT {} FROM {} WHERE {} > {} AND {} < {}').format(
                    sql.SQL(',').join(map(sql.Identifier, table.c.keys())), sql.Identifier(name),
                    sql.Identifier(item['pk']), sql.Literal(period * STRIDE),
                    sql.Identifier(item['pk']), sql.Literal((period + 1) * STRIDE))
                source_query = selection(table, item, period)
                cur.execute(sql.SQL('SELECT count(*) FROM (({} EXCEPT ALL {}) UNION ALL ({} EXCEPT ALL {})) AS differences').format(
                    source_query, public, public, source_query))
                require(cur.fetchone()[0] == 0, f'Typed content mismatch: {domain}.{name}, period {period}')
                dates = {}
                for col in table.columns:
                    if col.name in item['fields'] and str(col.type) in ('DATE', 'DATETIME'):
                        values = [r[col.name] for r in item['rows'] if r[col.name]]
                        if values:
                            dates[col.name] = {'min': min(values), 'max': max(values)}
                report['files'].append(dict(source=item['path'].relative_to(ROOT).as_posix(),
                    sha256=item['sha256'], database=domain, raw_schema=f'raw_p{period}',
                    table=name, rows=len(source), content_verified=True, dates=dates))
        conn.close()
        report['databases'][domain] = {'tables': totals, 'rows': sum(totals.values())}
    report['validation'] = 'All source values, normalized values, row counts and source foreign keys verified.'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Read-only validation of an existing load')
    args = parser.parse_args()
    items = inventory()
    print(f'Preflight: {len(items)} CSVs, {sum(len(i["rows"]) for i in items.values())} rows; IDs and references valid.', flush=True)
    if not args.verify:
        create_databases()
        for domain in MODULES:
            load(domain, items)
    report = verify(items)
    output = ROOT / 'reports/local_database_validation.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for domain, details in report['databases'].items():
        print(f'{domain}: {details["rows"]} rows verified')
    print(f'Validation report: {output}')


if __name__ == '__main__':
    main()
