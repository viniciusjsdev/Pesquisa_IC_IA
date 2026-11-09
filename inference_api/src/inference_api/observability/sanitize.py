"""Project onto known event fields, sanitize copies before crossing the queue."""
import hashlib
import json
import math
import os
import re
from .contracts import METADATA

DENY = re.compile(r'authorization|header|cookie|password|passwd|senha|secret|api.?key|credential|dsn|jwt|gabarito|ground.?truth|answer.?key|gold|environment|environ|client|(?:^|_)(?:access_token|refresh_token|id_token|token)$', re.I)
TOKEN = re.compile(r'(?i)(bearer\s+\S+|(?:postgres(?:ql)?|https?)://[^\s/@]+:[^\s/@]+@[^\s]+|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|\b(?:sk-|lsv2_|ls__)[A-Za-z0-9_-]+|(?:password|senha|api[_ -]?key|token|secret)\s*[:=]\s*[^\s,;]+)')
CREDENTIAL_ASSIGNMENT = re.compile(r'''(?i)["']?(?:password|passwd|senha|api[_ -]?key|access_token|refresh_token|id_token|token|secret)["']?\s*[:=]\s*["']?[^"'\s,;}]+''')

def clean(value, secrets=(), depth=0):
    if depth > 40: return '[omitted: depth]'
    if value is None or type(value) in (bool, int): return value
    if type(value) is float: return value if math.isfinite(value) else None
    if type(value) is str:
        value = TOKEN.sub('[REDACTED]', CREDENTIAL_ASSIGNMENT.sub('[REDACTED]', value))
        for secret in secrets:
            if len(secret) >= 4: value = value.replace(secret, '[REDACTED]')
        # Envelopes are JSON inside message strings; scrub nested forbidden keys too.
        if value.lstrip().startswith(('{', '[')):
            try: return json.dumps(clean(json.loads(value), secrets, depth+1), ensure_ascii=False)
            except (ValueError, RecursionError): return '[omitted: malformed structured content]'
        return value
    if type(value) is dict:
        return {k: '[REDACTED]' if DENY.search(k) else clean(v, secrets, depth+1)
                for k, v in value.items() if type(k) is str and type(v) in (dict, list, tuple, str, int, float, bool, type(None))}
    if type(value) in (list, tuple):
        return [clean(v, secrets, depth+1) for v in value
                if type(v) in (dict, list, tuple, str, int, float, bool, type(None))]
    return None

def project(event, mode, secrets=()):
    allowed = {'id', 'trace_id', 'parent_run_id', 'name', 'run_type', 'start_time', 'end_time',
               'dotted_order', 'error', 'status'}
    result = clean({k: v for k, v in event.items() if k in allowed}, secrets)
    metadata = {k: v for k, v in event.get('metadata', {}).items() if k in METADATA}
    if mode == 'metadata': metadata.pop('validation', None)
    result['metadata'] = clean(metadata, secrets)
    if mode == 'metadata' and result.get('error') and not re.fullmatch(r'[a-z_]+(?::[a-z_]+)?', result['error']):
        result['error'] = 'error_detail_omitted'
    for key in ('inputs', 'outputs'):
        content = clean(event.get(key) or {}, secrets)
        result[key] = content if mode == 'redacted' else {}
        result['metadata'][key+'_sha256'] = hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if len(json.dumps(result, ensure_ascii=False).encode()) > 65536:
        result['inputs'], result['outputs'] = {}, {}
        result['metadata'] = {k: v for k, v in result['metadata'].items()
                              if k not in {'validation'} and len(json.dumps(v)) < 2048}
        result['metadata'].update(content_omitted=True, omission_reason='event_byte_limit')
        if len(json.dumps(result, ensure_ascii=False).encode()) > 65536:
            result = {k: v for k, v in result.items() if k in
                      {'id','trace_id','parent_run_id','run_type','start_time','end_time','dotted_order','status'}}
            result.update(name='event_content_omitted', inputs={}, outputs={},
                          metadata={'content_omitted': True, 'omission_reason': 'event_byte_limit'})
    return result

def configured_secrets():
    return tuple(v for k, v in os.environ.items() if DENY.search(k) and len(v) >= 4)
