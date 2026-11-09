"""A has no data executor, including fingerprint reads."""
from copy import deepcopy
from ...model_service.registry import digest
from .repairs import require
from ..context.packet_index import build

def sources(packet):
    require(digest(packet['body']) == packet['sha256'], 'packet_hash_mismatch')
    index=build(packet)
    return {entry['item_id']: {**deepcopy(entry), 'id': entry['item_id'],
        'domain': entry['specialist_role'], 'description': entry['query'], 'evidence': deepcopy(item)}
        for entry,item in zip(index,packet['body']['evidence_items'])}
