# core/models/financeiro/contabil.py
"""
Modelos contábeis financeiros
"""
from sqlalchemy import Column, Integer, String, Text, Date, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from . import FinanceiroBase

class ContaContabil(FinanceiroBase):
    __tablename__ = "contas_contabeis"
    conta_id = Column(Integer, primary_key=True, index=True)
    numero_conta = Column(String)
    nome_conta = Column(String)
    tipo_conta = Column(String)

class LancamentoFinanceiro(FinanceiroBase):
    __tablename__ = "lancamentos_financeiros"
    lancamento_id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas_contabeis.conta_id"))
    data_lancamento = Column(Date)
    valor = Column(DECIMAL)
    descricao = Column(Text)

    conta = relationship("ContaContabil")

class CategoriaContabilPadrao(FinanceiroBase):
    __tablename__ = "categorias_contabeis_padrao"
    categoria_id = Column(Integer, primary_key=True, index=True)
    nome_categoria = Column(String, unique=True, nullable=False) # Ex: Ativo, Passivo, Receita, Despesa
    tipo_categoria = Column(String) # Ex: Balanço Patrimonial, Demonstração de Resultado

class SubcategoriaContabilPadrao(FinanceiroBase):
    __tablename__ = "subcategorias_contabeis_padrao"
    subcategoria_id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias_contabeis_padrao.categoria_id"))
    nome_subcategoria = Column(String, nullable=False) # Ex: Caixa e Equivalentes, Contas a Receber, Estoques

    categoria = relationship("CategoriaContabilPadrao")

class ContaContabilDetalhe(FinanceiroBase):
    __tablename__ = "contas_contabeis_detalhe"
    conta_detalhe_id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas_contabeis.conta_id"))
    subcategoria_id = Column(Integer, ForeignKey("subcategorias_contabeis_padrao.subcategoria_id"))
    data_associacao = Column(Date)

    conta = relationship("ContaContabil")
    subcategoria = relationship("SubcategoriaContabilPadrao")
