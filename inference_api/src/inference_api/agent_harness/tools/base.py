"""Tools accept typed plans; data services alone own database access."""
from typing import Protocol
from ..policies.repairs import require

class Tool(Protocol):
    tool_id: str
    input_schema: dict
    output_schema: dict
    def execute(self, request, context) -> dict: ...

class QueryTool:
    input_schema = {'type': 'object', 'required': ['fonte_id', 'campos', 'grao', 'limite', 'filtros']}
    output_schema = {'type': 'object', 'required': ['rows', 'coverage', 'units']}
    def execute(self, request, context):
        require(callable(context.query), 'scenario_policy_mismatch')
        return context.query(request)
