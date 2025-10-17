from app.repositories.base import BaseRepository
from app import models
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

