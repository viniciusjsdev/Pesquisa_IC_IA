"""Invented packet values for contract 3; never reads a research source."""
from copy import deepcopy
from inference_api.model_service.registry import digest

def packet(queries=('machine', 'financial'), empty=False):
    items=[]
    for n,kind in enumerate(queries):
        rows=[] if empty else ([{'observation_id':n+1,'observed_day':'2020-01-01',
            'reported_revenue':120,'reported_net_profit':12}] if kind=='financial' else
            [{'machine_id':7,'operation_rows':1,'reported_operation_quantity':42,
              'downtime_rows':0,'downtime_minutes':None}])
        items.append({'query':kind,'year':2020+n,'grain':kind+'/fixture-year',
            'rows':rows,'coverage':{'state':'observed' if rows else 'no_observation','rows':len(rows)},
            'sources':['dw.fixture_'+kind],'units':{},'filters':{'year':2020+n}})
        if kind=='financial':
            day=f'{2020+n}-01-01'
            if rows:rows[0]['observed_day']=day
            items[-1]['coverage'].update(observed_months=1 if rows else 0,first_day=day if rows else None,last_day=day if rows else None)
        if rows and kind=='product':
            rows[:]=[{'product_id':7,'operation_rows':1,'reported_operation_quantity':42,'sale_rows':1,'observed_sales_value':'120'}]
        if rows and kind=='material':
            rows[:]=[{'material_id':7,'consumption_rows':1,'quantity_consumed':'42','price_observation_rows':1,
                      'min_observed_unit_price':'2','max_observed_unit_price':'2'}]
        if rows and kind=='quality':
            rows[:]=[{'product_id':7,'inspection_rows':1,'approved_reported':42,'rejected_reported':0,'exceeds_lot_rows':0}]
    body={'case_id':'v3-invented','question':'Compare a produção e o lucro dos períodos inventados.',
          'domain':'integrado','source_snapshot':{'database':'db_pesquisa_dw'},'evidence_items':items}
    return {'body':body,'sha256':digest(body)}

def answer(envelope):
    role,i=envelope['role'],envelope['input']
    if role=='analista_pergunta':
        return {'tratavel':True,'necessidade':dict(entidade='fixture',medida='produção e lucro',periodo='2020/2021',grao='inventado'),
                'dominios':['industrial','financeiro'],'lacunas':[]}
    if role=='selecionador_fontes':
        sid=i['available_source_ids'][min(envelope['round']-1,len(i['available_source_ids'])-1)]
        return {'selection_kind':'packet_source','decisao':'analisar_item','justificativa':'Item inventado',
                'fonte_id':sid,'dominio_adicional':None,'map_refs':[sid]}
    if role=='especialista_consulta':
        return {'action':'analyze_packet','evidence_refs':i['available_evidence_ids'],
                'findings':['Resultado inventado.'],'gaps':[]}
    if role=='revisor_evidencias':
        more=envelope['round']==1
        return {'decisao':'precisa_aprofundar' if more else 'suficiente',
            'evidencias_utilizadas':i['available_evidence_ids'],'justificativa':'Fixture explícita',
            'lacuna':'Lucro' if more else None,'proximo_dado_necessario':'Item financeiro do pacote' if more else None,
            'dominio_sugerido':'financeiro' if more else None}
    return {'resposta':'Resposta inventada, sem score.','evidencias_utilizadas':i['available_evidence_ids'],
            'calculos':[],'ressalvas':['Sem inferência causal.']}
