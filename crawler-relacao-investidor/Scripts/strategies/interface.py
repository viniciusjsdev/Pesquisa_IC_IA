# Scripts/strategies/interface.py
from abc import ABC, abstractmethod
from typing import List

class RaspagemStrategy(ABC):
    """Interface para todas as estratégias de raspagem de dados."""
    
    @abstractmethod
    def baixar_relatorios(self) -> List:
        """Realiza a raspagem e retorna uma lista de RelatorioFinanceiro."""
        pass
    
    @property
    @abstractmethod
    def empresa(self) -> str:
        """Retorna o nome da empresa."""
        pass