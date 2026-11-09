"""B receives only approved maps and an injected bounded query service."""
from copy import deepcopy
def sources(maps):
    return {sid: {**deepcopy(source), 'id': sid, 'domain': domain}
            for domain, domain_map in maps.items() for sid, source in domain_map['sources'].items()}
