"""One explicit transition per node. No hidden orchestration or retry loop."""
from copy import deepcopy
from ...model_service.registry import digest
from ..agents.registry import resolve as agent_for
from ..agents.runner import invoke
from ..tools.registry import resolve as tool_for
from ..policies.budgets import remaining
from ..policies.repairs import require, ProtocolError, REPAIRABLE_QUERY
import json

def guard(fn):
    def guarded(s, context):
        s = deepcopy(s)
        try: return fn(s, context)
        except ProtocolError as exc:
            return {**s, 'status': 'contract_error', 'gap': {'error': str(exc)}, 'next': 'finish'}
    return guarded

def agent_node(role, context, domain='dw'):
    @guard
    def node(s, _):
        s['next'] = ''
        if (s['fixed'] and role not in {'analista_pergunta','redator_resposta'}
                and s['calls'] >= s['limits']['model_calls']-1):
            return {**s,'next':'writer','gap':{'reason':'model_call_budget_exhausted'},
                    'closure_reason':'model_call_budget_exhausted',
                    'repair':0,'repair_feedback':None,'call_input':{}}
        s = invoke(s, context, agent_for(role, domain))
        output = s.pop('_output')
        if s['next'] in ('finish', 'repair'): return s
        if role == 'analista_pergunta':
            s.update(analysis=output, next='round_gate')
        elif role == 'selecionador_fontes':
            s['selection'] = output
            if output['decisao'] == 'sem_fonte':
                s.update(gap={'reason': output['justificativa']}, next='writer')
                if s['fixed']:s['closure_reason']='sem_fonte'
            else: s['next'] = 'project_context'
        elif role == 'especialista_consulta':
            if s['fixed']:
                item=deepcopy(s['specialist_input']['evidence'][0])
                if not any(e['result_id']==item['result_id'] for e in s['evidence']):s['evidence'].append(item)
                s['findings'].append(output); s['next'] = 'reviewer'
                if s['source']['id'] not in s['examined_item_ids']:s['examined_item_ids'].append(s['source']['id'])
            else: s.update(planned=output, next='execute_tool')
        elif role == 'revisor_evidencias':
            s.update(review=output, gap={'review': output})
            if s['fixed']:
                decision=output['decisao']
                if decision=='precisa_aprofundar' and output['dominio_sugerido'] and output['dominio_sugerido'] not in s['available_domains']:
                    s.update(next='writer',closure_reason='requested_domain_absent_from_packet',
                             gap={'review':output,'reason':'requested_domain_absent_from_packet','missing_domain':output['dominio_sugerido']})
                elif decision=='precisa_aprofundar':s.update(round_no=s['round_no']+1,next='round_gate')
                else:
                    closure=None if decision=='suficiente' and not output['lacuna'] else 'review_'+decision
                    if closure is None and any(e.get('coverage',{}).get('state')=='no_observation' for e in s['evidence']):
                        closure='no_observation'
                    s.update(next='writer',closure_reason=closure)
                return s
            if output['decisao'] != 'precisa_aprofundar': s['next'] = 'writer'
            else: s.update(round_no=s['round_no']+1, next='round_gate')
        else:
            s.update(response=output, next='finish', status='answered_unverified' if any(
                e.get('coverage', {}).get('state') == 'observed' for e in s['evidence']) else 'insufficient_evidence')
            if s['fixed'] and (s.get('review',{}).get('decisao')!='suficiente' or s.get('closure_reason')):
                s['status']='insufficient_evidence'
        return s
    return lambda s: node(s, context)

@guard
def round_gate(s, context):
    if not s['analysis']['tratavel'] or s['round_no'] > s['limits']['investigation_rounds']:
        s['next'] = 'writer'
        if s['fixed']:
            reason='analysis_unanswerable' if not s['analysis']['tratavel'] else 'investigation_round_budget_exhausted'
            s.update(closure_reason=reason,gap={'reason':reason,'domains_required':s['analysis']['dominios'],
                                              'available_domains':s['available_domains']})
    elif s['fixed'] and s['calls'] >= s['limits']['model_calls']-1:
        s.update(next='writer',closure_reason='model_call_budget_exhausted',gap={'reason':'model_call_budget_exhausted'})
    elif not s['fixed'] and s['attempts'] >= s['limits']['query_attempts']:
        s.update(gap={'reason': 'query_attempt_budget_exhausted'}, next='writer')
    else: s['next'] = 'selector'
    return s

