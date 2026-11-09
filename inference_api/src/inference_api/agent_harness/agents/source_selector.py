from .base import BaseAgent
from ..policies.repairs import require

class SourceSelector(BaseAgent):
    role_id = 'selecionador_fontes'
    def validate_semantics(self, v, view):
        if view.scenario=='fixed_evidence':
            require(set(v['map_refs']) <= set(view.source_ids), 'source_forbidden')
            if v['decisao']=='analisar_item':
                require(v['fonte_id'] in view.source_ids, 'source_forbidden')
                require(set(v['map_refs'])=={v['fonte_id']}, 'missing_map_reference')
            else:
                require(v['fonte_id'] is None and v['map_refs']==[], 'invalid_no_source_decision')
            require(v['dominio_adicional'] is None,'invalid_additional_domain')
            return
        require(set(v['map_refs']) <= set(view.source_ids), 'source_forbidden')
        require(v['decisao'] != 'pedir_dominio', 'all_domains_already_available')
        if v['decisao'] == 'consultar':
            require(v['fonte_id'] in view.source_ids, 'source_forbidden')
            require(v['fonte_id'] in v['map_refs'], 'missing_map_reference')
        else: require(v['fonte_id'] is None, 'invalid_no_source_decision')
        require(v['dominio_adicional'] is None, 'invalid_additional_domain')
