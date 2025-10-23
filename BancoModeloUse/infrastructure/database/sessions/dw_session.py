# infrastructure/database/sessions/dw_session.py
"""
Sessões para Data Warehouse
"""
from sqlalchemy.orm import Session
from infrastructure.database.connections import dw_connection

def get_dw_db():
    """Dependency injection para sessão da DW"""
    db = dw_connection.get_session()
    try:
        yield db
    finally:
        db.close()

def get_dw_engine():
    """Retorna engine da DW"""
    return dw_connection.get_engine()

def test_dw_connection():
    """Testa conexão com DW"""
    return dw_connection.test_connection()
