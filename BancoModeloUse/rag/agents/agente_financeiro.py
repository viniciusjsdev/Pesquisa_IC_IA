"""
Agente Financeiro - Análise de dados financeiros
"""

from typing import Dict, Any
from datetime import datetime
from config.logger import get_logger
from rag.state import AgentState
from rag.guard_rails import as_turn, agent_exception
from rag.tools import get_tool

logger = get_logger(__name__)


class AgenteFinanceiro:
    """Agente especializado em análise financeira"""
    
    def __init__(self):
        self.name = "agente_financeiro"
    
    def processar_consulta(self, tipo_consulta: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Processa consulta financeira"""
        # Implementação simplificada
        return {
            "agente": "financeiro",
            "tipo_consulta": tipo_consulta,
            "parametros": parametros,
            "resultado": "Análise financeira processada",
            "timestamp": datetime.now().isoformat()
        }

@agent_exception("agente_financeiro", "Erro na análise financeira")
@as_turn()
def agente_financeiro(state: AgentState) -> Dict[str, Any]:
    """
    Agente especializado em análise financeira
    
    Args:
        state: Estado atual do agente
        
    Returns:
        Dict com análise financeira
    """
    logger.info("Executando agente financeiro")
    
    # Obter tarefa do agente
    task = state.get("tasks", {}).get("agente_financeiro", "")
    if not task:
        return {"error": "Tarefa não fornecida para agente financeiro"}
    
    try:
        # Usar tool de consulta financeira
        financeiro_tool = get_tool("query_financeira")
        
        # Preparar parâmetros baseados na tarefa
        if "vendas" in task.lower():
            consulta = "vendas"
        elif "custos" in task.lower():
            consulta = "custos"
        elif "lancamentos" in task.lower():
            consulta = "lancamentos"
        elif "orcamentos" in task.lower():
            consulta = "orcamentos"
        else:
            consulta = "vendas"  # Default
        
        # Executar consulta
        result = financeiro_tool.run({
            "consulta": consulta,
            "parametros": {}
        })
        
        if result.meta.get("erro"):
            return {"error": f"Erro na consulta financeira: {result.data}"}
        
        return {
            "answer": f"Análise financeira concluída: {result.data}",
            "data": result.data
        }
        
    except Exception as e:
        logger.error(f"Erro no agente financeiro: {str(e)}")
        return {"error": f"Erro na análise financeira: {str(e)}"}
