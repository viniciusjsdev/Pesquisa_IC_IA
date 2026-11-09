from .base import BaseAgent
from ..policies.repairs import require

class QuestionAnalyst(BaseAgent):
    role_id = 'analista_pergunta'
    def validate_semantics(self, output, view):
        if view.scenario=='fixed_evidence':
            require(set(output['dominios']) <= set(view.known_domains), 'domain_outside_index')
            require(not output['tratavel'] or bool(set(output['dominios']) & set(view.available_domains)),
                    'analysis_domain_consistency')
            return
        require(set(output['dominios']) <= set(view.domains), 'domain_outside_index')
        require(output['tratavel'] == bool(output['dominios']), 'analysis_domain_consistency')
