# infrastructure/database/sessions/financeiro_session.py
"""
Sessões para banco financeiro
"""
from sqlalchemy.orm import Session
from infrastructure.database.connections import financeiro_connection

def get_financeiro_db():
    """Dependency injection para sessão do banco financeiro"""
    db = financeiro_connection.get_session()
    try:
        yield db
    finally:
        db.close()

def get_financeiro_engine():
    """Retorna engine do banco financeiro"""
    return financeiro_connection.get_engine()

def test_financeiro_connection():
    """Testa conexão com banco financeiro"""
    return financeiro_connection.test_connection()
