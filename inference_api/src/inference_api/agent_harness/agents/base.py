"""Common agent contract. Implementations never route or execute SQL."""
from copy import deepcopy
from typing import Protocol
from ..policies.repairs import require

class Agent(Protocol):
    role_id: str
    def build_input(self, view, policy) -> dict: ...
    def output_contract(self, policy) -> dict: ...
    def validate_semantics(self, output, view) -> None: ...

class BaseAgent:
    def build_input(self, view, policy): return deepcopy(view.inputs)
    def output_contract(self, policy): return deepcopy(policy[self.role_id])
    def validate_semantics(self, output, view): pass

def refs(output, view, key='evidencias_utilizadas'):
    require(set(output[key]) <= set(view.evidence_ids), 'unknown_evidence_reference')

class Specialist(BaseAgent):
    role_id = 'especialista_consulta'
    def validate_semantics(self, output, view): refs(output, view, 'evidence_refs')
