# infrastructure/database/connections/dw_connection.py
"""
Conexão específica para a Data Warehouse
"""
import sys
import os

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sqlalchemy.ext.declarative import declarative_base
from infrastructure.config.database_config import DW_DB_CONFIG
from infrastructure.database.connections.base_connection import BaseConnection

# Base específica para modelos da DW
Base = declarative_base()

class DWConnection(BaseConnection):
    """Gerenciador de conexão para Data Warehouse"""
    
    def __init__(self):
        super().__init__(DW_DB_CONFIG, env_prefix="DW_DB_")

# Instância global da conexão DW
dw_connection = DWConnection()
