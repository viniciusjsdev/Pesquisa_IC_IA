import sys
import os
from fastapi import FastAPI
from infrastructure.database.session import engine, Base
from core.models import *  # Importa todos os modelos
from infrastructure.api.routers.financeiro import router as financeiro_router
# from rag.api import rag_router  # Comentado temporariamente devido a dependência langfuse
from infrastructure.database.multi_db_manager import multi_db_manager
from infrastructure.database.manager import db_manager
import logging

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from infrastructure.config.app_config import SERVER_CONFIG, LOGGING_CONFIG, DOCS_CONFIG

# Importar componentes do novo sistema multi-agente
from rag.graph import build_graph
from core.middleware import TraceIdMiddleware
from core.context_vars import get_trace_id, get_user_id, get_session_id
from config.logger import setup_logging, get_logger
# from telemetry.langfuse import is_langfuse_enabled, get_langfuse_handler  # Comentado temporariamente

# Configurar logging centralizado
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=SERVER_CONFIG["title"],
    description=SERVER_CONFIG["description"],
    version=SERVER_CONFIG["version"],
    docs_url=DOCS_CONFIG["docs_url"],
    redoc_url=DOCS_CONFIG["redoc_url"],
    openapi_url=DOCS_CONFIG["openapi_url"]
)

# Adicionar middleware de Trace ID
app.add_middleware(TraceIdMiddleware)

# Variável global para o graph
graph_ready = False
graph = None

# Função para criar tabelas (mantida para compatibilidade)
def create_tables():
    """Cria todas as tabelas no banco de dados"""
    return db_manager.create_tables()

# Função para atualizar tabelas
def update_tables():
    """Atualiza todas as tabelas no banco de dados"""
    return multi_db_manager.ensure_all_databases_ready()

# Verificação automática do banco na inicialização
@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    global graph_ready, graph
    
    logger.info("Iniciando aplicação...")
    
    # Garante que todos os bancos e tabelas estão prontos
    if multi_db_manager.ensure_all_databases_ready():
        logger.info("Bancos de dados inicializados com sucesso!")
    else:
        logger.error("Falha na inicialização dos bancos de dados!")
        raise Exception("Não foi possível inicializar os bancos de dados")
    
    # Inicializar graph multi-agente
    try:
        logger.info("Inicializando graph multi-agente...")
        graph = build_graph()
        graph_ready = True
        logger.info("Graph multi-agente inicializado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao inicializar graph: {str(e)}")
        raise Exception(f"Falha na inicialização do graph: {str(e)}")
    
    # Verificar telemetria
    # if is_langfuse_enabled():
    #     logger.info("Telemetria Langfuse habilitada")
    # else:
    #     logger.warning("Telemetria Langfuse desabilitada")
    logger.info("Telemetria temporariamente desabilitada")
    
    logger.info("Aplicação iniciada com sucesso!")

app.include_router(financeiro_router)
# app.include_router(rag_router)  # Comentado temporariamente
# app.include_router(etl_router)  # ETL removido temporariamente

@app.get("/")
def root():
    return {
        "service": "descomplica hub - sistema integrado", 
        "modules": ["financeiro", "rag", "multi-agent"],
        "description": "Sistema integrado financeiro-industrial com RAG Multi-Agente",
        "version": SERVER_CONFIG["version"]
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if graph_ready else "not_ready",
        "graph_ready": graph_ready,
        "langfuse_enabled": False,  # Temporariamente desabilitado
        "trace_id": get_trace_id(),
        "user_id": get_user_id(),
        "session_id": get_session_id()
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

