# core/models/financeiro/__init__.py
"""
Modelos do banco financeiro
"""
from sqlalchemy.ext.declarative import declarative_base

# Base específica para modelos financeiros
FinanceiroBase = declarative_base()

# Importa todos os modelos financeiros
from .custos import *
from .contabil import *
from .vendas import *
from .kpis import *

__all__ = [
    # Modelos de custos
    "CustoPadrao",
    "CustoIndiretoRateio", 
    "MaterialCustoHistorico",
    "CustoMaoObraHistorico",
    "CustoOperacionalVariavel",
    "CustoProducao",
    "ResultadoFinanceiro",
    "AnaliseFinanceira",
    
    # Modelos contábeis
    "ContaContabil",
    "LancamentoFinanceiro",
    "CategoriaContabilPadrao",
    "SubcategoriaContabilPadrao",
    "ContaContabilDetalhe",
    
    # Modelos de vendas
    "Venda",
    "Orcamento",
    
    # Modelos de KPIs
    "KPIGerencial"
]
