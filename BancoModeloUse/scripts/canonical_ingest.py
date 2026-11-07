"""Create the three canonical DataMind databases from the reviewed CSV set.

`plan` is offline. `load` creates databases and loads data, but never drops or
replaces existing objects. Do not run `load` before the user reviews the plan.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import date, datetime
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import validate_canonical_csvs as checks  # noqa: E402
from scripts import export_der_contract as der_contract  # noqa: E402

STRIDE = 1_000_000
BASE = ROOT / 'dados_complementares_datamind'
CONTRACT = BASE / 'contrato_tabelas_canonicas.json'
MANIFEST = BASE / 'manifesto_canonico.json'
DW_TABLES = {
    'dim_turn': ('turnos_trabalho',),
    'dim_component': ('componentes_maquinas',),
    'dim_tariff': ('tarifas_energia',),
    'dim_green_project': ('projetos_investimento_verde',),
    'fact_machine_event': ('eventos_maquina_turno',),
    'fact_production_target': ('metas_producao_maquina',),
    'fact_maintenance_order': ('ordens_manutencao', 'ordens_manutencao_geradas'),
    'fact_predictive_reading': ('telemetria_preditiva',),
    'bridge_maintenance_case': ('vinculos_manutencao_simulados',),
    'fact_energy_shift': ('consumo_energia_turno',),
    'fact_energy_interval': ('consumo_energia_intervalo',),
    'fact_energy_target': ('metas_energia_equipamento',),
    'fact_tariff_mix': ('composicao_tarifaria_inferida',),
    'fact_financial_month': ('resultados_financeiros_mensais',),
    'fact_product_cost_month': ('custos_produto_mensais_simulados',),
    'fact_co2_month': ('emissoes_co2',),
    'fact_esg_resource_month': ('consumo_recursos_esg',),
    'fact_esg_target_month': ('metas_esg_simuladas',),
    'fact_green_project_result_month': ('resultados_projeto_esg_simulados',),
    'fact_certification': ('certificacoes_ambientais',),
}
PHYSICAL_FK = {
    ('lancamentos_financeiros', 'conta_id'): ('contas_contabeis', 'conta_id'),
    ('consumo_materiais', 'registro_id'): ('registros_operacao', 'registro_id'),
    ('consumo_materiais', 'material_id'): ('materiais', 'material_id'),
    ('consumo_materiais', 'lote_material_id'): ('lotes_materiais', 'lote_id'),
    ('controle_qualidade', 'lote_producao_id'): ('lotes_producao', 'lote_producao_id'),
    ('lotes_materiais', 'material_id'): ('materiais', 'material_id'),
    ('lotes_materiais', 'fornecedor_id'): ('fornecedores', 'fornecedor_id'),
    ('lotes_producao', 'ordem_producao_id'): ('ordens_producao', 'ordem_producao_id'),
    ('ordens_producao', 'produto_id'): ('produtos', 'produto_id'),
    ('paradas_maquinas', 'maquina_id'): ('maquinas', 'maquina_id'),
    ('registros_operacao', 'ordem_producao_id'): ('ordens_producao', 'ordem_producao_id'),
    ('registros_operacao', 'maquina_id'): ('maquinas', 'maquina_id'),
    ('roteiros_producao', 'produto_id'): ('produtos', 'produto_id'),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def migration_v1_schema() -> dict:
    """Extract the physical V1 columns and keys from the reviewed SQL migration."""
    ddl = (ROOT / 'dw/migrations/001_init.sql').read_text(encoding='utf-8')
    tables = {}
    for name, body in re.findall(r'CREATE TABLE dw\.([a-z_]+)\s*\((.*?)\n\);', ddl, re.S):
        fields = []
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(',')
            if not line or line.startswith(('UNIQUE ', 'PRIMARY KEY ', 'CHECK ')):
                continue
            tokens = line.split()
            field_type = 'double precision' if tokens[1:3] == ['double', 'precision'] else tokens[1]
            fields.append({'name': tokens[0], 'type': field_type,
                           'key': ('PK' if 'PRIMARY KEY' in line else
                                   'FK' if 'REFERENCES' in line else '')})
        tables[name] = fields
    return tables


def validate_warehouse_model(full_contract: dict, source_contract: dict) -> None:
    """Stop offline when the saved DER, SQL, or dynamic DW mapping diverges."""
    require(der_contract.export(der_contract.MODEL_XML) == full_contract,
            'Saved DER XML differs from the canonical model contract.')
    require(migration_v1_schema() == full_contract['warehouse_v1_schema'],
            'Physical V1 DW migration differs from the saved DER.')
    modeled_new = full_contract['warehouse_new_schema']
    require(set(DW_TABLES) == set(modeled_new),
            'New DW table names differ from the saved DER.')
    for target, sources in DW_TABLES.items():
        fields = []
        for name in sources:
            for field in source_contract[name]['fields']:
                if field['name'] not in [known['name'] for known in fields]:
                    fields.append({'name': field['name'], 'type': field['type']})
                else:
                    known = next(known for known in fields if known['name'] == field['name'])
                    require(known['type'] == field['type'],
                            f'Incompatible union column in {target}.{field["name"]}')
        require(list(sources) == modeled_new[target]['sources'] and
                fields == modeled_new[target]['fields'],
                f'New DW schema differs from the saved DER: {target}')


def period_for(path: Path, row: dict | None = None) -> int:
    if path.stem == 'composicao_tarifaria_inferida':
        require(row is not None, 'Tariff composition must be partitioned by row.')
        return int(row['periodo_indice'])
    for index, (folder, original) in enumerate(checks.PERIODS):
        if folder in path.parts or original in path.parts or checks.FINANCE[index] in path.parts:
            return index
    raise RuntimeError(f'CSV without canonical period: {path}')


def partitions(manifest: list[dict]) -> list[dict]:
    """A root CSV with two periods produces two load partitions, one physical file."""
    result = []
    for item in manifest:
        path = ROOT / item['caminho']
        if path.stem != 'composicao_tarifaria_inferida':
            result.append({**item, 'period': period_for(path), 'rows': None})
            continue
        with path.open(encoding='utf-8-sig', newline='') as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            result.append({**item, 'period': period_for(path, row), 'rows': [row]})
    return result


def plan() -> dict:
    # All checks run before any database connection or CREATE DATABASE.
    classes = checks.validate_manifest()
    model = checks.validate_model_contract()
    full_contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    contract = full_contract['tables']
    validate_warehouse_model(full_contract, contract)
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    parts = partitions(manifest)
    keys = [(contract[Path(p['caminho']).stem]['database'], p['period'],
             contract[Path(p['caminho']).stem]['table']) for p in parts]
    require(len(parts) == 167 and len(set(keys)) == len(keys),
            'One canonical file/period must map to exactly one source table.')
    require(len(DW_TABLES) == 20 and all(name in contract for names in DW_TABLES.values()
                                         for name in names), 'Warehouse mapping is incomplete.')
    migration_tables = set(re.findall(r'CREATE TABLE dw\.([a-z_]+)',
                                      (ROOT / 'dw/migrations/001_init.sql').read_text(
                                          encoding='utf-8')))
    require(migration_tables == set(full_contract['warehouse_tables']['v1']) and
            set(DW_TABLES) == set(full_contract['warehouse_tables']['new']),
            'Warehouse migration or new table mapping differs from the reviewed DER.')
    marked_fks = {(name, field['name']) for name, table in contract.items()
                  for field in table['fields'] if field['key'] == 'FK'}
    require(marked_fks == set(PHYSICAL_FK),
            f'Physical FK mapping differs from DER: {marked_fks ^ set(PHYSICAL_FK)}')
    for (source_name, field), (target_name, target_pk) in PHYSICAL_FK.items():
        require(contract[source_name]['database'] == contract[target_name]['database'],
                f'Cross-database FK is forbidden: {source_name}.{field}')
        for period in range(3):
            target_files = [ROOT / item['caminho'] for item in manifest
                            if Path(item['caminho']).stem == target_name and
                            period_for(ROOT / item['caminho']) == period]
            source_files = [ROOT / item['caminho'] for item in manifest
                            if Path(item['caminho']).stem == source_name and
                            period_for(ROOT / item['caminho']) == period]
            require(len(target_files) == len(source_files) == 1,
                    f'FK files are missing: {source_name}->{target_name}, period {period}')
            with target_files[0].open(encoding='utf-8-sig', newline='') as handle:
                valid = {row[target_pk] for row in csv.DictReader(handle)}
            with source_files[0].open(encoding='utf-8-sig', newline='') as handle:
                missing = {row[field] for row in csv.DictReader(handle)
                           if row[field] and row[field] not in valid}
            require(not missing,
                    f'Unresolved physical FK: {source_name}.{field}, period {period}')
    digest = hashlib.sha256(MANIFEST.read_bytes() + CONTRACT.read_bytes()).hexdigest()
    downtime_sources = {
        name: sum(int(item['linhas']) for item in manifest
                  if Path(item['caminho']).stem == name)
        for name in ('paradas_maquinas', 'paradas_maquinas_geradas')
    }
    require(all(downtime_sources.values()), 'Canonical downtime sources are incomplete.')
    return {'csv_files': len(manifest), 'source_partitions': len(parts),
            'source_tables': {database: sum(t['database'] == database for t in contract.values())
                              for database in ('db_industrial', 'db_financeiro')},
            'dw_v1_tables': 15, 'dw_new_tables': len(DW_TABLES),
            'downtime_sources': downtime_sources,
            'expected_fact_downtime_rows': sum(downtime_sources.values()),
            'rows': model['rows'], 'classes': classes,
            'contract_sha256': digest, 'database_writes': False}


def db_modules():
    # Keep PostgreSQL dependencies out of offline preflight.
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import execute_values, Json
    from scripts import bootstrap_local as legacy
    return psycopg2, sql, execute_values, Json, legacy


def cluster_connector(psycopg2, database_home: Path):
    """Bind the load to one explicitly named isolated cluster, not a global service."""
    home = database_home.resolve()
    data = home / '.local' / 'postgres'
    env_file = home / '.env.local'
    require((data / 'PG_VERSION').is_file() and env_file.is_file(),
            'Explicit database home has no initialized local PostgreSQL cluster.')
    settings = {}
    for line in env_file.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            settings[key] = value
    require(settings.get('INDUSTRIAL_DB_HOST') == '127.0.0.1' and
            settings.get('INDUSTRIAL_DB_PORT') == '5544' and
            settings.get('INDUSTRIAL_DB_NAME') == 'db_industrial' and
            settings.get('FINANCEIRO_DB_NAME') == 'db_financeiro',
            'Database home does not match the isolated DataMind cluster.')

    def connect(domain: str, database: str | None = None):
        prefix = 'INDUSTRIAL' if domain == 'industrial' else 'FINANCEIRO'
        conn = psycopg2.connect(host=settings[f'{prefix}_DB_HOST'],
                                port=settings[f'{prefix}_DB_PORT'],
                                user=settings[f'{prefix}_DB_USER'],
                                password=settings[f'{prefix}_DB_PASSWORD'],
                                dbname=database or settings[f'{prefix}_DB_NAME'])
        try:
            with conn.cursor() as cur:
                cur.execute('SHOW data_directory')
                require(Path(cur.fetchone()[0]).resolve() == data.resolve(),
                        'Connected PostgreSQL data directory differs from explicit target.')
            conn.commit()
            return conn
        except Exception:
            conn.close()
            raise
    return connect


def assert_empty_targets(connect, sql) -> None:
    """Inspect every target before any CREATE DATABASE or table write."""
    names = ('db_industrial', 'db_financeiro', 'db_pesquisa_dw')
    conn = connect('industrial', 'postgres')
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT datname FROM pg_database WHERE datname = ANY(%s)', (list(names),))
            existing = {row[0] for row in cur.fetchall()}
    finally:
        conn.close()
    for name in existing:
        target = connect('industrial', name)
        try:
            with target.cursor() as cur:
                cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")
                count = cur.fetchone()[0]
                require(count == 0, f'{name} contains tables; refusing to replace or append data.')
        finally:
            target.close()


def create_missing_targets(connect, sql) -> None:
    conn = connect('industrial', 'postgres')
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            for name in ('db_industrial', 'db_financeiro', 'db_pesquisa_dw'):
                cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (name,))
                if cur.fetchone() is None:
                    cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    finally:
        conn.close()


def csv_stream(part: dict) -> io.StringIO:
    path = ROOT / part['caminho']
    if part['rows'] is None:
        return io.StringIO(path.read_text(encoding='utf-8-sig'))
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(part['rows'][0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(part['rows'])
    stream.seek(0)
    return stream


def source_load(database: str, contract: dict, parts: list[dict], connect, sql) -> dict:
    conn = connect('industrial', database)
    counts = defaultdict(int)
    try:
        with conn, conn.cursor() as cur:
            cur.execute('''CREATE TABLE public.canonical_source_file (
                source_path text NOT NULL, period_index smallint NOT NULL,
                table_name text NOT NULL, sha256 char(64) NOT NULL,
                row_count integer NOT NULL, PRIMARY KEY (period_index, table_name))''')
            for index in range(3):
                cur.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(f'raw_p{index}')))
            for name, table in contract.items():
                if table['database'] != database:
                    continue
                columns = [sql.SQL('{} {}').format(sql.Identifier(f['name']), sql.SQL(f['type']))
                           for f in table['fields']]
                pk = next(f['name'] for f in table['fields'] if 'PK' in f['key'].split(','))
                columns.append(sql.SQL('PRIMARY KEY ({})').format(sql.Identifier(pk)))
                cur.execute(sql.SQL('CREATE TABLE public.{} ({})').format(
                    sql.Identifier(table['table']), sql.SQL(',').join(columns)))
            for part in parts:
                name = Path(part['caminho']).stem
                table = contract[name]
                if table['database'] != database:
                    continue
                period, target = part['period'], table['table']
                header = [field['name'] for field in table['fields']]
                raw_name = sql.SQL('{}.{}').format(sql.Identifier(f'raw_p{period}'), sql.Identifier(target))
                raw_columns = sql.SQL(',').join(sql.SQL('{} text').format(sql.Identifier(field))
                                           for field in header)
                cur.execute(sql.SQL('CREATE TABLE {} ({})').format(raw_name, raw_columns))
                stream = csv_stream(part)
                cur.copy_expert(sql.SQL('COPY {} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)').format(
                    raw_name).as_string(conn), stream)
                projections = []
                for field in table['fields']:
                    key_parts = field['key'].split(',')
                    value = sql.SQL("NULLIF({}, '')::{}").format(
                        sql.Identifier(field['name']), sql.SQL(field['type']))
                    if (field['type'] == 'integer' and field['name'] != 'periodo_indice'
                            and any(key in key_parts for key in ('PK', 'FK', 'FK*', 'LNK'))):
                        value = sql.SQL('CASE WHEN {} IS NULL THEN NULL ELSE {} + {} END').format(
                            sql.Identifier(field['name']), value, sql.Literal(period * STRIDE))
                    projections.append(value)
                cur.execute(sql.SQL('INSERT INTO public.{} ({}) SELECT {} FROM {}').format(
                    sql.Identifier(target), sql.SQL(',').join(map(sql.Identifier, header)),
                    sql.SQL(',').join(projections), raw_name))
                expected = len(part['rows']) if part['rows'] is not None else int(part['linhas'])
                require(cur.rowcount == expected, f'Load count mismatch: {part["caminho"]}')
                cur.execute('INSERT INTO public.canonical_source_file VALUES (%s,%s,%s,%s,%s)',
                            (part['caminho'], period, target, part['sha256'], expected))
                counts[target] += expected
            for name, count in counts.items():
                cur.execute(sql.SQL('SELECT count(*) FROM public.{}').format(sql.Identifier(name)))
                require(cur.fetchone()[0] == count, f'Source count mismatch: {database}.{name}')
            for (source_name, field), (target_name, target_pk) in PHYSICAL_FK.items():
                if contract[source_name]['database'] != database:
                    continue
                cur.execute(sql.SQL('ALTER TABLE public.{} ADD FOREIGN KEY ({}) '
                                    'REFERENCES public.{} ({})').format(
                    sql.Identifier(contract[source_name]['table']), sql.Identifier(field),
                    sql.Identifier(contract[target_name]['table']), sql.Identifier(target_pk)))
    finally:
        conn.close()
    return dict(counts)


def source_date_bounds(contract: dict, manifest: list[dict]) -> tuple[date, date]:
    first = last = None
    for part in manifest:
        path = ROOT / part['caminho']
        date_fields = [field for field in contract[path.stem]['fields']
                       if field['type'] in ('date', 'timestamp')]
        if not date_fields:
            continue
        with path.open(encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                for field in date_fields:
                    value = row[field['name']]
                    if not value:
                        continue
                    day = date.fromisoformat(value[:10])
                    first = day if first is None or day < first else first
                    last = day if last is None or day > last else last
    require(first is not None and last is not None, 'Canonical date dimension has no bounds.')
    return first, last


def generated_downtime_row(record: tuple, source_file_id: int, period: int,
                           source_path: str) -> tuple:
    """Project one typed generated event into the existing downtime fact."""
    mapped_id, machine_id, start, end = record
    original_id = mapped_id - period * STRIDE
    require(0 < original_id < STRIDE, 'Generated downtime ID is outside its period.')
    match = re.search(r'periodo_(\d{4})_(\d{4})', source_path)
    require(match is not None, 'Generated downtime source has no period label.')
    invalid = bool(start and end and end < start)
    duration = (Decimal(str((end - start).total_seconds())) / 60
                if start and end and not invalid else None)
    outside = bool(start and not (int(match[1]) <= start.year <= int(match[2])))
    return (mapped_id, source_file_id, period, original_id,
            start.date() if start else None, machine_id, start, end,
            duration, invalid, outside)


def load_generated_downtime(cur, origin, parts: list[dict], ids: dict,
                            execute_values) -> int:
    """Append canonical synthetic stops with exact source-file lineage."""
    total = 0
    for part in parts:
        if Path(part['caminho']).stem != 'paradas_maquinas_geradas':
            continue
        period = part['period']
        with origin.cursor() as source_cur:
            source_cur.execute('''SELECT parada_id, maquina_id, hora_inicio_parada,
                                         hora_fim_parada
                                  FROM public.paradas_maquinas_geradas
                                  WHERE parada_id >= %s AND parada_id < %s
                                  ORDER BY parada_id''',
                               (period * STRIDE, (period + 1) * STRIDE))
            records = source_cur.fetchall()
        expected = int(part['linhas'])
        require(len(records) == expected,
                f'Generated downtime source count mismatch: {part["caminho"]}')
        source_id = ids['industrial', period, 'paradas_maquinas_geradas']
        values = [generated_downtime_row(record, source_id, period, part['caminho'])
                  for record in records]
        if values:
            execute_values(cur, '''INSERT INTO dw.fact_downtime
                (downtime_id, source_file_id, period_index, original_id, start_day,
                 machine_id, started_at, ended_at, duration_minutes,
                 interval_invalid, outside_source_label) VALUES %s''', values,
                           page_size=5000)
        total += len(values)
    require(total > 0, 'Canonical generated downtime files are missing.')
    cur.execute('''SELECT count(*) FROM dw.fact_downtime f
                   JOIN dw.source_file s USING (source_file_id)
                   WHERE s.domain = 'industrial'
                     AND s.table_name = 'paradas_maquinas_geradas' ''')
    require(cur.fetchone()[0] == total, 'Generated downtime DW count mismatch.')
    return total


def warehouse_load(contract: dict, manifest: list[dict], parts: list[dict],
                   digest: str, connect, legacy, sql, execute_values, Json) -> dict:
    """Build V1 analytical facts plus the 20 new source-grain DW tables."""
    from dw import cli as warehouse_v1
    conn = connect('industrial', 'db_pesquisa_dw')
    origins = {domain: connect(domain, database) for domain, database in
               (('industrial', 'db_industrial'), ('financeiro', 'db_financeiro'))}
    ids = {}
    for index, part in enumerate(sorted(parts, key=lambda p: (
            contract[Path(p['caminho']).stem]['database'], p['period'],
            contract[Path(p['caminho']).stem]['table'])), start=1):
        table = contract[Path(part['caminho']).stem]
        domain = table['database'][3:]
        ids[domain, part['period'], table['table']] = index
    first, last = source_date_bounds(contract, manifest)
    counts = {}
    try:
        for origin in origins.values():
            with origin.cursor() as source_cur:
                source_cur.execute('SET TRANSACTION READ ONLY')
        with conn, conn.cursor() as cur:
            cur.execute(warehouse_v1.MIGRATION.read_text(encoding='utf-8'))
            rows = []
            for part in parts:
                source = contract[Path(part['caminho']).stem]
                domain = source['database'][3:]
                pk = next(f['name'] for f in source['fields'] if 'PK' in f['key'].split(','))
                count = len(part['rows']) if part['rows'] is not None else int(part['linhas'])
                rows.append((ids[domain, part['period'], source['table']], domain,
                             part['period'], source['table'], pk, f'raw_p{part["period"]}',
                             part['caminho'], part['sha256'], count))
            execute_values(cur, 'INSERT INTO dw.source_file VALUES %s', rows)
            cur.execute('SELECT count(*),sum(row_count) FROM dw.source_file')
            require(cur.fetchone() == (len(parts), sum(int(p['linhas']) for p in manifest)),
                    'DW source-file inventory differs from canonical CSV coverage.')
            execute_values(cur, 'INSERT INTO dw.dim_source_period VALUES %s',
                           [(p, legacy.PERIODS['industrial'][p], legacy.PERIODS['financeiro'][p])
                            for p in range(3)])
            cur.execute('''INSERT INTO dw.dim_day (day,year,month,day_of_month)
                SELECT d::date, extract(year FROM d)::integer, extract(month FROM d)::integer,
                       extract(day FROM d)::integer
                FROM generate_series(%s::date,%s::date,interval '1 day') d''', (first, last))
            warehouse_v1.load_dimensions(cur, origins, ids)
            for target, source_name in (('dim_product', 'produtos'),
                                        ('dim_machine', 'maquinas'),
                                        ('dim_material', 'materiais'),
                                        ('dim_material_lot', 'lotes_materiais')):
                cur.execute(sql.SQL('SELECT count(*) FROM dw.{}').format(sql.Identifier(target)))
                expected = sum(int(p['linhas']) for p in manifest
                               if Path(p['caminho']).stem == source_name)
                require(cur.fetchone()[0] == expected,
                        f'DW dimension count mismatch for {target}')
            old_facts = warehouse_v1.load_facts(cur, origins, ids)
            for source_table, (domain, _) in warehouse_v1.FACTS.items():
                expected = sum(int(p['linhas']) for p in manifest
                               if Path(p['caminho']).stem == source_table)
                require(old_facts[source_table] == expected,
                        f'V1 fact count mismatch for {source_table}')
            generated_stops = load_generated_downtime(
                cur, origins['industrial'], parts, ids, execute_values)
            expected_generated = sum(int(p['linhas']) for p in manifest
                                     if Path(p['caminho']).stem == 'paradas_maquinas_geradas')
            require(generated_stops == expected_generated,
                    'Generated downtime manifest count mismatch.')
            cur.execute('SELECT count(*) FROM dw.fact_downtime')
            total_stops = old_facts['paradas_maquinas'] + generated_stops
            require(cur.fetchone()[0] == total_stops,
                    'Combined downtime fact count mismatch.')
            counts['fact_downtime'] = total_stops
            for target, sources in DW_TABLES.items():
                # New facts and dimensions retain the exact source fields plus
                # source-file and period provenance. Maintenance is a union.
                fields = []
                for name in sources:
                    for field in contract[name]['fields']:
                        if field['name'] not in [known['name'] for known in fields]:
                            fields.append(field)
                        else:
                            known = next(f for f in fields if f['name'] == field['name'])
                            require(known['type'] == field['type'],
                                    f'Incompatible union column in {target}.{field["name"]}')
                columns = [sql.SQL('{} {}').format(sql.Identifier(f['name']), sql.SQL(f['type']))
                           for f in fields]
                columns.extend([
                    sql.SQL('source_file_id integer NOT NULL REFERENCES dw.source_file'),
                    sql.SQL('period_index smallint NOT NULL REFERENCES dw.dim_source_period'),
                    sql.SQL('original_id integer NOT NULL'),
                    sql.SQL('PRIMARY KEY (source_file_id,original_id)'),
                ])
                cur.execute(sql.SQL('CREATE TABLE dw.{} ({})').format(
                    sql.Identifier(target), sql.SQL(',').join(columns)))
                total = 0
                for part in parts:
                    name = Path(part['caminho']).stem
                    if name not in sources:
                        continue
                    table = contract[name]
                    domain, period = table['database'][3:], part['period']
                    pk = next(f['name'] for f in table['fields'] if 'PK' in f['key'].split(','))
                    source_id = ids[domain, period, table['table']]
                    select_fields = [f['name'] for f in table['fields']]
                    predicate = sql.SQL('{}=%s').format(sql.Identifier(pk)) if name == \
                        'composicao_tarifaria_inferida' else sql.SQL('{} >= %s AND {} < %s').format(
                        sql.Identifier(pk), sql.Identifier(pk))
                    parameters = (period,) if name == 'composicao_tarifaria_inferida' else \
                                 (period * STRIDE, (period + 1) * STRIDE)
                    with origins[domain].cursor() as source_cur:
                        source_cur.execute(sql.SQL('SELECT {} FROM public.{} WHERE {} ORDER BY {}').format(
                            sql.SQL(',').join(map(sql.Identifier, select_fields)),
                            sql.Identifier(table['table']), predicate, sql.Identifier(pk)), parameters)
                        data = source_cur.fetchall()
                    positions = {name: index for index, name in enumerate(select_fields)}
                    values = []
                    for record in data:
                        mapped = record[positions[pk]]
                        original = mapped if name == 'composicao_tarifaria_inferida' else mapped % STRIDE
                        values.append(tuple(record[positions[f['name']]] if f['name'] in positions
                                            else None for f in fields) + (source_id, period, original))
                    insert_fields = [f['name'] for f in fields] + [
                        'source_file_id', 'period_index', 'original_id']
                    if values:
                        statement = sql.SQL('INSERT INTO dw.{} ({}) VALUES %s').format(
                            sql.Identifier(target), sql.SQL(',').join(map(sql.Identifier, insert_fields)))
                        execute_values(cur, statement.as_string(conn), values, page_size=5000)
                    expected = len(part['rows']) if part['rows'] is not None else int(part['linhas'])
                    require(len(values) == expected,
                            f'DW row count mismatch for {part["caminho"]}')
                    total += len(values)
                cur.execute(sql.SQL('SELECT count(*) FROM dw.{}').format(sql.Identifier(target)))
                require(cur.fetchone()[0] == total, f'DW table count mismatch: {target}')
                counts[target] = total
            cur.execute('INSERT INTO dw.schema_migrations (version,source_fingerprint,source_checks) '
                        'VALUES (%s,%s,%s)', (2, digest,
                        Json({'canonical_files': len(manifest), 'source_partitions': len(parts),
                              'source_rows': sum(int(p['linhas']) for p in manifest)})))
            cur.execute('ANALYZE')
    finally:
        conn.close()
        for origin in origins.values():
            origin.close()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('plan', 'load'))
    parser.add_argument('--database-home', type=Path,
                        help='Explicit BancoModeloUse folder containing .env.local and .local/postgres')
    args = parser.parse_args()
    review = plan()
    if args.command == 'plan':
        print(json.dumps(review, ensure_ascii=False, indent=2))
        return
    require(args.database_home is not None, 'load requires --database-home.')
    psycopg2, sql, execute_values, Json, legacy = db_modules()
    connect = cluster_connector(psycopg2, args.database_home)
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))['tables']
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    parts = partitions(manifest)
    assert_empty_targets(connect, sql)
    create_missing_targets(connect, sql)
    source_counts = {database: source_load(database, contract, parts, connect, sql)
                     for database in ('db_industrial', 'db_financeiro')}
    warehouse_counts = warehouse_load(contract, manifest, parts,
                                      review['contract_sha256'], connect, legacy, sql,
                                      execute_values, Json)
    print(json.dumps({**review, 'database_writes': True,
                      'source_counts': source_counts, 'dw_counts': warehouse_counts},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
