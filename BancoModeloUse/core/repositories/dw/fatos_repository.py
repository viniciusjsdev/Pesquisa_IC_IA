# core/repositories/dw/fatos_repository.py
"""
Repositório para operações em fatos da DW
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from core.models.dw.fatos import (
    FatoVendas, FatoProducao, FatoCustos, FatoQualidade, FatoEnergia
)
from core.repositories.base import BaseRepository

class FatosRepository(BaseRepository):
    """Repositório para operações em fatos"""
    
    # Operações com FatoVendas
    def get_all_vendas(self):
        """Retorna todas as vendas"""
        return self.db.query(FatoVendas).all()
    
    def get_vendas_by_periodo(self, data_inicio, data_fim):
        """Busca vendas por período"""
        return self.db.query(FatoVendas).filter(
            FatoVendas.data_venda.between(data_inicio, data_fim)
        ).all()
    
    def get_vendas_by_produto(self, produto_sk: int):
        """Busca vendas por produto"""
        return self.db.query(FatoVendas).filter(
            FatoVendas.produto_sk == produto_sk
        ).all()
    
    def get_vendas_by_cliente(self, cliente_sk: int):
        """Busca vendas por cliente"""
        return self.db.query(FatoVendas).filter(
            FatoVendas.cliente_sk == cliente_sk
        ).all()
    
    def get_total_vendas_periodo(self, data_inicio, data_fim):
        """Calcula total de vendas por período"""
        result = self.db.query(
            func.sum(FatoVendas.quantidade_vendida).label('total_quantidade'),
            func.sum(FatoVendas.valor_total).label('total_valor'),
            func.avg(FatoVendas.valor_unitario).label('preco_medio')
        ).filter(
            FatoVendas.data_venda.between(data_inicio, data_fim)
        ).first()
        
        return {
            'total_quantidade': result.total_quantidade or 0,
            'total_valor': result.total_valor or 0,
            'preco_medio': result.preco_medio or 0
        }
    
    # Operações com FatoProducao
    def get_all_producao(self):
        """Retorna toda a produção"""
        return self.db.query(FatoProducao).all()
    
    def get_producao_by_periodo(self, data_inicio, data_fim):
        """Busca produção por período"""
        return self.db.query(FatoProducao).filter(
            FatoProducao.data_producao.between(data_inicio, data_fim)
        ).all()
    
    def get_producao_by_produto(self, produto_sk: int):
        """Busca produção por produto"""
        return self.db.query(FatoProducao).filter(
            FatoProducao.produto_sk == produto_sk
        ).all()
    
    def get_producao_by_maquina(self, maquina_sk: int):
        """Busca produção por máquina"""
        return self.db.query(FatoProducao).filter(
            FatoProducao.maquina_sk == maquina_sk
        ).all()
    
    def get_total_producao_periodo(self, data_inicio, data_fim):
        """Calcula total de produção por período"""
        result = self.db.query(
            func.sum(FatoProducao.quantidade_produzida).label('total_produzido'),
            func.sum(FatoProducao.consumo_energia_kwh).label('total_energia'),
            func.avg(FatoProducao.eficiencia_percent).label('eficiencia_media')
        ).filter(
            FatoProducao.data_producao.between(data_inicio, data_fim)
        ).first()
        
        return {
            'total_produzido': result.total_produzido or 0,
            'total_energia': result.total_energia or 0,
            'eficiencia_media': result.eficiencia_media or 0
        }
    
    # Operações com FatoCustos
    def get_all_custos(self):
        """Retorna todos os custos"""
        return self.db.query(FatoCustos).all()
    
    def get_custos_by_periodo(self, data_inicio, data_fim):
        """Busca custos por período"""
        return self.db.query(FatoCustos).filter(
            FatoCustos.data_custo.between(data_inicio, data_fim)
        ).all()
    
    def get_custos_by_produto(self, produto_sk: int):
        """Busca custos por produto"""
        return self.db.query(FatoCustos).filter(
            FatoCustos.produto_sk == produto_sk
        ).all()
    
    def get_custos_by_maquina(self, maquina_sk: int):
        """Busca custos por máquina"""
        return self.db.query(FatoCustos).filter(
            FatoCustos.maquina_sk == maquina_sk
        ).all()
    
    def get_total_custos_periodo(self, data_inicio, data_fim):
        """Calcula total de custos por período"""
        result = self.db.query(
            func.sum(FatoCustos.custo_total).label('total_custos'),
            func.avg(FatoCustos.custo_unitario).label('custo_unitario_medio')
        ).filter(
            FatoCustos.data_custo.between(data_inicio, data_fim)
        ).first()
        
        return {
            'total_custos': result.total_custos or 0,
            'custo_unitario_medio': result.custo_unitario_medio or 0
        }
    
    # Operações com FatoQualidade
    def get_all_qualidade(self):
        """Retorna todos os registros de qualidade"""
        return self.db.query(FatoQualidade).all()
    
    def get_qualidade_by_periodo(self, data_inicio, data_fim):
        """Busca qualidade por período"""
        return self.db.query(FatoQualidade).filter(
            FatoQualidade.data_qualidade.between(data_inicio, data_fim)
        ).all()
    
    def get_qualidade_by_produto(self, produto_sk: int):
        """Busca qualidade por produto"""
        return self.db.query(FatoQualidade).filter(
            FatoQualidade.produto_sk == produto_sk
        ).all()
    
    def get_qualidade_by_maquina(self, maquina_sk: int):
        """Busca qualidade por máquina"""
        return self.db.query(FatoQualidade).filter(
            FatoQualidade.maquina_sk == maquina_sk
        ).all()
    
    def get_taxa_defeitos_periodo(self, data_inicio, data_fim):
        """Calcula taxa de defeitos por período"""
        result = self.db.query(
            func.sum(FatoQualidade.unidades_inspecionadas).label('total_inspecionadas'),
            func.sum(FatoQualidade.unidades_rejeitadas).label('total_rejeitadas'),
            func.avg(FatoQualidade.taxa_defeito_percent).label('taxa_defeito_media')
        ).filter(
            FatoQualidade.data_qualidade.between(data_inicio, data_fim)
        ).first()
        
        return {
            'total_inspecionadas': result.total_inspecionadas or 0,
            'total_rejeitadas': result.total_rejeitadas or 0,
            'taxa_defeito_media': result.taxa_defeito_media or 0
        }
    
    # Operações com FatoEnergia
    def get_all_energia(self):
        """Retorna todos os registros de energia"""
        return self.db.query(FatoEnergia).all()
    
    def get_energia_by_periodo(self, data_inicio, data_fim):
        """Busca energia por período"""
        return self.db.query(FatoEnergia).filter(
            FatoEnergia.data_energia.between(data_inicio, data_fim)
        ).all()
    
    def get_energia_by_maquina(self, maquina_sk: int):
        """Busca energia por máquina"""
        return self.db.query(FatoEnergia).filter(
            FatoEnergia.maquina_sk == maquina_sk
        ).all()
    
    def get_total_energia_periodo(self, data_inicio, data_fim):
        """Calcula total de energia por período"""
        result = self.db.query(
            func.sum(FatoEnergia.consumo_total_kwh).label('total_energia'),
            func.avg(FatoEnergia.eficiencia_energetica).label('eficiencia_media')
        ).filter(
            FatoEnergia.data_energia.between(data_inicio, data_fim)
        ).first()
        
        return {
            'total_energia': result.total_energia or 0,
            'eficiencia_media': result.eficiencia_media or 0
        }
    
    # Métodos de criação
    def create_venda(self, venda_data: dict):
        """Cria novo fato de venda"""
        venda = FatoVendas(**venda_data)
        self.db.add(venda)
        self.db.commit()
        self.db.refresh(venda)
        return venda
    
    def create_producao(self, producao_data: dict):
        """Cria novo fato de produção"""
        producao = FatoProducao(**producao_data)
        self.db.add(producao)
        self.db.commit()
        self.db.refresh(producao)
        return producao
    
    def create_custo(self, custo_data: dict):
        """Cria novo fato de custo"""
        custo = FatoCustos(**custo_data)
        self.db.add(custo)
        self.db.commit()
        self.db.refresh(custo)
        return custo
    
    def create_qualidade(self, qualidade_data: dict):
        """Cria novo fato de qualidade"""
        qualidade = FatoQualidade(**qualidade_data)
        self.db.add(qualidade)
        self.db.commit()
        self.db.refresh(qualidade)
        return qualidade
    
    def create_energia(self, energia_data: dict):
        """Cria novo fato de energia"""
        energia = FatoEnergia(**energia_data)
        self.db.add(energia)
        self.db.commit()
        self.db.refresh(energia)
        return energia
