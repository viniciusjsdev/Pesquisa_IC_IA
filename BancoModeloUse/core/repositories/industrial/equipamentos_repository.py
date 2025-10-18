# core/repositories/industrial/equipamentos_repository.py
"""
Repositório para operações de equipamentos industriais
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from core.models.industrial.equipamentos import Equipamento, ProcessoIndustrial
from core.repositories.base import BaseRepository

class EquipamentosRepository(BaseRepository):
    """Repositório para operações de equipamentos"""
    
    def get_all_equipamentos(self):
        """Retorna todos os equipamentos"""
        return self.db.query(Equipamento).all()
    
    def get_equipamento_by_id(self, equipamento_id: int):
        """Busca equipamento por ID"""
        return self.db.query(Equipamento).filter(
            Equipamento.id == equipamento_id
        ).first()
    
    def get_equipamentos_by_oee(self, oee_minimo: float):
        """Busca equipamentos por OEE mínimo"""
        return self.db.query(Equipamento).filter(
            Equipamento.oee >= oee_minimo
        ).all()
    
    def get_equipamentos_by_disponibilidade(self, disponibilidade_minima: float):
        """Busca equipamentos por disponibilidade mínima"""
        return self.db.query(Equipamento).filter(
            Equipamento.disponibilidade >= disponibilidade_minima
        ).all()
    
    def get_equipamentos_by_performance(self, performance_minima: float):
        """Busca equipamentos por performance mínima"""
        return self.db.query(Equipamento).filter(
            Equipamento.performance >= performance_minima
        ).all()
    
    def get_equipamentos_by_qualidade(self, qualidade_minima: float):
        """Busca equipamentos por qualidade mínima"""
        return self.db.query(Equipamento).filter(
            Equipamento.qualidade >= qualidade_minima
        ).all()
    
    def get_equipamentos_ordenados_por_oee(self):
        """Retorna equipamentos ordenados por OEE"""
        return self.db.query(Equipamento).order_by(desc(Equipamento.oee)).all()
    
    def get_equipamentos_ordenados_por_producao(self):
        """Retorna equipamentos ordenados por taxa de produção"""
        return self.db.query(Equipamento).order_by(desc(Equipamento.taxa_producao)).all()
    
    def get_media_oee_geral(self):
        """Calcula média OEE geral"""
        result = self.db.query(func.avg(Equipamento.oee)).first()
        return result[0] or 0
    
    def get_media_disponibilidade_geral(self):
        """Calcula média de disponibilidade geral"""
        result = self.db.query(func.avg(Equipamento.disponibilidade)).first()
        return result[0] or 0
    
    def get_media_performance_geral(self):
        """Calcula média de performance geral"""
        result = self.db.query(func.avg(Equipamento.performance)).first()
        return result[0] or 0
    
    def get_media_qualidade_geral(self):
        """Calcula média de qualidade geral"""
        result = self.db.query(func.avg(Equipamento.qualidade)).first()
        return result[0] or 0
    
    def get_all_processos_industriais(self):
        """Retorna todos os processos industriais"""
        return self.db.query(ProcessoIndustrial).all()
    
    def get_processo_by_id(self, processo_id: int):
        """Busca processo por ID"""
        return self.db.query(ProcessoIndustrial).filter(
            ProcessoIndustrial.id == processo_id
        ).first()
    
    def get_processos_by_nome(self, nome: str):
        """Busca processos por nome"""
        return self.db.query(ProcessoIndustrial).filter(
            ProcessoIndustrial.nome.ilike(f"%{nome}%")
        ).all()
    
    def create_equipamento(self, equipamento_data: dict):
        """Cria novo equipamento"""
        equipamento = Equipamento(**equipamento_data)
        self.db.add(equipamento)
        self.db.commit()
        self.db.refresh(equipamento)
        return equipamento
    
    def create_processo_industrial(self, processo_data: dict):
        """Cria novo processo industrial"""
        processo = ProcessoIndustrial(**processo_data)
        self.db.add(processo)
        self.db.commit()
        self.db.refresh(processo)
        return processo
    
    def update_equipamento_oee(self, equipamento_id: int, oee: float):
        """Atualiza OEE do equipamento"""
        equipamento = self.get_equipamento_by_id(equipamento_id)
        if equipamento:
            equipamento.oee = oee
            self.db.commit()
            return equipamento
        return None
    
    def update_equipamento_metricas(self, equipamento_id: int, metricas: dict):
        """Atualiza métricas do equipamento"""
        equipamento = self.get_equipamento_by_id(equipamento_id)
        if equipamento:
            for key, value in metricas.items():
                if hasattr(equipamento, key):
                    setattr(equipamento, key, value)
            self.db.commit()
            return equipamento
        return None
