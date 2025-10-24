"""
Middleware para rastreamento de requests
"""

import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from config.logger import get_logger
from core.context_vars import set_trace_id, set_user_id, set_session_id, get_trace_id

logger = get_logger(__name__)


class TraceIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware para geração e propagação de Trace ID
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processa request e adiciona Trace ID
        
        Args:
            request: Request HTTP
            call_next: Próximo middleware/handler
            
        Returns:
            Response HTTP
        """
        # Obter ou gerar trace_id
        trace_id = request.headers.get("X-Trace-ID")
        if not trace_id:
            trace_id = str(uuid.uuid4())
            logger.debug(f"Gerado novo trace_id: {trace_id}")
        else:
            logger.debug(f"Propagado trace_id: {trace_id}")
        
        # Obter user_id do header (se fornecido)
        user_id = request.headers.get("X-User-ID")
        
        # Obter session_id do header (se fornecido)
        session_id = request.headers.get("X-Session-ID")
        
        # Definir context variables
        set_trace_id(trace_id)
        if user_id:
            set_user_id(user_id)
        if session_id:
            set_session_id(session_id)
        
        # Log do request
        logger.info(f"Request iniciado - Trace ID: {trace_id}, User ID: {user_id}, Session ID: {session_id}")
        
        try:
            # Processar request
            response = await call_next(request)
            
            # Adicionar trace_id no header da response
            response.headers["X-Trace-ID"] = trace_id
            
            # Log da response
            logger.info(f"Request finalizado - Trace ID: {trace_id}, Status: {response.status_code}")
            
            return response
            
        except Exception as e:
            # Log de erro
            logger.error(f"Erro no request - Trace ID: {trace_id}, Erro: {str(e)}")
            raise
