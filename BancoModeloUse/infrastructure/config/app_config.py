# config/app_config.py
"""
Configurações da aplicação
"""

# Configurações do servidor
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port_range": (8000, 8010),  # Range de portas para tentar
    "reload": True,
    "title": "V&N Datamind - Financeiro",
    "description": "Sistema de gestão financeira integrado com dados industriais",
    "version": "1.0.0"
}

# Configurações de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "file": None  # None para apenas console, ou caminho para arquivo
}

# Configurações de CORS
CORS_CONFIG = {
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"]
}

# Configurações de documentação
DOCS_CONFIG = {
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "openapi_url": "/openapi.json"
}