@guard
def project_context(s, context):
    source = s['sources'][s['selection']['fonte_id']]
    progress = digest([source['id'], s['analysis']['necessidade'], [digest(e) for e in s['evidence']], s['gap']])
    if progress in s['seen']:
        return {**s, 'gap': {'reason': 'no_progress', 'source_id': source['id']}, 'next': 'writer',
                **({'closure_reason':'no_progress'} if s['fixed'] else {})}
    s['seen'].append(progress)
    projected = {**source, 'source_id': source['id']}
    s['trace'].append({'event_id': f"map_{s['round_no']}", 'role': 'map_projection', 'round': s['round_no'],
        'status': 'validated', 'output': {'selected_table_ids': [source['id']], 'detail_sha256': digest(projected)}})
    inputs = {'question': s['question'], 'necessidade': s['analysis']['necessidade'],
        'domain': source['domain'], 'source_contract': projected, 'gap': s['gap'],
        'evidence_state': s['evidence'], 'available_evidence_ids': [e['result_id'] for e in s['evidence']]}
    if s['fixed']:
        previous=deepcopy(s['evidence'])
        item = {**deepcopy(source['evidence']), 'result_id': source['id'], 'source_id': source['id']}
        inputs.update(evidence=[item], evidence_state=previous, source_contract={k:v for k,v in projected.items() if k!='evidence'},
                      semantic_domains=source['semantic_domains'],source_origin=source['source_origin'],
                      available_evidence_ids=list(dict.fromkeys([e['result_id'] for e in previous]+[item['result_id']])))
    s.update(source=source, specialist_input=deepcopy(inputs), correction=0,
             next={'dw': 'consolidated_specialist', 'industrial': 'industrial_specialist',
                   'financeiro': 'financial_specialist'}[source['domain']])
    return s

@guard
def execute_tool(s, context):
    require(not s['fixed'], 'scenario_policy_mismatch')
    plan, source = s['planned']['plano'], s['source']
    s['attempts'] += 1
    event = {'event_id': f"tool_{s['attempts']:02}", 'role': 'data_query', 'round': s['round_no'],
             'status': 'started', 'input': plan, 'query_attempt': s['attempts']}
    s['trace'].append(event)
    tool = tool_for(source)
    parent = next(e['event_id'] for e in reversed(s['trace'][:-1]) if e['role'] == 'especialista_consulta')
    span = context.observer.start(event['event_id'], tool.tool_id, 'tool', parent=parent, inputs=plan,
                                  metadata={'round': s['round_no'], 'attempt': s['attempts']})
    try:
        require(plan['fonte_id'] == source['id'], 'source_forbidden')
        require(set(plan['campos']) <= set(source['fields']) and plan['grao'] == source['grain'], 'plan_outside_selected_map')
        result = tool.execute(plan, context)
        require(isinstance(result, dict) and isinstance(result.get('rows'), list)
            and len(result['rows']) <= plan['limite'] and result.get('coverage', {}).get('rows') == len(result['rows'])
            and result['coverage'].get('state') == ('observed' if result['rows'] else 'no_observation')
            and isinstance(result.get('units'), dict)
            and len(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()) <= s['limits']['result_bytes'],
            'query_result_contract_error')
        s['queries'] += 1
        item = {'result_id': f"result_{s['queries']:02}", 'source_id': source['id'], 'grain': plan['grao'], 'plan': plan, **result}
        event.update(status='validated', output=item)
        s['evidence'].append(item); s['next'] = 'reviewer'
    except (ValueError, TypeError) as exc:
        code = str(exc); event.update(status='rejected', error=code)
        if code not in REPAIRABLE_QUERY: raise ProtocolError('query_blocked:'+code) from None
        s['gap'] = {'reason': code}
        s['specialist_input']['feedback'] = {'rejected_plan': plan, 'error_code': code,
            'event_id': event['event_id'], 'details': 'Corrija usando o contrato tipado da mesma fonte.',
            'remaining_budget': remaining(s)}
        s['correction'] += 1
        if s['correction'] >= 2: s['next'] = 'writer'
        elif s['attempts'] >= s['limits']['query_attempts']:
            s.update(gap={'reason': 'query_attempt_budget_exhausted'}, next='writer')
        else:
            s['next'] = {'dw': 'consolidated_specialist', 'industrial': 'industrial_specialist',
                         'financeiro': 'financial_specialist'}[source['domain']]
    except Exception:
        event.update(status='rejected', error='database_error')
        raise ProtocolError('database_error') from None
    finally:
        context.observer.end(span, outputs=event.get('output'), status=event['status'], error=event.get('error'))
    return s
