# core/rag/agents/agente_industrial.py
"""
Agente Industrial - especializado em consultas operacionais
"""
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from core.rag.tools.industrial_tools import IndustrialTools
import json

class AgenteIndustrial:
    """Agente especializado em consultas industriais"""
    
    def __init__(self):
        self.tools = IndustrialTools()
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Retorna o prompt do sistema para o agente industrial"""
        return """
        Você é um Agente Industrial especializado em análise de dados operacionais e industriais.
        Sua função é interpretar consultas operacionais e fornecer análises detalhadas e insights.
        
        ESPECIALIDADES:
        - Análise de produção e operações
        - Monitoramento de equipamentos e máquinas
        - Controle de qualidade e defeitos
        - Análise de eficiência (OEE, disponibilidade, performance)
        - Gestão de paradas e manutenção
        - Indicadores operacionais
        
        FERRAMENTAS DISPONÍVEIS:
        - query_operacional: Consultas genéricas (producao, equipamentos, qualidade, paradas)
        - calcular_kpis_ordem: KPIs específicos de uma ordem
        - obter_indicadores_operacionais: Indicadores consolidados
        
        INSTRUÇÕES:
        - Sempre forneça análises detalhadas e insights operacionais
        - Use dados quantitativos para suportar suas conclusões
        - Identifique tendências e padrões nos dados
        - Sugira ações para melhoria operacional
        - Seja preciso e objetivo nas análises
        """
    
    def processar_consulta(self, tipo_consulta: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa consulta industrial
        
        Args:
            tipo_consulta: Tipo de consulta ('producao', 'equipamentos', 'qualidade', 'paradas')
            parametros: Parâmetros da consulta
        
        Returns:
            Dict com resultado da consulta e análise
        """
        try:
            # Executar consulta
            resultado = self.tools.query_operacional(tipo_consulta, parametros)
            
            # Gerar análise
            analise = self._gerar_analise(tipo_consulta, resultado, parametros)
            
            return {
                'agente': 'industrial',
                'tipo_consulta': tipo_consulta,
                'parametros': parametros,
                'resultado': resultado,
                'analise': analise,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'agente': 'industrial',
                'erro': f'Erro ao processar consulta industrial: {str(e)}',
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
        if tipo_consulta == 'producao':
            total_registros = resultado.get('total_registros', 0)
            total_produzido = resultado.get('total_produzido', 0)
            total_energia = resultado.get('total_energia_kwh', 0)
            return f"Análise de produção: {total_registros} registros, {total_produzido} unidades produzidas, {total_energia:.2f} kWh consumidos."
        
        elif tipo_consulta == 'equipamentos':
            total_equipamentos = resultado.get('total_equipamentos', 0)
            media_oee = resultado.get('media_oee', 0)
            return f"Análise de equipamentos: {total_equipamentos} equipamentos, OEE médio de {media_oee:.1f}%."
        
        elif tipo_consulta == 'qualidade':
            total_controles = resultado.get('total_controles', 0)
            taxa_defeitos = resultado.get('taxa_defeitos_percent', 0)
            return f"Análise de qualidade: {total_controles} controles, taxa de defeitos de {taxa_defeitos:.1f}%."
        
        elif tipo_consulta == 'paradas':
            total_paradas = resultado.get('total_paradas', 0)
            total_tempo = resultado.get('total_tempo_parada_horas', 0)
            return f"Análise de paradas: {total_paradas} paradas, {total_tempo:.1f} horas de parada total."
        
        else:
            return "Análise operacional concluída com sucesso."
    
    def _gerar_insights(self, tipo_consulta: str, resultado: Dict[str, Any]) -> List[str]:
        """Gera insights baseados nos dados"""
        insights = []
        
        if tipo_consulta == 'producao':
            total_produzido = resultado.get('total_produzido', 0)
            total_energia = resultado.get('total_energia_kwh', 0)
            total_tempo = resultado.get('total_tempo_horas', 0)
            
            if total_tempo > 0:
                produtividade = total_produzido / total_tempo
                insights.append(f"Produtividade: {produtividade:.1f} unidades/hora")
            
            if total_energia > 0:
                eficiencia_energetica = total_produzido / total_energia
                insights.append(f"Eficiência energética: {eficiencia_energetica:.1f} unidades/kWh")
            
            if total_produzido > 1000:
                insights.append("Produção significativa acima de 1.000 unidades")
            elif total_produzido < 100:
                insights.append("Produção baixa, abaixo de 100 unidades")
        
        elif tipo_consulta == 'equipamentos':
            media_oee = resultado.get('media_oee', 0)
            media_disponibilidade = resultado.get('media_disponibilidade', 0)
            media_performance = resultado.get('media_performance', 0)
            media_qualidade = resultado.get('media_qualidade', 0)
            
            if media_oee >= 85:
                insights.append("OEE excelente - equipamentos performando muito bem")
            elif media_oee >= 75:
                insights.append("OEE bom - equipamentos performando bem")
            elif media_oee >= 65:
                insights.append("OEE regular - equipamentos com performance moderada")
            else:
                insights.append("OEE baixo - equipamentos com performance ruim")
            
            if media_disponibilidade >= 90:
                insights.append("Alta disponibilidade dos equipamentos")
            elif media_disponibilidade < 80:
                insights.append("Baixa disponibilidade - muitas paradas")
        
        elif tipo_consulta == 'qualidade':
            taxa_defeitos = resultado.get('taxa_defeitos_percent', 0)
            total_inspecionadas = resultado.get('total_inspecionadas', 0)
            
            if taxa_defeitos <= 1:
                insights.append("Taxa de defeitos excelente - qualidade muito alta")
            elif taxa_defeitos <= 3:
                insights.append("Taxa de defeitos boa - qualidade alta")
            elif taxa_defeitos <= 5:
                insights.append("Taxa de defeitos regular - qualidade moderada")
            else:
                insights.append("Taxa de defeitos alta - qualidade precisa melhorar")
            
            if total_inspecionadas > 1000:
                insights.append("Alto volume de inspeções - controle de qualidade robusto")
        
        elif tipo_consulta == 'paradas':
            total_paradas = resultado.get('total_paradas', 0)
            total_tempo = resultado.get('total_tempo_parada_horas', 0)
            
            if total_paradas > 0:
                tempo_medio_parada = total_tempo / total_paradas
                insights.append(f"Tempo médio de parada: {tempo_medio_parada:.1f} horas")
            
            if total_tempo > 100:
                insights.append("Alto tempo de parada - revisar estratégia de manutenção")
            elif total_tempo < 10:
                insights.append("Baixo tempo de parada - operação eficiente")
        
        return insights
    
    def _identificar_tendencias(self, tipo_consulta: str, resultado: Dict[str, Any]) -> List[str]:
        """Identifica tendências nos dados"""
        tendencias = []
        
        if tipo_consulta == 'producao':
            dados = resultado.get('dados', [])
            if len(dados) > 1:
                # Analisar tendência de produção
                producoes = [d.get('quantidade_produzida', 0) for d in dados if d.get('quantidade_produzida')]
                if len(producos) > 1:
                    if producos[-1] > producos[0]:
                        tendencias.append("Tendência de aumento na produção")
                    elif producos[-1] < producos[0]:
                        tendencias.append("Tendência de redução na produção")
        
        elif tipo_consulta == 'equipamentos':
            dados = resultado.get('dados', [])
            if len(dados) > 1:
                # Analisar tendência de OEE
                oees = [d.get('oee', 0) for d in dados if d.get('oee')]
                if len(oees) > 1:
                    if oees[-1] > oees[0]:
                        tendencias.append("Tendência de melhoria no OEE")
                    elif oees[-1] < oees[0]:
                        tendencias.append("Tendência de deterioração no OEE")
        
        elif tipo_consulta == 'qualidade':
            dados = resultado.get('dados', [])
            if len(dados) > 1:
                # Analisar tendência de qualidade
                defeitos = [d.get('unidades_rejeitadas', 0) for d in dados if d.get('unidades_rejeitadas')]
                if len(defeitos) > 1:
                    if defeitos[-1] < defeitos[0]:
                        tendencias.append("Tendência de melhoria na qualidade")
                    elif defeitos[-1] > defeitos[0]:
                        tendencias.append("Tendência de deterioração na qualidade")
        
        return tendencias
    
    def _gerar_recomendacoes(self, tipo_consulta: str, resultado: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recomendacoes = []
        
        if tipo_consulta == 'producao':
            total_produzido = resultado.get('total_produzido', 0)
            total_tempo = resultado.get('total_tempo_horas', 0)
            
            if total_tempo > 0:
                produtividade = total_produzido / total_tempo
                if produtividade < 10:
                    recomendacoes.append("Baixa produtividade - revisar processos operacionais")
                    recomendacoes.append("Considerar treinamento da equipe")
                elif produtividade > 50:
                    recomendacoes.append("Alta produtividade - manter padrões atuais")
        
        elif tipo_consulta == 'equipamentos':
            media_oee = resultado.get('media_oee', 0)
            media_disponibilidade = resultado.get('media_disponibilidade', 0)
            
            if media_oee < 75:
                recomendacoes.append("OEE baixo - revisar estratégia de manutenção")
                recomendacoes.append("Avaliar necessidade de melhorias nos equipamentos")
            
            if media_disponibilidade < 85:
                recomendacoes.append("Baixa disponibilidade - implementar manutenção preventiva")
                recomendacoes.append("Revisar procedimentos de parada e setup")
        
        elif tipo_consulta == 'qualidade':
            taxa_defeitos = resultado.get('taxa_defeitos_percent', 0)
            
            if taxa_defeitos > 5:
                recomendacoes.append("Taxa de defeitos alta - revisar processos de qualidade")
                recomendacoes.append("Implementar controles adicionais")
                recomendacoes.append("Treinar operadores em qualidade")
            elif taxa_defeitos <= 1:
                recomendacoes.append("Qualidade excelente - manter padrões atuais")
        
        elif tipo_consulta == 'paradas':
            total_tempo = resultado.get('total_tempo_parada_horas', 0)
            
            if total_tempo > 50:
                recomendacoes.append("Alto tempo de parada - implementar manutenção preventiva")
                recomendacoes.append("Revisar procedimentos de setup")
                recomendacoes.append("Considerar automação de processos")
        
        return recomendacoes
    
    def calcular_kpis_ordem(self, ordem_id: int) -> Dict[str, Any]:
        """Calcula KPIs para uma ordem de produção"""
        try:
            resultado = self.tools.calcular_kpis_ordem(ordem_id)
            
            if 'erro' in resultado:
                return resultado
            
            # Gerar análise dos KPIs
            analise = self._analisar_kpis_ordem(resultado)
            
            return {
                'agente': 'industrial',
                'consulta': 'kpis_ordem',
                'resultado': resultado,
                'analise': analise,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'agente': 'industrial',
                'erro': f'Erro ao calcular KPIs da ordem: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _analisar_kpis_ordem(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa KPIs de uma ordem"""
        eficiencia = resultado.get('eficiencia_percent', 0)
        produtividade = resultado.get('produtividade_unidades_hora', 0)
        total_energia = resultado.get('total_energia_kwh', 0)
        total_tempo = resultado.get('total_tempo_horas', 0)
        
        analise = {
            'resumo': f"Eficiência: {eficiencia:.1f}%, Produtividade: {produtividade:.1f} unidades/hora",
            'classificacao': self._classificar_performance_ordem(eficiencia, produtividade),
            'insights': self._insights_kpis_ordem(eficiencia, produtividade, total_energia, total_tempo),
            'recomendacoes': self._recomendacoes_kpis_ordem(eficiencia, produtividade)
        }
        
        return analise
    
    def _classificar_performance_ordem(self, eficiencia: float, produtividade: float) -> str:
        """Classifica performance da ordem"""
        if eficiencia >= 90 and produtividade >= 20:
            return "Excelente"
        elif eficiencia >= 80 and produtividade >= 15:
            return "Boa"
        elif eficiencia >= 70 and produtividade >= 10:
            return "Regular"
        else:
            return "Baixa"
    
    def _insights_kpis_ordem(self, eficiencia: float, produtividade: float, energia: float, tempo: float) -> List[str]:
        """Gera insights sobre KPIs da ordem"""
        insights = []
        
        if eficiencia >= 90:
            insights.append("Eficiência excelente - ordem executada muito bem")
        elif eficiencia >= 80:
            insights.append("Eficiência boa - ordem executada bem")
        elif eficiencia >= 70:
            insights.append("Eficiência regular - ordem executada com performance moderada")
        else:
            insights.append("Eficiência baixa - ordem com problemas de execução")
        
        if produtividade >= 20:
            insights.append("Alta produtividade - operação muito eficiente")
        elif produtividade >= 15:
            insights.append("Produtividade boa - operação eficiente")
        elif produtividade >= 10:
            insights.append("Produtividade regular - operação com eficiência moderada")
        else:
            insights.append("Baixa produtividade - operação ineficiente")
        
        if tempo > 0 and energia > 0:
            eficiencia_energetica = produtividade / (energia / tempo)
            insights.append(f"Eficiência energética: {eficiencia_energetica:.1f} unidades/kWh")
        
        return insights
    
    def _recomendacoes_kpis_ordem(self, eficiencia: float, produtividade: float) -> List[str]:
        """Gera recomendações baseadas nos KPIs da ordem"""
        recomendacoes = []
        
        if eficiencia < 80:
            recomendacoes.append("Revisar processos de execução da ordem")
            recomendacoes.append("Avaliar necessidade de treinamento da equipe")
            recomendacoes.append("Verificar condições dos equipamentos")
        
        if produtividade < 15:
            recomendacoes.append("Implementar melhorias nos processos operacionais")
            recomendacoes.append("Considerar automação de processos")
            recomendacoes.append("Revisar layout e fluxo de produção")
        
        if eficiencia >= 90 and produtividade >= 20:
            recomendacoes.append("Performance excelente - replicar práticas para outras ordens")
            recomendacoes.append("Manter padrões atuais")
        
        return recomendacoes
    
    def obter_indicadores_operacionais(self, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """Obtém indicadores operacionais consolidados"""
        try:
            resultado = self.tools.obter_indicadores_operacionais(data_inicio, data_fim)
            
            if 'erro' in resultado:
                return resultado
            
            # Gerar análise dos indicadores
            analise = self._analisar_indicadores_operacionais(resultado)
            
            return {
                'agente': 'industrial',
                'consulta': 'indicadores_operacionais',
                'resultado': resultado,
                'analise': analise,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'agente': 'industrial',
                'erro': f'Erro ao obter indicadores operacionais: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _analisar_indicadores_operacionais(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa indicadores operacionais"""
        producao_total = resultado.get('producao_total', 0)
        energia_total = resultado.get('energia_total_kwh', 0)
        media_oee = resultado.get('media_oee', 0)
        taxa_defeitos = resultado.get('taxa_defeitos_percent', 0)
        
        analise = {
            'resumo': f"Produção: {producao_total} unidades, OEE: {media_oee:.1f}%, Defeitos: {taxa_defeitos:.1f}%",
            'classificacao': self._classificar_performance_operacional(media_oee, taxa_defeitos),
            'insights': self._insights_indicadores_operacionais(producao_total, energia_total, media_oee, taxa_defeitos),
            'recomendacoes': self._recomendacoes_indicadores_operacionais(media_oee, taxa_defeitos)
        }
        
        return analise
    
    def _classificar_performance_operacional(self, oee: float, defeitos: float) -> str:
        """Classifica performance operacional"""
        if oee >= 85 and defeitos <= 2:
            return "Excelente"
        elif oee >= 75 and defeitos <= 5:
            return "Boa"
        elif oee >= 65 and defeitos <= 10:
            return "Regular"
        else:
            return "Baixa"
    
    def _insights_indicadores_operacionais(self, producao: int, energia: float, oee: float, defeitos: float) -> List[str]:
        """Gera insights sobre indicadores operacionais"""
        insights = []
        
        if oee >= 85:
            insights.append("OEE excelente - operação muito eficiente")
        elif oee >= 75:
            insights.append("OEE bom - operação eficiente")
        elif oee >= 65:
            insights.append("OEE regular - operação com eficiência moderada")
        else:
            insights.append("OEE baixo - operação ineficiente")
        
        if defeitos <= 2:
            insights.append("Taxa de defeitos excelente - qualidade muito alta")
        elif defeitos <= 5:
            insights.append("Taxa de defeitos boa - qualidade alta")
        elif defeitos <= 10:
            insights.append("Taxa de defeitos regular - qualidade moderada")
        else:
            insights.append("Taxa de defeitos alta - qualidade precisa melhorar")
        
        if producao > 1000:
            insights.append("Alta produção - operação em alta capacidade")
        elif producao < 100:
            insights.append("Baixa produção - operação em baixa capacidade")
        
        if energia > 0:
            eficiencia_energetica = producao / energia
            insights.append(f"Eficiência energética: {eficiencia_energetica:.1f} unidades/kWh")
        
        return insights
    
    def _recomendacoes_indicadores_operacionais(self, oee: float, defeitos: float) -> List[str]:
        """Gera recomendações baseadas nos indicadores operacionais"""
        recomendacoes = []
        
        if oee < 75:
            recomendacoes.append("Implementar melhorias na eficiência operacional")
            recomendacoes.append("Revisar processos de manutenção")
            recomendacoes.append("Avaliar necessidade de treinamento da equipe")
        
        if defeitos > 5:
            recomendacoes.append("Implementar controles de qualidade adicionais")
            recomendacoes.append("Revisar processos de inspeção")
            recomendacoes.append("Treinar operadores em qualidade")
        
        if oee >= 85 and defeitos <= 2:
            recomendacoes.append("Performance excelente - manter padrões atuais")
            recomendacoes.append("Considerar expansão da capacidade")
        
        return recomendacoes
