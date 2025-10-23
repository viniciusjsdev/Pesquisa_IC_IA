# core/rag/tools/industrial_tools.py
"""
Ferramentas RAG para consultas industriais
"""
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from infrastructure.database.sessions import get_industrial_db
from core.repositories.industrial import ProducaoRepository, EquipamentosRepository, QualidadeRepository
import json

class IndustrialTools:
    """Ferramentas para consultas industriais"""
    
    def __init__(self):
        self.producao_repo = None
        self.equipamentos_repo = None
        self.qualidade_repo = None
    
    def _get_repositories(self, db_session):
        """Inicializa repositórios com sessão"""
        if not self.producao_repo:
            self.producao_repo = ProducaoRepository(db_session)
        if not self.equipamentos_repo:
            self.equipamentos_repo = EquipamentosRepository(db_session)
        if not self.qualidade_repo:
            self.qualidade_repo = QualidadeRepository(db_session)
    
    def query_operacional(self, consulta: str, parametros: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executa consulta operacional genérica
        
        Args:
            consulta: Tipo de consulta ('producao', 'equipamentos', 'qualidade', 'paradas')
            parametros: Parâmetros da consulta (data_inicio, data_fim, maquina_id, etc.)
        
        Returns:
            Dict com resultados da consulta
        """
        if not parametros:
            parametros = {}
        
        data_inicio = parametros.get('data_inicio')
        data_fim = parametros.get('data_fim')
        
        with get_industrial_db() as db:
            self._get_repositories(db)
            
            if consulta == 'producao':
                return self._consultar_producao(data_inicio, data_fim, parametros)
            elif consulta == 'equipamentos':
                return self._consultar_equipamentos(data_inicio, data_fim, parametros)
            elif consulta == 'qualidade':
                return self._consultar_qualidade(data_inicio, data_fim, parametros)
            elif consulta == 'paradas':
                return self._consultar_paradas(data_inicio, data_fim, parametros)
            else:
                return {'erro': f'Tipo de consulta não suportado: {consulta}'}
    
    def _consultar_producao(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta produção"""
        try:
            if data_inicio and data_fim:
                registros = self.producao_repo.get_registros_operacao_by_periodo(data_inicio, data_fim)
            else:
                registros = self.producao_repo.get_all_registros_operacao()
            
            # Filtrar por máquina se especificado
            maquina_id = parametros.get('maquina_id')
            if maquina_id:
                registros = [r for r in registros if r.maquina_id == maquina_id]
            
            # Filtrar por ordem se especificado
            ordem_id = parametros.get('ordem_id')
            if ordem_id:
                registros = [r for r in registros if r.ordem_producao_id == ordem_id]
            
            # Calcular totais
            total_produzido = sum(r.quantidade_produzida_real for r in registros)
            total_energia = sum(float(r.consumo_energia_kwh) for r in registros if r.consumo_energia_kwh)
            total_tempo = sum(
                (r.hora_fim - r.hora_inicio).total_seconds() / 3600 
                for r in registros if r.hora_inicio and r.hora_fim
            )
            
            return {
                'tipo': 'producao',
                'total_registros': len(registros),
                'total_produzido': total_produzido,
                'total_energia_kwh': total_energia,
                'total_tempo_horas': total_tempo,
                'dados': [
                    {
                        'registro_id': r.registro_id,
                        'ordem_producao_id': r.ordem_producao_id,
                        'maquina_id': r.maquina_id,
                        'operador_id': r.operador_id,
                        'hora_inicio': r.hora_inicio.isoformat() if r.hora_inicio else None,
                        'hora_fim': r.hora_fim.isoformat() if r.hora_fim else None,
                        'quantidade_produzida': r.quantidade_produzida_real,
                        'consumo_energia_kwh': float(r.consumo_energia_kwh) if r.consumo_energia_kwh else 0
                    } for r in registros
                ]
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar produção: {str(e)}'}
    
    def _consultar_equipamentos(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta equipamentos"""
        try:
            equipamentos = self.equipamentos_repo.get_all_equipamentos()
            
            # Filtrar por OEE mínimo se especificado
            oee_minimo = parametros.get('oee_minimo')
            if oee_minimo:
                equipamentos = [e for e in equipamentos if e.oee >= oee_minimo]
            
            # Filtrar por disponibilidade mínima se especificado
            disponibilidade_minima = parametros.get('disponibilidade_minima')
            if disponibilidade_minima:
                equipamentos = [e for e in equipamentos if e.disponibilidade >= disponibilidade_minima]
            
            # Calcular médias
            media_oee = sum(e.oee for e in equipamentos) / len(equipamentos) if equipamentos else 0
            media_disponibilidade = sum(e.disponibilidade for e in equipamentos) / len(equipamentos) if equipamentos else 0
            media_performance = sum(e.performance for e in equipamentos) / len(equipamentos) if equipamentos else 0
            media_qualidade = sum(e.qualidade for e in equipamentos) / len(equipamentos) if equipamentos else 0
            
            return {
                'tipo': 'equipamentos',
                'total_equipamentos': len(equipamentos),
                'media_oee': media_oee,
                'media_disponibilidade': media_disponibilidade,
                'media_performance': media_performance,
                'media_qualidade': media_qualidade,
                'dados': [
                    {
                        'equipamento_id': e.id,
                        'nome': e.nome,
                        'disponibilidade': float(e.disponibilidade),
                        'performance': float(e.performance),
                        'qualidade': float(e.qualidade),
                        'oee': float(e.oee),
                        'taxa_producao': float(e.taxa_producao),
                        'capacidade_producao': float(e.capacidade_producao),
                        'data_registro': e.data_registro.isoformat() if e.data_registro else None
                    } for e in equipamentos
                ]
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar equipamentos: {str(e)}'}
    
    def _consultar_qualidade(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta qualidade"""
        try:
            if data_inicio and data_fim:
                controles = self.qualidade_repo.get_controles_qualidade_by_periodo(data_inicio, data_fim)
            else:
                controles = self.qualidade_repo.get_all_controles_qualidade()
            
            # Filtrar por lote se especificado
            lote_id = parametros.get('lote_id')
            if lote_id:
                controles = [c for c in controles if c.lote_producao_id == lote_id]
            
            # Calcular totais
            total_inspecionadas = sum(c.unidades_inspecionadas for c in controles)
            total_aprovadas = sum(c.unidades_aprovadas for c in controles)
            total_rejeitadas = sum(c.unidades_rejeitadas for c in controles)
            
            # Calcular taxa de defeitos
            taxa_defeitos = (total_rejeitadas / total_inspecionadas * 100) if total_inspecionadas > 0 else 0
            
            return {
                'tipo': 'qualidade',
                'total_controles': len(controles),
                'total_inspecionadas': total_inspecionadas,
                'total_aprovadas': total_aprovadas,
                'total_rejeitadas': total_rejeitadas,
                'taxa_defeitos_percent': taxa_defeitos,
                'dados': [
                    {
                        'controle_id': c.controle_id,
                        'lote_producao_id': c.lote_producao_id,
                        'data_inspecao': c.data_inspecao.isoformat() if c.data_inspecao else None,
                        'inspetor_id': c.inspetor_id,
                        'unidades_aprovadas': c.unidades_aprovadas,
                        'unidades_rejeitadas': c.unidades_rejeitadas,
                        'motivo_rejeicao': c.motivo_rejeicao
                    } for c in controles
                ]
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar qualidade: {str(e)}'}
    
    def _consultar_paradas(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta paradas de máquinas"""
        try:
            # Buscar todas as máquinas
            equipamentos = self.equipamentos_repo.get_all_equipamentos()
            
            paradas_data = []
            for equipamento in equipamentos:
                if data_inicio and data_fim:
                    paradas = self.producao_repo.get_paradas_maquina_by_periodo(
                        equipamento.id, data_inicio, data_fim
                    )
                else:
                    paradas = self.producao_repo.get_paradas_maquina_by_maquina(equipamento.id)
                
                for parada in paradas:
                    paradas_data.append({
                        'parada_id': parada.parada_id,
                        'maquina_id': parada.maquina_id,
                        'hora_inicio_parada': parada.hora_inicio_parada.isoformat() if parada.hora_inicio_parada else None,
                        'hora_fim_parada': parada.hora_fim_parada.isoformat() if parada.hora_fim_parada else None,
                        'motivo_parada': parada.motivo_parada
                    })
            
            # Filtrar por máquina se especificado
            maquina_id = parametros.get('maquina_id')
            if maquina_id:
                paradas_data = [p for p in paradas_data if p['maquina_id'] == maquina_id]
            
            # Calcular totais
            total_paradas = len(paradas_data)
            total_tempo_parada = sum(
                (datetime.fromisoformat(p['hora_fim_parada']) - datetime.fromisoformat(p['hora_inicio_parada'])).total_seconds() / 3600
                for p in paradas_data if p['hora_inicio_parada'] and p['hora_fim_parada']
            )
            
            return {
                'tipo': 'paradas',
                'total_paradas': total_paradas,
                'total_tempo_parada_horas': total_tempo_parada,
                'dados': paradas_data
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar paradas: {str(e)}'}
    
    def calcular_kpis_ordem(self, ordem_id: int) -> Dict[str, Any]:
        """Calcula KPIs para uma ordem de produção"""
        try:
            with get_industrial_db() as db:
                self._get_repositories(db)
                
                # Buscar ordem
                ordem = self.producao_repo.get_ordem_producao(ordem_id)
                if not ordem:
                    return {'erro': f'Ordem {ordem_id} não encontrada'}
                
                # Buscar registros de operação
                registros = self.producao_repo.get_registros_operacao_by_ordem(ordem_id)
                
                # Calcular KPIs
                total_produzido = sum(r.quantidade_produzida_real for r in registros)
                total_energia = sum(float(r.consumo_energia_kwh) for r in registros if r.consumo_energia_kwh)
                total_tempo = sum(
                    (r.hora_fim - r.hora_inicio).total_seconds() / 3600 
                    for r in registros if r.hora_inicio and r.hora_fim
                )
                
                # Calcular eficiência
                eficiencia = (total_produzido / ordem.quantidade_planejada * 100) if ordem.quantidade_planejada > 0 else 0
                
                # Calcular produtividade
                produtividade = total_produzido / total_tempo if total_tempo > 0 else 0
                
                return {
                    'ordem_id': ordem_id,
                    'quantidade_planejada': ordem.quantidade_planejada,
                    'quantidade_produzida': total_produzido,
                    'eficiencia_percent': eficiencia,
                    'total_energia_kwh': total_energia,
                    'total_tempo_horas': total_tempo,
                    'produtividade_unidades_hora': produtividade,
                    'total_registros': len(registros)
                }
        except Exception as e:
            return {'erro': f'Erro ao calcular KPIs da ordem: {str(e)}'}
    
    def obter_indicadores_operacionais(self, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """Obtém indicadores operacionais consolidados"""
        try:
            with get_industrial_db() as db:
                self._get_repositories(db)
                
                # Produção
                producao = self.producao_repo.get_producao_total_periodo(data_inicio, data_fim)
                
                # Equipamentos
                equipamentos = self.equipamentos_repo.get_all_equipamentos()
                media_oee = sum(e.oee for e in equipamentos) / len(equipamentos) if equipamentos else 0
                
                # Qualidade
                qualidade = self.qualidade_repo.get_taxa_defeitos_periodo(data_inicio, data_fim)
                
                return {
                    'periodo': {'inicio': data_inicio.isoformat(), 'fim': data_fim.isoformat()},
                    'producao_total': producao.get('total_produzido', 0),
                    'energia_total_kwh': producao.get('total_energia', 0),
                    'media_oee': media_oee,
                    'taxa_defeitos_percent': qualidade.get('taxa_defeitos_percent', 0),
                    'total_equipamentos': len(equipamentos),
                    'total_inspecionadas': qualidade.get('total_inspecionadas', 0)
                }
        except Exception as e:
            return {'erro': f'Erro ao obter indicadores operacionais: {str(e)}'}
