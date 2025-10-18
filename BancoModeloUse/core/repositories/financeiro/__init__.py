# core/repositories/financeiro/__init__.py
"""
Repositórios financeiros
"""

from .custos_repository import CustosRepository
from .vendas_repository import VendasRepository
from .contabil_repository import ContabilRepository

__all__ = [
    "CustosRepository",
    "VendasRepository", 
    "ContabilRepository"
]
