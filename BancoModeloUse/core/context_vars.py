"""
Context variables para rastreamento de requests
"""

import contextvars
from typing import Optional

# Context variables para rastreamento
trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('trace_id', default=None)
user_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('user_id', default=None)
session_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('session_id', default=None)


def get_trace_id() -> Optional[str]:
    """
    Obtém trace_id do contexto atual
    
    Returns:
        Trace ID ou None se não definido
    """
    return trace_id_var.get()


def set_trace_id(trace_id: str) -> None:
    """
    Define trace_id no contexto atual
    
    Args:
        trace_id: ID único para rastreamento
    """
    trace_id_var.set(trace_id)


def get_user_id() -> Optional[str]:
    """
    Obtém user_id do contexto atual
    
    Returns:
        User ID ou None se não definido
    """
    return user_id_var.get()


def set_user_id(user_id: str) -> None:
    """
    Define user_id no contexto atual
    
    Args:
        user_id: ID do usuário
    """
    user_id_var.set(user_id)


def get_session_id() -> Optional[str]:
    """
    Obtém session_id do contexto atual
    
    Returns:
        Session ID ou None se não definido
    """
    return session_id_var.get()


def set_session_id(session_id: str) -> None:
    """
    Define session_id no contexto atual
    
    Args:
        session_id: ID da sessão
    """
    session_id_var.set(session_id)


def clear_context() -> None:
    """
    Limpa todas as context variables
    """
    trace_id_var.set(None)
    user_id_var.set(None)
    session_id_var.set(None)
