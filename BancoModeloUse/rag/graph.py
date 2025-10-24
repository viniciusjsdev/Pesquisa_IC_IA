from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda

from config.logger import get_logger
from rag.enums import Agentes
from rag.state import AgentState
from rag.roteador import orquestrador, agent_handler

logger = get_logger(__name__)


def build_graph():
    """Constrói o grafo de estados com LangGraph"""
    logger.info("Construindo o grafo de estados...")
    graph = StateGraph(AgentState)

    # Ponto de entrada
    graph.set_entry_point(Agentes.ORQUESTRADOR)
    graph.add_node(Agentes.ORQUESTRADOR, RunnableLambda(orquestrador))

    # Adicionar nós para todos os agentes
    for agente in Agentes:
        if agente != Agentes.ORQUESTRADOR:
            graph.add_node(agente, RunnableLambda(lambda state, agent=agente: agent_handler(state, agent)))
            graph.add_edge(agente, Agentes.ORQUESTRADOR)

    # Edge final para validador
    graph.add_edge(Agentes.VALIDADOR_GLOBAL, END)

    # Edges condicionais do orquestrador
    graph.add_conditional_edges(
        Agentes.ORQUESTRADOR,
        lambda state: state["next"],
        {
            Agentes.PREPROCESSADOR: Agentes.PREPROCESSADOR,
            Agentes.VALIDADOR_GLOBAL: Agentes.VALIDADOR_GLOBAL,
            Agentes.FINANCEIRO: Agentes.FINANCEIRO,
            Agentes.INDUSTRIAL: Agentes.INDUSTRIAL,
            Agentes.INTEGRACAO: Agentes.INTEGRACAO,
            Agentes.FINALIZADOR: Agentes.FINALIZADOR,
            "END": END,
        }
    )

    compiled_graph = graph.compile()
    logger.info("Grafo de estados construído com sucesso.")
    return compiled_graph
