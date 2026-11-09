"""Real StateGraph, compiled per run without store, checkpoint or retry policy."""
from langgraph.graph import StateGraph, START, END
from .state import RunState
from . import nodes
from .routing import route

def build(context):
    graph = StateGraph(RunState)
    def record(node):
        def step(state):
            result = node(state)
            context.last_state = result
            return result
        return step
    roles = {'analyst': ('analista_pergunta','dw'), 'selector': ('selecionador_fontes','dw'),
        'consolidated_specialist': ('especialista_consulta','dw'),
        'industrial_specialist': ('especialista_consulta','industrial'),
        'financial_specialist': ('especialista_consulta','financeiro'),
        'reviewer': ('revisor_evidencias','dw'), 'writer': ('redator_resposta','dw')}
    for name, (role, domain) in roles.items(): graph.add_node(name, record(nodes.agent_node(role, context, domain)))
    for name in ('round_gate', 'project_context', 'execute_tool'):
        fn = getattr(nodes, name)
        graph.add_node(name, record(lambda s, fn=fn: fn(s, context)))
    graph.add_edge(START, 'analyst')
    specialists = ['consolidated_specialist', 'industrial_specialist', 'financial_specialist']
    allowed = {'analyst': ['analyst', 'round_gate', 'finish'],
        'selector': ['selector', 'project_context', 'writer', 'finish'],
        'reviewer': ['reviewer', 'round_gate', 'writer', 'finish'],
        'writer': ['writer', 'finish'], 'round_gate': ['selector', 'writer', 'finish'],
        'project_context': [*specialists, 'writer', 'finish'],
        'execute_tool': [*specialists, 'reviewer', 'writer', 'finish'],
        **{name: [name, 'execute_tool', 'reviewer', 'writer', 'finish'] for name in specialists}}
    for name, destinations in allowed.items():
        targets = {n: END if n == 'finish' else n for n in destinations}
        graph.add_conditional_edges(name, lambda s, name=name: route(s, name), targets)
    return graph.compile(checkpointer=None, store=None)
