# infrastructure/database/manager.py
import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from infrastructure.database.connection import DATABASE_URL
from infrastructure.database.session import Base, engine
import logging

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from infrastructure.config.database_config import MIGRATION_SETTINGS

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerenciador de banco de dados com verificação e criação automática"""
    
    def __init__(self):
        self.database_url = DATABASE_URL
        self.engine = engine
        
    def check_database_exists(self):
        """Verifica se o banco de dados existe"""
        try:
            # Extrai informações da URL de conexão
            url_parts = self.database_url.replace('postgresql://', '').split('/')
            db_name = url_parts[1]
            auth_host = url_parts[0].split('@')
            user_pass = auth_host[0].split(':')
            host_port = auth_host[1].split(':')
            
            user = user_pass[0]
            password = user_pass[1]
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            
            # Conecta ao PostgreSQL (banco padrão postgres)
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone() is not None
            
            cursor.close()
            conn.close()
            
            return exists
            
        except Exception as e:
            logger.error(f"Erro ao verificar banco de dados: {e}")
            return False
    
    def create_database(self):
        """Cria o banco de dados se não existir"""
        try:
            # Extrai informações da URL de conexão
            url_parts = self.database_url.replace('postgresql://', '').split('/')
            db_name = url_parts[1]
            auth_host = url_parts[0].split('@')
            user_pass = auth_host[0].split(':')
            host_port = auth_host[1].split(':')
            
            user = user_pass[0]
            password = user_pass[1]
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            
            # Conecta ao PostgreSQL (banco padrão postgres)
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
            logger.info(f"Banco de dados '{db_name}' criado com sucesso!")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar banco de dados: {e}")
            return False
    
    def check_tables_exist(self):
        """Verifica se as tabelas existem no banco"""
        try:
            with self.engine.connect() as conn:
                # Verifica se existe pelo menos uma tabela do nosso sistema
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('produtos', 'custos_padrao', 'contas_contabeis')
                """))
                count = result.scalar()
                return count > 0
                
        except Exception as e:
            logger.error(f"Erro ao verificar tabelas: {e}")
            return False
    
    def create_tables(self):
        """Cria todas as tabelas do sistema"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tabelas criadas/atualizadas com sucesso!")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            return False
    
    def update_tables(self):
        """Atualiza as tabelas (cria se não existirem, atualiza se existirem)"""
        try:
            # Sempre recria as tabelas para garantir consistência
            Base.metadata.drop_all(bind=self.engine)
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tabelas atualizadas com sucesso!")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar tabelas: {e}")
            return False
    
    def ensure_database_ready(self):
        """Garante que o banco e tabelas estão prontos"""
        logger.info("Verificando banco de dados...")
        
        # 1. Verifica se o banco existe
        if not self.check_database_exists():
            logger.info("Banco de dados não encontrado. Criando...")
            if not self.create_database():
                logger.error("Falha ao criar banco de dados!")
                return False
        
        # 2. Verifica se as tabelas existem
        if not self.check_tables_exist():
            logger.info("Tabelas não encontradas. Criando...")
            if not self.create_tables():
                logger.error("Falha ao criar tabelas!")
                return False
        else:
            logger.info("Tabelas encontradas. Atualizando...")
            if not self.update_tables():
                logger.error("Falha ao atualizar tabelas!")
                return False
        
        logger.info("Banco de dados pronto!")
        return True

# Instância global do gerenciador
db_manager = DatabaseManager()

