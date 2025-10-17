# infrastructure/database/session.py
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from infrastructure.database.connection import DATABASE_URL

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from infrastructure.config.database_config import DB_SETTINGS

# Cria engine com configurações do banco
engine = create_engine(
    DATABASE_URL,
    pool_size=DB_SETTINGS["pool_size"],
    max_overflow=DB_SETTINGS["max_overflow"],
    pool_pre_ping=DB_SETTINGS["pool_pre_ping"],
    pool_recycle=DB_SETTINGS["pool_recycle"],
    echo=DB_SETTINGS["echo"]
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
