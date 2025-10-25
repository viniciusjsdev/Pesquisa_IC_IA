# config/machine_config.py
"""
Configurações específicas por máquina
Copie este arquivo e modifique conforme necessário para cada máquina
"""

# CONFIGURAÇÕES POR MÁQUINA - MODIFIQUE APENAS ESTE ARQUIVO
MACHINE_DB_CONFIG = {
    "host": "localhost",
    "port": "5432", 
    "database": "db_datamind",
    "user": "postgres",
    "password": "p4ss#5"
}

# Configurações específicas da máquina
MACHINE_SETTINGS = {
    "auto_open_browser": True,  # Abre navegador automaticamente
    "auto_create_database": True,  # Cria banco automaticamente
    "show_sql_queries": False,  # Mostra queries SQL no console
    "backup_database": False,  # Faz backup antes de migrar
    "development_mode": True  # Modo desenvolvimento
}

# Configurações de rede específicas
NETWORK_CONFIG = {
    "allowed_hosts": ["localhost", "127.0.0.1"],
    "cors_origins": ["http://localhost:3000", "http://localhost:8000"],
    "ssl_enabled": False
}
