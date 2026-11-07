"""Read-only reconciliation of the canonical CSV set. No PostgreSQL access."""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path

try:
    from .generate_canonical_csvs import BASE, FINANCE, ORIGINAL, PERIODS, ROOT, read_rows, require
except ImportError:  # Direct script execution.
    from generate_canonical_csvs import BASE, FINANCE, ORIGINAL, PERIODS, ROOT, read_rows, require

EXCLUDED_AI = {'ia_modelos_registry.csv', 'ia_insights_log.csv', 'ia_impacto_mensal.csv'}
GENERATED = {'consumo_energia_intervalo.csv', 'vinculos_manutencao_simulados.csv',
             'ordens_manutencao_geradas.csv', 'paradas_maquinas_geradas.csv',
             'custos_produto_mensais_simulados.csv', 'eventos_maquina_turno.csv',
             'metas_esg_simuladas.csv', 'resultados_projeto_esg_simulados.csv',
             'clientes_referenciados.csv', 'operadores_referenciados.csv',
             'inspetores_referenciados.csv',
             'rateio_custos_producao_produto_simulado.csv',
             'rateio_custos_indiretos_maquina_simulado.csv',
             'resumo_estado_maquina_turno_simulado.csv',
             'custo_hora_operador_estimado.csv',
             'consumo_insumos_operacionais_simulado.csv',
             'oee_maquina_turno_simulado.csv'}


def validate_manifest() -> dict:
    manifest = json.loads((BASE / 'manifesto_canonico.json').read_text(encoding='utf-8'))
    require(len(manifest) == 166, 'Unexpected number of canonical CSVs.')
    require(len({row['caminho'] for row in manifest}) == len(manifest),
            'Duplicate canonical paths.')
    classes = Counter()
    for row in manifest:
        path = ROOT / row['caminho']
        require(path.is_file() and path.resolve().is_relative_to(ROOT.resolve()),
                f'Invalid manifest path: {row["caminho"]}')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'],
                f'Hash mismatch: {path}.')
        with path.open(encoding='utf-8-sig', newline='') as handle:
            count = sum(1 for _ in csv.DictReader(handle))
        require(count == int(row['linhas']), f'Row count mismatch: {path}.')
        classes[row['classe']] += 1
    require(classes == {'original_preservado': 69, 'original_corrigido': 6,
                        'complementar': 39, 'referencia_derivada': 9,
                        'sintetico_derivado': 43}, f'Unexpected classes: {classes}.')
    on_disk = {path.resolve() for path in ROOT.parent.rglob('*.csv')}
    expected = {(ROOT / row['caminho']).resolve() for row in manifest}
    require(on_disk == expected,
            'A CSV outside the canonical ingestion set exists, or a canonical CSV is missing.')
    # The former v1 source fingerprint is historical. The three corrected CSVs
    # have new columns and must be validated without invoking the old importer.
    composition = read_rows(BASE / 'composicao_tarifaria_inferida.csv')
    require({int(row['periodo_indice']) for row in composition} == {0, 2},
            'Mixed-tariff composition periods changed.')
    mixed_total = 0
    for period, row in ((int(row['periodo_indice']), row) for row in composition):
        folder = BASE / PERIODS[period][0]
        tariffs = {item['tarifa_id']: Decimal(item['valor_kwh_brl'])
                   for item in read_rows(folder / 'tarifas_energia.csv')}
        peak_share = Decimal(row['fracao_kwh_ponta_inferida'])
        offpeak_share = Decimal(row['fracao_kwh_fora_ponta_inferida'])
        effective = (peak_share * tariffs[row['tarifa_ponta_id']]
                     + offpeak_share * tariffs[row['tarifa_fora_ponta_id']])
        require(peak_share + offpeak_share == 1
                and effective == Decimal(row['valor_efetivo_brl_kwh_inferido']),
                'Mixed-tariff composition is inconsistent.')
        for energy in read_rows(folder / 'consumo_energia_turno.csv'):
            if energy['posto_tarifario'] != 'MISTO_PONTA':
                continue
            mixed_total += 1
            deviation = abs(Decimal(energy['kwh_consumido']) * effective
                            - Decimal(energy['custo_energia_brl']))
            require(deviation <= Decimal('.005'),
                    'Mixed-tariff formula does not reconcile to cents.')
    require(mixed_total == 1087, 'Mixed-tariff source coverage changed.')
    return dict(classes)


