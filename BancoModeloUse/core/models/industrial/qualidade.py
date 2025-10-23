# core/models/industrial/qualidade.py
"""
Modelos de qualidade industrial
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database.connections.industrial_connection import Base

class ControleQualidade(Base):
    __tablename__ = "controle_qualidade"
    controle_id = Column(Integer, primary_key=True, index=True)
    lote_producao_id = Column(Integer, ForeignKey("lotes_producao.lote_producao_id"))
    data_inspecao = Column(DateTime)
    inspetor_id = Column(Integer)
    unidades_aprovadas = Column(Integer)
    unidades_rejeitadas = Column(Integer)
    motivo_rejeicao = Column(String)

    lote = relationship("LoteProducao")

class Defeito(Base):
    __tablename__ = "defeitos"
    defeito_id = Column(Integer, primary_key=True, index=True)
    nome_defeito = Column(String)

class RegistroDefeito(Base):
    __tablename__ = "registros_defeitos"
    registro_defeito_id = Column(Integer, primary_key=True, index=True)
    controle_id = Column(Integer, ForeignKey("controle_qualidade.controle_id"))
    defeito_id = Column(Integer, ForeignKey("defeitos.defeito_id"))
    quantidade_defeito = Column(Integer)

    controle = relationship("ControleQualidade")
    defeito = relationship("Defeito")
