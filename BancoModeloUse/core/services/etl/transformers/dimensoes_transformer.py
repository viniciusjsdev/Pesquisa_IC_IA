# core/services/etl/transformers/dimensoes_transformer.py
"""
Transformador de dados para dimensões da DW
"""
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from core.models.dw.dimensoes import DimProduto, DimTempo, DimMaquina, DimCliente, DimFornecedor

class DimensoesTransformer:
    """Transformador para dimensões da DW"""
    
    def __init__(self):
        self.lookup_cache = {}
    
    def transformar_produtos(self, dados_financeiros: List[Dict], dados_industriais: List[Dict]) -> List[Dict[str, Any]]:
        """Transforma dados de produtos para dimensão"""
        produtos_transformados = []
        
        # Processar produtos financeiros
        for venda in dados_financeiros.get('vendas', []):
            produto_data = {
                'produto_id_financeiro': venda.get('produto_id'),
                'produto_id_industrial': None,  # Será preenchido se encontrar correspondência
                'nome_produto': f"Produto_{venda.get('produto_id')}",  # Nome padrão
                'categoria': 'Financeiro',
                'unidade_medida': 'unidade',
                'preco_unitario': venda.get('preco_unitario_venda', 0),
                'data_inicio_vigencia': venda.get('data_venda'),
                'data_fim_vigencia': None,
                'ativo': True
            }
            produtos_transformados.append(produto_data)
        
        # Processar produtos industriais
        for ordem in dados_industriais.get('ordens_producao', []):
            produto_data = {
                'produto_id_financeiro': None,  # Será preenchido se encontrar correspondência
                'produto_id_industrial': ordem.get('produto_id'),
                'nome_produto': f"Produto_Industrial_{ordem.get('produto_id')}",
                'categoria': 'Industrial',
                'unidade_medida': 'unidade',
                'preco_unitario': 0,  # Não disponível nos dados industriais
                'data_inicio_vigencia': ordem.get('data_planejamento'),
                'data_fim_vigencia': None,
                'ativo': True
            }
            produtos_transformados.append(produto_data)
        
        return produtos_transformados
    
    def transformar_tempo(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Transforma dados de tempo para dimensão"""
        tempos_transformados = []
        
        current_date = data_inicio
        while current_date <= data_fim:
            tempo_data = {
                'data': current_date,
                'dia': current_date.day,
                'mes': current_date.month,
                'trimestre': self._calcular_trimestre(current_date.month),
                'ano': current_date.year,
                'dia_semana': current_date.weekday(),
                'nome_dia_semana': self._obter_nome_dia_semana(current_date.weekday()),
                'nome_mes': self._obter_nome_mes(current_date.month),
                'nome_trimestre': f"T{self._calcular_trimestre(current_date.month)}",
                'feriado': self._verificar_feriado(current_date),
                'periodo_fiscal': f"{current_date.year}-{current_date.month:02d}",
                'semana_ano': current_date.isocalendar()[1],
                'dia_ano': current_date.timetuple().tm_yday
            }
            tempos_transformados.append(tempo_data)
            
            # Avançar para o próximo dia
            current_date = date(current_date.year, current_date.month, current_date.day + 1)
        
        return tempos_transformados
    
    def transformar_maquinas(self, dados_industriais: List[Dict]) -> List[Dict[str, Any]]:
        """Transforma dados de máquinas para dimensão"""
        maquinas_transformadas = []
        
        # Processar equipamentos
        for equipamento in dados_industriais.get('equipamentos', []):
            maquina_data = {
                'maquina_id_industrial': equipamento.get('equipamento_id'),
                'nome_maquina': equipamento.get('nome'),
                'linha_producao': 'Linha_Principal',  # Valor padrão
                'capacidade_max': equipamento.get('capacidade_producao', 0),
                'centro_custo': 'Centro_Custo_Principal',  # Valor padrão
                'data_inicio_vigencia': equipamento.get('data_registro'),
                'data_fim_vigencia': None,
                'ativo': True
            }
            maquinas_transformadas.append(maquina_data)
        
        return maquinas_transformadas
    
    def transformar_clientes(self, dados_financeiros: List[Dict]) -> List[Dict[str, Any]]:
        """Transforma dados de clientes para dimensão"""
        clientes_transformados = []
        
        # Processar clientes das vendas
        clientes_unicos = set()
        for venda in dados_financeiros.get('vendas', []):
            cliente_id = venda.get('cliente_id')
            if cliente_id and cliente_id not in clientes_unicos:
                cliente_data = {
                    'cliente_id_financeiro': cliente_id,
                    'nome_cliente': f"Cliente_{cliente_id}",
                    'segmento': 'Padrão',
                    'regiao': 'Nacional',
                    'data_inicio_vigencia': venda.get('data_venda'),
                    'data_fim_vigencia': None,
                    'ativo': True
                }
                clientes_transformados.append(cliente_data)
                clientes_unicos.add(cliente_id)
        
        return clientes_transformados
    
    def transformar_fornecedores(self, dados_industriais: List[Dict]) -> List[Dict[str, Any]]:
        """Transforma dados de fornecedores para dimensão"""
        fornecedores_transformados = []
        
        # Processar fornecedores dos lotes de materiais
        fornecedores_unicos = set()
        for lote in dados_industriais.get('lotes_producao', []):
            # Buscar fornecedor associado ao lote (se houver)
            fornecedor_id = lote.get('fornecedor_id')
            if fornecedor_id and fornecedor_id not in fornecedores_unicos:
                fornecedor_data = {
                    'fornecedor_id_industrial': fornecedor_id,
                    'nome_fornecedor': f"Fornecedor_{fornecedor_id}",
                    'categoria': 'Material',
                    'regiao': 'Nacional',
                    'data_inicio_vigencia': lote.get('data_lote'),
                    'data_fim_vigencia': None,
                    'ativo': True
                }
                fornecedores_transformados.append(fornecedor_data)
                fornecedores_unicos.add(fornecedor_id)
        
        return fornecedores_transformados
    
    def _calcular_trimestre(self, mes: int) -> int:
        """Calcula trimestre baseado no mês"""
        if mes <= 3:
            return 1
        elif mes <= 6:
            return 2
        elif mes <= 9:
            return 3
        else:
            return 4
    
    def _obter_nome_dia_semana(self, dia_semana: int) -> str:
        """Retorna nome do dia da semana"""
        dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        return dias[dia_semana]
    
    def _obter_nome_mes(self, mes: int) -> str:
        """Retorna nome do mês"""
        meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        return meses[mes - 1]
    
    def _verificar_feriado(self, data: date) -> bool:
        """Verifica se a data é feriado (implementação básica)"""
        # Implementação básica - pode ser expandida com calendário de feriados
        feriados_fixos = [
            (1, 1),   # Ano Novo
            (4, 21),  # Tiradentes
            (5, 1),   # Dia do Trabalhador
            (9, 7),   # Independência
            (10, 12), # Nossa Senhora Aparecida
            (11, 2),  # Finados
            (11, 15), # Proclamação da República
            (12, 25)  # Natal
        ]
        
        return (data.month, data.day) in feriados_fixos