def validate_model_contract() -> dict:
    """Require every canonical CSV to match one reviewed source table exactly."""
    contract_path = BASE / 'contrato_tabelas_canonicas.json'
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    tables = contract['tables']
    require(contract['version'] == 1 and len(tables) == 56,
            'Canonical source-table contract is missing or incomplete.')
    manifest = json.loads((BASE / 'manifesto_canonico.json').read_text(encoding='utf-8'))
    seen_tables = set()
    seen_keys = set()
    checked_rows = 0
    allowed_types = {'integer', 'numeric', 'text', 'date', 'timestamp', 'time', 'boolean'}
    for item in manifest:
        path = ROOT / item['caminho']
        csv_name = path.stem
        require(csv_name in tables, f'CSV has no modeled table: {item["caminho"]}')
        table = tables[csv_name]
        fields = table['fields']
        expected_header = [field['name'] for field in fields]
        require(len(expected_header) == len(set(expected_header)) and
                all(field['type'] in allowed_types for field in fields),
                f'Invalid model contract for {csv_name}')
        primary = [field['name'] for field in fields
                   if 'PK' in field['key'].split(',')]
        require(len(primary) == 1, f'Expected one modeled primary key: {csv_name}')
        with path.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            require(reader.fieldnames == expected_header,
                    f'CSV columns differ from modeled table: {item["caminho"]}')
            for number, row in enumerate(reader, start=2):
                require(None not in row and row[primary[0]] not in ('', None),
                        f'Invalid row or empty key: {item["caminho"]}:{number}')
                if csv_name == 'composicao_tarifaria_inferida':
                    period = int(row['periodo_indice'])
                else:
                    period = next((index for index, (folder, original) in enumerate(PERIODS)
                                   if folder in path.parts or original in path.parts or
                                   FINANCE[index] in path.parts), None)
                require(period in (0, 1, 2),
                        f'CSV is outside a modeled period: {item["caminho"]}')
                key = (csv_name, period, row[primary[0]])
                require(key not in seen_keys, f'Duplicate modeled key: {key}')
                seen_keys.add(key)
                for field in fields:
                    value = row[field['name']]
                    if value == '':
                        continue
                    typ = field['type']
                    try:
                        if typ == 'integer':
                            int(value)
                        elif typ == 'numeric':
                            Decimal(value)
                        elif typ == 'date':
                            date.fromisoformat(value)
                        elif typ == 'timestamp':
                            datetime.fromisoformat(value)
                        elif typ == 'time':
                            time.fromisoformat(value)
                        elif typ == 'boolean':
                            require(value.lower() in {'true', 'false', 't', 'f', '0', '1'},
                                    f'Invalid boolean: {value}')
                    except (ValueError, TypeError) as exc:
                        raise RuntimeError(
                            f'CSV value does not fit modeled type: '
                            f'{item["caminho"]}:{number}:{field["name"]}') from exc
                checked_rows += 1
        seen_tables.add(csv_name)
    require(seen_tables == set(tables),
            f'Modeled tables without canonical CSVs: {sorted(set(tables) - seen_tables)}')
    require(len(manifest) == 166, 'Every canonical file must have a modeled table.')
    return {'files': len(manifest), 'table_types': len(tables), 'rows': checked_rows,
            'missing_tables': 0, 'unmodeled_csvs': 0}


