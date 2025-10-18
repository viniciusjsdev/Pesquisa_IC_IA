# core/models/financeiro/vendas.py
"""
Modelos de vendas financeiros
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from . import FinanceiroBase

class Venda(FinanceiroBase):
    __tablename__ = "vendas"
    venda_id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer) # FK para Produto da tabela industrial
    quantidade_vendida = Column(Integer)
    preco_unitario_venda = Column(DECIMAL)
    data_venda = Column(Date)
    cliente_id = Column(Integer) # FK para Cliente (se existir na industrial, ou criar aqui)

class Orcamento(FinanceiroBase):
    __tablename__ = "orcamentos"
    orcamento_id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas_contabeis.conta_id"))
    valor_orcado = Column(DECIMAL)
    periodo = Column(Date)

    conta = relationship("ContaContabil")
