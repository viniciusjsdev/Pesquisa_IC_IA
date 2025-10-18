# core/repositories/dw/kpis_repository.py
"""
Repositório para consultas analíticas e KPIs da DW
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from core.models.dw.agregados import (
    KPIFinanceiro, KPIIndustrial, KPIIntegrado, DashboardExecutivo
)
from core.repositories.base import BaseRepository

class KPIsRepository(BaseRepository):
    """Repositório para consultas analíticas e KPIs"""
    
    # Operações com KPIFinanceiro
    def get_all_kpis_financeiros(self):
        """Retorna todos os KPIs financeiros"""
        return self.db.query(KPIFinanceiro).all()
    
    def get_kpis_financeiros_by_periodo(self, data_inicio, data_fim):
        """Busca KPIs financeiros por período"""
        return self.db.query(KPIFinanceiro).filter(
            KPIFinanceiro.data_referencia.between(data_inicio, data_fim)
        ).all()
    
    def get_kpis_financeiros_by_tipo(self, periodo_tipo: str):
        """Busca KPIs financeiros por tipo de período"""
        return self.db.query(KPIFinanceiro).filter(
            KPIFinanceiro.periodo_tipo == periodo_tipo
        ).all()
    
    def get_ultimo_kpi_financeiro(self):
        """Retorna o último KPI financeiro"""
        return self.db.query(KPIFinanceiro).order_by(
            desc(KPIFinanceiro.data_referencia)
        ).first()
    
    # Operações com KPIIndustrial
    def get_all_kpis_industriais(self):
        """Retorna todos os KPIs industriais"""
        return self.db.query(KPIIndustrial).all()
    
    def get_kpis_industriais_by_periodo(self, data_inicio, data_fim):
        """Busca KPIs industriais por período"""
        return self.db.query(KPIIndustrial).filter(
            KPIIndustrial.data_referencia.between(data_inicio, data_fim)
        ).all()
    
    def get_kpis_industriais_by_maquina(self, maquina_sk: int):
        """Busca KPIs industriais por máquina"""
        return self.db.query(KPIIndustrial).filter(
            KPIIndustrial.maquina_sk == maquina_sk
        ).all()
    
    def get_kpis_industriais_by_tipo(self, periodo_tipo: str):
        """Busca KPIs industriais por tipo de período"""
        return self.db.query(KPIIndustrial).filter(
            KPIIndustrial.periodo_tipo == periodo_tipo
        ).all()
    
    def get_media_oee_geral(self):
        """Calcula média OEE geral"""
        result = self.db.query(func.avg(KPIIndustrial.oee_percentual)).first()
        return result[0] or 0
    
    def get_media_disponibilidade_geral(self):
        """Calcula média de disponibilidade geral"""
        result = self.db.query(func.avg(KPIIndustrial.disponibilidade_percentual)).first()
        return result[0] or 0
    
    # Operações com KPIIntegrado
    def get_all_kpis_integrados(self):
        """Retorna todos os KPIs integrados"""
        return self.db.query(KPIIntegrado).all()
    
    def get_kpis_integrados_by_periodo(self, data_inicio, data_fim):
        """Busca KPIs integrados por período"""
        return self.db.query(KPIIntegrado).filter(
            KPIIntegrado.data_referencia.between(data_inicio, data_fim)
        ).all()
    
    def get_kpis_integrados_by_produto(self, produto_sk: int):
        """Busca KPIs integrados por produto"""
        return self.db.query(KPIIntegrado).filter(
            KPIIntegrado.produto_sk == produto_sk
        ).all()
    
    def get_kpis_integrados_by_tipo(self, periodo_tipo: str):
        """Busca KPIs integrados por tipo de período"""
        return self.db.query(KPIIntegrado).filter(
            KPIIntegrado.periodo_tipo == periodo_tipo
        ).all()
    
    def get_anomalias_detectadas(self, data_inicio, data_fim):
        """Busca anomalias detectadas no período"""
        return self.db.query(KPIIntegrado).filter(
            and_(
                KPIIntegrado.data_referencia.between(data_inicio, data_fim),
                KPIIntegrado.anomalia_custo != 'normal'
            )
        ).all()
    
    def get_correlacoes_energia_lucro(self, data_inicio, data_fim):
        """Busca correlações entre energia e lucro"""
        return self.db.query(KPIIntegrado).filter(
            and_(
                KPIIntegrado.data_referencia.between(data_inicio, data_fim),
                KPIIntegrado.correlacao_energia_lucro.isnot(None)
            )
        ).all()
    
    # Operações com DashboardExecutivo
    def get_all_dashboards(self):
        """Retorna todos os dashboards executivos"""
        return self.db.query(DashboardExecutivo).all()
    
    def get_dashboard_by_periodo(self, data_inicio, data_fim):
        """Busca dashboard por período"""
        return self.db.query(DashboardExecutivo).filter(
            DashboardExecutivo.data_referencia.between(data_inicio, data_fim)
        ).all()
    
    def get_dashboard_by_tipo(self, periodo_tipo: str):
        """Busca dashboard por tipo de período"""
        return self.db.query(DashboardExecutivo).filter(
            DashboardExecutivo.periodo_tipo == periodo_tipo
        ).all()
    
    def get_ultimo_dashboard(self):
        """Retorna o último dashboard"""
        return self.db.query(DashboardExecutivo).order_by(
            desc(DashboardExecutivo.data_referencia)
        ).first()
    
    def get_dashboards_criticos(self):
        """Retorna dashboards com status crítico"""
        return self.db.query(DashboardExecutivo).filter(
            DashboardExecutivo.status_geral == 'critico'
        ).all()
    
    def get_dashboards_atencao(self):
        """Retorna dashboards que precisam de atenção"""
        return self.db.query(DashboardExecutivo).filter(
            DashboardExecutivo.status_geral.in_(['atencao', 'critico'])
        ).all()
    
    # Consultas analíticas complexas
    def get_analise_correlacao_financeira_industrial(self, data_inicio, data_fim):
        """Análise de correlação entre dados financeiros e industriais"""
        return self.db.query(
            KPIIntegrado.produto_sk,
            KPIIntegrado.receita_por_unidade_produzida,
            KPIIntegrado.custo_por_unidade_produzida,
            KPIIntegrado.margem_por_unidade,
            KPIIntegrado.eficiencia_producao_vs_vendas,
            KPIIntegrado.correlacao_custo_qualidade,
            KPIIntegrado.correlacao_energia_lucro,
            KPIIntegrado.anomalia_custo,
            KPIIntegrado.anomalia_producao,
            KPIIntegrado.anomalia_qualidade
        ).filter(
            KPIIntegrado.data_referencia.between(data_inicio, data_fim)
        ).all()
    
    def get_tendencia_kpis_periodo(self, data_inicio, data_fim, periodo_tipo: str):
        """Análise de tendência de KPIs no período"""
        return self.db.query(
            KPIFinanceiro.data_referencia,
            KPIFinanceiro.receita_total,
            KPIFinanceiro.margem_bruta,
            KPIFinanceiro.roi_percentual,
            KPIIndustrial.oee_percentual,
            KPIIndustrial.disponibilidade_percentual,
            KPIIndustrial.performance_percentual,
            KPIIndustrial.qualidade_percentual
        ).join(
            KPIIndustrial, 
            KPIFinanceiro.tempo_sk == KPIIndustrial.tempo_sk
        ).filter(
            and_(
                KPIFinanceiro.data_referencia.between(data_inicio, data_fim),
                KPIFinanceiro.periodo_tipo == periodo_tipo
            )
        ).order_by(KPIFinanceiro.data_referencia).all()
    
    def get_ranking_produtos_lucratividade(self, data_inicio, data_fim):
        """Ranking de produtos por lucratividade"""
        return self.db.query(
            KPIIntegrado.produto_sk,
            KPIIntegrado.receita_por_unidade_produzida,
            KPIIntegrado.custo_por_unidade_produzida,
            KPIIntegrado.margem_por_unidade
        ).filter(
            KPIIntegrado.data_referencia.between(data_inicio, data_fim)
        ).order_by(desc(KPIIntegrado.margem_por_unidade)).all()
    
    def get_ranking_maquinas_eficiencia(self, data_inicio, data_fim):
        """Ranking de máquinas por eficiência"""
        return self.db.query(
            KPIIndustrial.maquina_sk,
            KPIIndustrial.oee_percentual,
            KPIIndustrial.disponibilidade_percentual,
            KPIIndustrial.performance_percentual,
            KPIIndustrial.qualidade_percentual
        ).filter(
            KPIIndustrial.data_referencia.between(data_inicio, data_fim)
        ).order_by(desc(KPIIndustrial.oee_percentual)).all()
    
    # Métodos de criação
    def create_kpi_financeiro(self, kpi_data: dict):
        """Cria novo KPI financeiro"""
        kpi = KPIFinanceiro(**kpi_data)
        self.db.add(kpi)
        self.db.commit()
        self.db.refresh(kpi)
        return kpi
    
    def create_kpi_industrial(self, kpi_data: dict):
        """Cria novo KPI industrial"""
        kpi = KPIIndustrial(**kpi_data)
        self.db.add(kpi)
        self.db.commit()
        self.db.refresh(kpi)
        return kpi
    
    def create_kpi_integrado(self, kpi_data: dict):
        """Cria novo KPI integrado"""
        kpi = KPIIntegrado(**kpi_data)
        self.db.add(kpi)
        self.db.commit()
        self.db.refresh(kpi)
        return kpi
    
    def create_dashboard_executivo(self, dashboard_data: dict):
        """Cria novo dashboard executivo"""
        dashboard = DashboardExecutivo(**dashboard_data)
        self.db.add(dashboard)
        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard
