# rag/api/__init__.py
"""
API RAG - Endpoints para o sistema RAG
"""

from .rag_router import router as rag_router

__all__ = [
    "rag_router"
]
