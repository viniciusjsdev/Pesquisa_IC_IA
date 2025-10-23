# core/repositories/industrial/__init__.py
"""
Repositórios industriais
"""

from .producao_repository import ProducaoRepository
from .equipamentos_repository import EquipamentosRepository
from .qualidade_repository import QualidadeRepository

__all__ = [
    "ProducaoRepository",
    "EquipamentosRepository",
    "QualidadeRepository"
]
