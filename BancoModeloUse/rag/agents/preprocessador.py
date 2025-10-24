"""
Agente Preprocessador - Decomposição de perguntas em subtarefas
"""

import json
from typing import Dict, Any
from config.logger import get_logger
from rag.state import AgentState
from rag.enums import Agentes
from rag.providers import get_llm
from rag.guard_rails import as_turn, agent_exception
from rag.utils.agentes import get_prompt, safe_parse_tasks

logger = get_logger(__name__)


@agent_exception("preprocessador", "Erro na decomposição da pergunta")
@as_turn()
def preprocessador(state: AgentState) -> Dict[str, Any]:
    """
    Agente preprocessador que decompõe perguntas complexas em subtarefas
    
    Args:
        state: Estado atual do agente
        
    Returns:
        Dict com tasks decompostas ou erro
    """
    logger.info("Executando agente preprocessador")
    
    # Obter pergunta do usuário
    question = state.get("question", "")
    if not question:
        return {"error": "Pergunta não fornecida"}
    
    # Carregar prompt do preprocessador
    try:
        with open("core/rag/agents/prompts/preprocessador_prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        logger.error("Arquivo de prompt do preprocessador não encontrado")
        system_prompt = "Você é um especialista em decomposição de perguntas. Decomponha a pergunta em subtarefas para agentes especializados."
    
    # Montar prompt completo
    full_prompt = get_prompt(state, system_prompt)
    
    # Obter modelo LLM
    try:
        llm = get_llm("finetuned_mistral")  # Usar modelo fine-tuned como padrão
    except Exception as e:
        logger.warning(f"Erro ao carregar modelo fine-tuned: {e}. Usando fallback.")
        llm = get_llm("gpt4o_fallback")
    
    # Executar decomposição
    try:
        response = llm.ask(
            system_prompt=system_prompt,
            user_message=full_prompt,
            temperature=0.1,  # Baixa temperatura para consistência
            max_tokens=1000,
            tools=[]
        )
        
        logger.debug(f"Resposta do preprocessador: {response[:200]}...")
        
        # Parsear JSON de resposta
        tasks = safe_parse_tasks(response)
        
        if not tasks:
            return {"error": "Não foi possível decompor a pergunta em subtarefas"}
        
        # Validar que sempre inclui finalizador
        if Agentes.FINALIZADOR not in tasks:
            tasks[Agentes.FINALIZADOR] = "Consolidar análises e apresentar resposta final"
            logger.info("Adicionado agente finalizador automaticamente")
        
        # Preparar resposta
        tasks_dict = {agent.value: task for agent, task in tasks.items()}
        
        return {
            "answer": f"Pergunta decomposta em {len(tasks)} subtarefas",
            "tasks": tasks_dict,
            "pending": list(tasks.keys())
        }
        
    except Exception as e:
        logger.error(f"Erro na decomposição: {str(e)}")
        return {"error": f"Erro na decomposição: {str(e)}"}
