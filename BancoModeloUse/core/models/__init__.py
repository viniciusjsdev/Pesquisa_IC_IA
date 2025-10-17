# models/__init__.py
"""
Módulo de modelos do banco de dados
"""

# Importa todos os modelos industriais
from .industria import *

# Importa todos os modelos financeiros
from .financeiro import (
    CustoPadrao, CustoIndiretoRateio, MaterialCustoHistorico, CustoMaoObraHistorico,
    CustoOperacionalVariavel, ContaContabil, LancamentoFinanceiro, Venda, Orcamento,
    KPIGerencial, CategoriaContabilPadrao, SubcategoriaContabilPadrao, ContaContabilDetalhe
)

__all__ = [
    # Modelos industriais (importados com *)
    # Modelos financeiros
    "CustoPadrao",
    "CustoIndiretoRateio", 
    "MaterialCustoHistorico",
    "CustoMaoObraHistorico",
    "CustoOperacionalVariavel",
    "ContaContabil",
    "LancamentoFinanceiro",
    "Venda",
    "Orcamento",
    "KPIGerencial",
    "CategoriaContabilPadrao",
    "SubcategoriaContabilPadrao",
    "ContaContabilDetalhe"
]
