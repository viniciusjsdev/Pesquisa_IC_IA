# core/models/industrial/__init__.py
"""
Modelos do banco industrial
"""
from sqlalchemy.ext.declarative import declarative_base

# Base específica para modelos industriais
IndustrialBase = declarative_base()

# Importa todos os modelos industriais
from .cadastros import *
from .producao import *
from .equipamentos import *
from .qualidade import *

__all__ = [
    # Modelos de cadastros
    "Produto",
    "Material", 
    "Maquina",
    "Fornecedor",
    
    # Modelos de produção
    "OrdemProducao",
    "RoteiroProducao",
    "OperacaoRoteiro",
    "RegistroOperacao",
    "ParadaMaquina",
    "ConsumoMaterial",
    "LoteMaterial",
    "LoteProducao",
    
    # Modelos de equipamentos
    "Equipamento",
    "ProcessoIndustrial",
    
    # Modelos de qualidade
    "ControleQualidade",
    "Defeito",
    "RegistroDefeito"
]
