# core/models/industrial/equipamentos.py
"""
Modelos de equipamentos industriais
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from infrastructure.database.connections.industrial_connection import Base

class Equipamento(Base):
    __tablename__ = "equipamentos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    disponibilidade = Column(Float, default=0.0)
    performance = Column(Float, default=0.0)
    qualidade = Column(Float, default=0.0)
    oee = Column(Float, default=0.0)  # Eficiência geral
    taxa_producao = Column(Float, default=0.0)
    capacidade_producao = Column(Float, default=0.0)
    eficiencia_linha = Column(Float, default=0.0)
    produtividade_mao_obra = Column(Float, default=0.0)
    data_registro = Column(DateTime, default=datetime.utcnow)

class ProcessoIndustrial(Base):
    __tablename__ = "processos_industriais"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    area1 = Column(Float, default=0.0)  # Para cálculo de vazão
    velocidade1 = Column(Float, default=0.0)
    area2 = Column(Float, default=0.0)
    velocidade2 = Column(Float, default=0.0)
    massa = Column(Float, default=0.0)
    calor_especifico = Column(Float, default=0.0)
    delta_t = Column(Float, default=0.0)
    calor_transferido = Column(Float, default=0.0)
    data_registro = Column(DateTime, default=datetime.utcnow)
