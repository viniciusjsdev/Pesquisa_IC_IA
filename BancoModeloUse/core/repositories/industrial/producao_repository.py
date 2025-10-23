# core/repositories/industrial/producao_repository.py
"""
Repositório para operações de produção industrial
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from core.models.industrial.producao import (
    OrdemProducao, RoteiroProducao, OperacaoRoteiro, RegistroOperacao,
    ParadaMaquina, ConsumoMaterial, LoteMaterial, LoteProducao
)
from core.repositories.base import BaseRepository

class ProducaoRepository(BaseRepository):
    """Repositório para operações de produção"""
    
    def get_ordem_producao(self, ordem_id: int):
        """Busca ordem de produção por ID"""
        return self.db.query(OrdemProducao).filter(
            OrdemProducao.ordem_producao_id == ordem_id
        ).first()
    
    def get_all_ordens_producao(self):
        """Retorna todas as ordens de produção"""
        return self.db.query(OrdemProducao).all()
    
    def get_ordens_by_status(self, status: str):
        """Busca ordens por status"""
        return self.db.query(OrdemProducao).filter(
            OrdemProducao.status_ordem == status
        ).all()
    
    def get_ordens_by_periodo(self, data_inicio, data_fim):
        """Busca ordens por período"""
        return self.db.query(OrdemProducao).filter(
            OrdemProducao.data_planejamento.between(data_inicio, data_fim)
        ).all()
    
    def get_registros_operacao_by_ordem(self, ordem_id: int):
        """Busca registros de operação por ordem"""
        return self.db.query(RegistroOperacao).filter(
            RegistroOperacao.ordem_producao_id == ordem_id
        ).all()
    
    def get_registros_operacao_by_maquina(self, maquina_id: int):
        """Busca registros de operação por máquina"""
        return self.db.query(RegistroOperacao).filter(
            RegistroOperacao.maquina_id == maquina_id
        ).all()
    
    def get_registros_operacao_by_periodo(self, data_inicio, data_fim):
        """Busca registros de operação por período"""
        return self.db.query(RegistroOperacao).filter(
            RegistroOperacao.hora_inicio.between(data_inicio, data_fim)
        ).all()
    
    def get_paradas_maquina_by_maquina(self, maquina_id: int):
        """Busca paradas de máquina por máquina"""
        return self.db.query(ParadaMaquina).filter(
            ParadaMaquina.maquina_id == maquina_id
        ).all()
    
    def get_paradas_maquina_by_periodo(self, maquina_id: int, data_inicio, data_fim):
        """Busca paradas de máquina por período"""
        return self.db.query(ParadaMaquina).filter(
            ParadaMaquina.maquina_id == maquina_id,
            ParadaMaquina.hora_inicio_parada.between(data_inicio, data_fim)
        ).all()
    
    def get_consumo_material_by_registro(self, registro_id: int):
        """Busca consumo de material por registro"""
        return self.db.query(ConsumoMaterial).filter(
            ConsumoMaterial.registro_id == registro_id
        ).all()
    
    def get_lotes_producao_by_ordem(self, ordem_id: int):
        """Busca lotes de produção por ordem"""
        return self.db.query(LoteProducao).filter(
            LoteProducao.ordem_producao_id == ordem_id
        ).all()
    
    def get_producao_total_periodo(self, data_inicio, data_fim):
        """Calcula produção total por período"""
        result = self.db.query(
            func.sum(RegistroOperacao.quantidade_produzida_real).label('total_produzido'),
            func.sum(RegistroOperacao.consumo_energia_kwh).label('total_energia'),
            func.avg(RegistroOperacao.quantidade_produzida_real).label('media_producao')
        ).filter(
            RegistroOperacao.hora_inicio.between(data_inicio, data_fim)
        ).first()
        
        return {
            'total_produzido': result.total_produzido or 0,
            'total_energia': result.total_energia or 0,
            'media_producao': result.media_producao or 0
        }
    
    def get_producao_por_maquina_periodo(self, data_inicio, data_fim):
        """Agrupa produção por máquina no período"""
        return self.db.query(
            RegistroOperacao.maquina_id,
            func.sum(RegistroOperacao.quantidade_produzida_real).label('total_produzido'),
            func.sum(RegistroOperacao.consumo_energia_kwh).label('total_energia'),
            func.count(RegistroOperacao.registro_id).label('total_registros')
        ).filter(
            RegistroOperacao.hora_inicio.between(data_inicio, data_fim)
        ).group_by(RegistroOperacao.maquina_id).all()
    
    def create_ordem_producao(self, ordem_data: dict):
        """Cria nova ordem de produção"""
        ordem = OrdemProducao(**ordem_data)
        self.db.add(ordem)
        self.db.commit()
        self.db.refresh(ordem)
        return ordem
    
    def create_registro_operacao(self, registro_data: dict):
        """Cria novo registro de operação"""
        registro = RegistroOperacao(**registro_data)
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro
