from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel


class ToolInput(BaseModel):
    """Modelo base para entrada de tools"""
    pass


class ToolResult(BaseModel):
    """Modelo base para resultado de tools"""
    data: Any
    meta: Optional[dict] = None


class BaseTool(ABC):
    """Classe base abstrata para todas as tools"""
    
    name: str
    description: str

    @abstractmethod
    def run(self, payload: ToolInput) -> ToolResult:
        """
        Executa a tool
        
        Args:
            payload: Dados de entrada validados
            
        Returns:
            Resultado da execução
        """
        pass
