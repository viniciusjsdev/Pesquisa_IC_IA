# core/repositories/financeiro/contabil_repository.py
"""
Repositório para operações contábeis
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from core.models.financeiro.contabil import (
    ContaContabil, LancamentoFinanceiro, CategoriaContabilPadrao,
    SubcategoriaContabilPadrao, ContaContabilDetalhe
)
from core.repositories.base import BaseRepository

class ContabilRepository(BaseRepository):
    """Repositório para operações contábeis"""
    
    def get_all_contas_contabeis(self):
        """Retorna todas as contas contábeis"""
        return self.db.query(ContaContabil).all()
    
    def get_conta_by_id(self, conta_id: int):
        """Busca conta contábil por ID"""
        return self.db.query(ContaContabil).filter(ContaContabil.conta_id == conta_id).first()
    
    def get_contas_by_tipo(self, tipo_conta: str):
        """Busca contas por tipo"""
        return self.db.query(ContaContabil).filter(ContaContabil.tipo_conta == tipo_conta).all()
    
    def get_all_lancamentos_financeiros(self):
        """Retorna todos os lançamentos financeiros"""
        return self.db.query(LancamentoFinanceiro).all()
    
    def get_lancamentos_by_periodo(self, data_inicio, data_fim):
        """Busca lançamentos por período"""
        return self.db.query(LancamentoFinanceiro).filter(
            LancamentoFinanceiro.data_lancamento.between(data_inicio, data_fim)
        ).all()
    
    def get_lancamentos_by_conta(self, conta_id: int):
        """Busca lançamentos por conta"""
        return self.db.query(LancamentoFinanceiro).filter(
            LancamentoFinanceiro.conta_id == conta_id
        ).all()
    
    def get_saldo_conta_periodo(self, conta_id: int, data_inicio, data_fim):
        """Calcula saldo da conta no período"""
        result = self.db.query(
            func.sum(LancamentoFinanceiro.valor).label('saldo_total')
        ).filter(
            LancamentoFinanceiro.conta_id == conta_id,
            LancamentoFinanceiro.data_lancamento.between(data_inicio, data_fim)
        ).first()
        
        return result.saldo_total or 0
    
    def get_categorias_contabeis_padrao(self):
        """Retorna categorias contábeis padrão"""
        return self.db.query(CategoriaContabilPadrao).all()
    
    def get_subcategorias_by_categoria(self, categoria_id: int):
        """Busca subcategorias por categoria"""
        return self.db.query(SubcategoriaContabilPadrao).filter(
            SubcategoriaContabilPadrao.categoria_id == categoria_id
        ).all()
    
    def get_contas_contabeis_detalhe(self):
        """Retorna detalhes das contas contábeis"""
        return self.db.query(ContaContabilDetalhe).all()
    
    def create_conta_contabil(self, conta_data: dict):
        """Cria nova conta contábil"""
        conta = ContaContabil(**conta_data)
        self.db.add(conta)
        self.db.commit()
        self.db.refresh(conta)
        return conta
    
    def create_lancamento_financeiro(self, lancamento_data: dict):
        """Cria novo lançamento financeiro"""
        lancamento = LancamentoFinanceiro(**lancamento_data)
        self.db.add(lancamento)
        self.db.commit()
        self.db.refresh(lancamento)
        return lancamento
