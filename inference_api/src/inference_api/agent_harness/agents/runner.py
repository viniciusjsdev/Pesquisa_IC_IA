"""Exactly one invocation. Repairs are graph transitions, never an internal loop."""
from copy import deepcopy
from dataclasses import replace
import json
from jsonschema import Draft202012Validator, ValidationError
from ...model_service.registry import digest
from ...model_service.service import ModelError
from ..contracts.loader import envelope_schema, input_identity
from ..context.projections import project
from ..policies.budgets import remaining
from ..policies.repairs import ProtocolError, require, validation_location, TERMINAL

def invoke(s, context, agent):
    role, repair, fixed = agent.role_id, s.get('repair', 0), s['fixed']
    require(not context.cancelled(), 'cancelled')
    require(s['calls'] < s['limits']['model_calls']-(0 if role == 'redator_resposta' else 1),
            'model_call_budget_exhausted')
    view = project(s, role)
    if repair:
        view = replace(view, inputs={**deepcopy(s['call_input']), 'feedback': s['repair_feedback']})
    else:
        s['call_input'] = deepcopy(view.inputs)
    s = {**s, 'calls': s['calls']+1}
    inputs = agent.build_input(view, s['scenario'])
    envelope = {'contract_version': 2 if fixed else 1, 'run_id': s['run_id'], 'call_id': f"call_{s['calls']:02}",
        'role': role, 'scenario': s['scenario'], 'round': s['round_no'], 'model_profile_id': s['profile_id'],
        'question': s['question'], 'allowed_actions': ['analyze_packet' if fixed else 'query_source'],
        'remaining_budget': remaining(s), 'request_byte_limit': s['limits']['input_bytes'],
        'timeout_seconds': s['limits']['timeout_seconds'], 'input': deepcopy(inputs),
        'source_event_ids': [e['event_id'] for e in s['trace'] if e.get('status') == 'validated']}
    contract = agent.output_contract(s['roles'])
    Draft202012Validator(envelope_schema(s['scenario'])).validate(envelope)
    Draft202012Validator(contract['input_schema']).validate(inputs)
    event = {'event_id': envelope['call_id'], 'role': role, 'round': s['round_no'],
        'input': envelope, 'status': 'started', 'attempt': repair+1,
        'contract_sha256': s['contract_sha'], 'input_contract_sha256': digest(input_identity(s['scenario']))}
    span = context.observer.start(envelope['call_id'], role, 'chain', inputs=envelope,
                                  metadata={'round': s['round_no'], 'attempt': repair+1})
    try:
        with context.observer.activate(span):
            raw, receipt = context.model_call(role, envelope, contract)
        event['model'] = receipt
        ident = (receipt.get('provider'), receipt.get('model_id'), receipt.get('profile_sha256'))
        require(all(ident), 'missing_model_identity')
        require(s['candidate'] is None or tuple(s['candidate']) == ident, 'model_identity_changed')
        s['candidate'] = ident
        require(len(raw.encode()) <= s['limits']['output_bytes'], 'model_output_limit')
        event['raw_output'] = raw
        def unique(pairs):
            obj = {}
            for k, v in pairs:
                if k in obj: raise ValueError('duplicate_key')
                obj[k] = v
            return obj
        output = json.loads(raw, object_pairs_hook=unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json')))
        if isinstance(output, dict) and role == 'especialista_consulta' and 'action' in output:
            require(output.get('action') == ('analyze_packet' if fixed else 'query_source'), 'action_forbidden')
        if isinstance(output, dict) and role == 'selecionador_fontes':
            selected = output.get('fonte_id')
            if isinstance(selected, str): require(selected in view.source_ids, 'source_forbidden')
            refs_out = output.get('map_refs')
            if isinstance(refs_out, list):
                require(all(ref in view.source_ids for ref in refs_out if isinstance(ref, str)), 'source_forbidden')
        if isinstance(output, dict) and role == 'especialista_consulta' and not fixed:
            plan = output.get('plano')
            if isinstance(plan, dict) and isinstance(plan.get('fonte_id'), str):
                require(plan['fonte_id'] == inputs['source_contract']['id'], 'source_forbidden')
        Draft202012Validator(contract['schema']).validate(output)
        agent.validate_semantics(output, view)
        event.update(status='validated', output=output)
        s.update(repair=0, repair_feedback=None)
    except ModelError as exc:
        event.update(status='provider_error', error=exc.status, model=exc.metadata)
        s.update(status='contract_error', gap={'error': exc.status}, next='finish')
    except (ValueError, ValidationError) as exc:
        code = str(exc) if isinstance(exc, ProtocolError) else 'model_output_schema_error'
        version=2 if fixed else 1
        detail = {'schema_id': f"{role}.{s['scenario']}.v{version}", 'schema_version': version,
            'schema_sha256': digest(contract['schema']),
            'path': validation_location(exc) if isinstance(exc, ValidationError) else '',
            'keyword': str(exc.validator) if isinstance(exc, ValidationError) else None,
            'attempt': repair+1, 'remaining_budget': remaining(s)}
        event.update(status='rejected', error=code, validation_feedback=detail)
        if repair or code in TERMINAL:
            s.update(status='contract_error', gap={'error': code}, next='finish')
        else:
            s.update(repair=repair+1, next='repair', repair_feedback={
                'error_code': code, 'event_id': event['event_id'],
                'rejected_output': event.get('raw_output'), **detail})
    finally:
        context.observer.end(span, outputs=event.get('output'), status=event['status'],
                             error=event.get('error'), metadata={'validation': event.get('validation_feedback')})
    s['trace'] = [*s['trace'], event]
    s['_output'] = event.get('output')
    return s
