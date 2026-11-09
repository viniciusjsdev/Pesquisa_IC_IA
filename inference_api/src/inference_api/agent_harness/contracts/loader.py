"""Effective baseline contracts, including formerly Python-generated schemas."""
from copy import deepcopy
import json
from pathlib import Path
BASE = Path(__file__).parent
INPUT = json.loads((BASE/'input.json').read_text(encoding='utf-8'))
INPUT_SCHEMA, INPUT_FIELDS = INPUT['envelope'], INPUT['fields']
def contracts(scenario):
    if scenario not in {'fixed_evidence', 'data_access'}: raise ValueError('invalid_scenario')
    return json.loads((BASE/(scenario+'.json')).read_text(encoding='utf-8'))
def input_schema(role, scenario):
    fields = dict(INPUT[scenario]['fields'][role])
    return {'type': 'object', 'required': list(fields), 'additionalProperties': False,
            'properties': {**{k: {'type': t} for k, t in fields.items()}, 'feedback': {'type': 'object'}}}

def envelope_schema(scenario):
    schema=deepcopy(INPUT_SCHEMA)
    if scenario=='fixed_evidence': schema['properties']['contract_version']={'const':2}
    return schema

def input_identity(scenario):
    return [envelope_schema(scenario),INPUT[scenario]['fields']] if scenario=='fixed_evidence' else [INPUT_SCHEMA,INPUT_FIELDS]
