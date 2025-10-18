# core/models/dw/dimensoes.py
"""
Dimensões da Data Warehouse
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, Boolean
from . import DWBase

class DimProduto(DWBase):
    """Dimensão Produto - consolida dados de ambos os sistemas"""
    __tablename__ = "dim_produto"
    
    produto_sk = Column(Integer, primary_key=True)  # Surrogate Key
    produto_id_financeiro = Column(Integer)  # FK para banco financeiro
    produto_id_industrial = Column(Integer)  # FK para banco industrial
    nome_produto = Column(String, nullable=False)
    categoria = Column(String)
    unidade_medida = Column(String)
    preco_unitario = Column(DECIMAL)
    data_inicio_vigencia = Column(Date)
    data_fim_vigencia = Column(Date)
    ativo = Column(Boolean, default=True)

class DimTempo(DWBase):
    """Dimensão Tempo - calendário unificado com granularidade diária"""
    __tablename__ = "dim_tempo"
    
    tempo_sk = Column(Integer, primary_key=True)
    data = Column(Date, nullable=False, unique=True)
    dia = Column(Integer)
    mes = Column(Integer)
    trimestre = Column(Integer)
    ano = Column(Integer)
    dia_semana = Column(String)
    nome_dia_semana = Column(String)
    nome_mes = Column(String)
    nome_trimestre = Column(String)
    feriado = Column(Boolean, default=False)
    periodo_fiscal = Column(String)
    semana_ano = Column(Integer)
    dia_ano = Column(Integer)

class DimMaquina(DWBase):
    """Dimensão Máquina - consolida equipamentos"""
    __tablename__ = "dim_maquina"
    
    maquina_sk = Column(Integer, primary_key=True)
    maquina_id_industrial = Column(Integer)  # FK para banco industrial
    nome_maquina = Column(String, nullable=False)
    linha_producao = Column(String)
    capacidade_max = Column(DECIMAL)
    centro_custo = Column(String)  # Dados financeiros
    data_inicio_vigencia = Column(Date)
    data_fim_vigencia = Column(Date)
    ativo = Column(Boolean, default=True)

class DimCliente(DWBase):
    """Dimensão Cliente - consolida dados de clientes"""
    __tablename__ = "dim_cliente"
    
    cliente_sk = Column(Integer, primary_key=True)
    cliente_id_financeiro = Column(Integer)  # FK para banco financeiro
    nome_cliente = Column(String, nullable=False)
    segmento = Column(String)
    regiao = Column(String)
    data_inicio_vigencia = Column(Date)
    data_fim_vigencia = Column(Date)
    ativo = Column(Boolean, default=True)

class DimFornecedor(DWBase):
    """Dimensão Fornecedor - consolida dados de fornecedores"""
    __tablename__ = "dim_fornecedor"
    
    fornecedor_sk = Column(Integer, primary_key=True)
    fornecedor_id_industrial = Column(Integer)  # FK para banco industrial
    nome_fornecedor = Column(String, nullable=False)
    categoria = Column(String)
    regiao = Column(String)
    data_inicio_vigencia = Column(Date)
    data_fim_vigencia = Column(Date)
    ativo = Column(Boolean, default=True)
