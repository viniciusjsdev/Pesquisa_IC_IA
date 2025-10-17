# config/__init__.py
"""
Módulo de configurações
"""

from .database_config import DEFAULT_DB_CONFIG, DB_SETTINGS, MIGRATION_SETTINGS
from .app_config import SERVER_CONFIG, LOGGING_CONFIG, CORS_CONFIG, DOCS_CONFIG

__all__ = [
    "DEFAULT_DB_CONFIG",
    "DB_SETTINGS", 
    "MIGRATION_SETTINGS",
    "SERVER_CONFIG",
    "LOGGING_CONFIG",
    "CORS_CONFIG",
    "DOCS_CONFIG"
]
