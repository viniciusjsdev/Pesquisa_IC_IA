"""Generate traceable synthetic companion CSVs. No database connections.

The 72 untouched original CSVs and the three reconciled material-cost CSVs
are read as inputs. Re-running produces identical companion files.
"""
from __future__ import annotations

from collections import defaultdict
import csv
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'dados_complementares_datamind'
ORIGINAL = ROOT / 'dados_simulados'
PERIODS = (
    ('periodo_2015_2016', 'dados_industriais_automotivo_eletronica_2015_2017'),
    ('periodo_2017_2020', 'dados_industriais_automotivo_eletronica_2017_2020'),
    ('periodo_2021_2025', 'dados_industriais_automotivo_eletronics_2021_2025'),
)
FINANCE = ('dados_financeiros_2015_2016', 'dados_financeiros_2017_2020',
           'dados_financeiros_2021_2025')
CENT = Decimal('0.01')
KWH = Decimal('0.0001')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fields: list[str], rows) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='',
                                     dir=path.parent, delete=False, suffix='.tmp') as handle:
        temporary = Path(handle.name)
        try:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
            writer.writeheader()
            count = 0
            for row in rows:
                require(set(row) == set(fields), f'Field mismatch in {path.name}')
                writer.writerow(row)
                count += 1
        except Exception:
            handle.close()
            temporary.unlink(missing_ok=True)
            raise
    if path.exists() and temporary.read_bytes() == path.read_bytes():
        temporary.unlink()
    else:
        temporary.replace(path)
    return count


def money(value: Decimal) -> str:
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


def shift_id(instant: datetime) -> int:
    hour = instant.hour
    return 1 if 6 <= hour < 14 else 2 if 14 <= hour < 22 else 3


def next_shift_boundary(instant: datetime) -> datetime:
    options = [datetime.combine(instant.date() + timedelta(days=offset), time(hour))
               for offset in (0, 1) for hour in (6, 14, 22)]
    return min(candidate for candidate in options if candidate > instant)


def allocate(total: Decimal, weights: list[Decimal], quantum: Decimal) -> list[Decimal]:
    require(total >= 0 and sum(weights) > 0, 'Invalid allocation.')
    result = [(total * weight / sum(weights)).quantize(quantum, rounding=ROUND_HALF_UP)
              for weight in weights[:-1]]
    result.append(total - sum(result))
    require(all(value >= 0 for value in result) and sum(result) == total,
            'Allocation failed to conserve its total.')
    return result


def energy_intervals(period: int, folder: Path) -> list[dict]:
    rows = read_rows(folder / 'consumo_energia_turno.csv')
    tariff_rows = read_rows(folder / 'tarifas_energia.csv')
    tariffs = {row['posto_tarifario']: row for row in tariff_rows}
    shifts = {row['turno_id']: row for row in read_rows(folder / 'turnos_trabalho.csv')}
    output = []
    for row in rows:
        shift = shifts[row['turno_id']]
        start = datetime.combine(date.fromisoformat(row['data']),
                                 time.fromisoformat(shift['hora_inicio']))
        hours = [start + timedelta(hours=i) for i in range(8)]
        peak = [18 <= hour.hour < 21 for hour in hours]
        post = row['posto_tarifario']
        if post == 'MISTO_PONTA':
            require(sum(peak) == 3, 'Mixed tariff outside peak shift.')
            weights = [Decimal('.4') / 3 if is_peak else Decimal('.6') / 5
                       for is_peak in peak]
        elif post == 'FORA_PONTA':
            weights = [Decimal(0) if is_peak else Decimal(1) for is_peak in peak]
        else:
            require(post == 'MADRUGADA' and not any(peak), 'Unexpected energy post.')
            weights = [Decimal(1)] * 8
        total_kwh = Decimal(row['kwh_consumido'])
        reported_cost = Decimal(row['custo_energia_brl'])
        portions = allocate(total_kwh, weights, KWH)
        rates = [Decimal(tariffs['PONTA' if is_peak else
                                 ('MADRUGADA' if post == 'MADRUGADA' else 'FORA_PONTA')]
                         ['valor_kwh_brl']) for is_peak in peak]
        calculated = sum(kwh * rate for kwh, rate in zip(portions, rates))
        require(abs(calculated - reported_cost) <= Decimal('.01'),
                f'Energy cost cannot be reconciled: {period}/{row["registro_id"]}.')
        costs = [(kwh * rate).quantize(CENT, rounding=ROUND_HALF_UP)
                 for kwh, rate in zip(portions[:-1], rates[:-1])]
        costs.append(reported_cost - sum(costs))
        require(all(cost >= 0 for cost in costs) and sum(costs) == reported_cost,
                'Energy cost allocation failed.')
        for index, (hour, kwh, cost, rate) in enumerate(zip(hours, portions, costs, rates), 1):
            interval_post = 'PONTA' if peak[index - 1] else (
                'MADRUGADA' if post == 'MADRUGADA' else 'FORA_PONTA')
            output.append({
                'intervalo_id': len(output) + 1,
                'registro_turno_id': row['registro_id'],
                'maquina_id': row['maquina_id'], 'turno_id': row['turno_id'],
                'inicio': hour.isoformat(sep=' '),
                'fim': (hour + timedelta(hours=1)).isoformat(sep=' '),
                'posto_tarifario': interval_post,
                'tarifa_id': tariffs[interval_post]['tarifa_id'],
                'kwh_simulado': str(kwh), 'custo_simulado_brl': money(cost),
                'tarifa_brl_kwh': str(rate),
                'origem': 'alocacao_sintetica_do_total_por_turno',
            })
    return output


