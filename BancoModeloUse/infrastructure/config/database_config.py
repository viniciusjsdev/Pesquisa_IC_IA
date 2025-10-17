# config/database_config.py
"""
Configurações do banco de dados
Modifique apenas este arquivo para diferentes máquinas/ambientes
"""

# Importa configurações específicas da máquina
try:
    from .machine_config import MACHINE_DB_CONFIG
    DEFAULT_DB_CONFIG = MACHINE_DB_CONFIG
except ImportError:
    # Configuração padrão se machine_config.py não existir
    DEFAULT_DB_CONFIG = {
        "host": "localhost",
        "port": "5432",
        "database": "db_datamind",
        "user": "postgres",
        "password": "host"
    }

# Configurações adicionais do banco
DB_SETTINGS = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "echo": False  # Mude para True para ver queries SQL
}

# Configurações de migração
MIGRATION_SETTINGS = {
    "auto_create_database": True,
    "auto_create_tables": True,
    "auto_update_tables": True,
    "backup_before_migration": False
}
