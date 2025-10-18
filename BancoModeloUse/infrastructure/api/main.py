import sys
import os
from fastapi import FastAPI
from infrastructure.database.session import engine, Base
from core.models import *  # Importa todos os modelos
from infrastructure.api.routers.financeiro import router as financeiro_router
from infrastructure.api.rag import rag_router, etl_router
from infrastructure.database.manager import db_manager
import logging

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from infrastructure.config.app_config import SERVER_CONFIG, LOGGING_CONFIG, DOCS_CONFIG

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=SERVER_CONFIG["title"],
    description=SERVER_CONFIG["description"],
    version=SERVER_CONFIG["version"],
    docs_url=DOCS_CONFIG["docs_url"],
    redoc_url=DOCS_CONFIG["redoc_url"],
    openapi_url=DOCS_CONFIG["openapi_url"]
)

# Função para criar tabelas (mantida para compatibilidade)
def create_tables():
    """Cria todas as tabelas no banco de dados"""
    return db_manager.create_tables()

# Função para atualizar tabelas
def update_tables():
    """Atualiza todas as tabelas no banco de dados"""
    return db_manager.update_tables()

# Verificação automática do banco na inicialização
@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    logger.info("Iniciando aplicação...")
    
    # Garante que o banco e tabelas estão prontos
    if db_manager.ensure_database_ready():
        logger.info("Aplicação iniciada com sucesso!")
    else:
        logger.error("Falha na inicialização do banco de dados!")
        raise Exception("Não foi possível inicializar o banco de dados")

app.include_router(financeiro_router)
app.include_router(rag_router)
app.include_router(etl_router)

@app.get("/")
def root():
    return {
        "service": "descomplica hub - sistema integrado", 
        "modules": ["financeiro", "rag", "etl"],
        "description": "Sistema integrado financeiro-industrial com RAG e ETL"
    }

@app.post("/create-tables")
def create_tables_endpoint():
    """Endpoint para criar todas as tabelas do banco de dados"""
    try:
        if create_tables():
            return {"message": "Tabelas criadas com sucesso!", "status": "success"}
        else:
            return {"message": "Falha ao criar tabelas", "status": "error"}
    except Exception as e:
        return {"message": f"Erro ao criar tabelas: {str(e)}", "status": "error"}

@app.post("/update-tables")
def update_tables_endpoint():
    """Endpoint para atualizar todas as tabelas do banco de dados"""
    try:
        if update_tables():
            return {"message": "Tabelas atualizadas com sucesso!", "status": "success"}
        else:
            return {"message": "Falha ao atualizar tabelas", "status": "error"}
    except Exception as e:
        return {"message": f"Erro ao atualizar tabelas: {str(e)}", "status": "error"}

@app.get("/database-status")
def database_status():
    """Endpoint para verificar o status do banco de dados"""
    try:
        db_exists = db_manager.check_database_exists()
        tables_exist = db_manager.check_tables_exist()
        
        return {
            "database_exists": db_exists,
            "tables_exist": tables_exist,
            "status": "ready" if db_exists and tables_exist else "not_ready",
            "message": "Banco e tabelas prontos" if db_exists and tables_exist else "Banco ou tabelas não encontrados"
        }
    except Exception as e:
        return {"message": f"Erro ao verificar status: {str(e)}", "status": "error"}

