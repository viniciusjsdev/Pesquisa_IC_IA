from enum import Enum


class Agentes(str, Enum):
    """Enum de agentes disponíveis no sistema RAG"""
    
    # Agentes de orquestração
    ORQUESTRADOR = "orquestrador"
    PREPROCESSADOR = "preprocessador"
    VALIDADOR_GLOBAL = "validador_global"
    
    # Agentes especializados
    FINANCEIRO = "agente_financeiro"
    INDUSTRIAL = "agente_industrial"
    INTEGRACAO = "agente_integracao"
    
    # Agente finalizador
    FINALIZADOR = "agente_finalizador"
    
    @classmethod
    def from_key(cls, key: str) -> "Agentes | None":
        """Converte string para enum, retorna None se não encontrado"""
        try:
            return cls(key)
        except ValueError:
            return None
    
    @classmethod
    def get_all_agents(cls) -> list[str]:
        """Retorna lista de todos os agentes"""
        return [agent.value for agent in cls]
    
    @classmethod
    def get_specialized_agents(cls) -> list[str]:
        """Retorna lista de agentes especializados (não orquestração)"""
        return [
            cls.FINANCEIRO.value,
            cls.INDUSTRIAL.value,
            cls.INTEGRACAO.value,
            cls.FINALIZADOR.value
        ]
    
    @classmethod
    def get_orchestration_agents(cls) -> list[str]:
        """Retorna lista de agentes de orquestração"""
        return [
            cls.ORQUESTRADOR.value,
            cls.PREPROCESSADOR.value,
            cls.VALIDADOR_GLOBAL.value
        ]
