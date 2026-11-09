"""Backend-owned configuration; global SDK tracing flags never enable export."""
from dataclasses import dataclass, field
import os
from urllib.parse import urlsplit
import hashlib
import json

@dataclass(frozen=True)
class Config:
    enabled: bool = False
    content: str = 'metadata'
    endpoint: str = 'https://api.smith.langchain.com'
    project: str = ''
    api_key: str = field(default='', repr=False)
    diagnostic: str | None = None

def load(env=None):
    e = os.environ if env is None else env
    mode = e.get('INFERENCE_OBSERVABILITY', 'off')
    if mode == 'off': return Config()
    content = e.get('INFERENCE_OBSERVABILITY_CONTENT', 'metadata')
    endpoint = e.get('INFERENCE_OBSERVABILITY_ENDPOINT', 'https://api.smith.langchain.com').rstrip('/')
    project = e.get('INFERENCE_OBSERVABILITY_PROJECT', '').strip()
    key = e.get('LANGSMITH_API_KEY', '').strip()
    try: url = urlsplit(endpoint)
    except ValueError: return Config(diagnostic='invalid_observability_configuration')
    if (mode != 'langsmith' or content not in {'metadata', 'redacted'} or not project or not key
        or url.scheme != 'https' or not url.hostname or url.username or url.password
        or url.query or url.fragment or url.path not in ('', '/')):
        return Config(diagnostic='invalid_observability_configuration')
    return Config(True, content, endpoint, project, key)

def trusted_web_origin(endpoint):
    return {'https://api.smith.langchain.com': 'https://smith.langchain.com',
            'https://eu.api.smith.langchain.com': 'https://eu.smith.langchain.com'}.get(endpoint)

def destination(config):
    descriptor={'endpoint':config.endpoint,'project':config.project,'config_ref':'LANGSMITH_API_KEY'}
    ident=hashlib.sha256(json.dumps(descriptor,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return ident,descriptor

def for_read(destination_id,descriptor):
    # Collection off does not prohibit an explicitly requested read. The current
    # backend credential/destination must still match the frozen destination.
    config=load({**os.environ,'INFERENCE_OBSERVABILITY':'langsmith'})
    if not config.enabled or destination(config)!=(destination_id,descriptor):return None
    return config
