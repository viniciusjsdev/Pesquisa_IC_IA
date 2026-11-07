"""Read back the three canonical DataMind databases after an authorized load.

This command is read-only. It checks the physical schema, every CSV partition,
typed/raw row counts, DW table counts, and the two downtime sources.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import canonical_ingest as ingest


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def columns(cur, schema: str) -> dict[str, list[tuple[str, str]]]:
    cur.execute('''SELECT table_name,column_name,data_type,character_maximum_length
        FROM information_schema.columns WHERE table_schema=%s
        ORDER BY table_name,ordinal_position''', (schema,))
    result = defaultdict(list)
    for table, name, data_type, maximum in cur.fetchall():
        if data_type == 'character':
            data_type = f'char({maximum})'
        elif data_type == 'timestamp without time zone':
            data_type = 'timestamp'
        elif data_type == 'timestamp with time zone':
            data_type = 'timestamptz'
        elif data_type == 'time without time zone':
            data_type = 'time'
        result[table].append((name, data_type))
    return dict(result)


def primary_keys(cur, schema: str) -> dict[str, list[str]]:
    cur.execute('''SELECT c.table_name,k.column_name FROM information_schema.table_constraints c
        JOIN information_schema.key_column_usage k
          ON c.constraint_catalog=k.constraint_catalog
         AND c.constraint_schema=k.constraint_schema
         AND c.constraint_name=k.constraint_name
        WHERE c.table_schema=%s AND c.constraint_type='PRIMARY KEY'
        ORDER BY c.table_name,k.ordinal_position''', (schema,))
    result = defaultdict(list)
    for table, column in cur.fetchall():
        result[table].append(column)
    return dict(result)


def fk_counts(cur, schema: str) -> dict[str, int]:
    cur.execute('''SELECT table_name,count(*) FROM information_schema.table_constraints
        WHERE table_schema=%s AND constraint_type='FOREIGN KEY'
        GROUP BY table_name''', (schema,))
    return dict(cur.fetchall())


def row_count(cur, schema: str, table: str, sql) -> int:
    cur.execute(sql.SQL('SELECT count(*) FROM {}.{}').format(
        sql.Identifier(schema), sql.Identifier(table)))
    return cur.fetchone()[0]


def verify(database_home: Path) -> dict:
    review = ingest.plan()
    contract = json.loads(ingest.CONTRACT.read_text(encoding='utf-8'))
    source_tables = contract['tables']
    manifest = json.loads(ingest.MANIFEST.read_text(encoding='utf-8'))
    parts = ingest.partitions(manifest)
    psycopg2, sql, *_ = ingest.db_modules()
    connect = ingest.cluster_connector(psycopg2, database_home)
    expected = {}
    by_table = defaultdict(int)
    for part in parts:
        name = Path(part['caminho']).stem
        definition = source_tables[name]
        database, table, period = definition['database'], definition['table'], part['period']
        amount = len(part['rows']) if part['rows'] is not None else int(part['linhas'])
        expected[database, period, table] = (part['caminho'], part['sha256'], amount)
        by_table[database, table] += amount
    output = {'database_writes': False, 'source_databases': {}, 'warehouse': {}}
    for database in ('db_industrial', 'db_financeiro'):
        conn = connect('industrial', database)
        try:
            with conn.cursor() as cur:
                cur.execute('SET TRANSACTION READ ONLY')
                actual = columns(cur, 'public')
                modeled = {item['table']: item for item in source_tables.values()
                           if item['database'] == database}
                require(set(actual) == set(modeled) | {'canonical_source_file'},
                        f'{database}: public table inventory differs from the DER.')
                pks = primary_keys(cur, 'public')
                fks = fk_counts(cur, 'public')
                for table, definition in modeled.items():
                    fields = definition['fields']
                    require(actual[table] == [(field['name'], field['type']) for field in fields],
                            f'{database}.{table}: physical columns differ from the DER.')
                    pk = [field['name'] for field in fields if 'PK' in field['key'].split(',')]
                    require(pks.get(table) == pk,
                            f'{database}.{table}: physical primary key differs from the DER.')
                    require(row_count(cur, 'public', table, sql) == by_table[database, table],
                            f'{database}.{table}: typed row count differs from the manifest.')
                expected_fk = sum(source_tables[name]['database'] == database
                                  for name, _ in ingest.PHYSICAL_FK)
                require(sum(fks.values()) == expected_fk,
                        f'{database}: physical FK count differs from the DER.')
                cur.execute('''SELECT source_path,period_index,table_name,sha256,row_count
                    FROM public.canonical_source_file''')
                tracked = {(database, period, table): (path, digest.strip(), count)
                           for path, period, table, digest, count in cur.fetchall()}
                wanted = {key: value for key, value in expected.items() if key[0] == database}
                require(tracked == wanted,
                        f'{database}: source-file inventory differs from the CSV manifest.')
                for _, period, table in wanted:
                    require(row_count(cur, f'raw_p{period}', table, sql) ==
                            wanted[database, period, table][2],
                            f'{database}.raw_p{period}.{table}: raw count mismatch.')
                output['source_databases'][database] = {
                    'typed_tables': len(modeled), 'csv_partitions': len(wanted),
                    'rows': sum(by_table[database, table] for table in modeled),
                    'physical_fks': expected_fk}
        finally:
            conn.rollback()
            conn.close()
    conn = connect('industrial', 'db_pesquisa_dw')
    try:
        with conn.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            actual = columns(cur, 'dw')
            require(set(actual) == set(contract['warehouse_v1_schema']) |
                    set(contract['warehouse_new_schema']),
                    'DW physical table inventory differs from the DER.')
            pks = primary_keys(cur, 'dw')
            fks = fk_counts(cur, 'dw')
            for table, fields in contract['warehouse_v1_schema'].items():
                require(actual[table] == [(field['name'], field['type']) for field in fields],
                        f'DW {table}: physical columns differ from the DER.')
                pk = [field['name'] for field in fields if field['key'] == 'PK']
                require(pks.get(table) == pk,
                        f'DW {table}: physical primary key differs from the DER.')
            from dw import cli as warehouse_v1
            v1_counts = {}
            for source_table, (domain, fact) in warehouse_v1.FACTS.items():
                count = row_count(cur, 'dw', fact, sql)
                amount = by_table[f'db_{domain}', source_table]
                if fact == 'fact_downtime':
                    amount += by_table['db_industrial', 'paradas_maquinas_geradas']
                require(count == amount, f'DW {fact}: row count differs from sources.')
                v1_counts[fact] = count
            new_counts = {}
            for table, definition in contract['warehouse_new_schema'].items():
                fields = [(field['name'], field['type']) for field in definition['fields']]
                fields.extend([('source_file_id', 'integer'),
                               ('period_index', 'smallint'), ('original_id', 'integer')])
                require(actual[table] == fields,
                        f'DW {table}: physical columns differ from the DER.')
                require(pks.get(table) == ['source_file_id', 'original_id'] and
                        fks.get(table) == 2,
                        f'DW {table}: physical primary/foreign keys differ from the DER.')
                count = row_count(cur, 'dw', table, sql)
                amount = sum(by_table[source_tables[name]['database'],
                                      source_tables[name]['table']]
                             for name in definition['sources'])
                require(count == amount, f'DW {table}: row count differs from sources.')
                new_counts[table] = count
            cur.execute('''SELECT domain,period_index,table_name,source_path,sha256,row_count
                FROM dw.source_file''')
            tracked = {(f'db_{domain}', period, table): (path, digest.strip(), count)
                       for domain, period, table, path, digest, count in cur.fetchall()}
            require(tracked == expected, 'DW source-file inventory differs from the CSV manifest.')
            cur.execute('''SELECT s.table_name,count(*) FROM dw.fact_downtime f
                JOIN dw.source_file s USING (source_file_id)
                GROUP BY s.table_name''')
            downtime = dict(cur.fetchall())
            require(downtime == review['downtime_sources'],
                    'DW fact_downtime differs from the two canonical stop sources.')
            cur.execute('SELECT version,source_fingerprint FROM dw.schema_migrations')
            migrations = [(version, digest.strip()) for version, digest in cur.fetchall()]
            require(migrations == [(2, review['contract_sha256'])],
                    'DW migration fingerprint differs from this canonical plan.')
            output['warehouse'] = {'tables': len(actual), 'v1_fact_rows': v1_counts,
                                   'new_table_rows': new_counts,
                                   'source_partitions': len(tracked),
                                   'source_rows': sum(item[2] for item in tracked.values()),
                                   'fact_downtime_by_source': downtime,
                                   'schema_version': 2,
                                   'contract_sha256': review['contract_sha256']}
    finally:
        conn.rollback()
        conn.close()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database-home', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.database_home), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
