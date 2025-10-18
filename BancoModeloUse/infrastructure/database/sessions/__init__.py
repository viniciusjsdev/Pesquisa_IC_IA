# infrastructure/database/sessions/__init__.py
"""
Módulo de sessões para múltiplos bancos de dados
"""

from .financeiro_session import get_financeiro_db, get_financeiro_engine, test_financeiro_connection
from .industrial_session import get_industrial_db, get_industrial_engine, test_industrial_connection
from .dw_session import get_dw_db, get_dw_engine, test_dw_connection

__all__ = [
    "get_financeiro_db",
    "get_financeiro_engine", 
    "test_financeiro_connection",
    "get_industrial_db",
    "get_industrial_engine",
    "test_industrial_connection", 
    "get_dw_db",
    "get_dw_engine",
    "test_dw_connection"
]
