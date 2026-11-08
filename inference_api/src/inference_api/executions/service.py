"""SPEC-014 creation boundary; historical snapshots are read-only in storage."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
from pathlib import Path
from inference_api import criteria, evidence_packets, storage
from inference_api.identity.auth import Principal
from inference_api.agent_harness import scenarios, approved_catalog, catalog_runtime, local_queries, real_pilot
from inference_api.agent_harness.runtime_identity import identity as runtime_identity
from inference_api.model_service import registry, ModelService

def _options(payload: dict) -> tuple[float, int | None]:
    temperature = payload.get("temperature", 0)
    max_tokens = payload.get("max_tokens")
    if type(temperature) not in (float, int) or not 0 <= temperature <= 2:
        raise ValueError("Temperature must be between 0 and 2")
    if max_tokens is not None and (type(max_tokens) is not int or max_tokens < 1):
        raise ValueError("max_tokens must be a positive integer when provided")
    return temperature, max_tokens


def _prompt(payload: dict) -> dict:
    prompt_id = payload.get("prompt_revision_id")
    draft = payload.get("system_prompt")
    if (prompt_id is None) == (draft is None):
        raise ValueError("Provide exactly one prompt_revision_id or system_prompt")
    if prompt_id is not None:
        prompt = storage.get_prompt(prompt_id)
        if prompt is None:
            raise ValueError("Prompt revision not found")
        return {"schema_version": 1, "revision_id": prompt_id, "revision": prompt["revision"],
                "system_prompt": prompt["system_prompt"]}
    if not isinstance(draft, str) or not draft.strip() or len(draft) > 20000:
        raise ValueError("System prompt is required and limited to 20000 characters")
    return {"schema_version": 1, "revision_id": None, "revision": None, "system_prompt": draft}


def _criteria(payload: dict) -> dict:
    criteria_id = payload.get("criteria_revision_id")
    draft = payload.get("criteria")
    if criteria_id is not None and draft is not None:
        raise ValueError("Provide criteria_revision_id or criteria, not both")
    if criteria_id is not None:
        if not isinstance(criteria_id, str):
            raise ValueError("criteria_revision_id must be a UUID string")
        from uuid import UUID
        criteria_id = str(UUID(criteria_id))
        saved = storage.get_criteria(criteria_id)
        if saved is None:
            raise ValueError("Criteria revision not found")
        return {"schema_version": criteria.CRITERIA_VERSION, "revision_id": criteria_id,
                "revision": saved["revision"], "config": criteria.validate(saved["config"])}
    return {"schema_version": criteria.CRITERIA_VERSION, "revision_id": None,
            "revision": None,
            "config": criteria.validate(draft if draft is not None else criteria.DEFAULT)}



def _checks(evidence_items: list[dict], answer: str, config: dict,
            source: str = "DW") -> list[dict]:
    """Literal checks only. They never assert numerical truth or causality."""
    results = []
    def add(name, result, detail):
        results.append({"schema_version": 3, "check": name, "result": result, "detail": detail})
    observed = any(item.get("coverage", {}).get("state") == "observed" for item in evidence_items)
    if config["require_evidence"]:
        add("criteria_evidence_presence", "passed" if observed else "failed", f"At least one {source} observation delivered.")
    if config["require_period"]:
        add("criteria_period", "passed" if all(type(item.get("year")) is int for item in evidence_items) and evidence_items else "failed", f"{source} evidence contains an explicit year.")
    for unit in config["required_units"]:
        add("criteria_unit", "passed" if any(unit in item.get("units", {}).values() for item in evidence_items) else "failed", unit)
    if config["require_cited_ids"]:
        add("criteria_cited_ids", "not_checked", f"{source} results have no stable per-row citation IDs.")
    for phrase in config["required_caveats"]:
        add("criteria_caveat_literal", "passed" if phrase.casefold() in answer.casefold() else "failed", phrase)
    add("numerical_truth", "not_checked", "No independent gold set in exploratory execution.")
    add("causality", "not_checked", "Temporal association does not establish causality.")
    return results



def _validate_input(payload):
    if not isinstance(payload, dict):
        raise ValueError('run_object_required')
    if any(k in payload for k in ('evidence_mode', 'model_alias', 'provider')):
        raise ValueError('legacy_execution_mode_retired: select fixed_evidence or data_access')
    allowed = {'execution_contract_version', 'scenario', 'model_profile_id', 'question',
               'evidence_packet', 'catalog_version', 'generation', 'limits'}
    if set(payload) - allowed or payload.get('execution_contract_version') != 1:
        raise ValueError('invalid_execution_contract')
    scenario = payload.get('scenario')
    if scenario not in {'fixed_evidence', 'data_access'}:
        raise ValueError('invalid_scenario')
    if not isinstance(payload.get('question'), str) or not payload['question'].strip() or len(payload['question']) > 4000:
        raise ValueError('invalid_question')
    if scenario == 'fixed_evidence':
        packet = payload.get('evidence_packet')
        if not isinstance(packet, dict) or set(packet) != {'id', 'sha256'} or 'catalog_version' in payload:
            raise ValueError('fixed_evidence_packet_required')
    elif (payload.get('evidence_packet') is not None or
          type(payload.get('catalog_version')) is not int or payload['catalog_version'] < 1):
        raise ValueError('data_access_catalog_required')
    generation = payload.get('generation', {})
    if not isinstance(generation, dict):
        raise ValueError('invalid_generation')
    profile = registry.resolve(payload.get('model_profile_id'))
    registry.preflight(profile, generation)
    requested = payload.get('limits', {})
    defaults = asdict(scenarios.ScenarioLimits(query_attempts=0 if scenario == 'fixed_evidence' else 3))
    if not isinstance(requested, dict) or set(requested) - set(defaults):
        raise ValueError('invalid_limits')
    for key, value in requested.items():
        minimum = 0 if key == 'query_attempts' else 1
        if type(value) is not int or not minimum <= value <= defaults[key]:
            raise ValueError('limit_may_only_reduce:' + key)
    return profile, {**defaults, **requested}


def prepare(payload):
    profile, limits = _validate_input(payload)
    packet = catalog = maps = None
    if payload['scenario'] == 'fixed_evidence':
        ref = payload['evidence_packet']
        packet, raw = evidence_packets.select_packet(ref['id'], ref['sha256'])
        if packet['body']['question'] != payload['question']:
            raise ValueError('packet_question_mismatch')
        data_sha = packet['sha256']
        source = {'kind': 'immutable_packet', 'sha256': data_sha,
                  'file_sha256': hashlib.sha256(raw).hexdigest()}
    else:
        catalog = approved_catalog.load()
        if catalog['version'] != payload['catalog_version']:
            raise ValueError('catalog_version_mismatch')
        maps = catalog_runtime.compile_maps(catalog)
        data_sha = registry.digest(catalog)
        source = {'kind': 'approved_local_catalog', 'catalog_sha256': data_sha,
                  'version': catalog['version'], 'data_contract_sha256': local_queries.DATA_CONTRACT_SHA256,
                  'dw_fingerprint': catalog['dw_source_fingerprint'],
                  'physical_inventory_sha256': catalog.get('physical_inventory_sha256')}
    authorization = registry.authorize(profile, payload['scenario'], data_sha, limits)
    return deepcopy({'profile': profile, 'limits': limits, 'packet': packet,
                     'catalog': catalog, 'maps': maps, 'source': source,
                     'authorization_sha256': authorization, 'request_sha256': registry.digest(payload)})


def require_provider_configuration(payload):
    prepare(payload)


def execute_run(payload, principal: Principal, *, prepared=None):
    context = prepared if prepared is not None else prepare(payload)
    if context['request_sha256'] != registry.digest(payload):
        raise ValueError('prepared_request_changed')
    profile = context['profile']
    source = deepcopy(context['source'])
    scenario = payload['scenario']
    query = None
    runtime_before = runtime_identity()
    if scenario == 'data_access':
        source['detail_loads'] = {'before': local_queries.source_fingerprints(context['catalog'])}
        query = lambda plan: local_queries.execute(plan, context['catalog'])
    result = scenarios.run(payload['question'], scenario, profile['id'],
        ModelService(profile, payload.get('generation', {})), maps=context['maps'],
        packet=context['packet'], query=query, limits=scenarios.ScenarioLimits(**context['limits']))
    if scenario == 'data_access':
        try:
            source['detail_loads']['after'] = local_queries.source_fingerprints(context['catalog'])
        except Exception as exc:
            source['detail_loads']['after'] = {'status': 'unavailable', 'error_type': type(exc).__name__}
            result['status'] = 'contract_error'
            result['final_state'] = {'error': 'source_fingerprint_after_failed'}
    snapshot = {'schema_version': 7, 'execution_contract_version': 1, 'scenario': scenario,
        'evidence_mode': scenario, 'provider': profile['provider_id'], 'status': result['status'],
        'scientific_status': 'not_scored', 'validation_purpose': 'engineering',
        'data_class': 'synthetic_fixture' if profile.get('fixture') else 'research_evidence',
        'data_destination': profile['deployment_id'],
        'authorization_sha256': context['authorization_sha256'],
        'question_request': {'question': payload['question'], 'model_alias': profile['id']},
        'packet': ({'case_id': context['packet']['body']['case_id'], 'sha256': context['packet']['sha256']}
                   if context['packet'] else None),
        'evidence_source': source,
        'runtime_contract': {'code': runtime_before, 'code_after': runtime_identity()},
        'model_profile': {k: v for k, v in profile.items() if k not in {'key_env', 'endpoint'}},
        'model': {'alias': profile['id'], 'provider': profile['provider_id'],
                  'model_id': profile['requested_model'], 'api_surface': profile['adapter_id'],
                  'parameters': payload.get('generation', {}), 'generation_confirmed': False},
        'prompt': {'version': scenarios.VERSION, 'system_prompt': 'Versioned role contracts',
                   'sha256': result['contract_sha256']},
        'verification_criteria': {'scientific_status': 'not_scored'},
        'harness_result': result, 'checks': [],
        'model_output': {'raw_text': result['response']['resposta']} if result['response'] else None,
        'error': {'stage': 'harness', 'type': result['status'], 'message': result['final_state']['error']}
                 if result['final_state'] and 'error' in result['final_state'] else None,
        'identity': {'principal_id': principal.id, 'author_verified': True}}
    try:
        return storage.create_run(principal.username, snapshot)
    except Exception as exc:
        real_pilot.preserve_failed_persistence(snapshot, exc)
        raise
