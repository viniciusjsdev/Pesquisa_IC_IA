# core/rag/agents/agente_financeiro.py
"""
Agente Financeiro - especializado em consultas financeiras
"""
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from core.rag.tools.financeiro_tools import FinanceiroTools
import json

class AgenteFinanceiro:
    """Agente especializado em consultas financeiras"""
    
    def __init__(self):
        self.tools = FinanceiroTools()
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Retorna o prompt do sistema para o agente financeiro"""
        return """
        Você é um Agente Financeiro especializado em análise de dados financeiros empresariais.
        Sua função é interpretar consultas financeiras e fornecer análises detalhadas e insights.
        
        ESPECIALIDADES:
        - Análise de vendas e receitas
        - Cálculo de custos e margens
        - Análise de lançamentos contábeis
        - Orçamentos e planejamento financeiro
        - Indicadores financeiros (ROI, margem, etc.)
        - Análise de lucratividade
        
        FERRAMENTAS DISPONÍVEIS:
        - query_financeira: Consultas genéricas (vendas, custos, lançamentos, orçamentos)
        - calcular_margem_contribuicao: Cálculo de margem de contribuição
        - obter_indicadores_financeiros: Indicadores consolidados
        
        INSTRUÇÕES:
        - Sempre forneça análises detalhadas e insights
        - Use dados quantitativos para suportar suas conclusões
        - Identifique tendências e padrões nos dados
        - Sugira ações baseadas nos resultados
        - Seja preciso e objetivo nas análises
        """
    
    def processar_consulta(self, tipo_consulta: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa consulta financeira
        
        Args:
            tipo_consulta: Tipo de consulta ('vendas', 'custos', 'lancamentos', 'orcamentos', 'indicadores')
            parametros: Parâmetros da consulta
        
        Returns:
            Dict com resultado da consulta e análise
        """
        try:
            # Executar consulta
            resultado = self.tools.query_financeira(tipo_consulta, parametros)
            
            # Gerar análise
            analise = self._gerar_analise(tipo_consulta, resultado, parametros)
            
            return {
                'agente': 'financeiro',
                'tipo_consulta': tipo_consulta,
                'parametros': parametros,
                'resultado': resultado,
                'analise': analise,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'agente': 'financeiro',
                'erro': f'Erro ao processar consulta financeira: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _gerar_analise(self, tipo_consulta: str, resultado: Dict[str, Any], parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Gera análise detalhada do resultado"""
        if 'erro' in resultado:
            return {'erro': resultado['erro']}
        
        analise = {
            'resumo': self._gerar_resumo(tipo_consulta, resultado),
            'insights': self._gerar_insights(tipo_consulta, resultado),
            'tendencias': self._identificar_tendencias(tipo_consulta, resultado),
            'recomendacoes': self._gerar_recomendacoes(tipo_consulta, resultado)
        }
        
        return analise
    
    def _gerar_resumo(self, tipo_consulta: str, resultado: Dict[str, Any]) -> str:
        """Gera resumo executivo"""
        if tipo_consulta == 'vendas':
            total_registros = resultado.get('total_registros', 0)
            total_quantidade = resultado.get('total_quantidade', 0)
            total_valor = resultado.get('total_valor', 0)
            return f"Análise de vendas: {total_registros} registros, {total_quantidade} unidades vendidas, R$ {total_valor:,.2f} em receita total."
        
        elif tipo_consulta == 'custos':
            total_registros = resultado.get('total_registros', 0)
            total_custos = resultado.get('total_custos', 0)
            return f"Análise de custos: {total_registros} registros, R$ {total_custos:,.2f} em custos totais."
        
        elif tipo_consulta == 'lancamentos':
            total_registros = resultado.get('total_registros', 0)
            total_valor = resultado.get('total_valor', 0)
            return f"Análise de lançamentos: {total_registros} registros, R$ {total_valor:,.2f} em valor total."
        
        elif tipo_consulta == 'orcamentos':
            total_registros = resultado.get('total_registros', 0)
            total_orcado = resultado.get('total_orcado', 0)
            return f"Análise de orçamentos: {total_registros} registros, R$ {total_orcado:,.2f} em valor orçado."
        
        else:
            return "Análise financeira concluída com sucesso."
    
    def _gerar_insights(self, tipo_consulta: str, resultado: Dict[str, Any]) -> List[str]:
        """Gera insights baseados nos dados"""
        insights = []
        
        if tipo_consulta == 'vendas':
            total_valor = resultado.get('total_valor', 0)
            total_quantidade = resultado.get('total_quantidade', 0)
            
            if total_quantidade > 0:
                ticket_medio = total_valor / total_quantidade
                insights.append(f"Ticket médio: R$ {ticket_medio:,.2f} por unidade")
            
            if total_valor > 100000:
                insights.append("Receita significativa acima de R$ 100.000")
            elif total_valor < 10000:
                insights.append("Receita baixa, abaixo de R$ 10.000")
        
        elif tipo_consulta == 'custos':
            total_custos = resultado.get('total_custos', 0)
            total_materia_prima = resultado.get('total_materia_prima', 0)
            total_mao_obra = resultado.get('total_mao_obra', 0)
            
            if total_custos > 0:
                percentual_materia_prima = (total_materia_prima / total_custos) * 100
                percentual_mao_obra = (total_mao_obra / total_custos) * 100
                
                insights.append(f"Matéria-prima representa {percentual_materia_prima:.1f}% dos custos")
                insights.append(f"Mão de obra representa {percentual_mao_obra:.1f}% dos custos")
        
        elif tipo_consulta == 'lancamentos':
            total_valor = resultado.get('total_valor', 0)
            if total_valor > 0:
                insights.append("Lançamentos com valor positivo")
            elif total_valor < 0:
                insights.append("Lançamentos com valor negativo (despesas)")
        
        return insights
    
    def _identificar_tendencias(self, tipo_consulta: str, resultado: Dict[str, Any]) -> List[str]:
        """Identifica tendências nos dados"""
        tendencias = []
        
        if tipo_consulta == 'vendas':
            dados = resultado.get('dados', [])
            if len(dados) > 1:
                # Analisar tendência de preços
                precos = [d.get('preco_unitario', 0) for d in dados if d.get('preco_unitario')]
                if len(precos) > 1:
                    if precos[-1] > precos[0]:
                        tendencias.append("Tendência de aumento nos preços")
                    elif precos[-1] < precos[0]:
                        tendencias.append("Tendência de redução nos preços")
        
        elif tipo_consulta == 'custos':
            dados = resultado.get('dados', [])
            if len(dados) > 1:
                # Analisar tendência de custos
                custos = [d.get('custo_total', 0) for d in dados if d.get('custo_total')]
                if len(custos) > 1:
                    if custos[-1] > custos[0]:
                        tendencias.append("Tendência de aumento nos custos")
                    elif custos[-1] < custos[0]:
                        tendencias.append("Tendência de redução nos custos")
        
        return tendencias
    
    def _gerar_recomendacoes(self, tipo_consulta: str, resultado: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recomendacoes = []
        
        if tipo_consulta == 'vendas':
            total_valor = resultado.get('total_valor', 0)
            total_quantidade = resultado.get('total_quantidade', 0)
            
            if total_valor < 10000:
                recomendacoes.append("Considerar estratégias para aumentar as vendas")
            
            if total_quantidade > 0:
                ticket_medio = total_valor / total_quantidade
                if ticket_medio < 100:
                    recomendacoes.append("Avaliar possibilidade de aumentar preços ou vender produtos de maior valor")
        
        elif tipo_consulta == 'custos':
            total_custos = resultado.get('total_custos', 0)
            total_materia_prima = resultado.get('total_materia_prima', 0)
            
            if total_custos > 0:
                percentual_materia_prima = (total_materia_prima / total_custos) * 100
                if percentual_materia_prima > 70:
                    recomendacoes.append("Matéria-prima representa alta porcentagem dos custos - considerar negociação com fornecedores")
        
        elif tipo_consulta == 'lancamentos':
            total_valor = resultado.get('total_valor', 0)
            if total_valor < 0:
                recomendacoes.append("Revisar despesas para otimizar fluxo de caixa")
        
        return recomendacoes
    
    def calcular_margem_contribuicao(self, produto_id: int, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """Calcula margem de contribuição para um produto"""
        try:
            resultado = self.tools.calcular_margem_contribuicao(produto_id, data_inicio, data_fim)
            
            if 'erro' in resultado:
                return resultado
            
            # Gerar análise da margem
            analise = self._analisar_margem_contribuicao(resultado)
            
            return {
                'agente': 'financeiro',
                'consulta': 'margem_contribuicao',
                'resultado': resultado,
                'analise': analise,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'agente': 'financeiro',
                'erro': f'Erro ao calcular margem de contribuição: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _analisar_margem_contribuicao(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa resultado da margem de contribuição"""
        margem = resultado.get('margem_contribuicao', 0)
        percentual = resultado.get('percentual_margem', 0)
        
        analise = {
            'resumo': f"Margem de contribuição: R$ {margem:,.2f} ({percentual:.1f}%)",
            'classificacao': self._classificar_margem(percentual),
            'insights': self._insights_margem(percentual, margem),
            'recomendacoes': self._recomendacoes_margem(percentual)
        }
        
        return analise
    
    def _classificar_margem(self, percentual: float) -> str:
        """Classifica a margem de contribuição"""
        if percentual >= 40:
            return "Excelente"
        elif percentual >= 30:
            return "Boa"
        elif percentual >= 20:
            return "Regular"
        elif percentual >= 10:
            return "Baixa"
        else:
            return "Crítica"
    
    def _insights_margem(self, percentual: float, margem: float) -> List[str]:
        """Gera insights sobre a margem"""
        insights = []
        
        if percentual >= 40:
            insights.append("Margem excelente - produto muito lucrativo")
        elif percentual >= 30:
            insights.append("Margem boa - produto lucrativo")
        elif percentual >= 20:
            insights.append("Margem regular - produto com lucratividade moderada")
        elif percentual >= 10:
            insights.append("Margem baixa - produto com baixa lucratividade")
        else:
            insights.append("Margem crítica - produto pode estar gerando prejuízo")
        
        if margem > 0:
            insights.append("Produto contribui positivamente para o resultado")
        else:
            insights.append("Produto está gerando prejuízo")
        
        return insights
    
    def _recomendacoes_margem(self, percentual: float) -> List[str]:
        """Gera recomendações baseadas na margem"""
        recomendacoes = []
        
        if percentual < 20:
            recomendacoes.append("Considerar aumento de preços")
            recomendacoes.append("Avaliar redução de custos")
            recomendacoes.append("Revisar estratégia de precificação")
        
        if percentual < 10:
            recomendacoes.append("Avaliar descontinuidade do produto")
            recomendacoes.append("Revisar completamente a estrutura de custos")
        
        if percentual >= 30:
            recomendacoes.append("Produto está performando bem - manter estratégia")
            recomendacoes.append("Considerar expansão da produção")
        
        return recomendacoes
    
    def obter_indicadores_financeiros(self, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """Obtém indicadores financeiros consolidados"""
        try:
            resultado = self.tools.obter_indicadores_financeiros(data_inicio, data_fim)
            
            if 'erro' in resultado:
                return resultado
            
            # Gerar análise dos indicadores
            analise = self._analisar_indicadores_financeiros(resultado)
            
            return {
                'agente': 'financeiro',
                'consulta': 'indicadores_financeiros',
                'resultado': resultado,
                'analise': analise,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'agente': 'financeiro',
                'erro': f'Erro ao obter indicadores financeiros: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _analisar_indicadores_financeiros(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa indicadores financeiros"""
        receita_total = resultado.get('receita_total', 0)
        custo_total = resultado.get('custo_total', 0)
        lucro_bruto = resultado.get('lucro_bruto', 0)
        margem_bruta = resultado.get('margem_bruta_percent', 0)
        
        analise = {
            'resumo': f"Receita: R$ {receita_total:,.2f}, Lucro: R$ {lucro_bruto:,.2f}, Margem: {margem_bruta:.1f}%",
            'classificacao': self._classificar_performance_financeira(margem_bruta),
            'insights': self._insights_indicadores(receita_total, custo_total, margem_bruta),
            'recomendacoes': self._recomendacoes_indicadores(margem_bruta, receita_total)
        }
        
        return analise
    
    def _classificar_performance_financeira(self, margem_bruta: float) -> str:
        """Classifica performance financeira"""
        if margem_bruta >= 30:
            return "Excelente"
        elif margem_bruta >= 20:
            return "Boa"
        elif margem_bruta >= 10:
            return "Regular"
        else:
            return "Baixa"
    
    def _insights_indicadores(self, receita: float, custo: float, margem: float) -> List[str]:
        """Gera insights sobre indicadores"""
        insights = []
        
        if receita > 100000:
            insights.append("Receita significativa acima de R$ 100.000")
        elif receita < 10000:
            insights.append("Receita baixa, abaixo de R$ 10.000")
        
        if margem >= 30:
            insights.append("Margem bruta excelente - operação muito lucrativa")
        elif margem >= 20:
            insights.append("Margem bruta boa - operação lucrativa")
        elif margem >= 10:
            insights.append("Margem bruta regular - operação com lucratividade moderada")
        else:
            insights.append("Margem bruta baixa - operação com baixa lucratividade")
        
        if custo > receita:
            insights.append("Custos superam receita - operação em prejuízo")
        elif custo > receita * 0.8:
            insights.append("Custos representam mais de 80% da receita")
        
        return insights
    
    def _recomendacoes_indicadores(self, margem: float, receita: float) -> List[str]:
        """Gera recomendações baseadas nos indicadores"""
        recomendacoes = []
        
        if margem < 20:
            recomendacoes.append("Focar na redução de custos")
            recomendacoes.append("Avaliar aumento de preços")
            recomendacoes.append("Revisar estrutura de custos")
        
        if margem < 10:
            recomendacoes.append("Revisão urgente da estratégia financeira")
            recomendacoes.append("Considerar reestruturação operacional")
        
        if receita < 10000:
            recomendacoes.append("Estratégias para aumentar receita")
            recomendacoes.append("Avaliar novos mercados ou produtos")
        
        if margem >= 25:
            recomendacoes.append("Performance excelente - manter estratégia")
            recomendacoes.append("Considerar expansão")
        
        return recomendacoes
