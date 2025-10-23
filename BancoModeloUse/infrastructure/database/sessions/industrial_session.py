# infrastructure/database/sessions/industrial_session.py
"""
Sessões para banco industrial
"""
from sqlalchemy.orm import Session
from infrastructure.database.connections import industrial_connection

def get_industrial_db():
    """Dependency injection para sessão do banco industrial"""
    db = industrial_connection.get_session()
    try:
        yield db
    finally:
        db.close()

def get_industrial_engine():
    """Retorna engine do banco industrial"""
    return industrial_connection.get_engine()

def test_industrial_connection():
    """Testa conexão com banco industrial"""
    return industrial_connection.test_connection()
