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

class Material(Base):
    __tablename__ = "materiais"
    material_id = Column(Integer, primary_key=True, index=True)
    nome_material = Column(String, nullable=False)
    unidade_medida = Column(String)

class Maquina(Base):
    __tablename__ = "maquinas"
    maquina_id = Column(Integer, primary_key=True, index=True)
    nome_maquina = Column(String, nullable=False)
    linha_producao = Column(String)
    capacidade_producao_max = Column(DECIMAL)

class Fornecedor(Base):
    __tablename__ = "fornecedores"
    fornecedor_id = Column(Integer, primary_key=True, index=True)
    nome_fornecedor = Column(String, nullable=False)

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

class RoteiroProducao(Base):
    __tablename__ = "roteiros_producao"
    roteiro_id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.produto_id"))
    versao = Column(Integer)

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

class ParadaMaquina(Base):
    __tablename__ = "paradas_maquinas"
    parada_id = Column(Integer, primary_key=True, index=True)
    maquina_id = Column(Integer, ForeignKey("maquinas.maquina_id"))
    hora_inicio_parada = Column(DateTime)
    hora_fim_parada = Column(DateTime)
    motivo_parada = Column(String)

    maquina = relationship("Maquina")

# Materiais e Lotes
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