ENERGY_FIELDS = ['intervalo_id', 'registro_turno_id', 'maquina_id', 'turno_id',
                 'inicio', 'fim', 'posto_tarifario', 'tarifa_id', 'kwh_simulado',
                 'custo_simulado_brl', 'tarifa_brl_kwh', 'origem']


def maintenance_links(folder: Path, industrial: Path) -> list[dict]:
    alerts = [row for row in read_rows(folder / 'telemetria_preditiva.csv')
              if row['status_alerta'] != 'NORMAL']
    orders = read_rows(folder / 'ordens_manutencao.csv')
    stops = read_rows(industrial / 'paradas_maquinas.csv')
    unused_alerts = {row['leitura_id'] for row in alerts}
    unused_stops = {row['parada_id'] for row in stops}
    output = []
    for order in sorted(orders, key=lambda row: (row['data_abertura'], int(row['om_id']))):
        opened = date.fromisoformat(order['data_abertura'])
        candidates = [row for row in alerts if row['leitura_id'] in unused_alerts
                      and row['maquina_id'] == order['maquina_id']
                      and row['componente_id'] == order['componente_id']
                      and 0 <= (opened - datetime.fromisoformat(row['data_hora']).date()).days <= 7]
        candidates.sort(key=lambda row: ((opened - datetime.fromisoformat(row['data_hora']).date()).days,
                                         int(row['leitura_id'])))
        alert = candidates[0] if candidates else None
        candidates = [row for row in stops if row['parada_id'] in unused_stops
                      and row['maquina_id'] == order['maquina_id']
                      and abs((datetime.fromisoformat(row['hora_inicio_parada']).date() - opened).days) <= 1]
        candidates.sort(key=lambda row: (abs((datetime.fromisoformat(row['hora_inicio_parada']).date() - opened).days),
                                         int(row['parada_id'])))
        stop = candidates[0] if candidates else None
        if alert is None and stop is None:
            continue
        if alert:
            unused_alerts.remove(alert['leitura_id'])
        if stop:
            unused_stops.remove(stop['parada_id'])
        output.append({'vinculo_id': len(output) + 1, 'om_id': order['om_id'],
                       'leitura_id': alert['leitura_id'] if alert else '',
                       'parada_id': stop['parada_id'] if stop else '',
                       'maquina_id': order['maquina_id'],
                       'componente_id': order['componente_id'],
                       'origem': 'pareamento_sintetico_maquina_componente_data'})
    return output


MAINTENANCE_FIELDS = ['vinculo_id', 'om_id', 'leitura_id', 'parada_id', 'maquina_id',
                      'componente_id', 'origem']

GENERATED_ORDER_FIELDS = ['om_id', 'codigo_om', 'maquina_id', 'componente_id',
                          'tipo_manutencao', 'prioridade', 'data_abertura',
                          'data_limite', 'data_conclusao', 'status',
                          'custo_estimado', 'custo_real', 'horas_estimadas',
                          'horas_reais', 'motivo', 'origem']
GENERATED_STOP_FIELDS = ['parada_id', 'maquina_id', 'hora_inicio_parada',
                         'hora_fim_parada', 'motivo_parada', 'data_registro', 'origem']


def synthetic_incidents(period: int, folder: Path, existing_links: list[dict]
                        ) -> tuple[list[dict], list[dict], list[dict]]:
    """Create separately identified simulated interventions for unlinked alerts."""
    linked_alerts = {str(row['leitura_id']) for row in existing_links if row['leitura_id']}
    existing_orders = read_rows(folder / 'ordens_manutencao.csv')
    costs = [Decimal(row['custo_real']) for row in existing_orders if row['custo_real']]
    require(costs, 'No maintenance cost basis for simulation.')
    typical_cost = (sum(costs) / len(costs)).quantize(CENT, rounding=ROUND_HALF_UP)
    orders = []
    stops = []
    links = []
    for alert in read_rows(folder / 'telemetria_preditiva.csv'):
        if alert['status_alerta'] == 'NORMAL' or alert['leitura_id'] in linked_alerts:
            continue
        event_id = 900000 + int(alert['leitura_id'])
        require(event_id < 1000000, 'Generated maintenance ID exceeds period stride.')
        alert_at = datetime.fromisoformat(alert['data_hora'])
        opened = alert_at + timedelta(hours=1)
        critical = alert['status_alerta'] == 'CRITICO'
        duration = Decimal('2.5') if critical else Decimal('1.0')
        closed = opened + timedelta(hours=float(duration))
        orders.append({
            'om_id': event_id, 'codigo_om': f'SIM-OM-{period}-{alert["leitura_id"]}',
            'maquina_id': alert['maquina_id'], 'componente_id': alert['componente_id'],
            'tipo_manutencao': 'CORRETIVA' if critical else 'PREDITIVA',
            'prioridade': 'CRITICA' if critical else 'MEDIA',
            'data_abertura': opened.date().isoformat(),
            'data_limite': (opened + timedelta(days=1)).date().isoformat(),
            'data_conclusao': closed.isoformat(sep=' '), 'status': 'CONCLUIDA',
            'custo_estimado': money(typical_cost), 'custo_real': money(typical_cost),
            'horas_estimadas': str(duration), 'horas_reais': str(duration),
            'motivo': 'Intervencao simulada apos alerta preditivo',
            'origem': 'incidente_sintetico_gerado',
        })
        stop_id = event_id if critical else ''
        if critical:
            stop_start = opened + timedelta(hours=1)
            stop_end = stop_start + timedelta(hours=float(duration))
            stops.append({
                'parada_id': stop_id, 'maquina_id': alert['maquina_id'],
                'hora_inicio_parada': stop_start.isoformat(sep=' '),
                'hora_fim_parada': stop_end.isoformat(sep=' '),
                'motivo_parada': 'falha_sintetica_apos_alerta',
                'data_registro': stop_start.isoformat(sep=' '),
                'origem': 'incidente_sintetico_gerado',
            })
        links.append({
            'vinculo_id': len(existing_links) + len(links) + 1,
            'om_id': event_id, 'leitura_id': alert['leitura_id'],
            'parada_id': stop_id, 'maquina_id': alert['maquina_id'],
            'componente_id': alert['componente_id'],
            'origem': 'incidente_sintetico_gerado',
        })
    return orders, stops, links


def product_costs(folder: Path, industrial: Path) -> list[dict]:
    orders = {row['ordem_producao_id']: row['produto_id']
              for row in read_rows(industrial / 'ordens_producao.csv')}
    products = [row['produto_id'] for row in read_rows(industrial / 'produtos.csv')]
    volume = defaultdict(int)
    with (industrial / 'registros_operacao.csv').open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            product = orders[row['ordem_producao_id']]
            volume[row['hora_inicio'][:7], product] += int(row['quantidade_produzida_real'])
    output = []
    for month in read_rows(folder / 'resultados_financeiros_mensais.csv'):
        key = month['mes_ano']
        weights = [Decimal(volume[key, product]) for product in products]
        if sum(weights) == 0:
            weights = [Decimal(1)] * len(products)
            rule = 'pesos_iguais_sem_operacao_no_mes'
        else:
            rule = 'peso_quantidade_reportada_nas_operacoes'
        revenue = allocate(Decimal(month['receita_total']), weights, CENT)
        cpv = allocate(Decimal(month['cpv']), weights, CENT)
        for product, weight, sales, cost in zip(products, weights, revenue, cpv):
            output.append({'registro_id': len(output) + 1, 'mes_ano': key,
                           'produto_id': product, 'unidades_base_operacoes': int(volume[key, product]),
                           'receita_atribuida_simulada_brl': money(sales),
                           'cpv_atribuido_simulado_brl': money(cost),
                           'origem': rule})
    return output


PRODUCT_FIELDS = ['registro_id', 'mes_ano', 'produto_id', 'unidades_base_operacoes',
                  'receita_atribuida_simulada_brl', 'cpv_atribuido_simulado_brl', 'origem']


def referenced_people(period: int, industrial: Path, financial: Path) -> dict[str, tuple[list[str], list[dict]]]:
    """Create key targets from observed IDs without inventing identities."""
    operations = {row['operador_id'] for row in read_rows(industrial / 'registros_operacao.csv')}
    labor = {row['operador_id'] for row in read_rows(financial / 'custo_mao_obra_historico.csv')}
    inspectors = {row['inspetor_id'] for row in read_rows(industrial / 'controle_qualidade.csv')}
    clients = {row['cliente_id'] for row in read_rows(financial / 'vendas.csv')}
    return {
        'clientes_referenciados.csv': (
            ['cliente_id', 'nome_exibicao_simulado', 'origem_referencia', 'identidade_cadastrada'],
            [{'cliente_id': key, 'origem_referencia': 'vendas.cliente_id',
              'nome_exibicao_simulado': f'Cliente simulado P{period + 1}-{int(key):03d}',
              'identidade_cadastrada': 'false'} for key in sorted(clients, key=int)]),
        'operadores_referenciados.csv': (
            ['operador_id', 'nome_exibicao_simulado', 'em_operacoes',
             'em_custo_mao_obra', 'identidade_cadastrada'],
            [{'operador_id': key, 'em_operacoes': str(key in operations).lower(),
              'em_custo_mao_obra': str(key in labor).lower(),
              'nome_exibicao_simulado': f'Operador simulado P{period + 1}-{int(key):03d}',
              'identidade_cadastrada': 'false'} for key in sorted(operations | labor, key=int)]),
        'inspetores_referenciados.csv': (
            ['inspetor_id', 'nome_exibicao_simulado', 'origem_referencia',
             'identidade_cadastrada'],
            [{'inspetor_id': key, 'origem_referencia': 'controle_qualidade.inspetor_id',
              'nome_exibicao_simulado': f'Inspetor simulado P{period + 1}-{int(key):03d}',
              'identidade_cadastrada': 'false'} for key in sorted(inspectors, key=int)]),
    }


PRODUCTION_ALLOCATION_FIELDS = [
    'rateio_id', 'custo_producao_id', 'mes_ano', 'produto_id',
    'unidades_base_operacoes', 'custo_total_origem_brl',
    'custo_atribuido_simulado_brl', 'origem']
INDIRECT_ALLOCATION_FIELDS = [
    'rateio_id', 'rateio_origem_id', 'mes_ano', 'maquina_id',
    'horas_base_operacoes', 'custo_total_origem_brl',
    'custo_atribuido_simulado_brl', 'origem']


def financial_allocations(industrial: Path, financial: Path) -> dict[str, tuple[list[str], list[dict]]]:
    """Allocate aggregate costs without claiming a source-level product or machine link."""
    orders = {row['ordem_producao_id']: row['produto_id']
              for row in read_rows(industrial / 'ordens_producao.csv')}
    products = [row['produto_id'] for row in read_rows(industrial / 'produtos.csv')]
    machines = [row['maquina_id'] for row in read_rows(industrial / 'maquinas.csv')]
    units = defaultdict(int)
    hours = defaultdict(Decimal)
    with (industrial / 'registros_operacao.csv').open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            month = row['hora_inicio'][:7]
            units[month, orders[row['ordem_producao_id']]] += int(row['quantidade_produzida_real'])
            duration = Decimal(str((datetime.fromisoformat(row['hora_fim']) -
                                    datetime.fromisoformat(row['hora_inicio'])).total_seconds())) / 3600
            require(duration > 0, f'Invalid operation duration: {row["registro_id"]}')
            hours[month, row['maquina_id']] += duration
    production = []
    for source in read_rows(financial / 'custos_producao.csv'):
        month = source['data_registro'][:7]
        weights = [Decimal(units[month, product]) for product in products]
        require(sum(weights) > 0, f'No production allocation basis in {month}')
        values = allocate(Decimal(source['custo_total']), weights, CENT)
        for product, weight, value in zip(products, weights, values):
            production.append({
                'rateio_id': len(production) + 1, 'custo_producao_id': source['id'],
                'mes_ano': month, 'produto_id': product,
                'unidades_base_operacoes': int(weight),
                'custo_total_origem_brl': source['custo_total'],
                'custo_atribuido_simulado_brl': money(value),
                'origem': 'rateio_sintetico_por_unidades_operadas_no_mes'})
    indirect = []
    for source in read_rows(financial / 'custos_indiretos_rateio.csv'):
        require(source['base_rateio'] == 'Horas Maquina', 'Unsupported indirect allocation base.')
        month = source['data_referencia'][:7]
        weights = [hours[month, machine] for machine in machines]
        require(sum(weights) > 0, f'No machine-hour allocation basis in {month}')
        values = allocate(Decimal(source['custo_total_mes']), weights, CENT)
        for machine, weight, value in zip(machines, weights, values):
            indirect.append({
                'rateio_id': len(indirect) + 1, 'rateio_origem_id': source['rateio_id'],
                'mes_ano': month, 'maquina_id': machine,
                'horas_base_operacoes': str(weight),
                'custo_total_origem_brl': source['custo_total_mes'],
                'custo_atribuido_simulado_brl': money(value),
                'origem': 'rateio_sintetico_por_horas_reportadas_no_mes'})
    return {
        'rateio_custos_producao_produto_simulado.csv': (PRODUCTION_ALLOCATION_FIELDS, production),
        'rateio_custos_indiretos_maquina_simulado.csv': (INDIRECT_ALLOCATION_FIELDS, indirect),
    }


LABOR_RATE_FIELDS = ['operador_id', 'custo_hora_estimado_brl', 'data_vigencia',
                     'base_mediana_periodo_brl', 'origem']
INPUT_CONSUMPTION_FIELDS = [
    'consumo_id', 'custo_operacional_id', 'mes_ano', 'maquina_id', 'insumo',
    'unidade_fonte', 'unidade_simulada', 'horas_base_operacoes',
    'fator_quantidade_por_hora', 'quantidade_simulada',
    'valor_unitario_origem_brl', 'custo_total_simulado_brl', 'origem']


