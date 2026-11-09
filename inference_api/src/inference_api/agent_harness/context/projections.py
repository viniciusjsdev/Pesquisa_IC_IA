"""Deterministic baseline projections; no state dump or LLM summarization."""
from copy import deepcopy
from .views import ContextView
from ..policies.budgets import remaining
from .packet_index import progress_index, KNOWN_DOMAINS

def project(s, role):
    question, evidence = s['question'], s['evidence']
    ids = [e['result_id'] for e in evidence]
    attempts = [e for e in s['trace'] if e['role'] == 'data_query']
    if role == 'analista_pergunta':
        inputs = {'question': question, 'domain_index': s['domains'], 'source_index': s['source_index']}
    elif role == 'selecionador_fontes':
        inputs = {'question': question, 'necessidade': s['analysis']['necessidade'],
            'source_index': s['source_index'], 'available_source_ids': sorted(s['sources']),
            'evidence_state': evidence, 'gap': s['gap'], 'attempts': attempts}
    elif role == 'especialista_consulta':
        inputs = s['specialist_input']
        if s['fixed']:ids=inputs['available_evidence_ids']
    elif role == 'revisor_evidencias':
        inputs = {'question': question, 'domains_identified': s['analysis']['dominios'],
            'necessidade': s['analysis']['necessidade'], 'query_result': evidence[-1],
            'evidence_state': evidence[:-1], 'findings': s['findings'],
            'available_evidence_ids': ids, 'attempts': attempts}
    elif role == 'redator_resposta':
        inputs = {'question': question, 'evidence_state': evidence, 'findings': s['findings'],
            'available_evidence_ids': ids, 'limits_and_errors': {'gap': s['gap'],
            'query_attempts_used': s['attempts'], 'remaining_budget': remaining(s)}}
    else: raise ValueError('unknown_role')
    if s['fixed']:
        index=progress_index(s['packet_index'],s['examined_item_ids'])
        remaining_ids=[entry['item_id'] for entry in index if entry['item_id'] not in s['examined_item_ids']]
        if role=='analista_pergunta':
            inputs.update(domain_index=list(KNOWN_DOMAINS), available_domains=s['available_domains'], source_index=index)
        elif role=='selecionador_fontes':
            inputs.update(source_index=index, examined_item_ids=s['examined_item_ids'], remaining_item_ids=remaining_ids)
        elif role=='revisor_evidencias':
            inputs.update(source_index=index, examined_item_ids=s['examined_item_ids'], remaining_item_ids=remaining_ids,
                          known_domains=list(KNOWN_DOMAINS), available_domains=s['available_domains'])
        elif role=='redator_resposta':
            inputs.update(review=s.get('review'), closure_reason=s.get('closure_reason'))
    if s.get('repair_feedback'):
        inputs = {**inputs, 'feedback': s['repair_feedback']}
    return ContextView(deepcopy(inputs), tuple(s['domains']), tuple(s['sources']), tuple(ids),
                       s['scenario'], tuple(KNOWN_DOMAINS) if s['fixed'] else tuple(s['domains']),
                       tuple(s.get('available_domains',s['domains'])))
