# core/repositories/financeiro/vendas_repository.py
"""
Repositório para operações de vendas financeiras
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from core.models.financeiro.vendas import Venda, Orcamento
from core.repositories.base import BaseRepository

class VendasRepository(BaseRepository):
    """Repositório para operações de vendas"""
    
    def get_all_vendas(self):
        """Retorna todas as vendas"""
        return self.db.query(Venda).all()
    
    def get_vendas_by_periodo(self, data_inicio, data_fim):
        """Busca vendas por período"""
        return self.db.query(Venda).filter(
            Venda.data_venda.between(data_inicio, data_fim)
        ).all()
    
    def get_vendas_by_produto(self, produto_id: int):
        """Busca vendas por produto"""
        return self.db.query(Venda).filter(Venda.produto_id == produto_id).all()
    
    def get_vendas_by_cliente(self, cliente_id: int):
        """Busca vendas por cliente"""
        return self.db.query(Venda).filter(Venda.cliente_id == cliente_id).all()
    
    def get_total_vendas_periodo(self, data_inicio, data_fim):
        """Calcula total de vendas por período"""
        result = self.db.query(
            func.sum(Venda.quantidade_vendida).label('total_quantidade'),
            func.sum(Venda.valor_total).label('total_valor'),
            func.avg(Venda.preco_unitario_venda).label('preco_medio')
        ).filter(
            Venda.data_venda.between(data_inicio, data_fim)
        ).first()
        
        return {
            'total_quantidade': result.total_quantidade or 0,
            'total_valor': result.total_valor or 0,
            'preco_medio': result.preco_medio or 0
        }
    
    def get_vendas_por_produto_periodo(self, data_inicio, data_fim):
        """Agrupa vendas por produto no período"""
        return self.db.query(
            Venda.produto_id,
            func.sum(Venda.quantidade_vendida).label('total_quantidade'),
            func.sum(Venda.valor_total).label('total_valor'),
            func.avg(Venda.preco_unitario_venda).label('preco_medio')
        ).filter(
            Venda.data_venda.between(data_inicio, data_fim)
        ).group_by(Venda.produto_id).all()
    
    def get_all_orcamentos(self):
        """Retorna todos os orçamentos"""
        return self.db.query(Orcamento).all()
    
    def get_orcamentos_by_periodo(self, data_inicio, data_fim):
        """Busca orçamentos por período"""
        return self.db.query(Orcamento).filter(
            Orcamento.periodo.between(data_inicio, data_fim)
        ).all()
    
    def get_orcamentos_by_conta(self, conta_id: int):
        """Busca orçamentos por conta"""
        return self.db.query(Orcamento).filter(Orcamento.conta_id == conta_id).all()
    
    def create_venda(self, venda_data: dict):
        """Cria nova venda"""
        venda = Venda(**venda_data)
        self.db.add(venda)
        self.db.commit()
        self.db.refresh(venda)
        return venda
    
    def create_orcamento(self, orcamento_data: dict):
        """Cria novo orçamento"""
        orcamento = Orcamento(**orcamento_data)
        self.db.add(orcamento)
        self.db.commit()
        self.db.refresh(orcamento)
        return orcamento