def missing_labor_rates(industrial: Path, financial: Path) -> list[dict]:
    observed = read_rows(financial / 'custo_mao_obra_historico.csv')
    rates = sorted(Decimal(row['custo_hora']) for row in observed)
    require(rates, 'No observed labor rates for scenario basis.')
    middle = len(rates) // 2
    median = (rates[middle] if len(rates) % 2 else
              (rates[middle - 1] + rates[middle]) / 2).quantize(CENT, rounding=ROUND_HALF_UP)
    observed_ids = {row['operador_id'] for row in observed}
    first_operation = {}
    with (industrial / 'registros_operacao.csv').open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            key = row['operador_id']
            day = row['hora_inicio'][:10]
            first_operation[key] = min(first_operation.get(key, day), day)
    return [{'operador_id': key, 'custo_hora_estimado_brl': money(median),
             'data_vigencia': first_operation[key], 'base_mediana_periodo_brl': money(median),
             'origem': 'mediana_simulada_de_tarifas_observadas_no_periodo'}
            for key in sorted(first_operation.keys() - observed_ids, key=int)]


def input_consumption(industrial: Path, financial: Path,
                      maintenance_orders: list[dict], generated_orders: list[dict]):
    hours = defaultdict(Decimal)
    energy = defaultdict(Decimal)
    with (industrial / 'registros_operacao.csv').open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            key = row['hora_inicio'][:7], row['maquina_id']
            seconds = Decimal(str((datetime.fromisoformat(row['hora_fim']) -
                                   datetime.fromisoformat(row['hora_inicio'])).total_seconds()))
            require(seconds > 0, 'Invalid operation duration for input scenario.')
            hours[key] += seconds / 3600
            energy[key] += Decimal(row['consumo_energia_kwh'])
    services = defaultdict(int)
    for row in [*maintenance_orders, *generated_orders]:
        services[row['data_abertura'][:7], row['maquina_id']] += 1
    machines = [row['maquina_id'] for row in read_rows(industrial / 'maquinas.csv')]
    factors = {'Agua': (Decimal('12'), 'l'),
               'Detergente Industrial': (Decimal('0.15'), 'l'),
               'Lubrificante': (Decimal('0.08'), 'l')}
    counter = 0
    for source in read_rows(financial / 'custos_operacionais_variaveis.csv'):
        month = source['data_leitura'][:7]
        label = source['insumo']
        for machine in machines:
            basis_hours = hours[month, machine]
            if label == 'Energia':
                quantity = energy[month, machine]
                unit, factor, rule = 'kWh', '', 'kwh_reportado_nas_operacoes;unidade_corrigida_na_fonte'
            elif label == 'Manutencao Tecnologica':
                quantity = Decimal(services[month, machine])
                unit, factor, rule = 'servico', '', 'contagem_oms_do_mes;unidade_corrigida_na_fonte'
            else:
                match = next((value for name, value in factors.items()
                              if label.startswith(name)), None)
                require(match is not None and basis_hours > 0,
                        f'No supported input scenario basis for {label}/{month}/{machine}')
                factor, unit = match
                quantity = basis_hours * factor
                rule = 'fator_sintetico_por_hora_reportada_de_operacao'
            quantity = quantity.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
            counter += 1
            yield {'consumo_id': counter, 'custo_operacional_id': source['custo_operacional_id'],
                   'mes_ano': month, 'maquina_id': machine, 'insumo': label,
                   'unidade_fonte': source['unidade_medida'], 'unidade_simulada': unit,
                   'horas_base_operacoes': str(basis_hours),
                   'fator_quantidade_por_hora': str(factor),
                   'quantidade_simulada': str(quantity),
                   'valor_unitario_origem_brl': source['valor_unitario'],
                   'custo_total_simulado_brl': money(quantity * Decimal(source['valor_unitario'])),
                   'origem': rule}


def machine_events(industrial: Path, generated_stops: list[dict]):
    event_id = 0
    with (industrial / 'registros_operacao.csv').open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            start = datetime.fromisoformat(row['hora_inicio'])
            finish = datetime.fromisoformat(row['hora_fim'])
            setup_end = start + timedelta(seconds=float(Decimal(row['tempo_setup_real_min']) * 60))
            require(start <= setup_end <= finish and
                    shift_id(start) == shift_id(finish - timedelta(microseconds=1)),
                    f'Operation crosses shift or has invalid setup: {row["registro_id"]}')
            common = {'maquina_id': row['maquina_id'], 'turno_id': shift_id(start),
                      'registro_operacao_id': row['registro_id'], 'parada_id': '',
                      'origem': 'evento_derivado_operacao_original'}
            if setup_end > start:
                event_id += 1
                yield {'evento_id': event_id, **common,
                       'inicio': start.isoformat(sep=' '),
                       'fim': setup_end.isoformat(sep=' '), 'estado': 'SETUP',
                       'unidades_reportadas': 0, 'unidades_boas_simuladas': 0}
            quantity = int(row['quantidade_produzida_real'])
            good = int((Decimal(quantity) * Decimal('.98')).quantize(Decimal(1), rounding=ROUND_HALF_UP))
            event_id += 1
            yield {'evento_id': event_id, **common,
                   'inicio': setup_end.isoformat(sep=' '),
                   'fim': finish.isoformat(sep=' '), 'estado': 'PRODUCAO',
                   'unidades_reportadas': quantity, 'unidades_boas_simuladas': good}
    for row in [*read_rows(industrial / 'paradas_maquinas.csv'), *generated_stops]:
        start = datetime.fromisoformat(row['hora_inicio_parada'])
        finish = datetime.fromisoformat(row['hora_fim_parada'])
        require(finish > start, f'Invalid downtime interval: {row["parada_id"]}')
        while start < finish:
            end = min(finish, next_shift_boundary(start))
            event_id += 1
            yield {'evento_id': event_id, 'maquina_id': row['maquina_id'],
                   'turno_id': shift_id(start), 'inicio': start.isoformat(sep=' '),
                   'fim': end.isoformat(sep=' '), 'estado': 'PARADA',
                   'registro_operacao_id': '', 'parada_id': row['parada_id'],
                   'unidades_reportadas': 0, 'unidades_boas_simuladas': 0,
                           'origem': ('evento_derivado_parada_simulada' if row.get('origem')
                                      else 'evento_derivado_parada_original')}
            start = end


