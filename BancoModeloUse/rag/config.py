# rag/config.py
"""
Configurações do sistema RAG
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class RAGConfig:
    """Configurações do sistema RAG"""
    
    # Configurações de LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    
    # Configurações de embedding
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-ada-002"
    
    # Configurações de cache
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hora
    
    # Configurações de rate limiting
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 60
    
    # Configurações de logging
    log_level: str = "INFO"
    log_requests: bool = True
    log_responses: bool = False
    
    # Configurações de telemetria
    telemetry_enabled: bool = True
    langfuse_enabled: bool = False
    
    # Configurações de agentes
    max_agent_iterations: int = 5
    agent_timeout: int = 30  # segundos
    
    # Configurações de tools
    tool_timeout: int = 10  # segundos
    max_tool_retries: int = 3
    
    @classmethod
    def from_env(cls) -> 'RAGConfig':
        """Cria configuração a partir de variáveis de ambiente"""
        return cls(
            llm_provider=os.getenv("RAG_LLM_PROVIDER", "openai"),
            llm_model=os.getenv("RAG_LLM_MODEL", "gpt-4"),
            llm_temperature=float(os.getenv("RAG_LLM_TEMPERATURE", "0.1")),
            llm_max_tokens=int(os.getenv("RAG_LLM_MAX_TOKENS", "4000")),
            embedding_provider=os.getenv("RAG_EMBEDDING_PROVIDER", "openai"),
            embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-ada-002"),
            cache_enabled=os.getenv("RAG_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv("RAG_CACHE_TTL", "3600")),
            rate_limit_enabled=os.getenv("RAG_RATE_LIMIT_ENABLED", "true").lower() == "true",
            max_requests_per_minute=int(os.getenv("RAG_MAX_REQUESTS_PER_MINUTE", "60")),
            log_level=os.getenv("RAG_LOG_LEVEL", "INFO"),
            log_requests=os.getenv("RAG_LOG_REQUESTS", "true").lower() == "true",
            log_responses=os.getenv("RAG_LOG_RESPONSES", "false").lower() == "true",
            telemetry_enabled=os.getenv("RAG_TELEMETRY_ENABLED", "true").lower() == "true",
            langfuse_enabled=os.getenv("RAG_LANGFUSE_ENABLED", "false").lower() == "true",
            max_agent_iterations=int(os.getenv("RAG_MAX_AGENT_ITERATIONS", "5")),
            agent_timeout=int(os.getenv("RAG_AGENT_TIMEOUT", "30")),
            tool_timeout=int(os.getenv("RAG_TOOL_TIMEOUT", "10")),
            max_tool_retries=int(os.getenv("RAG_MAX_TOOL_RETRIES", "3"))
        )

# Instância global de configuração
config = RAGConfig.from_env()

# Configurações específicas por domínio
DOMAIN_CONFIGS = {
    "financeiro": {
        "max_results": 100,
        "timeout": 15,
        "cache_ttl": 1800  # 30 minutos
    },
    "industrial": {
        "max_results": 100,
        "timeout": 15,
        "cache_ttl": 1800  # 30 minutos
    },
    "integracao": {
        "max_results": 50,
        "timeout": 30,
        "cache_ttl": 3600  # 1 hora
    }
}

# Palavras-chave para classificação de domínios
DOMAIN_KEYWORDS = {
    "financeiro": [
        "venda", "vendas", "receita", "lucro", "custo", "custos", "margem", "roi",
        "financeiro", "contábil", "orçamento", "lançamento", "conta", "cliente",
        "faturamento", "despesa", "investimento", "retorno", "lucratividade"
    ],
    "industrial": [
        "produção", "produto", "máquina", "equipamento", "operação", "ordem",
        "industrial", "qualidade", "defeito", "parada", "eficiencia", "oee",
        "disponibilidade", "performance", "energia", "consumo", "lote", "inspeção"
    ],
    "integracao": [
        "correlação", "integração", "dashboard", "kpi", "indicador", "análise",
        "comparação", "tendência", "anomalia", "alerta", "executivo", "consolidado"
    ]
}

def get_domain_config(domain: str) -> Dict[str, Any]:
    """Retorna configuração específica de um domínio"""
    return DOMAIN_CONFIGS.get(domain, {})

def get_domain_keywords(domain: str) -> list:
    """Retorna palavras-chave de um domínio"""
    return DOMAIN_KEYWORDS.get(domain, [])

def classify_domain(text: str) -> str:
    """Classifica o domínio baseado no texto"""
    text_lower = text.lower()
    
    domain_scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        domain_scores[domain] = score
    
    if not any(domain_scores.values()):
        return "integracao"  # Default para integração
    
    return max(domain_scores, key=domain_scores.get)
