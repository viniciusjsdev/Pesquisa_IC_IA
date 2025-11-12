# infrastructure/database/multi_db_manager.py
"""
Gerenciador para múltiplos bancos de dados
Cria e gerencia os 3 bancos: financeiro, industrial e DW
"""
import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import logging

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from infrastructure.config.database_config import (
    FINANCEIRO_DB_CONFIG, 
    INDUSTRIAL_DB_CONFIG, 
    DW_DB_CONFIG,
    MIGRATION_SETTINGS,
    get_database_url,
    DB_SETTINGS
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiDatabaseManager:
    """Gerenciador para múltiplos bancos de dados"""
    
    def __init__(self):
        self.configs = {
            'financeiro': FINANCEIRO_DB_CONFIG,
            'industrial': INDUSTRIAL_DB_CONFIG,
            'dw': DW_DB_CONFIG
        }
        self.engines = {}
        
    def get_connection_params(self, config):
        """Extrai parâmetros de conexão de uma configuração"""
        return {
            'host': config['host'],
            'port': config['port'],
            'user': config['user'],
            'password': config['password'],
            'database': config['database']
        }
    
    def check_database_exists(self, config):
        """Verifica se um banco específico existe"""
        try:
            params = self.get_connection_params(config)
            
            # Conecta ao PostgreSQL (banco padrão postgres)
            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                user=params['user'],
                password=params['password'],
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (params['database'],))
            exists = cursor.fetchone() is not None
            
            cursor.close()
            conn.close()
            
            return exists
            
        except Exception as e:
            logger.error(f"Erro ao verificar banco {config['database']}: {e}")
            return False
    
    def create_database(self, config):
        """Cria um banco específico se não existir"""
        try:
            params = self.get_connection_params(config)
            
            # Conecta ao PostgreSQL (banco padrão postgres)
            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                user=params['user'],
                password=params['password'],
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {params['database']}")
            logger.info(f"Banco de dados '{params['database']}' criado com sucesso!")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar banco {config['database']}: {e}")
            return False
    
    def get_engine(self, db_name):
        """Obtém engine para um banco específico"""
        if db_name not in self.engines:
            config = self.configs[db_name]
            
            # Usa a função centralizada de database_config
            database_url = get_database_url(config)
            
            self.engines[db_name] = create_engine(
                database_url,
                pool_size=DB_SETTINGS["pool_size"],
                max_overflow=DB_SETTINGS["max_overflow"],
                pool_pre_ping=DB_SETTINGS["pool_pre_ping"],
                pool_recycle=DB_SETTINGS["pool_recycle"],
                echo=DB_SETTINGS["echo"]
            )
        
        return self.engines[db_name]
    
    def check_tables_exist(self, db_name):
        """Verifica se as tabelas existem em um banco específico"""
        try:
            engine = self.get_engine(db_name)
            
            with engine.connect() as conn:
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
            logger.error(f"Erro ao verificar tabelas no banco {db_name}: {e}")
            return False
    
    def create_tables(self, db_name):
        """Cria tabelas em um banco específico"""
        try:
            engine = self.get_engine(db_name)
            
            # Importa os modelos corretos para cada banco
            if db_name == 'financeiro':
                from infrastructure.database.connections.financeiro_connection import Base
                # Importa todos os modelos financeiros
                import core.models.financeiro.custos
                import core.models.financeiro.contabil
                import core.models.financeiro.vendas
                import core.models.financeiro.kpis
            elif db_name == 'industrial':
                from infrastructure.database.connections.industrial_connection import Base
                # Importa todos os modelos industriais
                import core.models.industrial.cadastros
                import core.models.industrial.producao
                import core.models.industrial.equipamentos
                import core.models.industrial.qualidade
            elif db_name == 'dw':
                from infrastructure.database.connections.dw_connection import Base
                # Importa todos os modelos da DW
                import core.models.dw.dimensoes
                import core.models.dw.fatos
                import core.models.dw.agregados
            
            Base.metadata.create_all(bind=engine)
            logger.info(f"Tabelas criadas/atualizadas com sucesso no banco {db_name}!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar tabelas no banco {db_name}: {e}")
            return False
    
    def ensure_all_databases_ready(self):
        """Garante que todos os bancos e tabelas estão prontos"""
        logger.info("Verificando todos os bancos de dados...")
        
        for db_name, config in self.configs.items():
            logger.info(f"Verificando banco {db_name}...")
            
            # 1. Verifica se o banco existe
            if not self.check_database_exists(config):
                logger.info(f"Banco {db_name} não encontrado. Criando...")
                if not self.create_database(config):
                    logger.error(f"Falha ao criar banco {db_name}!")
                    return False
            
            # 2. Verifica se as tabelas existem
            if not self.check_tables_exist(db_name):
                logger.info(f"Tabelas não encontradas no banco {db_name}. Criando...")
                if not self.create_tables(db_name):
                    logger.error(f"Falha ao criar tabelas no banco {db_name}!")
                    return False
            else:
                logger.info(f"Tabelas encontradas no banco {db_name}. Atualizando...")
                if not self.create_tables(db_name):
                    logger.error(f"Falha ao atualizar tabelas no banco {db_name}!")
                    return False
        
        logger.info("Todos os bancos de dados estão prontos!")
        return True

# Instância global do gerenciador
multi_db_manager = MultiDatabaseManager()
