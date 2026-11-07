"""Trusted deployment profiles, separate from scenario and research permissions."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def profiles():
    from .. import openai_provider, groq, serving_catalog, config
    caps = dict(json_schema='prompt_validated', streaming=True, temperature=True,
                reasoning_effort=False, seed=False, omit_output_limit=True)
    entries = [dict(id='openai', provider_id='openai', adapter_id='openai_responses',
                    endpoint=openai_provider.ENDPOINT, requested_model=openai_provider.MODEL,
                    key_env='OPENAI_API_KEY', capabilities={**caps, 'temperature': False,
                    'reasoning_effort': True}),
               dict(id='groq', provider_id='groq', adapter_id='groq_chat',
                    endpoint=groq.ENDPOINT, requested_model=groq.harness_configuration()['model'],
                    key_env='GROQ_API_KEY', capabilities=caps)]
    for alias in serving_catalog.MODELS:
        entries.append(dict(id=alias, provider_id='compatible', adapter_id='chat_completions',
            endpoint=(config.vllm_url() + '/v1/chat/completions') if config.vllm_url() else '',
            requested_model=alias, key_env='INFERENCE_VLLM_TOKEN', capabilities=caps,
            require_serving_identity=True))
    # Private backend file; never accepted in an HTTP submission.
    path = os.getenv('INFERENCE_MODEL_PROFILES')
    if path:
        entries.extend(json.loads(Path(path).read_text(encoding='utf-8')))
    result = {}
    for entry in entries:
        p = deepcopy(entry)
        if p['id'] in result or p['adapter_id'] not in {'openai_responses', 'groq_chat', 'chat_completions'}:
            raise ValueError('invalid_model_profile_registry')
        u = urlsplit(p['endpoint'])
        if p['endpoint'] and (u.username or u.password or u.query or u.fragment or
            (u.scheme != 'https' and not (u.scheme == 'http' and u.hostname in {'127.0.0.1', 'localhost'}))):
            raise ValueError('invalid_model_endpoint')
        p.setdefault('version', 1)
        p.setdefault('deployment_id', p['id'])
        p.setdefault('capability_source', 'server_configuration_2026-11-06')
        p.setdefault('require_serving_identity', False)
        p['sha256'] = digest(p)
        p['configured'] = bool(p['endpoint'] and p['requested_model'] and
                               (not p.get('key_env') or os.getenv(p['key_env'])))
        p['availability'] = 'unknown' if p['configured'] else 'unavailable'
        p['capability_compatible'] = True
        p['reason'] = 'Disponibilidade remota não verificada' if p['configured'] else 'Configuração ausente no servidor'
        result[p['id']] = p
    return result


def resolve(profile_id):
    if not isinstance(profile_id, str) or profile_id not in profiles():
        raise ValueError('unknown_model_profile')
    return deepcopy(profiles()[profile_id])


def public_profiles():
    return {key: {k: v for k, v in p.items() if k not in {'key_env', 'endpoint'}}
            for key, p in profiles().items()}


def preflight(profile, generation):
    if not profile['configured']:
        raise ValueError('model_profile_unconfigured')
    if set(generation) - {'temperature', 'output_token_limit', 'reasoning_effort', 'seed'}:
        raise ValueError('unsupported_generation_parameter')
    c = profile['capabilities']
    for key in ('temperature', 'reasoning_effort', 'seed'):
        if key in generation and not c[key]:
            raise ValueError('unsupported_parameter:' + key)
    value = generation.get('output_token_limit')
    if value is None and not c['omit_output_limit']:
        raise ValueError('output_limit_required')
    if value is not None and (type(value) is not int or not 1 <= value <= 8192):
        raise ValueError('invalid_output_limit')
    if 'temperature' in generation and (type(generation['temperature']) not in (int, float) or
                                        not 0 <= generation['temperature'] <= 2):
        raise ValueError('invalid_temperature')
    if 'reasoning_effort' in generation and generation['reasoning_effort'] not in {'low', 'medium', 'high'}:
        raise ValueError('invalid_reasoning_effort')
    if 'seed' in generation and type(generation['seed']) is not int:
        raise ValueError('invalid_seed')
    if c['json_schema'] not in {'native_strict', 'json_object', 'prompt_validated'} or not c['streaming']:
        raise ValueError('unsupported_protocol_capability')


def authorize(profile, scenario, data_sha256, limits):
    """No implicit inheritance of SPEC-013 approvals or environment gates."""
    path = os.getenv('INFERENCE_SPEC014_AUTHORIZATION')
    if not path:
        raise ValueError('transmission_authorization_required')
    receipt = json.loads(Path(path).read_text(encoding='utf-8'))
    if (receipt.get('decision') != 'approved' or receipt.get('spec_id') != 'SPEC-014' or
        receipt.get('profile_sha256') != profile['sha256'] or
        receipt.get('destination') != profile['endpoint'] or receipt.get('scenario') != scenario or
        receipt.get('data_sha256') != data_sha256 or receipt.get('limits') != limits):
        raise ValueError('transmission_authorization_mismatch')
    return digest(receipt)
