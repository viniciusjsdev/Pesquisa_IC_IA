from sqlalchemy import Column, Integer, String, Text, Date, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database.session import Base

# Tabelas de Contabilidade de Custos

class CustoPadrao(Base):
    __tablename__ = "custos_padrao"
    custo_padrao_id = Column(Integer, primary_key=True, index=True)
    tipo_custo = Column(String)
    unidade_medida = Column(String)
    valor_unitario_padrao = Column(DECIMAL)
    data_vigencia = Column(Date)

class CustoIndiretoRateio(Base):
    __tablename__ = "custos_indiretos_rateio"
    rateio_id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String)
    custo_total_mes = Column(DECIMAL)
    base_rateio = Column(String)
    data_referencia = Column(Date)

class MaterialCustoHistorico(Base):
    __tablename__ = "materiais_custo_historico"
    custo_material_id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer) # FK para Material da tabela industrial
    custo_unitario = Column(DECIMAL)
    data_compra = Column(Date)
    lote_material_id = Column(Integer) # FK para LoteMaterial da tabela industrial

class CustoMaoObraHistorico(Base):
    __tablename__ = "custo_mao_obra_historico"
    custo_mo_id = Column(Integer, primary_key=True, index=True)
    operador_id = Column(Integer) # FK para Operador (se existir na industrial, ou criar aqui)
    custo_hora = Column(DECIMAL)
    data_vigencia = Column(Date)
    tipo_custo = Column(String)

class CustoOperacionalVariavel(Base):
    __tablename__ = "custos_operacionais_variaveis"
    custo_operacional_id = Column(Integer, primary_key=True, index=True)
    insumo = Column(String)
    valor_unitario = Column(DECIMAL)
    unidade_medida = Column(String)
    data_leitura = Column(Date)

# Tabelas de Dados Financeiros Adicionais

class ContaContabil(Base):
    __tablename__ = "contas_contabeis"
    conta_id = Column(Integer, primary_key=True, index=True)
    numero_conta = Column(String)
    nome_conta = Column(String)
    tipo_conta = Column(String)

class LancamentoFinanceiro(Base):
    __tablename__ = "lancamentos_financeiros"
    lancamento_id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas_contabeis.conta_id"))
    data_lancamento = Column(Date)
    valor = Column(DECIMAL)
    descricao = Column(Text)

    conta = relationship("ContaContabil")

class Venda(Base):
    __tablename__ = "vendas"
    venda_id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer) # FK para Produto da tabela industrial
    quantidade_vendida = Column(Integer)
    preco_unitario_venda = Column(DECIMAL)
    data_venda = Column(Date)
    cliente_id = Column(Integer) # FK para Cliente (se existir na industrial, ou criar aqui)

class Orcamento(Base):
    __tablename__ = "orcamentos"
    orcamento_id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas_contabeis.conta_id"))
    valor_orcado = Column(DECIMAL)
    periodo = Column(Date)

    conta = relationship("ContaContabil")

class KPIGerencial(Base):
    __tablename__ = "kpis_gerenciais"
    kpi_id = Column(Integer, primary_key=True, index=True)
    nome_kpi = Column(String)
    valor_kpi = Column(DECIMAL)
    data_referencia = Column(Date)

# Adicionando simulação de categorias da folha contábil padrão
class CategoriaContabilPadrao(Base):
    __tablename__ = "categorias_contabeis_padrao"
    categoria_id = Column(Integer, primary_key=True, index=True)
    nome_categoria = Column(String, unique=True, nullable=False) # Ex: Ativo, Passivo, Receita, Despesa
    tipo_categoria = Column(String) # Ex: Balanço Patrimonial, Demonstração de Resultado

class SubcategoriaContabilPadrao(Base):
    __tablename__ = "subcategorias_contabeis_padrao"
    subcategoria_id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias_contabeis_padrao.categoria_id"))
    nome_subcategoria = Column(String, nullable=False) # Ex: Caixa e Equivalentes, Contas a Receber, Estoques

    categoria = relationship("CategoriaContabilPadrao")

class ContaContabilDetalhe(Base):
    __tablename__ = "contas_contabeis_detalhe"
    conta_detalhe_id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas_contabeis.conta_id"))
    subcategoria_id = Column(Integer, ForeignKey("subcategorias_contabeis_padrao.subcategoria_id"))
    data_associacao = Column(Date)

    conta = relationship("ContaContabil")
    subcategoria = relationship("SubcategoriaContabilPadrao")



# --- NOVAS TABELAS E COLUNAS PARA CÁLCULOS FINANCEIROS E INDUSTRIAIS ---

from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime


class CustoProducao(Base):
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


class ResultadoFinanceiro(Base):
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









from datetime import datetime
from app.db_financeiro import Base #______________________________________---- VERIFICAR SE O CAMINHO ESTÁ CERTO

class AnaliseFinanceira(Base):
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


