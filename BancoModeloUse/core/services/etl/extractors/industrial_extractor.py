# core/services/etl/extractors/industrial_extractor.py
"""
Extrator de dados do banco industrial
"""
from datetime import datetime, date
from typing import List, Dict, Any
from infrastructure.database.sessions import get_industrial_db
from core.repositories.industrial import ProducaoRepository, EquipamentosRepository, QualidadeRepository

class IndustrialExtractor:
    """Extrator de dados industriais"""
    
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
    
    def extrair_ordens_producao(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Extrai ordens de produção do banco industrial"""
        with get_industrial_db() as db:
            self._get_repositories(db)
            ordens = self.producao_repo.get_ordens_by_periodo(data_inicio, data_fim)
            
            ordens_data = []
            for ordem in ordens:
                ordens_data.append({
                    'ordem_producao_id': ordem.ordem_producao_id,
                    'produto_id': ordem.produto_id,
                    'quantidade_planejada': ordem.quantidade_planejada,
                    'data_planejamento': ordem.data_planejamento,
                    'data_inicio_real': ordem.data_inicio_real,
                    'data_fim_real': ordem.data_fim_real,
                    'status_ordem': ordem.status_ordem
                })
            
            return ordens_data
    
    def extrair_registros_operacao(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Extrai registros de operação do banco industrial"""
        with get_industrial_db() as db:
            self._get_repositories(db)
            registros = self.producao_repo.get_registros_operacao_by_periodo(data_inicio, data_fim)
            
            registros_data = []
            for registro in registros:
                registros_data.append({
                    'registro_id': registro.registro_id,
                    'ordem_producao_id': registro.ordem_producao_id,
                    'maquina_id': registro.maquina_id,
                    'operador_id': registro.operador_id,
                    'hora_inicio': registro.hora_inicio,
                    'hora_fim': registro.hora_fim,
                    'tempo_setup_real_min': float(registro.tempo_setup_real_min) if registro.tempo_setup_real_min else 0,
                    'quantidade_produzida_real': registro.quantidade_produzida_real,
                    'consumo_energia_kwh': float(registro.consumo_energia_kwh) if registro.consumo_energia_kwh else 0
                })
            
            return registros_data
    
    def extrair_paradas_maquinas(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Extrai paradas de máquinas do banco industrial"""
        with get_industrial_db() as db:
            self._get_repositories(db)
            # Buscar paradas para todas as máquinas no período
            paradas_data = []
            
            # Primeiro, obter todas as máquinas
            equipamentos = self.equipamentos_repo.get_all_equipamentos()
            
            for equipamento in equipamentos:
                paradas = self.producao_repo.get_paradas_maquina_by_periodo(
                    equipamento.id, data_inicio, data_fim
                )
                
                for parada in paradas:
                    paradas_data.append({
                        'parada_id': parada.parada_id,
                        'maquina_id': parada.maquina_id,
                        'hora_inicio_parada': parada.hora_inicio_parada,
                        'hora_fim_parada': parada.hora_fim_parada,
                        'motivo_parada': parada.motivo_parada
                    })
            
            return paradas_data
    
    def extrair_controle_qualidade(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Extrai controles de qualidade do banco industrial"""
        with get_industrial_db() as db:
            self._get_repositories(db)
            controles = self.qualidade_repo.get_controles_qualidade_by_periodo(data_inicio, data_fim)
            
            controles_data = []
            for controle in controles:
                controles_data.append({
                    'controle_id': controle.controle_id,
                    'lote_producao_id': controle.lote_producao_id,
                    'data_inspecao': controle.data_inspecao,
                    'inspetor_id': controle.inspetor_id,
                    'unidades_aprovadas': controle.unidades_aprovadas,
                    'unidades_rejeitadas': controle.unidades_rejeitadas,
                    'motivo_rejeicao': controle.motivo_rejeicao
                })
            
            return controles_data
    
    def extrair_equipamentos(self) -> List[Dict[str, Any]]:
        """Extrai dados de equipamentos do banco industrial"""
        with get_industrial_db() as db:
            self._get_repositories(db)
            equipamentos = self.equipamentos_repo.get_all_equipamentos()
            
            equipamentos_data = []
            for equipamento in equipamentos:
                equipamentos_data.append({
                    'equipamento_id': equipamento.id,
                    'nome': equipamento.nome,
                    'disponibilidade': float(equipamento.disponibilidade),
                    'performance': float(equipamento.performance),
                    'qualidade': float(equipamento.qualidade),
                    'oee': float(equipamento.oee),
                    'taxa_producao': float(equipamento.taxa_producao),
                    'capacidade_producao': float(equipamento.capacidade_producao),
                    'eficiencia_linha': float(equipamento.eficiencia_linha),
                    'produtividade_mao_obra': float(equipamento.produtividade_mao_obra),
                    'data_registro': equipamento.data_registro
                })
            
            return equipamentos_data
    
    def extrair_consumo_materiais(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Extrai consumo de materiais do banco industrial"""
        with get_industrial_db() as db:
            self._get_repositories(db)
            
            # Buscar registros de operação no período
            registros = self.producao_repo.get_registros_operacao_by_periodo(data_inicio, data_fim)
            
            consumo_data = []
            for registro in registros:
                consumos = self.producao_repo.get_consumo_material_by_registro(registro.registro_id)
                
                for consumo in consumos:
                    consumo_data.append({
                        'consumo_id': consumo.consumo_id,
                        'registro_id': consumo.registro_id,
                        'material_id': consumo.material_id,
                        'lote_material_id': consumo.lote_material_id,
                        'quantidade_consumida': float(consumo.quantidade_consumida) if consumo.quantidade_consumida else 0
                    })
            
            return consumo_data
    
    def extrair_lotes_producao(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Extrai lotes de produção do banco industrial"""
        with get_industrial_db() as db:
            self._get_repositories(db)
            
            # Buscar ordens no período
            ordens = self.producao_repo.get_ordens_by_periodo(data_inicio, data_fim)
            
            lotes_data = []
            for ordem in ordens:
                lotes = self.producao_repo.get_lotes_producao_by_ordem(ordem.ordem_producao_id)
                
                for lote in lotes:
                    lotes_data.append({
                        'lote_producao_id': lote.lote_producao_id,
                        'ordem_producao_id': lote.ordem_producao_id,
                        'data_lote': lote.data_lote,
                        'quantidade_total': lote.quantidade_total
                    })
            
            return lotes_data
    
    def extrair_todos_dados_industriais(self, data_inicio: date, data_fim: date) -> Dict[str, List[Dict[str, Any]]]:
        """Extrai todos os dados industriais do período"""
        return {
            'ordens_producao': self.extrair_ordens_producao(data_inicio, data_fim),
            'registros_operacao': self.extrair_registros_operacao(data_inicio, data_fim),
            'paradas_maquinas': self.extrair_paradas_maquinas(data_inicio, data_fim),
            'controle_qualidade': self.extrair_controle_qualidade(data_inicio, data_fim),
            'equipamentos': self.extrair_equipamentos(),
            'consumo_materiais': self.extrair_consumo_materiais(data_inicio, data_fim),
            'lotes_producao': self.extrair_lotes_producao(data_inicio, data_fim)
        }
