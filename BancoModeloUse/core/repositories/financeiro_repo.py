from core.repositories.base import BaseRepository
from core import models
from sqlalchemy.orm import Session
from typing import List, Type

class FinanceiroRepository(BaseRepository):

    def get_all_custos_padrao(self) -> List[Type[models.CustoPadrao]]:
        return self.db.query(models.CustoPadrao).all()

    def get_all_contas_contabeis(self) -> List[Type[models.ContaContabil]]:
        return self.db.query(models.ContaContabil).all()

    def get_all_lancamentos_financeiros(self) -> List[Type[models.LancamentoFinanceiro]]:
        return self.db.query(models.LancamentoFinanceiro).all()

    def get_all_orcamentos(self) -> List[Type[models.Orcamento]]:
        return self.db.query(models.Orcamento).all()

    def get_all_kpis_gerenciais(self) -> List[Type[models.KPIGerencial]]:
        return self.db.query(models.KPIGerencial).all()

    def get_all_categorias_contabeis_padrao(self) -> List[Type[models.CategoriaContabilPadrao]]:
        return self.db.query(models.CategoriaContabilPadrao).all()

    def get_all_subcategorias_contabeis_padrao(self) -> List[Type[models.SubcategoriaContabilPadrao]]:
        return self.db.query(models.SubcategoriaContabilPadrao).all()

    def get_all_contas_contabeis_detalhe(self) -> List[Type[models.ContaContabilDetalhe]]:
        return self.db.query(models.ContaContabilDetalhe).all()

    # Adicione outros métodos conforme necessário para operações CRUD ou consultas específicas





# --- CRUD PARA NOVAS TABELAS ---

from core.models.financeiro import CustoProducao, ResultadoFinanceiro


def criar_custo_producao(db, dados: dict):
    novo = CustoProducao(**dados)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


def listar_custos_producao(db):
    return db.query(CustoProducao).all()


def criar_resultado_financeiro(db, dados: dict):
    novo = ResultadoFinanceiro(**dados)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


def listar_resultados_financeiros(db):
    return db.query(ResultadoFinanceiro).all()


