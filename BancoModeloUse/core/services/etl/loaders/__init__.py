# core/services/etl/loaders/__init__.py
"""
Loaders ETL
"""

from .dimensoes_loader import DimensoesLoader
from .fatos_loader import FatosLoader

__all__ = [
    "DimensoesLoader",
    "FatosLoader"
]
