# infrastructure/database/connections/base_connection.py
"""
Classe base para conexões de banco de dados
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from infrastructure.config.database_config import DB_SETTINGS, get_database_url

class BaseConnection:
    """Classe base para gerenciamento de conexão com banco de dados"""
    
    def __init__(self, config: dict, env_prefix: str = ""):
        """
        Inicializa conexão com banco de dados
        
        Args:
            config: Dicionário com configuração do banco (host, port, database, user, password)
            env_prefix: Prefixo para variáveis de ambiente (ex: "INDUSTRIAL_DB_")
        """
        self.config = config
        self.env_prefix = env_prefix
        self.engine = None
        self.SessionLocal = None
        self._create_engine()
    
    def _get_database_url(self) -> str:
        """Retorna URL de conexão para o banco"""
        # Permite sobrescrever via variáveis de ambiente
        host = os.getenv(f"{self.env_prefix}HOST", self.config["host"])
        port = os.getenv(f"{self.env_prefix}PORT", str(self.config["port"]))
        database = os.getenv(f"{self.env_prefix}NAME", self.config["database"])
        user = os.getenv(f"{self.env_prefix}USER", self.config["user"])
        password = os.getenv(f"{self.env_prefix}PASSWORD", self.config["password"])
        
        # Usa a função centralizada de database_config
        config_dict = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        return get_database_url(config_dict)
    
    def _create_engine(self):
        """Cria engine de conexão"""
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
    
    def get_session(self):
        """Retorna sessão do banco"""
        return self.SessionLocal()
    
    def get_engine(self):
        """Retorna engine do banco"""
        return self.engine
    
    def test_connection(self) -> bool:
        """Testa conexão com banco"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Erro na conexão: {e}")
            return False

