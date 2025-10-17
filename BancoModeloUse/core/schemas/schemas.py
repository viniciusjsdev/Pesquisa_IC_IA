# app/schemas.py
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

# Schemas existentes
class IndicadorResponse(BaseModel):
    indicador_nome: str
    valor: float
    unidade: Optional[str] = None
    detalhe: Optional[str] = None

class OrdemKPIResponse(BaseModel):
    ordem_producao_id: int
    eficiencia_percent: float
    taxa_defeitos_percent: float
    energia_por_unidade_kwh: float
    tempo_total_min: float

    class Config:
        from_attributes = True

# Schemas para modelos financeiros
class CustoPadrao(BaseModel):
    custo_padrao_id: Optional[int] = None
    tipo_custo: Optional[str] = None
    unidade_medida: Optional[str] = None
    valor_unitario_padrao: Optional[Decimal] = None
    data_vigencia: Optional[date] = None

    class Config:
        from_attributes = True

class CustoIndiretoRateio(BaseModel):
    rateio_id: Optional[int] = None
    descricao: Optional[str] = None
    custo_total_mes: Optional[Decimal] = None
    base_rateio: Optional[str] = None
    data_referencia: Optional[date] = None

    class Config:
        from_attributes = True

class MaterialCustoHistorico(BaseModel):
    custo_material_id: Optional[int] = None
    material_id: Optional[int] = None
    custo_unitario: Optional[Decimal] = None
    data_compra: Optional[date] = None
    lote_material_id: Optional[int] = None

    class Config:
        from_attributes = True

class CustoMaoObraHistorico(BaseModel):
    custo_mo_id: Optional[int] = None
    operador_id: Optional[int] = None
    custo_hora: Optional[Decimal] = None
    data_vigencia: Optional[date] = None
    tipo_custo: Optional[str] = None

    class Config:
        from_attributes = True

class CustoOperacionalVariavel(BaseModel):
    custo_operacional_id: Optional[int] = None
    insumo: Optional[str] = None
    valor_unitario: Optional[Decimal] = None
    unidade_medida: Optional[str] = None
    data_leitura: Optional[date] = None

    class Config:
        from_attributes = True

class ContaContabil(BaseModel):
    conta_id: Optional[int] = None
    numero_conta: Optional[str] = None
    nome_conta: Optional[str] = None
    tipo_conta: Optional[str] = None

    class Config:
        from_attributes = True

class LancamentoFinanceiro(BaseModel):
    lancamento_id: Optional[int] = None
    conta_id: Optional[int] = None
    data_lancamento: Optional[date] = None
    valor: Optional[Decimal] = None
    descricao: Optional[str] = None

    class Config:
        from_attributes = True

class Venda(BaseModel):
    venda_id: Optional[int] = None
    produto_id: Optional[int] = None
    quantidade_vendida: Optional[int] = None
    preco_unitario_venda: Optional[Decimal] = None
    data_venda: Optional[date] = None
    cliente_id: Optional[int] = None

    class Config:
        from_attributes = True

class Orcamento(BaseModel):
    orcamento_id: Optional[int] = None
    conta_id: Optional[int] = None
    valor_orcado: Optional[Decimal] = None
    periodo: Optional[date] = None

    class Config:
        from_attributes = True

class KPIGerencial(BaseModel):
    kpi_id: Optional[int] = None
    nome_kpi: Optional[str] = None
    valor_kpi: Optional[Decimal] = None
    data_referencia: Optional[date] = None

    class Config:
        from_attributes = True

class CategoriaContabilPadrao(BaseModel):
    categoria_id: Optional[int] = None
    nome_categoria: Optional[str] = None
    tipo_categoria: Optional[str] = None

    class Config:
        from_attributes = True

class SubcategoriaContabilPadrao(BaseModel):
    subcategoria_id: Optional[int] = None
    categoria_id: Optional[int] = None
    nome_subcategoria: Optional[str] = None

    class Config:
        from_attributes = True

class ContaContabilDetalhe(BaseModel):
    conta_detalhe_id: Optional[int] = None
    conta_id: Optional[int] = None
    subcategoria_id: Optional[int] = None
    data_associacao: Optional[date] = None

    class Config:
        from_attributes = True
