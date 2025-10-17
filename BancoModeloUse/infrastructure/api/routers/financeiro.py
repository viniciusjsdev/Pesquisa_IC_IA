from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from infrastructure.database.session import get_db
from typing import List

# Importar os modelos e schemas financeiros
from core.models.financeiro import (
    CustoPadrao, CustoIndiretoRateio, MaterialCustoHistorico, CustoMaoObraHistorico,
    CustoOperacionalVariavel, ContaContabil, LancamentoFinanceiro, Venda, Orcamento,
    KPIGerencial, CategoriaContabilPadrao, SubcategoriaContabilPadrao, ContaContabilDetalhe
)
from core.schemas.schemas import (
    CustoPadrao as CustoPadraoSchema, CustoIndiretoRateio as CustoIndiretoRateioSchema,
    MaterialCustoHistorico as MaterialCustoHistoricoSchema, CustoMaoObraHistorico as CustoMaoObraHistoricoSchema,
    CustoOperacionalVariavel as CustoOperacionalVariavelSchema, ContaContabil as ContaContabilSchema,
    LancamentoFinanceiro as LancamentoFinanceiroSchema, Venda as VendaSchema, Orcamento as OrcamentoSchema,
    KPIGerencial as KPIGerencialSchema, CategoriaContabilPadrao as CategoriaContabilPadraoSchema,
    SubcategoriaContabilPadrao as SubcategoriaContabilPadraoSchema, ContaContabilDetalhe as ContaContabilDetalheSchema
)

router = APIRouter(prefix="/financeiro", tags=["Financeiro"])

# Exemplo de endpoint para listar Custos Padrão
@router.get("/custos_padrao", response_model=List[CustoPadraoSchema])
def get_custos_padrao(db: Session = Depends(get_db)):
    # Lógica para buscar custos padrão do banco de dados
    # Por enquanto, retorna uma lista vazia ou dados mock
    return []

# Adicione outros endpoints conforme necessário para as demais tabelas financeiras
# Exemplo para Contas Contábeis
@router.get("/contas_contabeis", response_model=List[ContaContabilSchema])
def get_contas_contabeis(db: Session = Depends(get_db)):
    return []

# Exemplo para Lançamentos Financeiros
@router.get("/lancamentos_financeiros", response_model=List[LancamentoFinanceiroSchema])
def get_lancamentos_financeiros(db: Session = Depends(get_db)):
    return []

# Exemplo para KPIs Gerenciais
@router.get("/kpis_gerenciais", response_model=List[KPIGerencialSchema])
def get_kpis_gerenciais(db: Session = Depends(get_db)):
    return []








# --- NOVAS ROTAS DE CÁLCULOS FINANCEIROS E INDUSTRIAIS ---

@router.post("/custo-producao/")
def criar_custo_producao(dados: dict, db: Session = Depends(get_db)):
    cpp = financeiro_service.calcular_cpp(dados["materia_prima"], dados["mao_obra_direta"], dados["custos_indiretos"])
    cpa = financeiro_service.calcular_cpa(dados["estoque_inicial_elaboracao"], cpp, dados["estoque_final_elaboracao"])
    cpv = financeiro_service.calcular_cpv(dados["estoque_inicial_acabados"], cpa, dados["estoque_final_acabados"])
    custo_unitario = financeiro_service.custo_por_unidade(cpv, dados["unidades_produzidas"])

    dados["custo_total"] = cpv
    dados["custo_unitario"] = custo_unitario

    novo = financeiro_repo.criar_custo_producao(db, dados)
    return {"mensagem": "Custo de produção registrado com sucesso", "id": novo.id, "cpv": cpv, "custo_unitario": custo_unitario}


@router.post("/resultado-financeiro/")
def criar_resultado_financeiro(dados: dict, db: Session = Depends(get_db)):
    margem = financeiro_service.margem_contribuicao(dados["receita_total"], dados["custos_variaveis"], dados["despesas_variaveis"])
    ponto_eq = financeiro_service.ponto_equilibrio(dados["custos_fixos"], margem)
    lucro_b = financeiro_service.lucro_bruto(dados["receita_total"], dados["custos_variaveis"])
    lucro_l = financeiro_service.lucro_liquido(lucro_b, dados["despesas_operacionais"], dados["juros"], dados["impostos"])
    dep = financeiro_service.depreciacao_linear(dados["custo_ativo"], dados["valor_residual"], dados["vida_util_anos"])
    roi_calc = financeiro_service.roi(lucro_l, dados["custo_investimento"])
    cg = financeiro_service.capital_de_giro(dados["ativos_circulantes"], dados["passivos_circulantes"])

    dados.update({
        "margem_contribuicao": margem,
        "ponto_equilibrio": ponto_eq,
        "lucro_bruto": lucro_b,
        "lucro_liquido": lucro_l,
        "depreciacao_anual": dep,
        "roi_percentual": roi_calc,
        "capital_de_giro": cg
    })

    novo = financeiro_repo.criar_resultado_financeiro(db, dados)
    return {"mensagem": "Resultado financeiro calculado e salvo", "id": novo.id}

