# core/rag/agents/orquestrador.py
"""
Agente Orquestrador - interpreta prompts e direciona para agentes específicos
"""
from typing import Dict, Any, List, Optional
from datetime import date, datetime
import json
import re

class AgenteOrquestrador:
    """Agente orquestrador para interpretar prompts e direcionar consultas"""
    
    def __init__(self):
        self.system_prompt = self._get_system_prompt()
        self.palavras_chave_financeiro = [
            'venda', 'vendas', 'receita', 'lucro', 'custo', 'custos', 'margem', 'roi',
            'financeiro', 'contábil', 'orçamento', 'lancamento', 'conta', 'cliente',
            'faturamento', 'despesa', 'investimento', 'retorno', 'lucratividade'
        ]
        self.palavras_chave_industrial = [
            'produção', 'produto', 'máquina', 'equipamento', 'operação', 'ordem',
            'industrial', 'qualidade', 'defeito', 'parada', 'eficiencia', 'oee',
            'disponibilidade', 'performance', 'energia', 'consumo', 'lote', 'inspeção'
        ]
        self.palavras_chave_integracao = [
            'correlação', 'integração', 'dashboard', 'kpi', 'indicador', 'análise',
            'comparação', 'tendência', 'anomalia', 'alerta', 'executivo', 'consolidado'
        ]
    
    def _get_system_prompt(self) -> str:
        """Retorna o prompt do sistema para o orquestrador"""
        return """
        Você é um Agente Orquestrador especializado em análise de dados empresariais.
        Sua função é interpretar consultas do usuário e direcioná-las para o agente especializado correto.
        
        DOMÍNIOS DE ESPECIALIZAÇÃO:
        
        1. FINANCEIRO - Consultas sobre:
        - Vendas, receitas, lucros, custos
        - Análises financeiras, margens, ROI
        - Lançamentos contábeis, orçamentos
        - Indicadores financeiros
        
        2. INDUSTRIAL - Consultas sobre:
        - Produção, operações, equipamentos
        - Qualidade, defeitos, eficiência
        - OEE, disponibilidade, performance
        - Energia, consumo, paradas
        
        3. INTEGRAÇÃO - Consultas sobre:
        - Correlações financeiro-industrial
        - KPIs integrados, dashboards
        - Análises comparativas, tendências
        - Alertas e anomalias
        
        INSTRUÇÕES:
        - Analise a consulta do usuário
        - Identifique o domínio principal
        - Retorne o agente especializado apropriado
        - Se a consulta envolver múltiplos domínios, priorize INTEGRAÇÃO
        - Seja preciso na classificação para garantir respostas relevantes
        """
    
    def interpretar_consulta(self, consulta: str) -> Dict[str, Any]:
        """
        Interpreta a consulta do usuário e determina o agente apropriado
        
        Args:
            consulta: Consulta do usuário em linguagem natural
        
        Returns:
            Dict com informações sobre o agente e parâmetros
        """
        consulta_lower = consulta.lower()
        
        # Contar ocorrências de palavras-chave por domínio
        score_financeiro = sum(1 for palavra in self.palavras_chave_financeiro if palavra in consulta_lower)
        score_industrial = sum(1 for palavra in self.palavras_chave_industrial if palavra in consulta_lower)
        score_integracao = sum(1 for palavra in self.palavras_chave_integracao if palavra in consulta_lower)
        
        # Determinar domínio principal
        scores = {
            'financeiro': score_financeiro,
            'industrial': score_industrial,
            'integracao': score_integracao
        }
        
        dominio_principal = max(scores, key=scores.get)
        
        # Extrair parâmetros da consulta
        parametros = self._extrair_parametros(consulta)
        
        # Determinar tipo de consulta específica
        tipo_consulta = self._determinar_tipo_consulta(consulta, dominio_principal)
        
        return {
            'agente_destino': dominio_principal,
            'tipo_consulta': tipo_consulta,
            'parametros': parametros,
            'consulta_original': consulta,
            'scores': scores,
            'timestamp': datetime.now().isoformat()
        }
    
    def _extrair_parametros(self, consulta: str) -> Dict[str, Any]:
        """Extrai parâmetros da consulta do usuário"""
        parametros = {}
        
        # Extrair datas
        datas = self._extrair_datas(consulta)
        if datas:
            parametros.update(datas)
        
        # Extrair IDs
        ids = self._extrair_ids(consulta)
        if ids:
            parametros.update(ids)
        
        # Extrair valores numéricos
        valores = self._extrair_valores(consulta)
        if valores:
            parametros.update(valores)
        
        return parametros
    
    def _extrair_datas(self, consulta: str) -> Dict[str, Any]:
        """Extrai datas da consulta"""
        parametros = {}
        
        # Padrões de data
        padroes_data = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})/(\d{1,2})',  # DD/MM
        ]
        
        for padrao in padroes_data:
            matches = re.findall(padrao, consulta)
            if matches:
                if len(matches[0]) == 3:  # Data completa
                    if '/' in consulta:
                        dia, mes, ano = matches[0]
                        parametros['data'] = f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
                    else:
                        ano, mes, dia = matches[0]
                        parametros['data'] = f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
                elif len(matches[0]) == 2:  # Mês/ano
                    mes, ano = matches[0]
                    parametros['mes'] = int(mes)
                    parametros['ano'] = int(ano)
        
        # Palavras-chave de período
        if 'hoje' in consulta.lower():
            parametros['data_inicio'] = date.today().isoformat()
            parametros['data_fim'] = date.today().isoformat()
        elif 'ontem' in consulta.lower():
            ontem = date.today() - datetime.timedelta(days=1)
            parametros['data_inicio'] = ontem.isoformat()
            parametros['data_fim'] = ontem.isoformat()
        elif 'semana' in consulta.lower():
            hoje = date.today()
            inicio_semana = hoje - datetime.timedelta(days=hoje.weekday())
            parametros['data_inicio'] = inicio_semana.isoformat()
            parametros['data_fim'] = hoje.isoformat()
        elif 'mês' in consulta.lower():
            hoje = date.today()
            inicio_mes = date(hoje.year, hoje.month, 1)
            parametros['data_inicio'] = inicio_mes.isoformat()
            parametros['data_fim'] = hoje.isoformat()
        
        return parametros
    
    def _extrair_ids(self, consulta: str) -> Dict[str, Any]:
        """Extrai IDs da consulta"""
        parametros = {}
        
        # Padrões de ID
        padroes_id = [
            r'produto\s*(\d+)',
            r'produto_id\s*(\d+)',
            r'máquina\s*(\d+)',
            r'maquina_id\s*(\d+)',
            r'cliente\s*(\d+)',
            r'cliente_id\s*(\d+)',
            r'ordem\s*(\d+)',
            r'ordem_id\s*(\d+)',
        ]
        
        for padrao in padroes_id:
            matches = re.findall(padrao, consulta, re.IGNORECASE)
            if matches:
                if 'produto' in padrao:
                    parametros['produto_id'] = int(matches[0])
                elif 'máquina' in padrao or 'maquina' in padrao:
                    parametros['maquina_id'] = int(matches[0])
                elif 'cliente' in padrao:
                    parametros['cliente_id'] = int(matches[0])
                elif 'ordem' in padrao:
                    parametros['ordem_id'] = int(matches[0])
        
        return parametros
    
    def _extrair_valores(self, consulta: str) -> Dict[str, Any]:
        """Extrai valores numéricos da consulta"""
        parametros = {}
        
        # Padrões de valor
        padroes_valor = [
            r'(\d+(?:\.\d+)?)\s*%',  # Percentual
            r'(\d+(?:\.\d+)?)\s*reais',  # Valor em reais
            r'(\d+(?:\.\d+)?)\s*unidades',  # Quantidade
        ]
        
        for padrao in padroes_valor:
            matches = re.findall(padrao, consulta, re.IGNORECASE)
            if matches:
                if '%' in padrao:
                    parametros['percentual'] = float(matches[0])
                elif 'reais' in padrao:
                    parametros['valor'] = float(matches[0])
                elif 'unidades' in padrao:
                    parametros['quantidade'] = float(matches[0])
        
        return parametros
    
    def _determinar_tipo_consulta(self, consulta: str, dominio: str) -> str:
        """Determina o tipo específico de consulta"""
        consulta_lower = consulta.lower()
        
        if dominio == 'financeiro':
            if any(palavra in consulta_lower for palavra in ['venda', 'vendas', 'receita']):
                return 'vendas'
            elif any(palavra in consulta_lower for palavra in ['custo', 'custos']):
                return 'custos'
            elif any(palavra in consulta_lower for palavra in ['lancamento', 'contábil']):
                return 'lancamentos'
            elif any(palavra in consulta_lower for palavra in ['orçamento', 'orcamento']):
                return 'orcamentos'
            else:
                return 'indicadores'
        
        elif dominio == 'industrial':
            if any(palavra in consulta_lower for palavra in ['produção', 'producao', 'operação']):
                return 'producao'
            elif any(palavra in consulta_lower for palavra in ['máquina', 'maquina', 'equipamento']):
                return 'equipamentos'
            elif any(palavra in consulta_lower for palavra in ['qualidade', 'defeito', 'inspeção']):
                return 'qualidade'
            elif any(palavra in consulta_lower for palavra in ['parada', 'paradas']):
                return 'paradas'
            else:
                return 'indicadores'
        
        elif dominio == 'integracao':
            if any(palavra in consulta_lower for palavra in ['venda', 'produção', 'correlação']):
                return 'vendas_producao'
            elif any(palavra in consulta_lower for palavra in ['custo', 'eficiencia', 'eficiência']):
                return 'custos_eficiencia'
            elif any(palavra in consulta_lower for palavra in ['qualidade', 'lucratividade']):
                return 'qualidade_lucratividade'
            elif any(palavra in consulta_lower for palavra in ['kpi', 'indicador', 'dashboard']):
                return 'kpis_integrados'
            else:
                return 'dashboard_executivo'
        
        return 'geral'
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do orquestrador"""
        return {
            'palavras_chave_financeiro': len(self.palavras_chave_financeiro),
            'palavras_chave_industrial': len(self.palavras_chave_industrial),
            'palavras_chave_integracao': len(self.palavras_chave_integracao),
            'total_palavras_chave': len(self.palavras_chave_financeiro) + len(self.palavras_chave_industrial) + len(self.palavras_chave_integracao),
            'timestamp': datetime.now().isoformat()
        }
