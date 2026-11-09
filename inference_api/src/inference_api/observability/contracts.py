"""Versioned event identity and allowlisted metadata."""
from uuid import uuid5, NAMESPACE_URL
VERSION = 'spec015.observability.v1'
METADATA = {'scenario', 'profile_id', 'ls_provider', 'ls_model_name', 'round', 'attempt',
    'contract_sha256', 'input_contract_sha256', 'runtime_sha256', 'map_sha256',
    'profile_sha256', 'generation_sha256',
    'status', 'validation', 'usage_metadata', 'input_tokens', 'output_tokens', 'total_tokens',
    'output_token_details', 'reasoning', 'model_calls', 'queries', 'query_attempts',
    'local_run_id', 'local_event_id', 'harness_run_id', 'app_run_id', 'job_id', 'instrumentation_version', 'content_mode'}
def sdk_id(run_id, event_id): return str(uuid5(NAMESPACE_URL, f'Pesquisa_IC_IA/{run_id}/{event_id}'))

def usage_metadata(usage):
    usage = usage or {}
    result = {target: usage[source] for source, target in
        [('input', 'input_tokens'), ('output', 'output_tokens'), ('total', 'total_tokens')]
        if type(usage.get(source)) is int and usage[source] >= 0}
    if type(usage.get('reasoning')) is int and usage['reasoning'] >= 0:
        result['output_token_details'] = {'reasoning': usage['reasoning']}
    return result
