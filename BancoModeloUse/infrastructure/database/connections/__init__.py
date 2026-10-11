# infrastructure/database/connections/__init__.py
"""
Módulo de conexões para múltiplos bancos de dados
"""

from .base_connection import BaseConnection
from .financeiro_connection import FinanceiroConnection, financeiro_connection, Base as FinanceiroBase
from .industrial_connection import IndustrialConnection, industrial_connection, Base as IndustrialBase

__all__ = [
    "BaseConnection",
    "FinanceiroConnection",
    "financeiro_connection",
    "FinanceiroBase",
    "IndustrialConnection", 
    "industrial_connection",
    "IndustrialBase"
]
