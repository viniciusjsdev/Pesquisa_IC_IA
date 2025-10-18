# infrastructure/database/connections/industrial_connection.py
"""
Conexão específica para o banco industrial
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from infrastructure.config.database_config import INDUSTRIAL_DB_CONFIG, DB_SETTINGS

class IndustrialConnection:
    """Gerenciador de conexão para banco industrial"""
    
    def __init__(self):
        self.config = INDUSTRIAL_DB_CONFIG
        self.engine = None
        self.SessionLocal = None
        self._create_engine()
    
    def _create_engine(self):
        """Cria engine de conexão para banco industrial"""
        database_url = self._get_database_url()
        
        self.engine = create_engine(
            database_url,
            pool_size=DB_SETTINGS["pool_size"],
            max_overflow=DB_SETTINGS["max_overflow"],
            pool_pre_ping=DB_SETTINGS["pool_pre_ping"],
            pool_recycle=DB_SETTINGS["pool_recycle"],
            echo=DB_SETTINGS["echo"]
        )
        
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
    
    def _get_database_url(self):
        """Retorna URL de conexão para banco industrial"""
        # Permite sobrescrever via variáveis de ambiente
        host = os.getenv("INDUSTRIAL_DB_HOST", self.config["host"])
        port = os.getenv("INDUSTRIAL_DB_PORT", self.config["port"])
        database = os.getenv("INDUSTRIAL_DB_NAME", self.config["database"])
        user = os.getenv("INDUSTRIAL_DB_USER", self.config["user"])
        password = os.getenv("INDUSTRIAL_DB_PASSWORD", self.config["password"])
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def get_session(self):
        """Retorna sessão do banco industrial"""
        return self.SessionLocal()
    
    def get_engine(self):
        """Retorna engine do banco industrial"""
        return self.engine
    
    def test_connection(self):
        """Testa conexão com banco industrial"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Erro na conexão industrial: {e}")
            return False

# Instância global da conexão industrial
industrial_connection = IndustrialConnection()
