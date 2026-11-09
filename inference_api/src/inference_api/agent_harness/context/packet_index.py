"""Versioned, local-only semantic projection of immutable v1 packet items."""
from copy import deepcopy
import json
from pathlib import Path
from ..policies.repairs import require

VERSION = 2
KNOWN_DOMAINS = ('industrial', 'financeiro')
SEMANTICS = {'machine': (['industrial'], 'industrial'), 'quality': (['industrial'], 'industrial'),
             'financial': (['financeiro'], 'financeiro'),
             'product': (['industrial', 'financeiro'], 'dw'),
             'material': (['industrial', 'financeiro'], 'dw')}
FIELDS = json.loads((Path(__file__).resolve().parents[1]/'data_contracts.json').read_text(encoding='utf-8'))['fixed_output_fields']

def build(packet):
    body = packet['body']
    index=[]
    for position, item in enumerate(body['evidence_items'], 1):
        kind=item.get('query')
        require(isinstance(kind,str) and kind in SEMANTICS, 'invalid_packet_query')
        domains, specialist = SEMANTICS[kind]
        index.append({'item_id': f"packet:{body['case_id']}:{position}", 'query': kind,
            'semantic_domains': list(domains), 'specialist_role': specialist,
            'source_origin': {'database': body.get('source_snapshot',{}).get('database','dw'),
                              'sources': deepcopy(item.get('sources',[]))},
            'grain': item.get('grain','packet_item'), 'fields': deepcopy(FIELDS[kind]),
            'filters': deepcopy(item.get('filters',{})), 'year': item.get('year'),
            'coverage': deepcopy(item.get('coverage',{})), 'units': deepcopy(item.get('units',{}))})
    return index

def progress_index(index, examined):
    return [{**deepcopy(item), 'examination_state': 'item_examinado' if item['item_id'] in examined
             else 'item_disponivel'} for item in index]
