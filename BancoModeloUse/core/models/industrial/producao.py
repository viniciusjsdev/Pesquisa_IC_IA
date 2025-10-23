# core/models/industrial/producao.py
"""
Modelos de produção industrial
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from infrastructure.database.connections.industrial_connection import Base

class OrdemProducao(Base):
    __tablename__ = "ordens_producao"
    ordem_producao_id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.produto_id"))
    quantidade_planejada = Column(Integer)
    data_planejamento = Column(Date)
    data_inicio_real = Column(DateTime)
    data_fim_real = Column(DateTime)
    status_ordem = Column(String)
    data_registro = Column(DateTime, default=datetime.utcnow)

    produto = relationship("Produto")

class RoteiroProducao(Base):
    __tablename__ = "roteiros_producao"
    roteiro_id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.produto_id"))
    versao = Column(Integer)
    data_registro = Column(DateTime, default=datetime.utcnow)

    produto = relationship("Produto")

class OperacaoRoteiro(Base):
    __tablename__ = "operacoes_roteiro"
    operacao_roteiro_id = Column(Integer, primary_key=True, index=True)
    roteiro_id = Column(Integer, ForeignKey("roteiros_producao.roteiro_id"))
    sequencia = Column(Integer)
    maquina_id = Column(Integer, ForeignKey("maquinas.maquina_id"))
    tempo_ideal_min = Column(DECIMAL)
    tempo_setup_ideal_min = Column(DECIMAL)
    data_registro = Column(DateTime, default=datetime.utcnow)

    roteiro = relationship("RoteiroProducao")
    maquina = relationship("Maquina")

class RegistroOperacao(Base):
    __tablename__ = "registros_operacao"
    registro_id = Column(Integer, primary_key=True, index=True)
    ordem_producao_id = Column(Integer, ForeignKey("ordens_producao.ordem_producao_id"))
    maquina_id = Column(Integer, ForeignKey("maquinas.maquina_id"))
    operador_id = Column(Integer)  # poderia ser FK para tabela Operadores
    hora_inicio = Column(DateTime)
    hora_fim = Column(DateTime)
    tempo_setup_real_min = Column(DECIMAL)
    quantidade_produzida_real = Column(Integer)
    consumo_energia_kwh = Column(DECIMAL)
    data_registro = Column(DateTime, default=datetime.utcnow)

    ordem = relationship("OrdemProducao")
    maquina = relationship("Maquina")

class ParadaMaquina(Base):
    __tablename__ = "paradas_maquinas"
    parada_id = Column(Integer, primary_key=True, index=True)
    maquina_id = Column(Integer, ForeignKey("maquinas.maquina_id"))
    hora_inicio_parada = Column(DateTime)
    hora_fim_parada = Column(DateTime)
    motivo_parada = Column(String)
    data_registro = Column(DateTime, default=datetime.utcnow)

    maquina = relationship("Maquina")

class ConsumoMaterial(Base):
    __tablename__ = "consumo_materiais"
    consumo_id = Column(Integer, primary_key=True, index=True)
    registro_id = Column(Integer, ForeignKey("registros_operacao.registro_id"))
    material_id = Column(Integer, ForeignKey("materiais.material_id"))
    lote_material_id = Column(Integer, ForeignKey("lotes_materiais.lote_id"))
    quantidade_consumida = Column(DECIMAL)

    registro = relationship("RegistroOperacao")
    material = relationship("Material")

class LoteMaterial(Base):
    __tablename__ = "lotes_materiais"
    lote_id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materiais.material_id"))
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.fornecedor_id"))
    data_recebimento = Column(Date)
    lote_fornecedor = Column(String)

    material = relationship("Material")
    fornecedor = relationship("Fornecedor")

class LoteProducao(Base):
    __tablename__ = "lotes_producao"
    lote_producao_id = Column(Integer, primary_key=True, index=True)
    ordem_producao_id = Column(Integer, ForeignKey("ordens_producao.ordem_producao_id"))
    data_lote = Column(Date)
    quantidade_total = Column(Integer)

    ordem = relationship("OrdemProducao")
