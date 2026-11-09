"""Prepare an isolated serializable state and invoke the compiled graph."""
from copy import deepcopy
from dataclasses import asdict
from importlib.metadata import version
import hashlib
from pathlib import Path
from langgraph.errors import GraphRecursionError
from langsmith import tracing_context
from ...model_service.registry import digest
from ...model_service.request_budget import POLICY
from ...observability.service import create
from ..contracts.loader import contracts, input_schema, input_identity
from ..context.packet_index import build as packet_index, KNOWN_DOMAINS
from ..policies import fixed_evidence, tool_access
from ..policies.repairs import require
from ..policies.budgets import recursion_limit
from .state import RunContext
from .builder import build

VERSION = 'scenarios_v1'

def execute(question, scenario, profile_id, model_call, *, maps, packet, query, limits,
            cancelled, run_id, observer=None,managed=False):
    require(scenario in {'fixed_evidence','data_access'}, 'invalid_scenario')
    fixed = scenario == 'fixed_evidence'
    require((fixed and packet is not None and query is None and maps is None and limits.query_attempts == 0)
        or (not fixed and packet is None and callable(query) and maps), 'scenario_policy_mismatch')
    roles = contracts(scenario)
    for role, contract in roles.items(): contract['input_schema'] = input_schema(role, scenario)
    maps = deepcopy(maps) if maps else {}
    sources = fixed_evidence.sources(packet) if fixed else tool_access.sources(maps)
    s = {'run_id': run_id, 'question': question, 'scenario': scenario, 'profile_id': profile_id,
        'fixed': fixed, 'limits': asdict(limits), 'roles': roles, 'contract_sha': digest(roles),
        'maps': maps, 'packet': deepcopy(packet), 'sources': sources,
        'domains': sorted({v['domain'] for v in sources.values()}),
        'source_index': [{k: v[k] for k in ('id','domain','grain','description') if k in v} for v in sources.values()],
        'evidence': [], 'trace': [], 'findings': [], 'calls': 0, 'attempts': 0, 'queries': 0,
        'round_no': 1, 'gap': None, 'candidate': None, 'seen': [], 'response': None,
        'repair': 0, 'repair_feedback': None, 'correction': 0, 'status': 'contract_error', 'next': ''}
    if fixed:
        s.update(packet_index=packet_index(packet), domains=list(KNOWN_DOMAINS),
                 available_domains=sorted({d for source in sources.values() for d in source['semantic_domains']}),
                 examined_item_ids=[], closure_reason=None)
    observer = observer if observer is not None else create(run_id)
    from ..runtime_identity import identity
    profile = getattr(model_call, 'profile', {})
    generation = getattr(model_call, 'generation', None)
    observer.annotate({'scenario': scenario, 'profile_id': profile_id,
        **({'profile_sha256': profile['sha256']} if profile.get('sha256') else {}),
        **({'generation_sha256': digest(generation)} if generation is not None else {}),
        **({'ls_provider': profile['provider_id'], 'ls_model_name': profile['requested_model']}
           if profile.get('provider_id') and profile.get('requested_model') else {}),
        'contract_sha256': s['contract_sha'], 'runtime_sha256': digest(identity()),
        'map_sha256': {d: digest(m) for d,m in maps.items()} if not fixed else {'packet':packet['sha256']}})
    context = RunContext(model_call, query, cancelled or (lambda: False), observer)
    graph = build(context)
    # Disable automatic framework spans even if a global LANGSMITH_TRACING flag is set.
    with tracing_context(enabled=False):
        try: s = graph.invoke(s, config={'recursion_limit': recursion_limit(limits), 'callbacks': []})
        except GraphRecursionError:
            s = context.last_state or s
            s.update(status='contract_error', gap={'error': 'internal_graph_recursion_limit'})
    result = {'run_id': run_id, 'status': s['status'], 'question': question, 'scenario': scenario,
        'protocol': 'fixed_evidence_v2' if fixed else VERSION, 'contract_sha256': s['contract_sha'], 'input_contract_sha256': digest(input_identity(scenario)),
        'engine_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'dependency_policy': 'explicit_context_v1', 'request_budget_policy': POLICY,
        'map_sha256': {d: digest(m) for d,m in maps.items()} if not fixed else {'packet': packet['sha256']},
        'candidate': s['candidate'], 'model_calls': s['calls'], 'queries': s['queries'], 'query_attempts': s['attempts'],
        'limits': asdict(limits), 'trace': s['trace'], 'evidence': s['evidence'], 'response': s['response'],
        'final_state': s['gap'], 'scientific_status': 'not_scored',
        'framework': {'name': 'langgraph', 'version': version('langgraph'), 'langsmith_version': version('langsmith'),
            'nodes': sorted(graph.get_graph().nodes), 'checkpoint': False, 'automatic_retries': False}}
    if fixed:
        result.update(scenario_contract_version=2,packet_projection_version=2,
                      packet_index_sha256=digest(s['packet_index']),packet_sha256=packet['sha256'],
                      examined_item_ids=s['examined_item_ids'],closure_reason=s['closure_reason'])
    result['observability'] = observer.snapshot() if managed else observer.finish(result)
    return result
