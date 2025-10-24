"""
Utilitários para agentes
"""

from datetime import datetime
import json
import re
from typing import Optional, Dict, OrderedDict
from rag.state import AgentState, AgentTurn
from rag.enums import Agentes
from config.logger import get_logger

logger = get_logger(__name__)


def _get_question(state: AgentState) -> str:
    """Obtém a pergunta apropriada baseada no agente atual"""
    agent = state.get("current")
    if agent == Agentes.PREPROCESSADOR or agent == Agentes.VALIDADOR_GLOBAL:
        return state["question"]
    return state.get("tasks", {}).get(agent, "")


def _strip_mentions_and_directives(text: str) -> str:
    """
    Remove menções e diretivas do texto
    
    Args:
        text: Texto a ser limpo
        
    Returns:
        Texto sanitizado
    """
    if not text:
        return ""
    
    # Compacta espaços em branco
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def build_context_for_agent(state: AgentState) -> str:
    """
    Constrói contexto a partir de respostas prévias dos agentes.
    Mantém ordem de execução e sanitiza respostas.
    
    Args:
        state: Estado atual
        
    Returns:
        String com contexto formatado
    """
    answers: Dict[Agentes, AgentTurn] = state.get("answers", {}) or {}
    if not answers:
        return ""
    
    chunks = []
    for agent_enum, agent_turn in answers.items():
        clean = _strip_mentions_and_directives(agent_turn["answer"])
        if not clean:
            continue
        
        head = f"--- {agent_enum} ---\n"
        task = f"Task: {agent_turn['task']}\n"
        clean_answer = f"Resposta: {clean}\n"
        
        chunks.append(head + task + clean_answer)
    
    return "\n".join(chunks).strip()


def get_prompt(state: AgentState, context: Optional[str] = None) -> str:
    """
    Monta prompt completo para o agente
    
    Args:
        state: Estado atual
        context: Contexto adicional
        
    Returns:
        Prompt completo formatado
    """
    question = _get_question(state)
    agent_history = build_context_for_agent(state)
    retry = retry_prompt(state)
    
    full_prompt = f"Data atual: {datetime.now()}\n\n"
    full_prompt += "Abaixo podem estar presentes: contexto, pergunta do usuário e "
    full_prompt += "histórico dos agentes (quando disponíveis)."
    
    if context:
        full_prompt += f"\n\n=== Contexto ===\n{context}"
    
    if retry:
        full_prompt += retry
    
    full_prompt += f"\n\n=== Pergunta do usuário ===\n{question}"
    
    if agent_history:
        full_prompt += f"\n\n=== Histórico dos agentes ===\n{agent_history}"
    
    return full_prompt


def safe_parse_tasks(raw: str) -> OrderedDict[Agentes, str]:
    """
    Valida JSON e mapeia chaves em roles → enum Agentes;
    ignora desconhecidos.
    
    Args:
        raw: String JSON com tasks
        
    Returns:
        OrderedDict com tasks mapeadas
    """
    try:
        data = json.loads(raw)
        out = OrderedDict()
        tasks = data.get("tasks", {})
        
        for role, task in tasks.items():
            enum_role = Agentes.from_key(role)
            if not enum_role:
                logger.warning(f"Role desconhecida no YAML: {role}")
                continue
            if isinstance(task, str) and task.strip():
                out[enum_role] = task.strip()
        
        return out
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao parsear JSON de tasks: {str(e)}")
        return OrderedDict()
    except Exception as e:
        logger.error(f"Erro inesperado ao parsear tasks: {str(e)}")
        return OrderedDict()
