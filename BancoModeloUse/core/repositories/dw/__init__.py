# core/repositories/dw/__init__.py
"""
Repositórios da Data Warehouse
"""

from .dimensoes_repository import DimensoesRepository
from .fatos_repository import FatosRepository
from .kpis_repository import KPIsRepository

__all__ = [
    "DimensoesRepository",
    "FatosRepository",
    "KPIsRepository"
]
