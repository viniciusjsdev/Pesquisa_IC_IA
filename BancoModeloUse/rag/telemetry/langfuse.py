"""
Integração com Langfuse para telemetria e observabilidade
"""

import os
from typing import Optional
from langfuse import Langfuse
from langfuse.callback import CallbackHandler
from config.logger import get_logger

logger = get_logger(__name__)

# Instância global do Langfuse
lf: Optional[Langfuse] = None
langfuse_handler: Optional[CallbackHandler] = None


def init_langfuse() -> None:
    """
    Inicializa Langfuse com configurações do ambiente
    
    Variáveis de ambiente necessárias:
    - LANGFUSE_PUBLIC_KEY
    - LANGFUSE_SECRET_KEY  
    - LANGFUSE_HOST (opcional, padrão: https://cloud.langfuse.com)
    """
    global lf, langfuse_handler
    
    try:
        # Verificar se variáveis de ambiente estão configuradas
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        if not public_key or not secret_key:
            logger.warning("Variáveis de ambiente Langfuse não configuradas. Telemetria desabilitada.")
            return
        
        # Inicializar Langfuse
        lf = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        
        # Criar callback handler
        langfuse_handler = CallbackHandler(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        
        logger.info("Langfuse inicializado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar Langfuse: {str(e)}")
        lf = None
        langfuse_handler = None


def get_langfuse() -> Optional[Langfuse]:
    """
    Obtém instância do Langfuse
    
    Returns:
        Instância do Langfuse ou None se não inicializado
    """
    return lf


def get_langfuse_handler() -> Optional[CallbackHandler]:
    """
    Obtém callback handler do Langfuse
    
    Returns:
        CallbackHandler ou None se não inicializado
    """
    return langfuse_handler


def is_langfuse_enabled() -> bool:
    """
    Verifica se Langfuse está habilitado
    
    Returns:
        True se Langfuse está configurado e funcionando
    """
    return lf is not None and langfuse_handler is not None


# Inicializar automaticamente
init_langfuse()
