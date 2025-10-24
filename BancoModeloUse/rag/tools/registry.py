"""
Registry centralizado para tools
"""

from typing import Dict, Type
from config.logger import get_logger

from .base import BaseTool

logger = get_logger(__name__)

# Registry global de tools
TOOLS: Dict[str, BaseTool] = {}


def register_tool(tool: BaseTool) -> None:
    """
    Registra uma tool no registry
    
    Args:
        tool: Instância da tool a ser registrada
    """
    TOOLS[tool.name] = tool
    logger.debug(f"Tool '{tool.name}' registrada")


def get_tool(name: str) -> BaseTool:
    """
    Obtém tool por nome
    
    Args:
        name: Nome da tool
        
    Returns:
        Instância da tool
        
    Raises:
        KeyError: Se tool não encontrada
    """
    if name not in TOOLS:
        available = list(TOOLS.keys())
        raise KeyError(f"Tool '{name}' não encontrada. Disponíveis: {available}")
    
    return TOOLS[name]


def list_tools() -> Dict[str, str]:
    """
    Lista todas as tools registradas
    
    Returns:
        Dict com nome e descrição das tools
    """
    return {name: tool.description for name, tool in TOOLS.items()}


def clear_tools():
    """Limpa registry de tools"""
    TOOLS.clear()
    logger.info("Registry de tools limpo")
