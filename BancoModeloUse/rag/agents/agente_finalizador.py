"""
Agente Finalizador - Consolidação e apresentação final
"""

from typing import Dict, Any, List
from datetime import datetime
from config.logger import get_logger
from rag.state import AgentState
from rag.guard_rails import as_turn, agent_exception
from rag.utils.agentes import build_context_for_agent

logger = get_logger(__name__)


class AgenteFinalizador:
    """Agente especializado em consolidação e apresentação final"""
    
    def __init__(self):
        self.name = "agente_finalizador"
    
    def consolidar_respostas(self, respostas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolida respostas de múltiplos agentes"""
        # Implementação simplificada
        return {
            "agente": "finalizador",
            "respostas_consolidadas": respostas,
            "resumo": "Análise consolidada concluída",
            "timestamp": datetime.now().isoformat()
        }

@agent_exception("agente_finalizador", "Erro na finalização")
@as_turn()
def agente_finalizador(state: AgentState) -> Dict[str, Any]:
    """
    Agente finalizador que consolida todas as análises
    
    Args:
        state: Estado atual do agente
        
    Returns:
        Dict com resposta final consolidada
    """
    logger.info("Executando agente finalizador")
    
    # Obter tarefa do agente
    task = state.get("tasks", {}).get("agente_finalizador", "")
    if not task:
        return {"error": "Tarefa não fornecida para agente finalizador"}
    
    try:
        # Obter contexto de todas as respostas
        context = build_context_for_agent(state)
        
        # Obter pergunta original
        question = state.get("question", "")
        
        # Consolidar resposta final
        final_answer = f"""
# Análise Consolidada

**Pergunta:** {question}

## Respostas dos Agentes Especializados

{context}

## Conclusão

Análise consolidada baseada nas respostas dos agentes especializados acima.
        """.strip()
        
        return {
            "answer": final_answer,
            "data": {
                "tipo": "finalizacao",
                "pergunta_original": question,
                "contexto": context,
                "status": "concluida"
            }
        }
        
    except Exception as e:
        logger.error(f"Erro no agente finalizador: {str(e)}")
        return {"error": f"Erro na finalização: {str(e)}"}
