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
        "password": "root"
    }

# Configurações adicionais do banco
DB_SETTINGS = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "echo": False  # Mude para True para ver queries SQL
}

# =============================================================================
# CONFIGURAÇÕES DOS 3 BANCOS DE DADOS
# =============================================================================

# Banco Financeiro (ERP/Contábil)
FINANCEIRO_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "db_financeiro",
    "user": "postgres",
    "password": "root",
    "schema": "financeiro"
}

# Banco Industrial (MES/SCADA)
INDUSTRIAL_DB_CONFIG = {
    "host": "localhost", 
    "port": 5432,
    "database": "db_industrial",
    "user": "postgres",
    "password": "root",
    "schema": "industrial"
}

# Data Warehouse (Consolidado)
DW_DB_CONFIG = {
    "host": "localhost",
    "port": 5432, 
    "database": "db_datamind_dw",
    "user": "postgres",
    "password": "root",
    "schema": "dw"
}

# Configurações de migração
MIGRATION_SETTINGS = {
    "auto_create_database": True,
    "auto_create_tables": True,
    "auto_update_tables": True,
    "backup_before_migration": False
}

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def get_database_url(config: dict) -> str:
    """
    Gera URL de conexão a partir da configuração
    
    Args:
        config: Dicionário com configuração do banco
        
    Returns:
        URL de conexão PostgreSQL
    """
    return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

def get_all_database_configs() -> dict:
    """
    Retorna todas as configurações de banco
    
    Returns:
        Dicionário com todas as configurações
    """
    return {
        "financeiro": FINANCEIRO_DB_CONFIG,
        "industrial": INDUSTRIAL_DB_CONFIG, 
        "dw": DW_DB_CONFIG
    }

def get_database_ports() -> dict:
    """
    Retorna mapeamento de bancos para portas
    
    Returns:
        Dicionário com portas dos bancos
    """
    return {
        "financeiro": FINANCEIRO_DB_CONFIG["port"],
        "industrial": INDUSTRIAL_DB_CONFIG["port"],
        "dw": DW_DB_CONFIG["port"]
    }

def validate_database_configs() -> bool:
    """
    Valida se todas as configurações estão corretas
    
    Returns:
        True se todas as configurações são válidas
    """
    configs = get_all_database_configs()
    
    for name, config in configs.items():
        required_keys = ["host", "port", "database", "user", "password"]
        if not all(key in config for key in required_keys):
            print(f"ERRO: Configuração inválida para {name}: chaves obrigatórias ausentes")
            return False
            
        if not isinstance(config["port"], int):
            print(f"ERRO: Porta inválida para {name}: deve ser inteiro")
            return False
    
    print("OK: Todas as configurações de banco são válidas")
    return True
