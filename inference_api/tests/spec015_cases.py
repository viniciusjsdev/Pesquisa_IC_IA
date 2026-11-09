"""Deterministic synthetic cases shared by baseline capture and differential tests."""
from dataclasses import replace
from unittest.mock import patch
from uuid import UUID
from spec014_fixture import profile, packet, Transport, MAPS, fixture_query, QUESTION
from inference_api.model_service import ModelService

CASES = ('success', 'json_repair', 'no_source', 'no_progress', 'review_gap',
         'forbidden_source', 'forbidden_action', 'budget', 'cancelled', 'timeout',
         'query_repair', 'query_terminal', 'invalid_refs')


def execute(module, scenario, adapter, case):
    fixed = scenario == 'fixed_evidence'
    count = {}
    def mutate(e, v):
        role = e['role']; count[role] = count.get(role, 0) + 1
        if case == 'json_repair' and role == 'analista_pergunta' and count[role] == 1:
            return 'not-json'
        if case == 'no_source' and role == 'selecionador_fontes':
            v.update(decisao='sem_fonte', fonte_id=None, map_refs=[])
        if case in ('no_progress', 'review_gap') and role == 'revisor_evidencias':
            v.update(decisao='precisa_aprofundar', lacuna='gap', proximo_dado_necessario='data',
                     dominio_sugerido='industrial' if fixed and case == 'review_gap' else 'dw')
        if case == 'forbidden_source' and role == 'selecionador_fontes': v['fonte_id'] = 'external'
        if case == 'forbidden_action' and role == 'especialista_consulta':
            v['action'] = 'query_source' if fixed else 'analyze_packet'
        if case == 'invalid_refs' and role == 'redator_resposta': v['evidencias_utilizadas'] = ['invented']
        return v
    transport = Transport(mutate, fail=TimeoutError() if case == 'timeout' else None)
    plans = []
    def query(plan):
        plans.append(plan)
        if case == 'query_repair' and len(plans) == 1: raise ValueError('filters_outside_catalog')
        if case == 'query_terminal': raise ValueError('source_not_enabled')
        return fixture_query(plan)
    limits = module.ScenarioLimits(query_attempts=0 if fixed else 3)
    if case == 'budget': limits = replace(limits, model_calls=3)
    p = profile(adapter)
    # Same UUID produces identical HTTP bytes; time fields alone are normalized later.
    with patch.object(module, 'uuid4', return_value=UUID('00000000-0000-4000-8000-000000000015')):
        result = module.run(QUESTION, scenario, p['id'], ModelService(p, {}, transport=transport),
            packet=packet() if fixed else None, maps=None if fixed else MAPS,
            query=None if fixed else query, limits=limits, cancelled=lambda: case == 'cancelled')
    return {'result': result, 'requests': [r.data.decode() for r in transport.requests], 'plans': plans}


def normalize(value):
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()
                if k not in ('latency_ms', 'engine_sha256', 'framework', 'observability')}
    if isinstance(value, list): return [normalize(v) for v in value]
    return value
