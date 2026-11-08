"""Local shared inference application.

Old attribute imports resolve to the relocated module object for compatibility.
"""
from importlib import import_module

_MODULES = {'server': 'api.server', 'auth': 'identity.auth', 'budget': 'executions.budget', 'criteria': 'executions.criteria', 'jobs': 'executions.jobs', 'limits': 'executions.limits', 'service': 'executions.service', 'dw_tools': 'data_access.dw_tools', 'serving_catalog': 'data_access.serving_catalog', 'synthetic_data': 'data_access.synthetic_data', 'evidence_packets': 'evidence.evidence_packets', 'storage': 'persistence.storage', 'models': 'model_service.models', 'groq': 'model_service.groq', 'openai_provider': 'model_service.openai_provider', 'request_budget': 'model_service.request_budget'}

def __getattr__(name):
    if name in _MODULES:
        module = import_module("." + _MODULES[name], __name__)
        globals()[name] = module
        return module
    raise AttributeError(name)
