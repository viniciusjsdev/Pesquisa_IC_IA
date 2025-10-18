# core/services/etl/transformers/fatos_transformer.py
"""
Transformador de dados para fatos da DW
"""
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from core.models.dw.fatos import FatoVendas, FatoProducao, FatoCustos, FatoQualidade, FatoEnergia

class FatosTransformer:
    """Transformador para fatos da DW"""
    
    def __init__(self, lookup_service):
        self.lookup_service = lookup_service
    
    def transformar_vendas(self, dados_financeiros: List[Dict], dimensoes: Dict) -> List[Dict[str, Any]]:
        """Transforma dados de vendas para fato"""
        vendas_transformadas = []
        
        for venda in dados_financeiros.get('vendas', []):
            # Buscar surrogate keys
            produto_sk = self.lookup_service.buscar_produto_sk(
                venda.get('produto_id'), 'financeiro'
            )
            tempo_sk = self.lookup_service.buscar_tempo_sk(venda.get('data_venda'))
            cliente_sk = self.lookup_service.buscar_cliente_sk(
                venda.get('cliente_id')
            )
            
            if produto_sk and tempo_sk and cliente_sk:
                venda_data = {
                    'produto_sk': produto_sk,
                    'tempo_sk': tempo_sk,
                    'cliente_sk': cliente_sk,
                    'quantidade_vendida': venda.get('quantidade_vendida', 0),
                    'valor_unitario': venda.get('preco_unitario_venda', 0),
                    'valor_total': venda.get('valor_total', 0),
                    'desconto': 0,  # Valor padrão
                    'margem_contribuicao': self._calcular_margem_contribuicao(venda),
                    'data_venda': venda.get('data_venda')
                }
                vendas_transformadas.append(venda_data)
        
        return vendas_transformadas
    
    def transformar_producao(self, dados_industriais: List[Dict], dimensoes: Dict) -> List[Dict[str, Any]]:
        """Transforma dados de produção para fato"""
        producao_transformada = []
        
        for registro in dados_industriais.get('registros_operacao', []):
            # Buscar surrogate keys
            produto_sk = self.lookup_service.buscar_produto_sk(
                registro.get('produto_id'), 'industrial'
            )
            maquina_sk = self.lookup_service.buscar_maquina_sk(
                registro.get('maquina_id')
            )
            tempo_sk = self.lookup_service.buscar_tempo_sk(
                registro.get('hora_inicio').date() if registro.get('hora_inicio') else None
            )
            
            if produto_sk and maquina_sk and tempo_sk:
                # Buscar dados da ordem para quantidade planejada
                ordem_id = registro.get('ordem_producao_id')
                quantidade_planejada = self._buscar_quantidade_planejada(
                    dados_industriais, ordem_id
                )
                
                # Calcular eficiência
                eficiencia = self._calcular_eficiencia(
                    registro.get('quantidade_produzida_real', 0),
                    quantidade_planejada
                )
                
                # Buscar defeitos relacionados
                defeitos = self._buscar_defeitos_registro(
                    dados_industriais, registro.get('registro_id')
                )
                
                producao_data = {
                    'produto_sk': produto_sk,
                    'maquina_sk': maquina_sk,
                    'tempo_sk': tempo_sk,
                    'quantidade_produzida': registro.get('quantidade_produzida_real', 0),
                    'quantidade_planejada': quantidade_planejada,
                    'tempo_producao_min': self._calcular_tempo_producao(
                        registro.get('hora_inicio'),
                        registro.get('hora_fim')
                    ),
                    'tempo_setup_min': registro.get('tempo_setup_real_min', 0),
                    'consumo_energia_kwh': registro.get('consumo_energia_kwh', 0),
                    'eficiencia_percent': eficiencia,
                    'defeitos_quantidade': defeitos.get('quantidade', 0),
                    'defeitos_percent': defeitos.get('percentual', 0),
                    'data_producao': registro.get('hora_inicio').date() if registro.get('hora_inicio') else None
                }
                producao_transformada.append(producao_data)
        
        return producao_transformada
    
    def transformar_custos(self, dados_financeiros: List[Dict], dimensoes: Dict) -> List[Dict[str, Any]]:
        """Transforma dados de custos para fato"""
        custos_transformados = []
        
        for custo in dados_financeiros.get('custos', []):
            # Buscar surrogate keys
            produto_sk = self.lookup_service.buscar_produto_sk(
                custo.get('produto_id'), 'financeiro'
            )
            maquina_sk = self.lookup_service.buscar_maquina_sk(
                custo.get('maquina_id')
            )
            tempo_sk = self.lookup_service.buscar_tempo_sk(
                custo.get('data_registro')
            )
            
            if produto_sk and tempo_sk:
                custo_data = {
                    'produto_sk': produto_sk,
                    'maquina_sk': maquina_sk,
                    'tempo_sk': tempo_sk,
                    'custo_materia_prima': custo.get('materia_prima', 0),
                    'custo_mao_obra': custo.get('mao_obra_direta', 0),
                    'custo_indireto': custo.get('custos_indiretos', 0),
                    'custo_energia': 0,  # Será preenchido por outros fatos
                    'custo_total': custo.get('custo_total', 0),
                    'custo_unitario': custo.get('custo_unitario', 0),
                    'data_custo': custo.get('data_registro')
                }
                custos_transformados.append(custo_data)
        
        return custos_transformados
    
    def transformar_qualidade(self, dados_industriais: List[Dict], dimensoes: Dict) -> List[Dict[str, Any]]:
        """Transforma dados de qualidade para fato"""
        qualidade_transformada = []
        
        for controle in dados_industriais.get('controle_qualidade', []):
            # Buscar surrogate keys
            produto_sk = self.lookup_service.buscar_produto_sk(
                controle.get('produto_id'), 'industrial'
            )
            maquina_sk = self.lookup_service.buscar_maquina_sk(
                controle.get('maquina_id')
            )
            tempo_sk = self.lookup_service.buscar_tempo_sk(
                controle.get('data_inspecao')
            )
            
            if produto_sk and tempo_sk:
                unidades_inspecionadas = controle.get('unidades_aprovadas', 0) + controle.get('unidades_rejeitadas', 0)
                unidades_rejeitadas = controle.get('unidades_rejeitadas', 0)
                taxa_defeito = (unidades_rejeitadas / unidades_inspecionadas * 100) if unidades_inspecionadas > 0 else 0
                
                qualidade_data = {
                    'produto_sk': produto_sk,
                    'maquina_sk': maquina_sk,
                    'tempo_sk': tempo_sk,
                    'unidades_inspecionadas': unidades_inspecionadas,
                    'unidades_aprovadas': controle.get('unidades_aprovadas', 0),
                    'unidades_rejeitadas': unidades_rejeitadas,
                    'taxa_defeito_percent': taxa_defeito,
                    'cp': 0,  # Será calculado por análise estatística
                    'cpk': 0,  # Será calculado por análise estatística
                    'data_qualidade': controle.get('data_inspecao')
                }
                qualidade_transformada.append(qualidade_data)
        
        return qualidade_transformada
    
    def transformar_energia(self, dados_industriais: List[Dict], dimensoes: Dict) -> List[Dict[str, Any]]:
        """Transforma dados de energia para fato"""
        energia_transformada = []
        
        for registro in dados_industriais.get('registros_operacao', []):
            # Buscar surrogate keys
            maquina_sk = self.lookup_service.buscar_maquina_sk(
                registro.get('maquina_id')
            )
            tempo_sk = self.lookup_service.buscar_tempo_sk(
                registro.get('hora_inicio').date() if registro.get('hora_inicio') else None
            )
            
            if maquina_sk and tempo_sk:
                consumo_total = registro.get('consumo_energia_kwh', 0)
                quantidade_produzida = registro.get('quantidade_produzida_real', 0)
                consumo_por_producao = (consumo_total / quantidade_produzida) if quantidade_produzida > 0 else 0
                
                energia_data = {
                    'maquina_sk': maquina_sk,
                    'tempo_sk': tempo_sk,
                    'consumo_total_kwh': consumo_total,
                    'consumo_por_producao_kwh': consumo_por_producao,
                    'eficiencia_energetica': self._calcular_eficiencia_energetica(consumo_total, quantidade_produzida),
                    'custo_energia': 0,  # Será preenchido por dados financeiros
                    'data_energia': registro.get('hora_inicio').date() if registro.get('hora_inicio') else None
                }
                energia_transformada.append(energia_data)
        
        return energia_transformada
    
    def _calcular_margem_contribuicao(self, venda: Dict) -> float:
        """Calcula margem de contribuição"""
        # Implementação básica - pode ser expandida
        return venda.get('valor_total', 0) * 0.3  # 30% de margem padrão
    
    def _buscar_quantidade_planejada(self, dados_industriais: List[Dict], ordem_id: int) -> int:
        """Busca quantidade planejada da ordem"""
        for ordem in dados_industriais.get('ordens_producao', []):
            if ordem.get('ordem_producao_id') == ordem_id:
                return ordem.get('quantidade_planejada', 0)
        return 0
    
    def _calcular_eficiencia(self, quantidade_produzida: int, quantidade_planejada: int) -> float:
        """Calcula eficiência de produção"""
        if quantidade_planejada > 0:
            return (quantidade_produzida / quantidade_planejada) * 100
        return 0
    
    def _calcular_tempo_producao(self, hora_inicio, hora_fim) -> float:
        """Calcula tempo de produção em minutos"""
        if hora_inicio and hora_fim:
            delta = hora_fim - hora_inicio
            return delta.total_seconds() / 60
        return 0
    
    def _buscar_defeitos_registro(self, dados_industriais: List[Dict], registro_id: int) -> Dict:
        """Busca defeitos relacionados ao registro"""
        # Implementação básica - pode ser expandida
        return {'quantidade': 0, 'percentual': 0}
    
    def _calcular_eficiencia_energetica(self, consumo_kwh: float, quantidade_produzida: int) -> float:
        """Calcula eficiência energética"""
        if quantidade_produzida > 0:
            return quantidade_produzida / consumo_kwh if consumo_kwh > 0 else 0
        return 0
