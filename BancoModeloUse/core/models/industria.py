# app/models.py
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, DECIMAL, ForeignKey
)
from sqlalchemy.orm import relationship
from infrastructure.database.session import Base

# Cadastro
class Produto(Base):
    __tablename__ = "produtos"
    produto_id = Column(Integer, primary_key=True, index=True)
    nome_produto = Column(String, nullable=False)
    descricao = Column(Text)
    unidade_medida = Column(String)
    data_registro = Column(DateTime, default=datetime.utcnow)

class Material(Base):
    __tablename__ = "materiais"
    material_id = Column(Integer, primary_key=True, index=True)
    nome_material = Column(String, nullable=False)
    unidade_medida = Column(String)
    data_registro = Column(DateTime, default=datetime.utcnow)

class Maquina(Base):
    __tablename__ = "maquinas"
    maquina_id = Column(Integer, primary_key=True, index=True)
    nome_maquina = Column(String, nullable=False)
    linha_producao = Column(String)
    capacidade_producao_max = Column(DECIMAL)
    data_registro = Column(DateTime, default=datetime.utcnow)

class Fornecedor(Base):
    __tablename__ = "fornecedores"
    fornecedor_id = Column(Integer, primary_key=True, index=True)
    nome_fornecedor = Column(String, nullable=False)
    data_registro = Column(DateTime, default=datetime.utcnow)

# Ordens e Roteiros
class OrdemProducao(Base):
    __tablename__ = "ordens_producao"
    ordem_producao_id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.produto_id"))
    quantidade_planejada = Column(Integer)
    data_planejamento = Column(Date)
    data_inicio_real = Column(DateTime)
    data_fim_real = Column(DateTime)
    status_ordem = Column(String)

    produto = relationship("Produto")


class OperacaoRoteiro(Base):
    __tablename__ = "operacoes_roteiro"
    operacao_roteiro_id = Column(Integer, primary_key=True, index=True)
    roteiro_id = Column(Integer, ForeignKey("roteiros_producao.roteiro_id"))
    sequencia = Column(Integer)
    maquina_id = Column(Integer, ForeignKey("maquinas.maquina_id"))
    tempo_ideal_min = Column(DECIMAL)
    tempo_setup_ideal_min = Column(DECIMAL)
    roteiro = relationship("RoteiroProducao")
    maquina = relationship("Maquina")
    data_registro = Column(DateTime, default=datetime.utcnow)

# Execução chão de fábrica
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
    ordem = relationship("OrdemProducao")
    maquina = relationship("Maquina")
    data_registro = Column(DateTime, default=datetime.utcnow)

class ParadaMaquina(Base):
    __tablename__ = "paradas_maquinas"
    parada_id = Column(Integer, primary_key=True, index=True)
    maquina_id = Column(Integer, ForeignKey("maquinas.maquina_id"))
    hora_inicio_parada = Column(DateTime)
    hora_fim_parada = Column(DateTime)
    motivo_parada = Column(String)
    maquina = relationship("Maquina")
    data_registro = Column(DateTime, default=datetime.utcnow)

# Materiais e Lotes
class ConsumoMaterial(Base):
    __tablename__ = "consumo_materiais"
    consumo_id = Column(Integer, primary_key=True, index=True)
    registro_id = Column(Integer, ForeignKey("registros_operacao.registro_id"))
    material_id = Column(Integer, ForeignKey("materiais.material_id"))
    lote_material_id = Column(Integer, ForeignKey("lotes_materiais.lote_id"))
    quantidade_consumida = Column(DECIMAL)
    data_registro = Column(DateTime, default=datetime.utcnow)
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

# Qualidade
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


class RegistroDefeito(Base):
    __tablename__ = "registros_defeitos"
    registro_defeito_id = Column(Integer, primary_key=True, index=True)
    controle_id = Column(Integer, ForeignKey("controle_qualidade.controle_id"))
    defeito_id = Column(Integer, ForeignKey("defeitos.defeito_id"))
    quantidade_defeito = Column(Integer)
    controle = relationship("ControleQualidade")
    defeito = relationship("Defeito")
    defeito_id = Column(Integer, primary_key=True, index=True)
    nome_defeito = Column(String)
    data_registro = Column(DateTime, default=datetime.utcnow)







from sqlalchemy.orm import relationship
from datetime import datetime
from app.db_industrial import Base #__________________________________________ CORRIGIR CAMINHO E NOME DO ARQUIVO CHAMADO

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

class ControleQualidade(Base):
    __tablename__ = "controle_qualidade"
    id = Column(Integer, primary_key=True, index=True)
    unidades_inspecionadas = Column(Integer, default=0)
    defeitos = Column(Integer, default=0)
    taxa_defeito = Column(Float, default=0.0)
    desvio_padrao = Column(Float, default=0.0)
    cp = Column(Float, default=0.0)
    cpk = Column(Float, default=0.0)
    data_registro = Column(DateTime, default=datetime.utcnow)

