# core/repositories/industrial/qualidade_repository.py
"""
Repositório para operações de qualidade industrial
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from core.models.industrial.qualidade import (
    ControleQualidade, Defeito, RegistroDefeito
)
from core.repositories.base import BaseRepository

class QualidadeRepository(BaseRepository):
    """Repositório para operações de qualidade"""
    
    def get_all_controles_qualidade(self):
        """Retorna todos os controles de qualidade"""
        return self.db.query(ControleQualidade).all()
    
    def get_controle_qualidade_by_id(self, controle_id: int):
        """Busca controle de qualidade por ID"""
        return self.db.query(ControleQualidade).filter(
            ControleQualidade.controle_id == controle_id
        ).first()
    
    def get_controles_qualidade_by_lote(self, lote_id: int):
        """Busca controles de qualidade por lote"""
        return self.db.query(ControleQualidade).filter(
            ControleQualidade.lote_producao_id == lote_id
        ).all()
    
    def get_controles_qualidade_by_periodo(self, data_inicio, data_fim):
        """Busca controles de qualidade por período"""
        return self.db.query(ControleQualidade).filter(
            ControleQualidade.data_inspecao.between(data_inicio, data_fim)
        ).all()
    
    def get_controles_qualidade_by_inspetor(self, inspetor_id: int):
        """Busca controles de qualidade por inspetor"""
        return self.db.query(ControleQualidade).filter(
            ControleQualidade.inspetor_id == inspetor_id
        ).all()
    
    def get_taxa_defeitos_periodo(self, data_inicio, data_fim):
        """Calcula taxa de defeitos por período"""
        result = self.db.query(
            func.sum(ControleQualidade.unidades_inspecionadas).label('total_inspecionadas'),
            func.sum(ControleQualidade.unidades_rejeitadas).label('total_rejeitadas')
        ).filter(
            ControleQualidade.data_inspecao.between(data_inicio, data_fim)
        ).first()
        
        total_inspecionadas = result.total_inspecionadas or 0
        total_rejeitadas = result.total_rejeitadas or 0
        
        if total_inspecionadas > 0:
            taxa_defeitos = (total_rejeitadas / total_inspecionadas) * 100
        else:
            taxa_defeitos = 0
        
        return {
            'total_inspecionadas': total_inspecionadas,
            'total_rejeitadas': total_rejeitadas,
            'taxa_defeitos_percent': taxa_defeitos
        }
    
    def get_taxa_defeitos_por_lote(self, lote_id: int):
        """Calcula taxa de defeitos por lote"""
        result = self.db.query(
            func.sum(ControleQualidade.unidades_inspecionadas).label('total_inspecionadas'),
            func.sum(ControleQualidade.unidades_rejeitadas).label('total_rejeitadas')
        ).filter(
            ControleQualidade.lote_producao_id == lote_id
        ).first()
        
        total_inspecionadas = result.total_inspecionadas or 0
        total_rejeitadas = result.total_rejeitadas or 0
        
        if total_inspecionadas > 0:
            taxa_defeitos = (total_rejeitadas / total_inspecionadas) * 100
        else:
            taxa_defeitos = 0
        
        return {
            'lote_id': lote_id,
            'total_inspecionadas': total_inspecionadas,
            'total_rejeitadas': total_rejeitadas,
            'taxa_defeitos_percent': taxa_defeitos
        }
    
    def get_all_defeitos(self):
        """Retorna todos os defeitos"""
        return self.db.query(Defeito).all()
    
    def get_defeito_by_id(self, defeito_id: int):
        """Busca defeito por ID"""
        return self.db.query(Defeito).filter(
            Defeito.defeito_id == defeito_id
        ).first()
    
    def get_defeito_by_nome(self, nome_defeito: str):
        """Busca defeito por nome"""
        return self.db.query(Defeito).filter(
            Defeito.nome_defeito.ilike(f"%{nome_defeito}%")
        ).all()
    
    def get_registros_defeitos_by_controle(self, controle_id: int):
        """Busca registros de defeitos por controle"""
        return self.db.query(RegistroDefeito).filter(
            RegistroDefeito.controle_id == controle_id
        ).all()
    
    def get_registros_defeitos_by_defeito(self, defeito_id: int):
        """Busca registros de defeitos por tipo de defeito"""
        return self.db.query(RegistroDefeito).filter(
            RegistroDefeito.defeito_id == defeito_id
        ).all()
    
    def get_quantidade_defeitos_por_tipo(self, data_inicio, data_fim):
        """Agrupa quantidade de defeitos por tipo"""
        return self.db.query(
            RegistroDefeito.defeito_id,
            Defeito.nome_defeito,
            func.sum(RegistroDefeito.quantidade_defeito).label('total_defeitos')
        ).join(Defeito, RegistroDefeito.defeito_id == Defeito.defeito_id)\
         .join(ControleQualidade, RegistroDefeito.controle_id == ControleQualidade.controle_id)\
         .filter(ControleQualidade.data_inspecao.between(data_inicio, data_fim))\
         .group_by(RegistroDefeito.defeito_id, Defeito.nome_defeito)\
         .order_by(desc('total_defeitos')).all()
    
    def create_controle_qualidade(self, controle_data: dict):
        """Cria novo controle de qualidade"""
        controle = ControleQualidade(**controle_data)
        self.db.add(controle)
        self.db.commit()
        self.db.refresh(controle)
        return controle
    
    def create_defeito(self, defeito_data: dict):
        """Cria novo defeito"""
        defeito = Defeito(**defeito_data)
        self.db.add(defeito)
        self.db.commit()
        self.db.refresh(defeito)
        return defeito
    
    def create_registro_defeito(self, registro_data: dict):
        """Cria novo registro de defeito"""
        registro = RegistroDefeito(**registro_data)
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro
