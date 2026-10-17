"""Single fixed DW query implementation shared by CLI, exporter and Bancada."""
from datetime import date, datetime
from decimal import Decimal

def query(kind: str, year: int, identifier: int | None, *, connection=None,
          readonly_already: bool = False) -> dict:
    if type(year) is not int or not 2015 <= year <= 2026:
        raise ValueError('Year outside available study range.')
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
    if kind not in statements:
        raise ValueError(f'Unknown fixed query: {kind}')
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
    if kind == 'financial' and identifier is not None:
        raise ValueError('Financial query forbids id')
    if kind != 'financial' and (type(identifier) is not int or identifier <= 0):
        raise ValueError('Positive id required')
    if connection is None:
        from scripts import bootstrap_local as source
        conn = source.connect('industrial', 'db_pesquisa_dw')
        owns_connection = True
    else:
        conn = connection
        owns_connection = False
    try:
        with conn.cursor() as cur:
            if not readonly_already:
                cur.execute('SET TRANSACTION READ ONLY')
            cur.execute(statements[kind][0], params)
            rows = [dict(zip(statements[kind][1], row)) for row in cur.fetchall()]
    finally:
        if owns_connection:
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