def validate_period(folder: Path, industrial: Path, financial: Path, period_index: int) -> dict:
    active = {path.name for path in folder.glob('*.csv')}
    require(len(active) == 13 and not active & EXCLUDED_AI and
            'consumo_energia_turno.csv' in active, 'Active complementary file set changed.')
    generated = BASE / 'gerados' / folder.name
    require({path.name for path in generated.glob('*.csv')} == GENERATED,
            'Generated file set changed.')
    energy = {row['registro_id']: row for row in read_rows(folder / 'consumo_energia_turno.csv')}
    tariffs = {row['tarifa_id']: row for row in read_rows(folder / 'tarifas_energia.csv')}
    group = defaultdict(lambda: [Decimal(0), Decimal(0), 0])
    for row in read_rows(generated / 'consumo_energia_intervalo.csv'):
        original = energy[row['registro_turno_id']]
        tariff = tariffs[row['tarifa_id']]
        start, end = (datetime.fromisoformat(row[key]) for key in ('inicio', 'fim'))
        require((end - start).total_seconds() == 3600 and row['maquina_id'] == original['maquina_id']
                and row['turno_id'] == original['turno_id']
                and tariff['posto_tarifario'] == row['posto_tarifario']
                and Decimal(row['kwh_simulado']) >= 0 and Decimal(row['custo_simulado_brl']) >= 0,
                'Invalid energy interval.')
        aggregate = group[row['registro_turno_id']]
        aggregate[0] += Decimal(row['kwh_simulado'])
        aggregate[1] += Decimal(row['custo_simulado_brl'])
        aggregate[2] += 1
    require(set(group) == set(energy), 'Energy row coverage differs.')
    for key, original in energy.items():
        kwh, cost, count = group[key]
        require(count == 8 and kwh == Decimal(original['kwh_consumido'])
                and cost == Decimal(original['custo_energia_brl']),
                f'Energy does not reconcile: {key}.')

    original_orders = read_rows(folder / 'ordens_manutencao.csv')
    generated_orders = read_rows(generated / 'ordens_manutencao_geradas.csv')
    orders = {row['om_id']: row for row in [*original_orders, *generated_orders]}
    alerts = {row['leitura_id']: row for row in read_rows(folder / 'telemetria_preditiva.csv')}
    original_stops = read_rows(industrial / 'paradas_maquinas.csv')
    generated_stops = read_rows(generated / 'paradas_maquinas_geradas.csv')
    stops = {row['parada_id']: row for row in [*original_stops, *generated_stops]}
    require(len(orders) == len(original_orders) + len(generated_orders)
            and len(stops) == len(original_stops) + len(generated_stops),
            'Generated maintenance IDs overlap originals.')
    links = read_rows(generated / 'vinculos_manutencao_simulados.csv')
    require(len({row['om_id'] for row in links}) == len(links), 'Maintenance order linked twice.')
    for row in links:
        order = orders[row['om_id']]
        require(row['maquina_id'] == order['maquina_id']
                and row['componente_id'] == order['componente_id']
                and (row['leitura_id'] or row['parada_id']), 'Invalid maintenance link.')
        if row['leitura_id']:
            alert = alerts[row['leitura_id']]
            require(alert['maquina_id'] == order['maquina_id']
                    and alert['componente_id'] == order['componente_id']
                    and alert['status_alerta'] != 'NORMAL', 'Invalid linked alert.')
        if row['parada_id']:
            require(stops[row['parada_id']]['maquina_id'] == order['maquina_id'],
                    'Invalid linked downtime.')
    require({row['om_id'] for row in generated_orders} <= {row['om_id'] for row in links},
            'Generated maintenance order without link.')
    require({row['parada_id'] for row in generated_stops} <=
            {row['parada_id'] for row in links if row['parada_id']},
            'Generated downtime without link.')

    finance = {row['mes_ano']: row for row in read_rows(folder / 'resultados_financeiros_mensais.csv')}
    products = {row['produto_id'] for row in read_rows(industrial / 'produtos.csv')}
    costs = defaultdict(lambda: [Decimal(0), Decimal(0), set()])
    for row in read_rows(generated / 'custos_produto_mensais_simulados.csv'):
        require(row['mes_ano'] in finance and row['produto_id'] in products,
                'Invalid product cost reference.')
        bucket = costs[row['mes_ano']]
        require(row['produto_id'] not in bucket[2], 'Duplicate product/month.')
        bucket[0] += Decimal(row['receita_atribuida_simulada_brl'])
        bucket[1] += Decimal(row['cpv_atribuido_simulado_brl'])
        bucket[2].add(row['produto_id'])
    require(set(costs) == set(finance), 'Product cost month coverage differs.')
    for month, source in finance.items():
        revenue, cpv, listed = costs[month]
        require(listed == products and revenue == Decimal(source['receita_total'])
                and cpv == Decimal(source['cpv']), f'Product allocation differs: {month}.')

    client_rows = read_rows(generated / 'clientes_referenciados.csv')
    inspector_rows = read_rows(generated / 'inspetores_referenciados.csv')
    clients = {row['cliente_id'] for row in client_rows}
    inspectors = {row['inspetor_id'] for row in inspector_rows}
    operator_rows = read_rows(generated / 'operadores_referenciados.csv')
    operators = {row['operador_id'] for row in operator_rows}
    operation_rows = read_rows(industrial / 'registros_operacao.csv')
    labor_rows = read_rows(financial / 'custo_mao_obra_historico.csv')
    sales_rows = read_rows(financial / 'vendas.csv')
    quality_rows = read_rows(industrial / 'controle_qualidade.csv')
    require(clients == {row['cliente_id'] for row in sales_rows}
            and inspectors == {row['inspetor_id'] for row in quality_rows}
            and operators == ({row['operador_id'] for row in operation_rows}
                              | {row['operador_id'] for row in labor_rows})
            and len(operator_rows) == len(operators)
            and len(client_rows) == len(clients)
            and len(inspector_rows) == len(inspectors)
            and all(row['identidade_cadastrada'] == 'false'
                    and row['nome_exibicao_simulado'].startswith(
                        f'{label} simulado P{period_index + 1}-')
                    for label, rows in (('Cliente', client_rows),
                                        ('Operador', operator_rows),
                                        ('Inspetor', inspector_rows)) for row in rows),
            'Reference catalogs do not cover source IDs or claim unsupported identities.')
    missing_rates = read_rows(generated / 'custo_hora_operador_estimado.csv')
    expected_missing_rates = ({row['operador_id'] for row in operation_rows}
                              - {row['operador_id'] for row in labor_rows})
    require(len(missing_rates) == len(expected_missing_rates)
            and {row['operador_id'] for row in missing_rates} == expected_missing_rates
            and all(row['operador_id'] in operators
                    and Decimal(row['custo_hora_estimado_brl']) > 0
                    and row['custo_hora_estimado_brl'] == row['base_mediana_periodo_brl']
                    and row['origem'] == 'mediana_simulada_de_tarifas_observadas_no_periodo'
                    for row in missing_rates), 'Missing labor-rate scenario is inconsistent.')

    production_sources = {row['id']: row for row in read_rows(financial / 'custos_producao.csv')}
    machine_ids = {row['maquina_id'] for row in read_rows(industrial / 'maquinas.csv')}
    indirect_sources = {row['rateio_id']: row
                        for row in read_rows(financial / 'custos_indiretos_rateio.csv')}
    production_allocations = defaultdict(lambda: [Decimal(0), set()])
    for row in read_rows(generated / 'rateio_custos_producao_produto_simulado.csv'):
        source = production_sources[row['custo_producao_id']]
        require(row['mes_ano'] == source['data_registro'][:7]
                and row['produto_id'] in products
                and row['custo_total_origem_brl'] == source['custo_total']
                and row['origem'] == 'rateio_sintetico_por_unidades_operadas_no_mes',
                'Invalid production cost allocation reference.')
        bucket = production_allocations[row['custo_producao_id']]
        require(row['produto_id'] not in bucket[1], 'Duplicate production allocation.')
        bucket[0] += Decimal(row['custo_atribuido_simulado_brl'])
        bucket[1].add(row['produto_id'])
    require(set(production_allocations) == set(production_sources)
            and all(total == Decimal(production_sources[key]['custo_total'])
                    and listed == products
                    for key, (total, listed) in production_allocations.items()),
            'Production cost allocations do not reconcile.')
    indirect_allocations = defaultdict(lambda: [Decimal(0), set()])
    for row in read_rows(generated / 'rateio_custos_indiretos_maquina_simulado.csv'):
        source = indirect_sources[row['rateio_origem_id']]
        require(row['mes_ano'] == source['data_referencia'][:7]
                and row['maquina_id'] in machine_ids
                and row['custo_total_origem_brl'] == source['custo_total_mes']
                and row['origem'] == 'rateio_sintetico_por_horas_reportadas_no_mes',
                'Invalid indirect cost allocation reference.')
        bucket = indirect_allocations[row['rateio_origem_id']]
        require(row['maquina_id'] not in bucket[1], 'Duplicate indirect allocation.')
        bucket[0] += Decimal(row['custo_atribuido_simulado_brl'])
        bucket[1].add(row['maquina_id'])
    require(set(indirect_allocations) == set(indirect_sources)
            and all(total == Decimal(indirect_sources[key]['custo_total_mes'])
                    and listed == machine_ids
                    for key, (total, listed) in indirect_allocations.items()),
            'Indirect cost allocations do not reconcile.')

    variable_sources = {row['custo_operacional_id']: row
                        for row in read_rows(financial / 'custos_operacionais_variaveis.csv')}
    variable_keys = set()
    normalized_units = 0
    for row in read_rows(generated / 'consumo_insumos_operacionais_simulado.csv'):
        source = variable_sources[row['custo_operacional_id']]
        key = row['custo_operacional_id'], row['maquina_id']
        quantity = Decimal(row['quantidade_simulada'])
        price = Decimal(row['valor_unitario_origem_brl'])
        expected_cost = (quantity * price).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        require(key not in variable_keys and row['maquina_id'] in machine_ids
                and row['mes_ano'] == source['data_leitura'][:7]
                and row['insumo'] == source['insumo']
                and row['unidade_fonte'] == source['unidade_medida']
                and row['valor_unitario_origem_brl'] == source['valor_unitario']
                and quantity >= 0 and Decimal(row['horas_base_operacoes']) >= 0
                and Decimal(row['custo_total_simulado_brl']) == expected_cost,
                'Invalid simulated variable-input consumption.')
        variable_keys.add(key)
        if source['insumo'] in {'Energia', 'Manutencao Tecnologica'}:
            require(row['unidade_simulada'] in {'kWh', 'servico'}
                    and row['unidade_simulada'] == row['unidade_fonte']
                    and row['fator_quantidade_por_hora'] == ''
                    and source['unidade_medida_original'] == 'l'
                    and source['origem_ajuste_unidade'] == 'corrigida_por_tipo_insumo'
                    and 'unidade_corrigida_na_fonte' in row['origem'],
                    'The corrected source unit has no provenance.')
            normalized_units += 1
        else:
            require(row['unidade_simulada'] == row['unidade_fonte']
                    and source['unidade_medida_original'] == source['unidade_medida']
                    and source['origem_ajuste_unidade'] == 'original_preservada'
                    and Decimal(row['fator_quantidade_por_hora']) > 0
                    and row['origem'] == 'fator_sintetico_por_hora_reportada_de_operacao',
                    'Invalid synthetic consumption factor.')
    require(variable_keys == {(source_id, machine)
                              for source_id in variable_sources for machine in machine_ids},
            'Variable-input consumption does not cover every source and machine.')

    sales = sales_rows
    require(all(row['produto_id'] in products for row in sales),
            'Sale refers to a product outside its source period.')
    materials = {row['material_id'] for row in read_rows(industrial / 'materiais.csv')}
    lots = {row['lote_id']: row for row in read_rows(industrial / 'lotes_materiais.csv')}
    material_costs = read_rows(financial / 'materiais_custo_historico.csv')
    expected_fields = {'custo_material_id', 'material_id', 'custo_unitario',
                       'data_compra', 'lote_material_id',
                       'lote_material_id_original', 'origem_vinculo_lote'}
    relinked = 0
    for row in material_costs:
        require(set(row) == expected_fields and row['material_id'] in materials
                and row['lote_material_id'] in lots
                and lots[row['lote_material_id']]['material_id'] == row['material_id'],
                'Invalid material-cost lot relationship.')
        original_lot = row['lote_material_id_original']
        require(original_lot in lots, 'Original material-cost lot not found.')
        if row['origem_vinculo_lote'] == 'original_coerente':
            require(original_lot == row['lote_material_id'],
                    'An original lot was changed without provenance.')
        else:
            require(row['origem_vinculo_lote'] == 'reassociado_por_material_e_data'
                    and original_lot != row['lote_material_id']
                    and lots[original_lot]['material_id'] != row['material_id'],
                    'Invalid provenance for a reassociated lot.')
            relinked += 1

    operations = {row['registro_id']: int(row['quantidade_produzida_real'])
                  for row in operation_rows}
    event_quantity = defaultdict(int)
    event_count = Counter()
    shift_quantities = defaultdict(lambda: [0, 0])
    for row in read_rows(generated / 'eventos_maquina_turno.csv'):
        start, end = (datetime.fromisoformat(row[key]) for key in ('inicio', 'fim'))
        require(end > start and row['turno_id'] in {'1', '2', '3'}
                and row['estado'] in {'SETUP', 'PRODUCAO', 'PARADA'}, 'Invalid machine event.')
        quantity = int(row['unidades_reportadas'])
        good = int(row['unidades_boas_simuladas'])
        require(0 <= good <= quantity, 'Invalid simulated quality.')
        shift_day = start.date() - timedelta(days=1) if row['turno_id'] == '3' and start.hour < 6 else start.date()
        shift_bucket = shift_quantities[row['maquina_id'], shift_day.isoformat(), row['turno_id']]
        shift_bucket[0] += quantity
        shift_bucket[1] += good
        if row['registro_operacao_id']:
            require(row['registro_operacao_id'] in operations and not row['parada_id'],
                    'Invalid operation event reference.')
            event_quantity[row['registro_operacao_id']] += quantity
            event_count[row['registro_operacao_id']] += 1
        else:
            require(row['parada_id'] in stops and row['estado'] == 'PARADA',
                    'Invalid downtime event reference.')
    require(set(event_quantity) == set(operations), 'Operation event coverage differs.')
    require(all(event_quantity[key] == value for key, value in operations.items()),
            'Operation quantities changed in events.')
    summary_keys = set()
    summaries = {}
    overlap_seconds = Decimal(0)
    for row in read_rows(generated / 'resumo_estado_maquina_turno_simulado.csv'):
        key = row['maquina_id'], row['data_turno'], row['turno_id']
        require(key in shift_quantities and key not in summary_keys,
                'Missing or duplicate machine-state summary key.')
        summary_keys.add(key)
        require(row['resumo_id'] not in summaries, 'Duplicate machine-state summary ID.')
        summaries[row['resumo_id']] = row
        durations = [Decimal(row[field]) for field in (
            'segundos_producao', 'segundos_setup', 'segundos_parada',
            'segundos_sem_evento')]
        overlap = Decimal(row['segundos_sobreposicao_fonte'])
        require(all(value >= 0 for value in durations)
                and sum(durations) == 28800 and 0 <= overlap <= 28800
                and [int(row['unidades_reportadas']), int(row['unidades_boas_simuladas'])]
                == shift_quantities[key]
                and row['origem'] == 'prioridade_parada_setup_producao_sobre_eventos_derivados',
                'Machine-state summary does not reconcile.')
        overlap_seconds += overlap
    require(summary_keys == set(shift_quantities), 'Machine-state shift coverage differs.')
    target_rows = {row['meta_id']: row for row in read_rows(folder / 'metas_producao_maquina.csv')}
    oee_ids = set()
    oee_summary_ids = set()
    capped_performance = 0
    outside_target = 0
    for row in read_rows(generated / 'oee_maquina_turno_simulado.csv'):
        summary = summaries[row['resumo_estado_id']]
        target = target_rows[row['meta_id']]
        availability = Decimal(row['disponibilidade_simulada'])
        performance_raw = Decimal(row['performance_bruta_simulada'])
        performance = Decimal(row['performance_limitada_simulada'])
        quality = Decimal(row['qualidade_simulada'])
        oee = Decimal(row['oee_simulado'])
        inside = (target['data_vigencia_inicio'] <= row['data_turno'] <=
                  target['data_vigencia_fim'])
        require(row['oee_id'] not in oee_ids
                and row['resumo_estado_id'] not in oee_summary_ids
                and row['maquina_id'] == summary['maquina_id'] == target['maquina_id']
                and row['data_turno'] == summary['data_turno']
                and row['turno_id'] == summary['turno_id']
                and row['segundos_programados'] == '28800'
                and row['segundos_producao_exclusivos'] == summary['segundos_producao']
                and row['unidades_reportadas'] == summary['unidades_reportadas']
                and row['unidades_boas_simuladas'] == summary['unidades_boas_simuladas']
                and row['segundos_conflito_fonte'] == summary['segundos_sobreposicao_fonte']
                and row['meta_produtividade_un_h'] == target['meta_produtividade_un_h']
                and row['meta_fora_vigencia'] == str(not inside).lower()
                and 0 <= availability <= 1 and performance_raw >= 0
                and 0 <= performance <= 1 and 0 <= quality <= 1 and 0 <= oee <= 1
                and abs(performance - min(performance_raw, Decimal(1))) <= Decimal('.000001')
                and abs(oee - availability * performance * quality) <= Decimal('.000003')
                and row['performance_acima_meta'] == str(performance_raw > 1).lower(),
                'Simulated OEE does not reconcile to its source shift and target.')
        oee_ids.add(row['oee_id'])
        oee_summary_ids.add(row['resumo_estado_id'])
        capped_performance += performance_raw > 1
        outside_target += not inside
    require(oee_summary_ids == set(summaries), 'OEE scenario shift coverage differs.')

    resources = {row['mes_ano'] for row in read_rows(folder / 'consumo_recursos_esg.csv')}
    emissions = {row['mes_ano']: row for row in read_rows(folder / 'emissoes_co2.csv')}
    goals = read_rows(generated / 'metas_esg_simuladas.csv')
    require(len(goals) == 5 * len(resources)
            and {row['mes_ano'] for row in goals} == resources == set(emissions),
            'ESG goal coverage differs.')
    for row in goals:
        require(row['vigencia_inicio'][:7] == row['mes_ano']
                and row['vigencia_fim'][:7] == row['mes_ano']
                and row['vigencia_inicio'] <= row['vigencia_fim']
                and Decimal(row['valor_meta']) >= 0,
                'Invalid ESG goal validity.')
    projects = {row['projeto_id']: row for row in read_rows(folder / 'projetos_investimento_verde.csv')}
    results = read_rows(generated / 'resultados_projeto_esg_simulados.csv')
    require(len({(row['projeto_id'], row['mes_ano']) for row in results}) == len(results),
            'Duplicate ESG project/month.')
    for row in results:
        require(row['projeto_id'] in projects and row['mes_ano'] in resources
                and row['mes_ano'] >= projects[row['projeto_id']]['data_aprovacao'][:7]
                and Decimal(row['valor_atribuido_simulado']) >= 0,
                'Invalid ESG result reference.')
    return {'energy_turns': len(energy), 'energy_intervals': sum(x[2] for x in group.values()),
            'maintenance_links': len(links), 'generated_orders': len(generated_orders),
            'generated_stops': len(generated_stops), 'product_months': len(costs),
            'operation_events': sum(event_count.values()), 'sales_product_links': len(sales),
            'material_cost_lot_links': len(material_costs),
            'material_cost_lots_reassociated': relinked, 'esg_goals': len(goals),
            'esg_project_results': len(results), 'reference_clients': len(clients),
            'reference_operators': len(operators), 'reference_inspectors': len(inspectors),
            'allocated_production_cost_rows': len(production_allocations),
            'allocated_indirect_cost_rows': len(indirect_allocations),
            'machine_state_shifts': len(summary_keys),
            'machine_state_overlap_seconds': str(overlap_seconds),
            'simulated_operator_rates': len(missing_rates),
            'simulated_input_rows': len(variable_keys),
            'normalized_source_units': normalized_units,
            'simulated_oee_shifts': len(oee_ids),
            'oee_performance_capped': capped_performance,
            'oee_target_outside_validity': outside_target}


def main() -> None:
    report = {'canonical_classes': validate_manifest(),
              'model_contract': validate_model_contract(),
              'periods': {}, 'database_writes': False}
    for period, (folder_name, original_name) in enumerate(PERIODS):
        report['periods'][folder_name] = validate_period(BASE / folder_name,
                                                         ORIGINAL / original_name,
                                                         ORIGINAL / FINANCE[period], period)
    report['ai_csv_in_active_set'] = 0
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
