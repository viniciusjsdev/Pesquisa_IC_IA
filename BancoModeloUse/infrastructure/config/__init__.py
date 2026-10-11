# config/__init__.py
"""
Módulo de configurações
"""

from .database_config import (
    FINANCEIRO_DB_CONFIG,
    INDUSTRIAL_DB_CONFIG, 
    DB_SETTINGS, 
    get_database_url,
    get_all_database_configs,
    get_database_ports,
    validate_database_configs
)
__all__ = [
    "FINANCEIRO_DB_CONFIG", 
    "INDUSTRIAL_DB_CONFIG",
    "DB_SETTINGS", 
    "get_database_url",
    "get_all_database_configs",
    "get_database_ports",
    "validate_database_configs"
]