EVENT_FIELDS = ['evento_id', 'maquina_id', 'turno_id', 'inicio', 'fim', 'estado',
                'registro_operacao_id', 'parada_id', 'unidades_reportadas',
                'unidades_boas_simuladas', 'origem']

STATE_SUMMARY_FIELDS = [
    'resumo_id', 'maquina_id', 'data_turno', 'turno_id',
    'segundos_producao', 'segundos_setup', 'segundos_parada',
    'segundos_sem_evento', 'segundos_sobreposicao_fonte',
    'unidades_reportadas', 'unidades_boas_simuladas', 'origem']


def state_summary(events_path: Path):
    """Sweep event intervals so each machine/shift second receives one state."""
    groups = defaultdict(list)
    quantities = defaultdict(lambda: [0, 0])
    with events_path.open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            start = datetime.fromisoformat(row['inicio'])
            end = datetime.fromisoformat(row['fim'])
            shift = int(row['turno_id'])
            shift_day = (start.date() - timedelta(days=1)
                         if shift == 3 and start.hour < 6 else start.date())
            key = (row['maquina_id'], shift_day, shift)
            groups[key].append((start, end, row['estado']))
            quantities[key][0] += int(row['unidades_reportadas'])
            quantities[key][1] += int(row['unidades_boas_simuladas'])
    for index, key in enumerate(sorted(groups, key=lambda x: (x[1], x[2], int(x[0]))), 1):
        machine, day, shift = key
        begins = {1: 6, 2: 14, 3: 22}
        shift_start = datetime.combine(day, time(begins[shift]))
        shift_end = shift_start + timedelta(hours=8)
        points = [(shift_start, '', 0), (shift_end, '', 0)]
        for start, end, state in groups[key]:
            require(shift_start <= start < end <= shift_end,
                    f'Event outside shift: {machine}/{day}/{shift}')
            points.extend(((start, state, 1), (end, state, -1)))
        points.sort(key=lambda item: item[0])
        active = {'PRODUCAO': 0, 'SETUP': 0, 'PARADA': 0}
        durations = {'PRODUCAO': Decimal(0), 'SETUP': Decimal(0),
                     'PARADA': Decimal(0), 'SEM_EVENTO': Decimal(0)}
        overlap = Decimal(0)
        previous = shift_start
        for instant, state, delta in points:
            seconds = Decimal(str((instant - previous).total_seconds()))
            require(seconds >= 0, 'Unsorted machine-state event.')
            chosen = next((name for name in ('PARADA', 'SETUP', 'PRODUCAO')
                           if active[name] > 0), 'SEM_EVENTO')
            durations[chosen] += seconds
            if sum(active.values()) > 1:
                overlap += seconds
            if state:
                active[state] += delta
                require(active[state] >= 0, 'Unbalanced machine-state event.')
            previous = instant
        require(sum(durations.values()) == 28800 and all(v == 0 for v in active.values()),
                'Machine-state shift does not reconcile.')
        yield {
            'resumo_id': index, 'maquina_id': machine, 'data_turno': day.isoformat(),
            'turno_id': shift,
            'segundos_producao': str(durations['PRODUCAO']),
            'segundos_setup': str(durations['SETUP']),
            'segundos_parada': str(durations['PARADA']),
            'segundos_sem_evento': str(durations['SEM_EVENTO']),
            'segundos_sobreposicao_fonte': str(overlap),
            'unidades_reportadas': quantities[key][0],
            'unidades_boas_simuladas': quantities[key][1],
            'origem': 'prioridade_parada_setup_producao_sobre_eventos_derivados'}


OEE_FIELDS = [
    'oee_id', 'resumo_estado_id', 'maquina_id', 'data_turno', 'turno_id',
    'meta_id', 'meta_produtividade_un_h', 'segundos_programados',
    'segundos_producao_exclusivos', 'unidades_reportadas',
    'unidades_boas_simuladas', 'segundos_conflito_fonte',
    'disponibilidade_simulada', 'performance_bruta_simulada',
    'performance_limitada_simulada', 'qualidade_simulada',
    'oee_simulado', 'performance_acima_meta', 'meta_fora_vigencia', 'origem']


