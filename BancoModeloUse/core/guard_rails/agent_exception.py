import functools
from config.logger import get_logger
from rag.state import AgentState

logger = get_logger(__name__)


def agent_exception(agent_name: str, default_answer: str = ""):
    """
    Decorator para tratamento de exceções em agentes
    
    Args:
        agent_name: Nome do agente para logging
        default_answer: Resposta padrão em caso de erro
    """
    def deco(func):
        @functools.wraps(func)
        def wrapper(state: AgentState) -> AgentState:
            try:
                return func(state)
            except Exception as e:
                logger.exception(f"Falha no agente '{agent_name}'")
                return {
                    "answer": default_answer,
                    "error": str(e)
                }
        return wrapper
    return deco
