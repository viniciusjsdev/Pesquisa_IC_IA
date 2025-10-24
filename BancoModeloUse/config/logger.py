"""
Sistema de logging centralizado
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional

# Configuração global de logging
_logging_configured = False


def setup_logging(config_path: Optional[str] = None) -> None:
    """
    Configura o sistema de logging
    
    Args:
        config_path: Caminho para arquivo de configuração JSON
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    # Caminho padrão para configuração
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "..", "logging_config.json")
    
    # Verificar se arquivo de configuração existe
    if not os.path.exists(config_path):
        # Configuração básica se arquivo não existir
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        _logging_configured = True
        return
    
    try:
        # Carregar configuração JSON
        logging.config.dictConfig(load_logging_config(config_path))
        
        # Criar diretório de logs se não existir
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        _logging_configured = True
        
    except Exception as e:
        # Fallback para configuração básica
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        _logging_configured = True


def load_logging_config(config_path: str) -> dict:
    """
    Carrega configuração de logging do arquivo JSON
    
    Args:
        config_path: Caminho para arquivo de configuração
        
    Returns:
        Dict com configuração de logging
    """
    import json
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_logger(name: str) -> logging.Logger:
    """
    Obtém logger para um módulo específico
    
    Args:
        name: Nome do módulo
        
    Returns:
        Logger configurado
    """
    if not _logging_configured:
        setup_logging()
    
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """
    Define nível de log global
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.getLogger().setLevel(getattr(logging, level.upper()))
