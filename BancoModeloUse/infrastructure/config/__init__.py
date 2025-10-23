# config/__init__.py
"""
Módulo de configurações
"""

from .database_config import (
    DEFAULT_DB_CONFIG, 
    FINANCEIRO_DB_CONFIG,
    INDUSTRIAL_DB_CONFIG, 
    DW_DB_CONFIG,
    DB_SETTINGS, 
    MIGRATION_SETTINGS,
    get_database_url,
    get_all_database_configs,
    get_database_ports,
    validate_database_configs
)
from .app_config import SERVER_CONFIG, LOGGING_CONFIG, CORS_CONFIG, DOCS_CONFIG

__all__ = [
    "DEFAULT_DB_CONFIG",
    "FINANCEIRO_DB_CONFIG", 
    "INDUSTRIAL_DB_CONFIG",
    "DW_DB_CONFIG",
    "DB_SETTINGS", 
    "MIGRATION_SETTINGS",
    "get_database_url",
    "get_all_database_configs",
    "get_database_ports",
    "validate_database_configs",
    "SERVER_CONFIG",
    "LOGGING_CONFIG",
    "CORS_CONFIG",
    "DOCS_CONFIG"
]
