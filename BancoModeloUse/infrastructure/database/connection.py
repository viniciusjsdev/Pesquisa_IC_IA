# infrastructure/database/connection.py
import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from infrastructure.config.database_config import DEFAULT_DB_CONFIG

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
    config = DEFAULT_DB_CONFIG
    
    # Permite sobrescrever configurações individuais via variáveis de ambiente
    host = os.getenv("DB_HOST", config["host"])
    port = os.getenv("DB_PORT", config["port"])
    database = os.getenv("DB_NAME", config["database"])
    user = os.getenv("DB_USER", config["user"])
    password = os.getenv("DB_PASSWORD", config["password"])
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

# URL de conexão para uso nos outros módulos
DATABASE_URL = get_database_url()