def simulated_oee(folder: Path, state_path: Path):
    targets = defaultdict(list)
    for row in read_rows(folder / 'metas_producao_maquina.csv'):
        targets[row['maquina_id']].append(row)
    for index, state in enumerate(read_rows(state_path), 1):
        day = state['data_turno']
        matches = [row for row in targets[state['maquina_id']]
                   if row['data_vigencia_inicio'] <= day <= row['data_vigencia_fim']]
        require(len(matches) <= 1 and targets[state['maquina_id']],
                f'Ambiguous or absent OEE scenario target for {state["maquina_id"]}/{day}')
        outside_validity = not matches
        target = (matches[0] if matches else
                  min(targets[state['maquina_id']],
                      key=lambda row: (min(abs((date.fromisoformat(day) -
                                                 date.fromisoformat(bound)).days)
                                           for bound in (row['data_vigencia_inicio'],
                                                         row['data_vigencia_fim'])),
                                       int(row['meta_id']))))
        ideal = Decimal(target['meta_produtividade_un_h'])
        running = Decimal(state['segundos_producao'])
        units = Decimal(state['unidades_reportadas'])
        good = Decimal(state['unidades_boas_simuladas'])
        require(ideal > 0 and 0 <= good <= units, 'Invalid OEE scenario inputs.')
        availability = running / Decimal(28800)
        performance_raw = units / (ideal * running / 3600) if running > 0 else Decimal(0)
        performance = min(performance_raw, Decimal(1))
        quality = good / units if units > 0 else Decimal(0)
        oee = availability * performance * quality
        fmt = lambda value: str(value.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
        yield {
            'oee_id': index, 'resumo_estado_id': state['resumo_id'],
            'maquina_id': state['maquina_id'], 'data_turno': day,
            'turno_id': state['turno_id'], 'meta_id': target['meta_id'],
            'meta_produtividade_un_h': target['meta_produtividade_un_h'],
            'segundos_programados': '28800', 'segundos_producao_exclusivos': str(running),
            'unidades_reportadas': state['unidades_reportadas'],
            'unidades_boas_simuladas': state['unidades_boas_simuladas'],
            'segundos_conflito_fonte': state['segundos_sobreposicao_fonte'],
            'disponibilidade_simulada': fmt(availability),
            'performance_bruta_simulada': fmt(performance_raw),
            'performance_limitada_simulada': fmt(performance),
            'qualidade_simulada': fmt(quality), 'oee_simulado': fmt(oee),
            'performance_acima_meta': str(performance_raw > 1).lower(),
            'meta_fora_vigencia': str(outside_validity).lower(),
            'origem': 'cenario_oee_meta_maquina_tempo_exclusivo_qualidade_98pct'}


def esg_goals_and_results(folder: Path) -> tuple[list[dict], list[dict]]:
    resources = read_rows(folder / 'consumo_recursos_esg.csv')
    emissions = {row['mes_ano']: row for row in read_rows(folder / 'emissoes_co2.csv')}
    projects = read_rows(folder / 'projetos_investimento_verde.csv')
    require(resources and {row['mes_ano'] for row in resources} == set(emissions),
            'ESG monthly coverage differs.')
    first = resources[0]
    first_water = Decimal(first['agua_por_unidade_m3'])
    first_waste = Decimal(first['residuos_gerados_kg']) / Decimal(first['unidades_produzidas'])
    first_renewable = Decimal(first['perc_energia_renovavel'])
    first_recycling = Decimal(first['taxa_reciclagem_perc'])
    targets = {
        'agua_por_unidade_m3': (first_water * Decimal('.9')).quantize(Decimal('.001')),
        'residuos_por_unidade_kg': (first_waste * Decimal('.9')).quantize(Decimal('.001')),
        'perc_energia_renovavel': min(Decimal(100), first_renewable + Decimal(5)),
        'taxa_reciclagem_perc': min(Decimal(100), first_recycling + Decimal(5)),
    }
    goals = []
    results = []
    for resource in resources:
        month = resource['mes_ano']
        month_start = date.fromisoformat(month + '-01')
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        emission = emissions[month]
        monthly_goals = {**targets,
                         'emissoes_totais_kg_co2': Decimal(emission['meta_emissao_kg_co2'])}
        for metric, target in monthly_goals.items():
            goals.append({'meta_id': len(goals) + 1, 'mes_ano': month,
                          'vigencia_inicio': month_start.isoformat(),
                          'vigencia_fim': month_end.isoformat(),
                          'indicador': metric, 'valor_meta': str(target),
                          'origem': 'csv_emissoes' if metric == 'emissoes_totais_kg_co2'
                          else 'meta_sintetica_base_primeiro_mes'})
        category_rules = {
            'Energia Renovável': ('energia_renovavel_atribuida_kwh',
                                  Decimal(resource['consumo_energia_renovavel_kwh']) * Decimal('.25')),
            'Recursos Hídricos': ('agua_economizada_simulada_m3',
                                   Decimal(resource['consumo_agua_m3']) * Decimal('.10')),
            'Eficiência Energética': ('energia_economizada_simulada_kwh',
                                       Decimal(resource['consumo_energia_total_kwh']) * Decimal('.04')),
            'Gestão de Resíduos': ('residuos_reciclados_atribuidos_kg',
                                    Decimal(resource['residuos_reciclados_kg']) * Decimal('.25')),
        }
        for project in projects:
            if month < project['data_aprovacao'][:7]:
                continue
            require(project['categoria'] in category_rules,
                    f'Unknown ESG category: {project["categoria"]}')
            metric, value = category_rules[project['categoria']]
            results.append({'resultado_id': len(results) + 1, 'mes_ano': month,
                            'projeto_id': project['projeto_id'], 'indicador': metric,
                            'valor_atribuido_simulado': str(value.quantize(Decimal('.001'))),
                            'origem': 'atribuicao_sintetica_nao_causal'})
    return goals, results


GOAL_FIELDS = ['meta_id', 'mes_ano', 'vigencia_inicio', 'vigencia_fim',
               'indicador', 'valor_meta', 'origem']
RESULT_FIELDS = ['resultado_id', 'mes_ano', 'projeto_id', 'indicador',
                 'valor_atribuido_simulado', 'origem']


def manifest() -> list[dict]:
    paths = sorted(ORIGINAL.glob('*/*.csv'))
    paths += sorted(BASE.glob('periodo_*/*.csv'))
    paths += sorted(BASE.glob('gerados/periodo_*/*.csv'))
    paths.append(BASE / 'composicao_tarifaria_inferida.csv')
    output = []
    for path in paths:
        with path.open(encoding='utf-8-sig', newline='') as handle:
            rows = sum(1 for _ in csv.DictReader(handle))
        category = ('original_corrigido' if ORIGINAL in path.parents and
                    path.name in {'materiais_custo_historico.csv',
                                  'custos_operacionais_variaveis.csv'} else
                    'original_preservado' if ORIGINAL in path.parents else
                    'referencia_derivada' if path.name in {
                        'clientes_referenciados.csv', 'operadores_referenciados.csv',
                        'inspetores_referenciados.csv'} else
                    'sintetico_derivado' if 'gerados' in path.parts or
                    path.name == 'composicao_tarifaria_inferida.csv' else 'complementar')
        output.append({'classe': category, 'caminho': path.relative_to(ROOT).as_posix(),
                       'linhas': rows, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return output


def main() -> None:
    report = {'periods': {}, 'database_writes': False}
    for period, (folder_name, original_name) in enumerate(PERIODS):
        folder = BASE / folder_name
        industrial = ORIGINAL / original_name
        output = BASE / 'gerados' / folder_name
        existing_links = maintenance_links(folder, industrial)
        new_orders, new_stops, new_links = synthetic_incidents(period, folder,
                                                                existing_links)
        datasets = {
            'consumo_energia_intervalo.csv': (ENERGY_FIELDS, energy_intervals(period, folder)),
            'vinculos_manutencao_simulados.csv': (MAINTENANCE_FIELDS,
                                                  [*existing_links, *new_links]),
            'ordens_manutencao_geradas.csv': (GENERATED_ORDER_FIELDS, new_orders),
            'paradas_maquinas_geradas.csv': (GENERATED_STOP_FIELDS, new_stops),
            'custos_produto_mensais_simulados.csv': (PRODUCT_FIELDS,
                                                     product_costs(folder, industrial)),
            'eventos_maquina_turno.csv': (EVENT_FIELDS,
                                         machine_events(industrial, new_stops)),
        }
        goals, results = esg_goals_and_results(folder)
        datasets['metas_esg_simuladas.csv'] = (GOAL_FIELDS, goals)
        datasets['resultados_projeto_esg_simulados.csv'] = (RESULT_FIELDS, results)
        datasets.update(referenced_people(period, industrial, ORIGINAL / FINANCE[period]))
        datasets.update(financial_allocations(industrial, ORIGINAL / FINANCE[period]))
        datasets['custo_hora_operador_estimado.csv'] = (
            LABOR_RATE_FIELDS, missing_labor_rates(industrial, ORIGINAL / FINANCE[period]))
        datasets['consumo_insumos_operacionais_simulado.csv'] = (
            INPUT_CONSUMPTION_FIELDS,
            input_consumption(industrial, ORIGINAL / FINANCE[period],
                              read_rows(folder / 'ordens_manutencao.csv'), new_orders))
        report['periods'][folder_name] = {
            name: write_rows(output / name, fields, rows)
            for name, (fields, rows) in datasets.items()
        }
        report['periods'][folder_name]['resumo_estado_maquina_turno_simulado.csv'] = write_rows(
            output / 'resumo_estado_maquina_turno_simulado.csv', STATE_SUMMARY_FIELDS,
            state_summary(output / 'eventos_maquina_turno.csv'))
        report['periods'][folder_name]['oee_maquina_turno_simulado.csv'] = write_rows(
            output / 'oee_maquina_turno_simulado.csv', OEE_FIELDS,
            simulated_oee(folder, output / 'resumo_estado_maquina_turno_simulado.csv'))
    entries = manifest()
    report['canonical_files'] = len(entries)
    (BASE / 'manifesto_canonico.json').write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (BASE / 'validacao_geracao.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
