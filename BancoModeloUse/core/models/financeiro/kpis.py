# core/models/financeiro/kpis.py
"""
Modelos de KPIs financeiros
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL
from . import FinanceiroBase

class KPIGerencial(FinanceiroBase):
    __tablename__ = "kpis_gerenciais"
    kpi_id = Column(Integer, primary_key=True, index=True)
    nome_kpi = Column(String)
    valor_kpi = Column(DECIMAL)
    data_referencia = Column(Date)
