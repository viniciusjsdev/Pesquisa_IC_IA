# infrastructure/database/connections/industrial_connection.py
"""
Conexão específica para o banco industrial
"""
import sys
import os

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sqlalchemy.ext.declarative import declarative_base
from infrastructure.config.database_config import INDUSTRIAL_DB_CONFIG
from infrastructure.database.connections.base_connection import BaseConnection

# Base específica para modelos industriais
Base = declarative_base()

class IndustrialConnection(BaseConnection):
    """Gerenciador de conexão para banco industrial"""
    
    def __init__(self):
        super().__init__(INDUSTRIAL_DB_CONFIG, env_prefix="INDUSTRIAL_DB_")

# Instância global da conexão industrial
industrial_connection = IndustrialConnection()
