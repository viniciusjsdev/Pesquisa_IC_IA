# infrastructure/database/connection.py
"""
Módulo legado de conexão - mantido para compatibilidade
Recomendado usar as classes de conexão específicas em connections/
"""
import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from infrastructure.config.database_config import DEFAULT_DB_CONFIG, get_database_url as get_db_url

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

def get_database_url():
    """
    Retorna a URL de conexão do banco de dados.
    Prioridade: variável de ambiente DATABASE_URL > configuração padrão
    """
    # Tenta usar a variável de ambiente primeiro
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        return database_url
    
    # Se não houver variável de ambiente, usa a configuração padrão
    config = DEFAULT_DB_CONFIG.copy()
    
    # Permite sobrescrever configurações individuais via variáveis de ambiente
    config["host"] = os.getenv("DB_HOST", config["host"])
    config["port"] = os.getenv("DB_PORT", str(config["port"]))
    config["database"] = os.getenv("DB_NAME", config["database"])
    config["user"] = os.getenv("DB_USER", config["user"])
    config["password"] = os.getenv("DB_PASSWORD", config["password"])
    
    # Usa a função centralizada de database_config
    return get_db_url(config)

# URL de conexão para uso nos outros módulos
DATABASE_URL = get_database_url()
