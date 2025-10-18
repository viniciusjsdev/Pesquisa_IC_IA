# infrastructure/database/connections/__init__.py
"""
Módulo de conexões para múltiplos bancos de dados
"""

from .financeiro_connection import FinanceiroConnection, financeiro_connection
from .industrial_connection import IndustrialConnection, industrial_connection
from .dw_connection import DWConnection, dw_connection

__all__ = [
    "FinanceiroConnection",
    "financeiro_connection",
    "IndustrialConnection", 
    "industrial_connection",
    "DWConnection",
    "dw_connection"
]
