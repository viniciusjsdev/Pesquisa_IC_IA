# models/__init__.py
"""
Módulo de modelos do banco de dados
"""

# Importa todos os modelos industriais
from .industrial.cadastros import *
from .industrial.producao import *
from .industrial.equipamentos import *
from .industrial.qualidade import *

# Importa todos os modelos financeiros
from .financeiro.custos import *
from .financeiro.contabil import *
from .financeiro.vendas import *
from .financeiro.kpis import *

# Importa todos os modelos da DW
from .dw.dimensoes import *
from .dw.fatos import *
from .dw.agregados import *

__all__ = [
    # Modelos industriais
    "Produto", "Material", "Maquina", "Fornecedor",
    "OrdemProducao", "RoteiroProducao", "OperacaoRoteiro", "RegistroOperacao", "ParadaMaquina",
    "ConsumoMaterial", "LoteMaterial", "LoteProducao",
    "Equipamento", "ProcessoIndustrial",
    "ControleQualidade", "Defeito", "RegistroDefeito",
    
    # Modelos financeiros
    "CustoPadrao", "CustoIndiretoRateio", "MaterialCustoHistorico", "CustoMaoObraHistorico",
    "CustoOperacionalVariavel", "CustoProducao", "ResultadoFinanceiro", "AnaliseFinanceira",
    "ContaContabil", "LancamentoFinanceiro", "CategoriaContabilPadrao", "SubcategoriaContabilPadrao", "ContaContabilDetalhe",
    "Venda", "Orcamento",
    "KPIGerencial",
    
    # Modelos da Data Warehouse
    "DimProduto", "DimTempo", "DimMaquina", "DimCliente", "DimFornecedor",
    "FatoVendas", "FatoProducao", "FatoCustos", "FatoQualidade", "FatoEnergia",
    "KPIFinanceiro", "KPIIndustrial", "KPIIntegrado", "DashboardExecutivo"
]
