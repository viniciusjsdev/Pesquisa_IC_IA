# core/models/dw/fatos.py
"""
Fatos da Data Warehouse - mantém granularidade diária
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from infrastructure.database.connections.dw_connection import Base

class FatoVendas(Base):
    """Fato Vendas - transações de vendas (granularidade diária)"""
    __tablename__ = "fato_vendas"
    
    venda_sk = Column(Integer, primary_key=True)
    produto_sk = Column(Integer, ForeignKey("dim_produto.produto_sk"))
    tempo_sk = Column(Integer, ForeignKey("dim_tempo.tempo_sk"))
    cliente_sk = Column(Integer, ForeignKey("dim_cliente.cliente_sk"))
    
    quantidade_vendida = Column(Integer)
    valor_unitario = Column(DECIMAL)
    valor_total = Column(DECIMAL)
    desconto = Column(DECIMAL)
    margem_contribuicao = Column(DECIMAL)
    data_venda = Column(Date)  # Data específica da venda

class FatoProducao(Base):
    """Fato Produção - registros de produção (granularidade diária)"""
    __tablename__ = "fato_producao"
    
    producao_sk = Column(Integer, primary_key=True)
    produto_sk = Column(Integer, ForeignKey("dim_produto.produto_sk"))
    maquina_sk = Column(Integer, ForeignKey("dim_maquina.maquina_sk"))
    tempo_sk = Column(Integer, ForeignKey("dim_tempo.tempo_sk"))
    
    quantidade_produzida = Column(Integer)
    quantidade_planejada = Column(Integer)
    tempo_producao_min = Column(DECIMAL)
    tempo_setup_min = Column(DECIMAL)
    consumo_energia_kwh = Column(DECIMAL)
    eficiencia_percent = Column(DECIMAL)
    defeitos_quantidade = Column(Integer)
    defeitos_percent = Column(DECIMAL)
    data_producao = Column(Date)  # Data específica da produção

class FatoCustos(Base):
    """Fato Custos - custos integrados (granularidade diária)"""
    __tablename__ = "fato_custos"
    
    custo_sk = Column(Integer, primary_key=True)
    produto_sk = Column(Integer, ForeignKey("dim_produto.produto_sk"))
    maquina_sk = Column(Integer, ForeignKey("dim_maquina.maquina_sk"))
    tempo_sk = Column(Integer, ForeignKey("dim_tempo.tempo_sk"))
    
    custo_materia_prima = Column(DECIMAL)
    custo_mao_obra = Column(DECIMAL)
    custo_indireto = Column(DECIMAL)
    custo_energia = Column(DECIMAL)
    custo_total = Column(DECIMAL)
    custo_unitario = Column(DECIMAL)
    data_custo = Column(Date)  # Data específica do custo

class FatoQualidade(Base):
    """Fato Qualidade - registros de qualidade (granularidade diária)"""
    __tablename__ = "fato_qualidade"
    
    qualidade_sk = Column(Integer, primary_key=True)
    produto_sk = Column(Integer, ForeignKey("dim_produto.produto_sk"))
    maquina_sk = Column(Integer, ForeignKey("dim_maquina.maquina_sk"))
    tempo_sk = Column(Integer, ForeignKey("dim_tempo.tempo_sk"))
    
    unidades_inspecionadas = Column(Integer)
    unidades_aprovadas = Column(Integer)
    unidades_rejeitadas = Column(Integer)
    taxa_defeito_percent = Column(DECIMAL)
    cp = Column(DECIMAL)  # Capability Process
    cpk = Column(DECIMAL)  # Capability Process Index
    data_qualidade = Column(Date)  # Data específica da inspeção

class FatoEnergia(Base):
    """Fato Energia - consumo energético (granularidade diária)"""
    __tablename__ = "fato_energia"
    
    energia_sk = Column(Integer, primary_key=True)
    maquina_sk = Column(Integer, ForeignKey("dim_maquina.maquina_sk"))
    tempo_sk = Column(Integer, ForeignKey("dim_tempo.tempo_sk"))
    
    consumo_total_kwh = Column(DECIMAL)
    consumo_por_producao_kwh = Column(DECIMAL)
    eficiencia_energetica = Column(DECIMAL)
    custo_energia = Column(DECIMAL)
    data_energia = Column(Date)  # Data específica do consumo
