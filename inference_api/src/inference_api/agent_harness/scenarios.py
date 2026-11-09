"""Compatible scenario facade. All production orchestration runs through StateGraph."""
from uuid import uuid4
from .contracts.loader import contracts, input_schema, INPUT_SCHEMA, INPUT_FIELDS
from .policies.budgets import ScenarioLimits
from .policies.repairs import ProtocolError, require, validation_location
from .graph.execution import execute, VERSION

def run(question, scenario, profile_id, model_call, *, maps=None, packet=None,
        query=None, limits=ScenarioLimits(), cancelled=None, observer=None,run_id=None,managed=False):
    return execute(question, scenario, profile_id, model_call, maps=maps, packet=packet,
        query=query, limits=limits, cancelled=cancelled, run_id=run_id or str(uuid4()), observer=observer,managed=managed)
