# core/rag/tools/integracao_tools.py
"""
Ferramentas RAG para consultas integradas (DW)
"""
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from infrastructure.database.sessions import get_dw_db
from core.repositories.dw import FatosRepository, KPIsRepository
import json

class IntegracaoTools:
    """Ferramentas para consultas integradas na DW"""
    
    def __init__(self):
        self.fatos_repo = None
        self.kpis_repo = None
    
    def _get_repositories(self, db_session):
        """Inicializa repositórios com sessão"""
        if not self.fatos_repo:
            self.fatos_repo = FatosRepository(db_session)
        if not self.kpis_repo:
            self.kpis_repo = KPIsRepository(db_session)
    
    def join_financeiro_industrial(self, consulta: str, parametros: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executa consulta integrada financeiro-industrial
        
        Args:
            consulta: Tipo de consulta ('vendas_producao', 'custos_eficiencia', 'qualidade_lucratividade')
            parametros: Parâmetros da consulta (data_inicio, data_fim, produto_sk, etc.)
        
        Returns:
            Dict com resultados da consulta integrada
        """
        if not parametros:
            parametros = {}
        
        data_inicio = parametros.get('data_inicio')
        data_fim = parametros.get('data_fim')
        
        with get_dw_db() as db:
            self._get_repositories(db)
            
            if consulta == 'vendas_producao':
                return self._consultar_vendas_producao(data_inicio, data_fim, parametros)
            elif consulta == 'custos_eficiencia':
                return self._consultar_custos_eficiencia(data_inicio, data_fim, parametros)
            elif consulta == 'qualidade_lucratividade':
                return self._consultar_qualidade_lucratividade(data_inicio, data_fim, parametros)
            elif consulta == 'kpis_integrados':
                return self._consultar_kpis_integrados(data_inicio, data_fim, parametros)
            else:
                return {'erro': f'Tipo de consulta não suportado: {consulta}'}
    
    def _consultar_vendas_producao(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta integrada vendas vs produção"""
        try:
            # Buscar vendas
            vendas = self.fatos_repo.get_vendas_by_periodo(data_inicio, data_fim)
            
            # Buscar produção
            producao = self.fatos_repo.get_producao_by_periodo(data_inicio, data_fim)
            
            # Filtrar por produto se especificado
            produto_sk = parametros.get('produto_sk')
            if produto_sk:
                vendas = [v for v in vendas if v.produto_sk == produto_sk]
                producao = [p for p in producao if p.produto_sk == produto_sk]
            
            # Calcular totais
            total_vendas = sum(v.quantidade_vendida for v in vendas)
            total_producao = sum(p.quantidade_produzida for p in producao)
            total_receita = sum(v.valor_total for v in vendas)
            
            # Calcular eficiência vendas vs produção
            eficiencia_vendas = (total_vendas / total_producao * 100) if total_producao > 0 else 0
            
            return {
                'tipo': 'vendas_producao',
                'periodo': {'inicio': data_inicio.isoformat(), 'fim': data_fim.isoformat()},
                'total_vendas': total_vendas,
                'total_producao': total_producao,
                'total_receita': float(total_receita),
                'eficiencia_vendas_percent': eficiencia_vendas,
                'dados_vendas': [
                    {
                        'produto_sk': v.produto_sk,
                        'quantidade_vendida': v.quantidade_vendida,
                        'valor_total': float(v.valor_total),
                        'data_venda': v.data_venda.isoformat() if v.data_venda else None
                    } for v in vendas
                ],
                'dados_producao': [
                    {
                        'produto_sk': p.produto_sk,
                        'maquina_sk': p.maquina_sk,
                        'quantidade_produzida': p.quantidade_produzida,
                        'eficiencia_percent': float(p.eficiencia_percent) if p.eficiencia_percent else 0,
                        'data_producao': p.data_producao.isoformat() if p.data_producao else None
                    } for p in producao
                ]
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar vendas vs produção: {str(e)}'}
    
    def _consultar_custos_eficiencia(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta integrada custos vs eficiência"""
        try:
            # Buscar custos
            custos = self.fatos_repo.get_custos_by_periodo(data_inicio, data_fim)
            
            # Buscar produção
            producao = self.fatos_repo.get_producao_by_periodo(data_inicio, data_fim)
            
            # Filtrar por produto se especificado
            produto_sk = parametros.get('produto_sk')
            if produto_sk:
                custos = [c for c in custos if c.produto_sk == produto_sk]
                producao = [p for p in producao if p.produto_sk == produto_sk]
            
            # Calcular totais
            total_custos = sum(float(c.custo_total) for c in custos if c.custo_total)
            total_producao = sum(p.quantidade_produzida for p in producao)
            media_eficiencia = sum(float(p.eficiencia_percent) for p in producao if p.eficiencia_percent) / len(producao) if producao else 0
            
            # Calcular custo por unidade
            custo_por_unidade = total_custos / total_producao if total_producao > 0 else 0
            
            return {
                'tipo': 'custos_eficiencia',
                'periodo': {'inicio': data_inicio.isoformat(), 'fim': data_fim.isoformat()},
                'total_custos': total_custos,
                'total_producao': total_producao,
                'custo_por_unidade': custo_por_unidade,
                'media_eficiencia_percent': media_eficiencia,
                'dados_custos': [
                    {
                        'produto_sk': c.produto_sk,
                        'maquina_sk': c.maquina_sk,
                        'custo_total': float(c.custo_total) if c.custo_total else 0,
                        'custo_unitario': float(c.custo_unitario) if c.custo_unitario else 0,
                        'data_custo': c.data_custo.isoformat() if c.data_custo else None
                    } for c in custos
                ],
                'dados_producao': [
                    {
                        'produto_sk': p.produto_sk,
                        'maquina_sk': p.maquina_sk,
                        'quantidade_produzida': p.quantidade_produzida,
                        'eficiencia_percent': float(p.eficiencia_percent) if p.eficiencia_percent else 0,
                        'data_producao': p.data_producao.isoformat() if p.data_producao else None
                    } for p in producao
                ]
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar custos vs eficiência: {str(e)}'}
    
    def _consultar_qualidade_lucratividade(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta integrada qualidade vs lucratividade"""
        try:
            # Buscar qualidade
            qualidade = self.fatos_repo.get_qualidade_by_periodo(data_inicio, data_fim)
            
            # Buscar vendas
            vendas = self.fatos_repo.get_vendas_by_periodo(data_inicio, data_fim)
            
            # Filtrar por produto se especificado
            produto_sk = parametros.get('produto_sk')
            if produto_sk:
                qualidade = [q for q in qualidade if q.produto_sk == produto_sk]
                vendas = [v for v in vendas if v.produto_sk == produto_sk]
            
            # Calcular totais
            total_inspecionadas = sum(q.unidades_inspecionadas for q in qualidade)
            total_rejeitadas = sum(q.unidades_rejeitadas for q in qualidade)
            total_receita = sum(v.valor_total for v in vendas)
            
            # Calcular taxa de defeitos
            taxa_defeitos = (total_rejeitadas / total_inspecionadas * 100) if total_inspecionadas > 0 else 0
            
            # Calcular impacto financeiro dos defeitos
            impacto_defeitos = total_receita * (taxa_defeitos / 100)
            
            return {
                'tipo': 'qualidade_lucratividade',
                'periodo': {'inicio': data_inicio.isoformat(), 'fim': data_fim.isoformat()},
                'total_inspecionadas': total_inspecionadas,
                'total_rejeitadas': total_rejeitadas,
                'taxa_defeitos_percent': taxa_defeitos,
                'total_receita': float(total_receita),
                'impacto_defeitos': float(impacto_defeitos),
                'dados_qualidade': [
                    {
                        'produto_sk': q.produto_sk,
                        'maquina_sk': q.maquina_sk,
                        'unidades_inspecionadas': q.unidades_inspecionadas,
                        'unidades_rejeitadas': q.unidades_rejeitadas,
                        'taxa_defeito_percent': float(q.taxa_defeito_percent) if q.taxa_defeito_percent else 0,
                        'data_qualidade': q.data_qualidade.isoformat() if q.data_qualidade else None
                    } for q in qualidade
                ],
                'dados_vendas': [
                    {
                        'produto_sk': v.produto_sk,
                        'quantidade_vendida': v.quantidade_vendida,
                        'valor_total': float(v.valor_total),
                        'data_venda': v.data_venda.isoformat() if v.data_venda else None
                    } for v in vendas
                ]
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar qualidade vs lucratividade: {str(e)}'}
    
    def _consultar_kpis_integrados(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta KPIs integrados"""
        try:
            # Buscar KPIs integrados
            kpis_integrados = self.kpis_repo.get_kpis_integrados_by_periodo(data_inicio, data_fim)
            
            # Filtrar por produto se especificado
            produto_sk = parametros.get('produto_sk')
            if produto_sk:
                kpis_integrados = [k for k in kpis_integrados if k.produto_sk == produto_sk]
            
            # Calcular médias
            media_receita_por_unidade = sum(float(k.receita_por_unidade_produzida) for k in kpis_integrados if k.receita_por_unidade_produzida) / len(kpis_integrados) if kpis_integrados else 0
            media_custo_por_unidade = sum(float(k.custo_por_unidade_produzida) for k in kpis_integrados if k.custo_por_unidade_produzida) / len(kpis_integrados) if kpis_integrados else 0
            media_margem_por_unidade = sum(float(k.margem_por_unidade) for k in kpis_integrados if k.margem_por_unidade) / len(kpis_integrados) if kpis_integrados else 0
            
            # Contar anomalias
            anomalias_custo = len([k for k in kpis_integrados if k.anomalia_custo != 'normal'])
            anomalias_producao = len([k for k in kpis_integrados if k.anomalia_producao != 'normal'])
            anomalias_qualidade = len([k for k in kpis_integrados if k.anomalia_qualidade != 'normal'])
            
            return {
                'tipo': 'kpis_integrados',
                'periodo': {'inicio': data_inicio.isoformat(), 'fim': data_fim.isoformat()},
                'total_kpis': len(kpis_integrados),
                'media_receita_por_unidade': media_receita_por_unidade,
                'media_custo_por_unidade': media_custo_por_unidade,
                'media_margem_por_unidade': media_margem_por_unidade,
                'anomalias_custo': anomalias_custo,
                'anomalias_producao': anomalias_producao,
                'anomalias_qualidade': anomalias_qualidade,
                'dados': [
                    {
                        'produto_sk': k.produto_sk,
                        'receita_por_unidade_produzida': float(k.receita_por_unidade_produzida) if k.receita_por_unidade_produzida else 0,
                        'custo_por_unidade_produzida': float(k.custo_por_unidade_produzida) if k.custo_por_unidade_produzida else 0,
                        'margem_por_unidade': float(k.margem_por_unidade) if k.margem_por_unidade else 0,
                        'eficiencia_producao_vs_vendas': float(k.eficiencia_producao_vs_vendas) if k.eficiencia_producao_vs_vendas else 0,
                        'correlacao_custo_qualidade': float(k.correlacao_custo_qualidade) if k.correlacao_custo_qualidade else 0,
                        'correlacao_energia_lucro': float(k.correlacao_energia_lucro) if k.correlacao_energia_lucro else 0,
                        'anomalia_custo': k.anomalia_custo,
                        'anomalia_producao': k.anomalia_producao,
                        'anomalia_qualidade': k.anomalia_qualidade,
                        'data_referencia': k.data_referencia.isoformat() if k.data_referencia else None
                    } for k in kpis_integrados
                ]
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar KPIs integrados: {str(e)}'}
    
    def obter_dashboard_executivo(self, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """Obtém dashboard executivo consolidado"""
        try:
            with get_dw_db() as db:
                self._get_repositories(db)
                
                # Buscar dashboard executivo
                dashboards = self.kpis_repo.get_dashboard_by_periodo(data_inicio, data_fim)
                
                if not dashboards:
                    return {'erro': 'Nenhum dashboard executivo encontrado para o período'}
                
                # Pegar o mais recente
                dashboard = max(dashboards, key=lambda d: d.data_referencia)
                
                return {
                    'periodo': {'inicio': data_inicio.isoformat(), 'fim': data_fim.isoformat()},
                    'receita_total': float(dashboard.receita_total) if dashboard.receita_total else 0,
                    'lucro_bruto': float(dashboard.lucro_bruto) if dashboard.lucro_bruto else 0,
                    'margem_bruta_percentual': float(dashboard.margem_bruta_percentual) if dashboard.margem_bruta_percentual else 0,
                    'producao_total': dashboard.producao_total,
                    'eficiencia_media_percentual': float(dashboard.eficiencia_media_percentual) if dashboard.eficiencia_media_percentual else 0,
                    'qualidade_media_percentual': float(dashboard.qualidade_media_percentual) if dashboard.qualidade_media_percentual else 0,
                    'consumo_energia_total': float(dashboard.consumo_energia_total) if dashboard.consumo_energia_total else 0,
                    'alertas_ativos': dashboard.alertas_ativos,
                    'anomalias_detectadas': dashboard.anomalias_detectadas,
                    'status_geral': dashboard.status_geral,
                    'data_referencia': dashboard.data_referencia.isoformat() if dashboard.data_referencia else None
                }
        except Exception as e:
            return {'erro': f'Erro ao obter dashboard executivo: {str(e)}'}
