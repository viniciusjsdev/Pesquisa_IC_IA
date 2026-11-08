"""SPEC-014 v1: five shared roles with explicit acquisition policies.

Only B receives a query callable. A uses an immutable in-memory packet.
No provider, URL, credentials, database connection or gold lives in this engine.
"""
from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from uuid import uuid4
from jsonschema import Draft202012Validator
from .engine import CONTRACT, BLOCKED_QUERY_ERRORS, _bytes
from ..model_service.registry import digest
from ..model_service.service import ModelError
from inference_api.model_service.request_budget import POLICY


VERSION = 'scenarios_v1'
ENGINE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


@dataclass(frozen=True)
class ScenarioLimits:
    model_calls: int = 48
    query_attempts: int = 3
    investigation_rounds: int = 3
    input_bytes: int = 32768
    output_bytes: int = 32768
    result_bytes: int = 32768
    timeout_seconds: int = 600


def contracts(scenario):
    roles = deepcopy(CONTRACT['roles'])
    selector = roles['selecionador_fontes']['schema']
    selector['required'].append('selection_kind')
    selector['properties']['selection_kind'] = {'const': 'packet_source' if scenario == 'fixed_evidence' else 'query_source'}
    specialist = roles['especialista_consulta']
    if scenario == 'fixed_evidence':
        specialist['task'] = 'Analise integralmente a fonte selecionada do pacote. Não consulte dados. Declare achados e lacunas; cite somente IDs de available_evidence_ids.'
        specialist['schema'] = {'type': 'object', 'additionalProperties': False,
            'required': ['action', 'evidence_refs', 'findings', 'gaps'], 'properties': {
                'action': {'const': 'analyze_packet'},
                **{k: {'type': 'array', 'items': {'type': 'string'}} for k in ['evidence_refs', 'findings', 'gaps']}}}
        roles['selecionador_fontes']['task'] = 'Selecione uma fonte do pacote em available_source_ids. Use decisao=consultar para analisar o trecho; isto nunca executa consulta. Se nada puder responder, sem_fonte. dominio_adicional=null. map_refs contém o ID selecionado.'
    else:
        specialist['schema']['required'].append('action')
        specialist['schema']['properties']['action'] = {'const': 'query_source'}
    return roles


INPUT_SCHEMA = {'type': 'object', 'additionalProperties': False,
    'required': ['contract_version', 'run_id', 'call_id', 'role', 'scenario', 'round',
                 'model_profile_id', 'question', 'allowed_actions', 'remaining_budget',
                 'request_byte_limit', 'timeout_seconds', 'input', 'source_event_ids'],
    'properties': {
        'contract_version': {'const': 1},
        **{k: {'type': 'string'} for k in ['run_id', 'call_id', 'role', 'model_profile_id', 'question']},
        'scenario': {'enum': ['fixed_evidence', 'data_access']},
        **{k: {'type': 'integer', 'minimum': 1} for k in ['round', 'request_byte_limit', 'timeout_seconds']},
        'allowed_actions': {'type': 'array', 'items': {'enum': ['analyze_packet', 'query_source']}, 'minItems': 1, 'maxItems': 1},
        'remaining_budget': {'type': 'object'}, 'input': {'type': 'object'},
        'source_event_ids': {'type': 'array', 'items': {'type': 'string'}}}}

INPUT_FIELDS = {
    'analista_pergunta': {'question': 'string', 'domain_index': 'array', 'source_index': 'array'},
    'selecionador_fontes': {'question': 'string', 'necessidade': 'object', 'source_index': 'array',
        'available_source_ids': 'array', 'evidence_state': 'array', 'gap': ['object', 'null'], 'attempts': 'array'},
    'especialista_consulta': {'question': 'string', 'necessidade': 'object', 'domain': 'string',
        'source_contract': 'object', 'gap': ['object', 'null'], 'evidence_state': 'array', 'available_evidence_ids': 'array'},
    'revisor_evidencias': {'question': 'string', 'domains_identified': 'array', 'necessidade': 'object',
        'query_result': 'object', 'evidence_state': 'array', 'findings': 'array', 'available_evidence_ids': 'array', 'attempts': 'array'},
    'redator_resposta': {'question': 'string', 'evidence_state': 'array', 'findings': 'array',
        'available_evidence_ids': 'array', 'limits_and_errors': 'object'}}


def input_schema(role, scenario):
    fields = dict(INPUT_FIELDS[role])
    if role == 'especialista_consulta' and scenario == 'fixed_evidence':
        fields['evidence'] = 'array'
    return {'type': 'object', 'required': list(fields), 'additionalProperties': False,
            'properties': {**{k: {'type': t} for k, t in fields.items()}, 'feedback': {'type': 'object'}}}


