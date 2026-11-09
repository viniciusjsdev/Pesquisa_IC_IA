from .base import BaseAgent, refs
from ..policies.repairs import require

class EvidenceReviewer(BaseAgent):
    role_id = 'revisor_evidencias'
    def validate_semantics(self, v, view):
        refs(v, view)
        if view.scenario=='fixed_evidence':
            require(v['dominio_sugerido'] is None or v['dominio_sugerido'] in view.known_domains, 'invalid_review_domain')
            if v['decisao'] in {'precisa_aprofundar','indisponivel','contraditoria'}:
                require(isinstance(v['lacuna'],str) and bool(v['lacuna'].strip()), 'invalid_review_gap')
            if v['decisao']=='precisa_aprofundar':
                require(isinstance(v['proximo_dado_necessario'],str) and bool(v['proximo_dado_necessario'].strip()),
                        'invalid_review_gap')
            return
        if v['decisao'] == 'precisa_aprofundar':
            require(v['dominio_sugerido'] in view.domains and v['lacuna'] and v['proximo_dado_necessario'],
                    'invalid_review_gap')
