# core/models/dw/agregados.py
"""
Agregados e KPIs da Data Warehouse - visões consolidadas
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from . import DWBase

class KPIFinanceiro(DWBase):
    """KPIs Financeiros - agregados semanais/trimestrais"""
    __tablename__ = "kpi_financeiro"
    
    kpi_financeiro_sk = Column(Integer, primary_key=True)
    tempo_sk = Column(Integer, ForeignKey("dim_tempo.tempo_sk"))
    
    receita_total = Column(DECIMAL)
    custos_totais = Column(DECIMAL)
    margem_bruta = Column(DECIMAL)
    margem_liquida = Column(DECIMAL)
    roi_percentual = Column(DECIMAL)
    ponto_equilibrio = Column(DECIMAL)
    periodo_tipo = Column(String)  # 'semanal', 'mensal', 'trimestral'
    data_referencia = Column(Date)

class KPIIndustrial(DWBase):
    """KPIs Industriais - agregados semanais/trimestrais"""
    __tablename__ = "kpi_industrial"
    
    kpi_industrial_sk = Column(Integer, primary_key=True)
    maquina_sk = Column(Integer, ForeignKey("dim_maquina.maquina_sk"))
    tempo_sk = Column(Integer, ForeignKey("dim_tempo.tempo_sk"))
    
    oee_percentual = Column(DECIMAL)  # Overall Equipment Effectiveness
    disponibilidade_percentual = Column(DECIMAL)
    performance_percentual = Column(DECIMAL)
    qualidade_percentual = Column(DECIMAL)
    mtbf_horas = Column(DECIMAL)  # Mean Time Between Failures
    mttr_horas = Column(DECIMAL)  # Mean Time To Repair
    eficiencia_energetica = Column(DECIMAL)
    periodo_tipo = Column(String)  # 'semanal', 'mensal', 'trimestral'
    data_referencia = Column(Date)

class KPIIntegrado(DWBase):
    """KPIs Integrados - correlação financeiro-industrial"""
    __tablename__ = "kpi_integrado"
    
    kpi_integrado_sk = Column(Integer, primary_key=True)
    produto_sk = Column(Integer, ForeignKey("dim_produto.produto_sk"))
    tempo_sk = Column(Integer, ForeignKey("dim_tempo.tempo_sk"))
    
    # Métricas integradas
    receita_por_unidade_produzida = Column(DECIMAL)
    custo_por_unidade_produzida = Column(DECIMAL)
    margem_por_unidade = Column(DECIMAL)
    eficiencia_producao_vs_vendas = Column(DECIMAL)
    correlacao_custo_qualidade = Column(DECIMAL)
    correlacao_energia_lucro = Column(DECIMAL)
    
    # Indicadores de anomalia
    anomalia_custo = Column(String)  # 'normal', 'alto', 'baixo'
    anomalia_producao = Column(String)  # 'normal', 'alta', 'baixa'
    anomalia_qualidade = Column(String)  # 'normal', 'alta', 'baixa'
    
    periodo_tipo = Column(String)  # 'semanal', 'mensal', 'trimestral'
    data_referencia = Column(Date)

class DashboardExecutivo(DWBase):
    """Dashboard Executivo - visão consolidada"""
    __tablename__ = "dashboard_executivo"
    
    dashboard_sk = Column(Integer, primary_key=True)
    tempo_sk = Column(Integer, ForeignKey("dim_tempo.tempo_sk"))
    
    # Indicadores principais
    receita_total = Column(DECIMAL)
    lucro_bruto = Column(DECIMAL)
    margem_bruta_percentual = Column(DECIMAL)
    producao_total = Column(Integer)
    eficiencia_media_percentual = Column(DECIMAL)
    qualidade_media_percentual = Column(DECIMAL)
    consumo_energia_total = Column(DECIMAL)
    
    # Alertas e anomalias
    alertas_ativos = Column(Integer)
    anomalias_detectadas = Column(Integer)
    status_geral = Column(String)  # 'excelente', 'bom', 'atencao', 'critico'
    
    periodo_tipo = Column(String)  # 'diario', 'semanal', 'mensal'
    data_referencia = Column(Date)
    data_criacao = Column(Date)
