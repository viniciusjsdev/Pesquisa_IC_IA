from .base import BaseAgent, refs
class AnswerWriter(BaseAgent):
    role_id = 'redator_resposta'
    def validate_semantics(self, output, view): refs(output, view)
