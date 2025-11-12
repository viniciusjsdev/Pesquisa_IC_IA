# infrastructure/database/connections/financeiro_connection.py
"""
Conexão específica para o banco financeiro
"""
import sys
import os

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sqlalchemy.ext.declarative import declarative_base
from infrastructure.config.database_config import FINANCEIRO_DB_CONFIG
from infrastructure.database.connections.base_connection import BaseConnection

# Base específica para modelos financeiros
Base = declarative_base()

class FinanceiroConnection(BaseConnection):
    """Gerenciador de conexão para banco financeiro"""
    
    def __init__(self):
        super().__init__(FINANCEIRO_DB_CONFIG, env_prefix="FINANCEIRO_DB_")

# Instância global da conexão financeira
financeiro_connection = FinanceiroConnection()
