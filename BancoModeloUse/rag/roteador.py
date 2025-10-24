"""
Roteador para coordenação de fluxo entre agentes
"""

from typing import Dict, Any
from config.logger import get_logger
from rag.state import AgentState
from rag.enums import Agentes
from rag.state_service import wrap_state
from rag.agents import (
    preprocessador, 
    validador_global,
    agente_financeiro,
    agente_industrial, 
    agente_integracao,
    agente_finalizador
)

logger = get_logger(__name__)

# Mapeamento de agentes para funções
AGENT_MAP = {
    Agentes.PREPROCESSADOR: preprocessador,
    Agentes.VALIDADOR_GLOBAL: validador_global,
    Agentes.FINANCEIRO: agente_financeiro,
    Agentes.INDUSTRIAL: agente_industrial,
    Agentes.INTEGRACAO: agente_integracao,
    Agentes.FINALIZADOR: agente_finalizador,
}


def orquestrador(state: AgentState) -> AgentState:
    """
    Orquestrador principal - coordena o fluxo entre agentes
    
    Args:
        state: Estado atual do agente
        
    Returns:
        Estado atualizado
    """
    logger.info("Executando orquestrador")
    
    service = wrap_state(state)
    
    # Primeira etapa - decomposição
    if service.is_starting_flow():
        logger.info("Iniciando fluxo - primeira etapa")
        return service.state_first_step()
    
    # Processar próximo passo
    return next_step(service)


def next_step(service) -> AgentState:
    """
    Processa próximo passo no fluxo
    
    Args:
        service: StateService wrapper
        
    Returns:
        Estado atualizado
    """
    logger.debug("Processando próximo passo")
    
    # Verificar se agente tem turno
    if service.has_agent_turn():
        logger.debug("Agente tem turno")
        
        # Se não é validador e tem erro, retry
        if service.is_not_validators_turn() and service.has_agent_turn_error():
            logger.debug("Erro no turno do agente - retry")
            return service.state_retry_agent_turn()
        
        # Registrar resposta do agente
        service.push_answer()
        service.pop_next_pending()
    
    # Se há agentes pendentes, próximo agente
    if service.has_pending():
        logger.debug("Há agentes pendentes")
        return service.state_next_agent_turn()
    
    # Finalizar fluxo
    return end_step(service)


def end_step(service) -> AgentState:
    """
    Finaliza o fluxo ou chama validador
    
    Args:
        service: StateService wrapper
        
    Returns:
        Estado final
    """
    logger.debug("Finalizando etapa")
    
    # Se precisa chamar validador
    if service.should_call_validador_global():
        logger.debug("Chamando validador global")
        return service.state_call_validador_global()
    
    # Se validação ok, finalizar
    if service.is_validation_ok():
        logger.debug("Validação ok - finalizando")
        return service.state_end()
    
    # Se atingiu limite de loops
    if service.max_loops_reached():
        logger.debug("Limite de loops atingido")
        return service.state_end()
    
    # Se há issues de validação, reprocessar
    if service.has_validation_issues():
        logger.debug("Há issues de validação")
        return service.state_validation_issues()
    
    # Voltar ao preprocessador
    logger.debug("Voltando ao preprocessador")
    return service.state_back_to_preprocessador()


def agent_handler(state: AgentState, agent: Agentes) -> AgentState:
    """
    Handler genérico para agentes especializados
    
    Args:
        state: Estado atual
        agent: Agente a ser executado
        
    Returns:
        Estado atualizado
    """
    logger.debug(f"Executando agente: {agent}")
    
    # Obter função do agente
    if agent not in AGENT_MAP:
        logger.error(f"Agente não encontrado: {agent}")
        return {
            **state,
            "error": f"Agente {agent} não encontrado"
        }
    
    agent_func = AGENT_MAP[agent]
    
    try:
        # Executar agente
        result = agent_func(state)
        
        # Se resultado contém turn, processar
        if isinstance(result, dict) and "turn" in result:
            turn = result["turn"]
            return {
                **state,
                "turn": turn,
                "answer": turn.get("answer", ""),
                "error": turn.get("error", "")
            }
        
        # Se resultado é dict direto, mesclar
        if isinstance(result, dict):
            return {**state, **result}
        
        # Fallback
        return {
            **state,
            "answer": str(result) if result else "",
            "error": ""
        }
        
    except Exception as e:
        logger.error(f"Erro no agente {agent}: {str(e)}")
        return {
            **state,
            "error": f"Erro no agente {agent}: {str(e)}"
        }
