# core/models/financeiro/custos.py
"""
Modelos de custos financeiros
"""
from sqlalchemy import Column, Integer, String, Text, Date, DECIMAL, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from . import FinanceiroBase

# Tabelas de Contabilidade de Custos
class CustoPadrao(FinanceiroBase):
    __tablename__ = "custos_padrao"
    custo_padrao_id = Column(Integer, primary_key=True, index=True)
    tipo_custo = Column(String)
    unidade_medida = Column(String)
    valor_unitario_padrao = Column(DECIMAL)
    data_vigencia = Column(Date)

class CustoIndiretoRateio(FinanceiroBase):
    __tablename__ = "custos_indiretos_rateio"
    rateio_id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String)
    custo_total_mes = Column(DECIMAL)
    base_rateio = Column(String)
    data_referencia = Column(Date)

class MaterialCustoHistorico(FinanceiroBase):
    __tablename__ = "materiais_custo_historico"
    custo_material_id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer) # FK para Material da tabela industrial
    custo_unitario = Column(DECIMAL)
    data_compra = Column(Date)
    lote_material_id = Column(Integer) # FK para LoteMaterial da tabela industrial

class CustoMaoObraHistorico(FinanceiroBase):
    __tablename__ = "custo_mao_obra_historico"
    custo_mo_id = Column(Integer, primary_key=True, index=True)
    operador_id = Column(Integer) # FK para Operador (se existir na industrial, ou criar aqui)
    custo_hora = Column(DECIMAL)
    data_vigencia = Column(Date)
    tipo_custo = Column(String)

class CustoOperacionalVariavel(FinanceiroBase):
    __tablename__ = "custos_operacionais_variaveis"
    custo_operacional_id = Column(Integer, primary_key=True, index=True)
    insumo = Column(String)
    valor_unitario = Column(DECIMAL)
    unidade_medida = Column(String)
    data_leitura = Column(Date)

class CustoProducao(FinanceiroBase):
    """
    Representa o custo de produção (CPP, CPA, CPV e custo unitário).
    """
    __tablename__ = "custos_producao"

    id = Column(Integer, primary_key=True, index=True)
    materia_prima = Column(Float, nullable=False)
    mao_obra_direta = Column(Float, nullable=False)
    custos_indiretos = Column(Float, nullable=False)
    estoque_inicial_elaboracao = Column(Float, nullable=False)
    estoque_final_elaboracao = Column(Float, nullable=False)
    estoque_inicial_acabados = Column(Float, nullable=False)
    estoque_final_acabados = Column(Float, nullable=False)
    unidades_produzidas = Column(Float, nullable=False)
    custo_total = Column(Float, nullable=True)
    custo_unitario = Column(Float, nullable=True)
    data_registro = Column(DateTime, default=datetime.utcnow)

class ResultadoFinanceiro(FinanceiroBase):
    """
    Representa o resultado financeiro e indicadores de desempenho.
    """
    __tablename__ = "resultados_financeiros"

    id = Column(Integer, primary_key=True, index=True)
    receita_total = Column(Float, nullable=False)
    custos_variaveis = Column(Float, nullable=False)
    despesas_variaveis = Column(Float, nullable=False)
    custos_fixos = Column(Float, nullable=False)
    despesas_operacionais = Column(Float, nullable=False)
    juros = Column(Float, nullable=False)
    impostos = Column(Float, nullable=False)
    custo_ativo = Column(Float, nullable=False)
    valor_residual = Column(Float, nullable=False)
    vida_util_anos = Column(Float, nullable=False)
    custo_investimento = Column(Float, nullable=False)
    ativos_circulantes = Column(Float, nullable=False)
    passivos_circulantes = Column(Float, nullable=False)

    # Resultados calculados
    margem_contribuicao = Column(Float, nullable=True)
    ponto_equilibrio = Column(Float, nullable=True)
    lucro_bruto = Column(Float, nullable=True)
    lucro_liquido = Column(Float, nullable=True)
    depreciacao_anual = Column(Float, nullable=True)
    roi_percentual = Column(Float, nullable=True)
    capital_de_giro = Column(Float, nullable=True)
    data_registro = Column(DateTime, default=datetime.utcnow)

class AnaliseFinanceira(FinanceiroBase):
    __tablename__ = "analises_financeiras"
    id = Column(Integer, primary_key=True, index=True)
    vendas_totais = Column(Float, default=0.0)
    lucro_bruto = Column(Float, default=0.0)
    estoque_inicial = Column(Float, default=0.0)
    compras = Column(Float, default=0.0)
    estoque_final = Column(Float, default=0.0)
    custo_por_minuto = Column(Float, default=0.0)
    investimento = Column(Float, default=0.0)
    retorno = Column(Float, default=0.0)
    ponto_equilibrio = Column(Float, default=0.0)
    margem_lucro_bruto = Column(Float, default=0.0)
    cmv = Column(Float, default=0.0)
    roi = Column(Float, default=0.0)
    data_registro = Column(DateTime, default=datetime.utcnow)