def validation_location(error):
    """JSON pointer from schema-defined names, never untrusted instance keys."""
    path = list(error.absolute_schema_path)
    segments = []
    for index, segment in enumerate(path[:-1]):
        if segment == 'properties' and isinstance(path[index + 1], str):
            segments.append(path[index + 1])
        elif segment == 'items':
            segments.append('*')
    return ''.join('/' + part.replace('~', '~0').replace('/', '~1') for part in segments)


class ProtocolError(ValueError):
    pass


def require(value, error):
    if not value:
        raise ProtocolError(error)


def run(question, scenario, profile_id, model_call, *, maps=None, packet=None,
        query=None, limits=ScenarioLimits(), cancelled=None):
    require(scenario in {'fixed_evidence', 'data_access'}, 'invalid_scenario')
    fixed = scenario == 'fixed_evidence'
    require((fixed and packet is not None and query is None and maps is None and limits.query_attempts == 0)
            or (not fixed and packet is None and callable(query) and maps), 'scenario_policy_mismatch')
    roles = contracts(scenario)
    for role, contract in roles.items():
        contract['input_schema'] = input_schema(role, scenario)
    contract_sha = digest(roles)
    run_id = str(uuid4())
    maps = deepcopy(maps) if maps else {}
    sources = {}
    if fixed:
        require(digest(packet['body']) == packet['sha256'], 'packet_hash_mismatch')
        for i, item in enumerate(packet['body']['evidence_items']):
            sid = f"packet:{packet['body']['case_id']}:{i+1}"
            sources[sid] = {'id': sid, 'domain': 'dw', 'grain': item.get('grain', 'packet_item'),
                            'description': item.get('query', sid), 'evidence': deepcopy(item)}
    else:
        for domain, domain_map in maps.items():
            for sid, source in domain_map['sources'].items():
                sources[sid] = {**deepcopy(source), 'id': sid, 'domain': domain}
    domains = sorted({s['domain'] for s in sources.values()})
    source_index = [{k: s[k] for k in ('id', 'domain', 'grain', 'description') if k in s}
                    for s in sources.values()]
    evidence, trace, findings = [], [], []
    calls = attempts = queries = 0
    gap = None
    candidate = None
    seen = set()
    round_no = 1
    cancelled = cancelled or (lambda: False)

    def budget():
        return {'remaining_model_calls': limits.model_calls-calls,
                'remaining_queries': limits.query_attempts-attempts,
                'remaining_rounds': limits.investigation_rounds-round_no}

    def invoke(role, inputs, check=lambda _: None):
        nonlocal calls, candidate
        for repair in range(2):
            require(not cancelled(), 'cancelled')
            require(calls < limits.model_calls - (0 if role == 'redator_resposta' else 1), 'model_call_budget_exhausted')
            calls += 1
            envelope = {'contract_version': 1, 'run_id': run_id, 'call_id': f'call_{calls:02}',
                'role': role, 'scenario': scenario, 'round': round_no, 'model_profile_id': profile_id,
                'question': question, 'allowed_actions': ['analyze_packet' if fixed else 'query_source'],
                'remaining_budget': budget(), 'request_byte_limit': limits.input_bytes,
                'timeout_seconds': limits.timeout_seconds, 'input': deepcopy(inputs),
                'source_event_ids': [e['event_id'] for e in trace if e.get('status') == 'validated']}
            Draft202012Validator(INPUT_SCHEMA).validate(envelope)
            Draft202012Validator(roles[role]['input_schema']).validate(inputs)
            event = {'event_id': envelope['call_id'], 'role': role, 'round': round_no,
                     'input': envelope, 'status': 'started', 'attempt': repair+1,
                     'contract_sha256': contract_sha, 'input_contract_sha256': digest([INPUT_SCHEMA, INPUT_FIELDS])}
            trace.append(event)
            try:
                raw, receipt = model_call(role, envelope, roles[role])
                event['model'] = receipt
                ident = (receipt.get('provider'), receipt.get('model_id'), receipt.get('profile_sha256'))
                require(all(ident), 'missing_model_identity')
                require(candidate is None or candidate == ident, 'model_identity_changed')
                candidate = ident
                require(len(raw.encode()) <= limits.output_bytes, 'model_output_limit')
                event['raw_output'] = raw
                def unique(pairs):
                    obj = {}
                    for k, v in pairs:
                        if k in obj:
                            raise ValueError('duplicate_key')
                        obj[k] = v
                    return obj
                output = json.loads(raw, object_pairs_hook=unique,
                    parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json')))
                # Policy denial is terminal even when the rest of the JSON is malformed.
                if isinstance(output, dict) and role == 'especialista_consulta' and 'action' in output:
                    require(output.get('action') == ('analyze_packet' if fixed else 'query_source'), 'action_forbidden')
                if isinstance(output, dict) and role == 'selecionador_fontes':
                    selected = output.get('fonte_id')
                    if isinstance(selected, str):
                        require(selected in sources, 'source_forbidden')
                    refs_out = output.get('map_refs')
                    if isinstance(refs_out, list):
                        require(all(ref in sources for ref in refs_out if isinstance(ref, str)), 'source_forbidden')
                if isinstance(output, dict) and role == 'especialista_consulta' and not fixed:
                    plan = output.get('plano')
                    if isinstance(plan, dict) and isinstance(plan.get('fonte_id'), str):
                        require(plan['fonte_id'] == inputs['source_contract']['id'], 'source_forbidden')
                Draft202012Validator(roles[role]['schema']).validate(output)
                check(output)
                event.update(status='validated', output=output)
                return output
            except ModelError as exc:
                event.update(status='provider_error', error=exc.status, model=exc.metadata)
                raise ProtocolError(exc.status) from None
            except Exception as exc:
                from jsonschema import ValidationError
                if not isinstance(exc, (ValueError, ValidationError)):
                    raise
                code = str(exc) if isinstance(exc, ProtocolError) else 'model_output_schema_error'
                detail = {'schema_id': f'{role}.{scenario}.v1', 'schema_version': 1,
                          'schema_sha256': digest(roles[role]['schema']),
                          'path': validation_location(exc) if isinstance(exc, ValidationError) else '',
                          'keyword': str(exc.validator) if isinstance(exc, ValidationError) else None,
                          'attempt': repair + 1, 'remaining_budget': budget()}
                event.update(status='rejected', error=code, validation_feedback=detail)
                if repair or code in {'action_forbidden', 'source_forbidden', 'model_identity_changed',
                                      'missing_model_identity', 'model_output_limit'}:
                    raise ProtocolError(code) from None
                inputs = {**inputs, 'feedback': {'error_code': code, 'event_id': event['event_id'],
                    'rejected_output': event.get('raw_output'), **detail}}

    def refs(value, key='evidencias_utilizadas'):
        require(set(value[key]) <= {e['result_id'] for e in evidence}, 'unknown_evidence_reference')

    response = None
    try:
        def analysis_check(v):
            require(set(v['dominios']) <= set(domains), 'domain_outside_index')
            require(v['tratavel'] == bool(v['dominios']), 'analysis_domain_consistency')
        analysis = invoke('analista_pergunta', {'question': question, 'domain_index': domains,
                                               'source_index': source_index}, analysis_check)
        while analysis['tratavel'] and round_no <= limits.investigation_rounds:
            if not fixed and attempts >= limits.query_attempts:
                gap = {'reason': 'query_attempt_budget_exhausted'}
                break
            def selection_check(v):
                require(set(v['map_refs']) <= set(sources), 'source_forbidden')
                require(v['decisao'] != 'pedir_dominio', 'all_domains_already_available')
                if v['decisao'] == 'consultar':
                    require(v['fonte_id'] in sources, 'source_forbidden')
                    require(v['fonte_id'] in v['map_refs'], 'missing_map_reference')
                else:
                    require(v['fonte_id'] is None, 'invalid_no_source_decision')
                require(v['dominio_adicional'] is None, 'invalid_additional_domain')
            selection = invoke('selecionador_fontes', {'question': question,
                'necessidade': analysis['necessidade'], 'source_index': source_index,
                'available_source_ids': sorted(sources), 'evidence_state': evidence,
                'gap': gap, 'attempts': [e for e in trace if e['role'] == 'data_query']}, selection_check)
            if selection['decisao'] == 'sem_fonte':
                gap = {'reason': selection['justificativa']}
                break
            source = sources[selection['fonte_id']]
            progress = digest([source['id'], analysis['necessidade'], [digest(e) for e in evidence], gap])
            if progress in seen:
                gap = {'reason': 'no_progress', 'source_id': source['id']}
                break
            seen.add(progress)
            projected = {**source, 'source_id': source['id']}
            trace.append({'event_id': f'map_{round_no}', 'role': 'map_projection', 'round': round_no,
                          'status': 'validated', 'output': {'selected_table_ids': [source['id']],
                                                          'detail_sha256': digest(projected)}})
            inputs = {'question': question, 'necessidade': analysis['necessidade'],
                      'domain': source['domain'], 'source_contract': projected, 'gap': gap,
                      'evidence_state': evidence, 'available_evidence_ids': [e['result_id'] for e in evidence]}
            if fixed:
                item = {'result_id': source['id'], 'source_id': source['id'], **deepcopy(source['evidence'])}
                if not any(e['result_id'] == item['result_id'] for e in evidence):
                    evidence.append(item)
                inputs.update(evidence=[item], available_evidence_ids=[e['result_id'] for e in evidence])
                finding = invoke('especialista_consulta', inputs, lambda v: refs(v, 'evidence_refs'))
                findings.append(finding)
            else:
                for correction in range(2):
                    if attempts >= limits.query_attempts:
                        gap = {'reason': 'query_attempt_budget_exhausted'}
                        break
                    planned = invoke('especialista_consulta', inputs, lambda v: refs(v, 'evidence_refs'))
                    plan = planned['plano']
                    attempts += 1
                    event = {'event_id': f'tool_{attempts:02}', 'role': 'data_query', 'round': round_no,
                             'status': 'started', 'input': plan, 'query_attempt': attempts}
                    trace.append(event)
                    try:
                        require(plan['fonte_id'] == source['id'], 'source_forbidden')
                        require(set(plan['campos']) <= set(source['fields']) and plan['grao'] == source['grain'],
                                'plan_outside_selected_map')
                        result = query(plan)
                        require(isinstance(result, dict) and isinstance(result.get('rows'), list)
                            and len(result['rows']) <= plan['limite'] and
                            result.get('coverage', {}).get('rows') == len(result['rows']) and
                            result['coverage'].get('state') == ('observed' if result['rows'] else 'no_observation')
                            and isinstance(result.get('units'), dict) and len(_bytes(result)) <= limits.result_bytes,
                            'query_result_contract_error')
                        queries += 1
                        item = {'result_id': f'result_{queries:02}', 'source_id': source['id'],
                                'grain': plan['grao'], 'plan': plan, **result}
                        event.update(status='validated', output=item)
                        evidence.append(item)
                        break
                    except (ValueError, TypeError) as exc:
                        code = str(exc)
                        event.update(status='rejected', error=code)
                        repairable = {'plan_outside_selected_map', 'invalid_typed_plan',
                            'plan_source_or_grain_mismatch', 'fields_outside_catalog', 'row_limit_invalid',
                            'filters_outside_catalog', 'invalid_range_filter', 'invalid_id_filter',
                            'invalid_lineage_filter', 'invalid_synthetic_filters', 'unsupported_synthetic_filter',
                            'invalid_synthetic_date_filter'}
                        if code not in repairable:
                            raise ProtocolError('query_blocked:' + code) from None
                        gap = {'reason': code}
                        inputs['feedback'] = {'rejected_plan': plan, 'error_code': code,
                            'event_id': event['event_id'], 'details': 'Corrija usando o contrato tipado da mesma fonte.',
                            'remaining_budget': budget()}
                    except Exception:
                        event.update(status='rejected', error='database_error')
                        raise ProtocolError('database_error') from None
                if event['status'] != 'validated':
                    break
            def review_check(v):
                refs(v)
                if v['decisao'] == 'precisa_aprofundar':
                    require(v['dominio_sugerido'] in domains and v['lacuna'] and v['proximo_dado_necessario'], 'invalid_review_gap')
            review = invoke('revisor_evidencias', {'question': question,
                'domains_identified': analysis['dominios'], 'necessidade': analysis['necessidade'],
                'query_result': evidence[-1], 'evidence_state': evidence[:-1], 'findings': findings,
                'available_evidence_ids': [e['result_id'] for e in evidence],
                'attempts': [e for e in trace if e['role'] == 'data_query']}, review_check)
            gap = {'review': review}
            if review['decisao'] != 'precisa_aprofundar':
                break
            round_no += 1
        response = invoke('redator_resposta', {'question': question, 'evidence_state': evidence,
            'findings': findings, 'available_evidence_ids': [e['result_id'] for e in evidence],
            'limits_and_errors': {'gap': gap, 'query_attempts_used': attempts, 'remaining_budget': budget()}}, refs)
        status = 'answered_unverified' if any(e.get('coverage', {}).get('state') == 'observed' for e in evidence) else 'insufficient_evidence'
    except ProtocolError as exc:
        status, gap = 'contract_error', {'error': str(exc)}
    return {'run_id': run_id, 'status': status, 'question': question, 'scenario': scenario,
        'protocol': VERSION, 'contract_sha256': contract_sha, 'input_contract_sha256': digest([INPUT_SCHEMA, INPUT_FIELDS]),
        'engine_sha256': ENGINE_SHA256, 'dependency_policy': 'explicit_context_v1',
        'request_budget_policy': POLICY, 'map_sha256': {d: digest(m) for d, m in maps.items()} if not fixed else {'packet': packet['sha256']},
        'candidate': candidate, 'model_calls': calls, 'queries': queries, 'query_attempts': attempts,
        'limits': asdict(limits), 'trace': trace, 'evidence': evidence, 'response': response,
        'final_state': gap, 'scientific_status': 'not_scored'}
