"""
Agente Validador Global - Auditoria automática de qualidade
"""

import json
from typing import Dict, Any
from config.logger import get_logger
from rag.state import AgentState
from rag.enums import Agentes
from rag.providers import get_llm
from rag.guard_rails import as_turn, agent_exception
from rag.utils.agentes import get_prompt, build_context_for_agent

logger = get_logger(__name__)


@agent_exception("validador_global", "Erro na validação global")
@as_turn()
def validador_global(state: AgentState) -> Dict[str, Any]:
    """
    Agente validador que audita a qualidade das respostas
    
    Args:
        state: Estado atual do agente
        
    Returns:
        Dict com resultado da validação
    """
    logger.info("Executando validador global")
    
    # Obter pergunta original e respostas
    question = state.get("question", "")
    answers = state.get("answers", {})
    
    if not question:
        return {"error": "Pergunta original não fornecida"}
    
    if not answers:
        return {"error": "Nenhuma resposta para validar"}
    
    # Carregar prompt do validador
    try:
        with open("core/rag/agents/prompts/validador_prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        logger.error("Arquivo de prompt do validador não encontrado")
        system_prompt = "Você é um especialista em auditoria de qualidade. Avalie se as respostas atendem à pergunta."
    
    # Montar contexto com histórico de respostas
    context = build_context_for_agent(state)
    
    # Montar prompt completo
    full_prompt = get_prompt(state, system_prompt)
    
    # Obter modelo LLM
    try:
        llm = get_llm("finetuned_mistral")
    except Exception as e:
        logger.warning(f"Erro ao carregar modelo fine-tuned: {e}. Usando fallback.")
        llm = get_llm("gpt4o_fallback")
    
    # Executar validação
    try:
        response = llm.ask(
            system_prompt=system_prompt,
            user_message=full_prompt,
            temperature=0.1,  # Baixa temperatura para consistência
            max_tokens=800,
            tools=[]
        )
        
        logger.debug(f"Resposta do validador: {response[:200]}...")
        
        # Parsear JSON de resposta
        try:
            validation_result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON do validador: {e}")
            return {"error": "Resposta do validador em formato inválido"}
        
        # Validar estrutura da resposta
        if not isinstance(validation_result, dict):
            return {"error": "Resposta do validador deve ser um objeto JSON"}
        
        if "ok" not in validation_result:
            return {"error": "Resposta do validador deve conter campo 'ok'"}
        
        # Processar resultado
        is_ok = validation_result.get("ok", False)
        issues = validation_result.get("issues", {})
        
        if not isinstance(issues, dict):
            issues = {}
        
        # Log do resultado
        if is_ok:
            logger.info("Validação global: APROVADA")
        else:
            logger.warning(f"Validação global: REPROVADA - Issues: {list(issues.keys())}")
        
        return {
            "answer": "Validação global concluída",
            "validation": {
                "ok": is_ok,
                "issues": issues
            }
        }
        
    except Exception as e:
        logger.error(f"Erro na validação: {str(e)}")
        return {"error": f"Erro na validação: {str(e)}"}
