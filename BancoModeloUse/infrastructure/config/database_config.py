# config/database_config.py
"""
Configurações dos bancos de origem industrial e financeiro.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine import URL

# Explicit process variables take precedence over this ignored local file.
load_dotenv(Path(__file__).resolve().parents[2] / '.env.local', override=False)

# Configurações adicionais do banco
DB_SETTINGS = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "echo": False  # Mude para True para ver queries SQL
}

# =============================================================================
# CONFIGURAÇÕES DOS BANCOS DE ORIGEM
# =============================================================================

# Banco Financeiro (ERP/Contábil)
FINANCEIRO_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "db_financeiro",
    "user": "postgres",
    "password": "host",
    "schema": "financeiro"
}

# Banco Industrial (MES/SCADA)
INDUSTRIAL_DB_CONFIG = {
    "host": "localhost", 
    "port": 5432,
    "database": "db_industrial",
    "user": "postgres",
    "password": "host",
    "schema": "industrial"
}

for _prefix, _config in [('FINANCEIRO', FINANCEIRO_DB_CONFIG),
                          ('INDUSTRIAL', INDUSTRIAL_DB_CONFIG)]:
    for _key, _suffix in [('host', 'HOST'), ('port', 'PORT'), ('database', 'NAME'),
                           ('user', 'USER'), ('password', 'PASSWORD')]:
        _value = os.getenv(f'{_prefix}_DB_{_suffix}')
        if _value is not None:
            _config[_key] = int(_value) if _key == 'port' else _value

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def get_database_url(config: dict) -> str:
    """
    Gera URL de conexão a partir da configuração
    
    Args:
        config: Dicionário com configuração do banco (host, port, database, user, password)
        
    Returns:
        URL de conexão PostgreSQL
    """
    # Garante que port seja string
    return URL.create('postgresql+psycopg2', username=config['user'],
                      password=config['password'], host=config['host'],
                      port=int(config['port']), database=config['database']).render_as_string(hide_password=False)

def get_all_database_configs() -> dict:
    """
    Retorna todas as configurações de banco
    
    Returns:
        Dicionário com todas as configurações
    """
    return {
        "financeiro": FINANCEIRO_DB_CONFIG,
        "industrial": INDUSTRIAL_DB_CONFIG
    }

def get_database_ports() -> dict:
    """
    Retorna mapeamento de bancos para portas
    
    Returns:
        Dicionário com portas dos bancos
    """
    return {
        "financeiro": FINANCEIRO_DB_CONFIG["port"],
        "industrial": INDUSTRIAL_DB_CONFIG["port"]
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
