"""
Utilitários para turnos de agentes
"""

from typing import Optional, Dict, Any
from datetime import datetime
from rag.state import AgentState, AgentTurn
from rag.enums import Agentes
from config.logger import get_logger

logger = get_logger(__name__)


def make_turn(state: AgentState, answer: Optional[str] = None, 
              error: Optional[str] = None, extra: Optional[Dict[str, Any]] = None) -> AgentTurn:
    """
    Constrói um AgentTurn padronizado
    
    Args:
        state: Estado atual do agente
        answer: Resposta do agente
        error: Erro ocorrido
        extra: Dados extras
        
    Returns:
        AgentTurn estruturado
    """
    current_agent = state.get("current")
    task = state.get("tasks", {}).get(current_agent, "") if current_agent else ""
    
    turn = AgentTurn(
        agent=current_agent,
        task=task,
        answer=answer or "",
        error=error or ""
    )
    
    # Adicionar dados extras se fornecidos
    if extra:
        turn.update(extra)
    
    logger.debug(f"Turn criado para agente {current_agent}: {answer[:50] if answer else 'erro'}")
    return turn


def retry_prompt(state: AgentState) -> str:
    """
    Gera prompt de retry com informações de erro anterior
    
    Args:
        state: Estado atual
        
    Returns:
        String com prompt de retry
    """
    prev_answer = state.get("answers", {}).get(state.get("current"), {})
    issue = state.get("issues", {}).get(state.get("current"), "")
    
    if prev_answer or issue:
        return (
            "\n\n=== Retentativa ===\n"
            f"Retentativa, ocorreu o seguinte problema anteriormente:\n"
            "--- análise do erro ---\n"
            f"{issue}\n\n"
            "--- Sua resposta anterior ---\n"
            f"{prev_answer.get('answer', 'N/A')}\n"
        )
    
    return ""
