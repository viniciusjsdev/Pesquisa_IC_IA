"""
Utilitários para o sistema RAG
"""

from .turns import make_turn
from .agentes import build_context_for_agent, get_prompt

__all__ = [
    "make_turn",
    "build_context_for_agent", 
    "get_prompt"
]
