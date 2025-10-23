# core/models/dw/__init__.py
"""
Modelos da Data Warehouse
"""
from sqlalchemy.ext.declarative import declarative_base

# Base específica para modelos da DW
DWBase = declarative_base()

# Importa todos os modelos da DW
from .dimensoes import *
from .fatos import *
from .agregados import *

__all__ = [
    # Dimensões
    "DimProduto",
    "DimTempo", 
    "DimMaquina",
    "DimCliente",
    "DimFornecedor",
    
    # Fatos
    "FatoVendas",
    "FatoProducao",
    "FatoCustos",
    "FatoQualidade",
    "FatoEnergia",
    
    # Agregados/KPIs
    "KPIFinanceiro",
    "KPIIndustrial", 
    "KPIIntegrado",
    "DashboardExecutivo"
]
