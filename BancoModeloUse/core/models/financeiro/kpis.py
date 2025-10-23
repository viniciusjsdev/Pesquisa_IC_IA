# core/models/financeiro/kpis.py
"""
Modelos de KPIs financeiros
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL
from infrastructure.database.connections.financeiro_connection import Base

class KPIGerencial(Base):
    __tablename__ = "kpis_gerenciais"
    kpi_id = Column(Integer, primary_key=True, index=True)
    nome_kpi = Column(String)
    valor_kpi = Column(DECIMAL)
    data_referencia = Column(Date)
