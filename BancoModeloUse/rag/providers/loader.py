"""
Factory para carregar modelos LLM com cache
"""

from functools import lru_cache
from typing import Dict, Any
import yaml
import os
from config.logger import get_logger

from .base import LLMClient, Provider, ModelConfig

logger = get_logger(__name__)


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Carrega configuração YAML"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar configuração YAML: {str(e)}")
        return {}


def get_model_config(model_alias: str) -> ModelConfig:
    """
    Obtém configuração do modelo por alias
    
    Args:
        model_alias: Nome do modelo na configuração
        
    Returns:
        Configuração do modelo
    """
    # Carregar configuração
    config_path = os.path.join("config", "modelos.yaml")
    config = load_yaml_config(config_path)
    
    if model_alias not in config:
        raise ValueError(f"Modelo '{model_alias}' não encontrado na configuração")
    
    model_config = config[model_alias]
    return ModelConfig(**model_config)


@lru_cache(maxsize=None)
def get_llm(model_alias: str) -> LLMClient:
    """
    Factory para obter cliente LLM com cache
    
    Args:
        model_alias: Nome do modelo na configuração
        
    Returns:
        Cliente LLM configurado
    """
    try:
        logger.info(f"Carregando modelo: {model_alias}")
        
        # Obter configuração
        cfg = get_model_config(model_alias)
        
        # Obter provider
        if cfg.provider not in Provider.REGISTRY:
            raise ValueError(f"Provider '{cfg.provider}' não encontrado")
        
        provider_cls = Provider.REGISTRY[cfg.provider]
        
        # Construir cliente
        client = provider_cls.build_client(cfg)
        
        logger.info(f"Modelo '{model_alias}' carregado com sucesso")
        return client
        
    except Exception as e:
        logger.error(f"Erro ao carregar modelo '{model_alias}': {str(e)}")
        raise


def clear_llm_cache():
    """Limpa cache de modelos LLM"""
    get_llm.cache_clear()
    logger.info("Cache de modelos LLM limpo")
