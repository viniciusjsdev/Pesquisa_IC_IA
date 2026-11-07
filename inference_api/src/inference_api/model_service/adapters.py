"""Protocol mapping only. Existing SSE parsers are shared with historical readers."""
from .. import models, openai_provider, serving_catalog


class AdapterError(ValueError):
    def __init__(self, status, metadata):
        super().__init__(status)
        self.status, self.metadata = status, metadata


def payload(profile, messages, schema, generation):
    responses = profile['adapter_id'] == 'openai_responses'
    body = {'model': profile['requested_model'], 'stream': True}
    body['input' if responses else 'messages'] = messages
    if responses:
        body['store'] = False
    else:
        body['stream_options'] = {'include_usage': True}
    for key in ('temperature', 'seed'):
        if key in generation:
            body[key] = generation[key]
    if 'reasoning_effort' in generation:
        if responses:
            body['reasoning'] = {'effort': generation['reasoning_effort']}
        else:
            body['reasoning_effort'] = generation['reasoning_effort']
    if generation.get('output_token_limit') is not None:
        body['max_output_tokens' if responses else 'max_tokens'] = generation['output_token_limit']
    mode = profile['capabilities']['json_schema']
    if mode != 'prompt_validated':
        fmt = {'type': 'json_object'} if mode == 'json_object' else {
            'type': 'json_schema', 'name': 'role_output', 'strict': True, 'schema': schema}
        if responses:
            body['text'] = {'format': fmt}
        else:
            body['response_format'] = ({'type': 'json_schema', 'json_schema':
                                       {k: v for k, v in fmt.items() if k != 'type'}}
                                      if mode == 'native_strict' else fmt)
    return body


def read(profile, response):
    if response.headers.get('Content-Type', '').split(';')[0].strip() != 'text/event-stream':
        raise ValueError('response_not_stream')
    provenance = {}
    if profile.get('require_serving_identity'):
        identity = serving_catalog.response_identity(response)
        if identity is None:
            raise ValueError('serving_identity_missing')
        provenance = serving_catalog.provenance(profile['requested_model'], identity,
                         profile['endpoint'].removesuffix('/v1/chat/completions'))
    if profile['adapter_id'] == 'openai_responses':
        result = openai_provider._read_stream(response)
        known = {'served_model': result.get('model'), 'response_id': result.get('id'),
                 'raw_usage': result.get('usage'), 'finish_reason': result.get('status')}
        if result.get('status') != 'completed':
            raise AdapterError('response_incomplete', known)
        parts = [part for item in result.get('output', []) if item.get('type') == 'message'
                 for part in item.get('content', [])]
        if any(part.get('type') == 'refusal' for part in parts):
            raise AdapterError('provider_refusal', {'finish_reason': 'completed',
                'raw_usage': result.get('usage'), 'model_id': result.get('model'),
                'response_id': result.get('id')})
        if any(item.get('type') == 'function_call' for item in result.get('output', [])):
            raise AdapterError('unexpected_native_tool_call', known)
        content = ''.join(part['text'] for part in parts if part.get('type') == 'output_text')
        finish = 'completed'
    else:
        result, _ = models._read_chat_stream(response, profile['endpoint'], profile['requested_model'], provenance)
        choice = result['choices'][0]
        finish = choice['finish_reason']
        content = choice['message']['content']
        if choice['message'].get('refusal'):
            raise AdapterError('provider_refusal', {'finish_reason': finish,
                'raw_usage': result.get('usage'), 'model_id': result.get('model')})
        if finish != 'stop':
            raise AdapterError('output_truncated' if finish == 'length' else 'provider_refusal',
                {'finish_reason': finish, 'raw_usage': result.get('usage'), 'model_id': result.get('model')})
    if result.get('model') != profile['requested_model']:
        raise AdapterError('provider_model_mismatch', {'served_model': result.get('model'),
            'raw_usage': result.get('usage'), 'response_id': result.get('id'), 'finish_reason': finish})
    return content, {'model_id': result['model'], 'finish_reason': finish,
                     'raw_usage': result.get('usage'), 'provenance': provenance,
                     'response_id': result.get('id')}
