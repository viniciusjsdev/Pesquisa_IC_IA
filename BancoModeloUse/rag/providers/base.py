from abc import ABC, abstractmethod
from langchain_core.tools import BaseTool
from typing import Any, Dict, Optional


class LLMClient(ABC):
    """Interface abstrata para clientes LLM"""
    
    @abstractmethod
    def ask(self, system_prompt: str, user_message: str,
            temperature: float, max_tokens: int, tools: list[BaseTool]) -> str:
        """
        Executa consulta ao modelo LLM
        
        Args:
            system_prompt: Prompt do sistema
            user_message: Mensagem do usuário
            temperature: Temperatura para geração
            max_tokens: Máximo de tokens
            tools: Lista de ferramentas disponíveis
            
        Returns:
            Resposta do modelo
        """
        pass


class Provider(ABC):
    """Classe base para provedores de LLM com auto-registro"""
    REGISTRY: dict[str, type["Provider"]] = {}

    provider_name: str

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "provider_name"):
            raise TypeError("Subclasse Provider deve definir provider_name")
        Provider.REGISTRY[cls.provider_name] = cls

    @classmethod
    @abstractmethod
    def build_client(cls, cfg: "ModelConfig") -> LLMClient:
        """
        Constrói cliente LLM a partir da configuração
        
        Args:
            cfg: Configuração do modelo
            
        Returns:
            Cliente LLM configurado
        """
        pass


class ModelConfig:
    """Configuração de modelo"""
    
    def __init__(self, **kwargs):
        self.provider = kwargs.get("provider")
        self.model_name = kwargs.get("model_name")
        self.model_path = kwargs.get("model_path")
        self.temperature = kwargs.get("temperature", 0.2)
        self.max_tokens = kwargs.get("max_tokens", 2000)
        self.api_key = kwargs.get("api_key")
        self.base_url = kwargs.get("base_url")
        self.extra = kwargs.get("extra", {})
