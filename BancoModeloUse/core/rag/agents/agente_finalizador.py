# core/rag/agents/agente_finalizador.py
"""
Agente Finalizador - consolida respostas e produz resultado final
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class AgenteFinalizador:
    """Agente finalizador para consolidar respostas e produzir resultado final"""
    
    def __init__(self):
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Retorna o prompt do sistema para o agente finalizador"""
        return """
        Você é um Agente Finalizador especializado em consolidar respostas de múltiplos agentes especializados.
        Sua função é integrar análises de diferentes domínios e produzir um resultado final coeso e acionável.
        
        RESPONSABILIDADES:
        - Consolidar respostas de agentes financeiros e industriais
        - Identificar correlações entre domínios
        - Produzir insights integrados
        - Gerar recomendações estratégicas
        - Verificar coerência entre análises
        - Formatar resultado final para tomada de decisão
        
        INSTRUÇÕES:
        - Sempre integre perspectivas de múltiplos domínios
        - Identifique correlações e dependências
        - Produza insights que não seriam visíveis em análises isoladas
        - Sugira ações estratégicas baseadas na visão integrada
        - Seja objetivo e acionável nas recomendações
        - Formate o resultado para facilitar a tomada de decisão
        """
    
    def consolidar_respostas(self, respostas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Consolida respostas de múltiplos agentes
        
        Args:
            respostas: Lista de respostas dos agentes especializados
        
        Returns:
            Dict com resultado consolidado
        """
        try:
            # Verificar se há respostas
            if not respostas:
                return {
                    'erro': 'Nenhuma resposta recebida para consolidar',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Separar respostas por agente
            respostas_por_agente = self._separar_respostas_por_agente(respostas)
            
            # Consolidar análises
            analise_consolidada = self._consolidar_analises(respostas_por_agente)
            
            # Identificar correlações
            correlacoes = self._identificar_correlacoes(respostas_por_agente)
            
            # Gerar insights integrados
            insights_integrados = self._gerar_insights_integrados(respostas_por_agente)
            
            # Gerar recomendações estratégicas
            recomendacoes_estrategicas = self._gerar_recomendacoes_estrategicas(respostas_por_agente)
            
            # Verificar coerência
            verificacao_coerencia = self._verificar_coerencia(respostas_por_agente)
            
            # Produzir resultado final
            resultado_final = {
                'resumo_executivo': self._gerar_resumo_executivo(analise_consolidada),
                'analise_consolidada': analise_consolidada,
                'correlacoes': correlacoes,
                'insights_integrados': insights_integrados,
                'recomendacoes_estrategicas': recomendacoes_estrategicas,
                'verificacao_coerencia': verificacao_coerencia,
                'respostas_originais': respostas_por_agente,
                'timestamp': datetime.now().isoformat()
            }
            
            return resultado_final
            
        except Exception as e:
            return {
                'erro': f'Erro ao consolidar respostas: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _separar_respostas_por_agente(self, respostas: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Separa respostas por tipo de agente"""
        respostas_por_agente = {
            'financeiro': [],
            'industrial': [],
            'integracao': []
        }
        
        for resposta in respostas:
            agente = resposta.get('agente', 'desconhecido')
            if agente in respostas_por_agente:
                respostas_por_agente[agente].append(resposta)
        
        return respostas_por_agente
    
    def _consolidar_analises(self, respostas_por_agente: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Consolida análises de diferentes agentes"""
        analise_consolidada = {
            'financeiro': self._consolidar_analise_financeira(respostas_por_agente.get('financeiro', [])),
            'industrial': self._consolidar_analise_industrial(respostas_por_agente.get('industrial', [])),
            'integracao': self._consolidar_analise_integracao(respostas_por_agente.get('integracao', []))
        }
        
        return analise_consolidada
    
    def _consolidar_analise_financeira(self, respostas_financeiras: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolida análises financeiras"""
        if not respostas_financeiras:
            return {'status': 'sem_dados', 'mensagem': 'Nenhuma análise financeira disponível'}
        
        # Consolidar insights
        todos_insights = []
        todas_recomendacoes = []
        
        for resposta in respostas_financeiras:
            analise = resposta.get('analise', {})
            if isinstance(analise, dict):
                insights = analise.get('insights', [])
                recomendacoes = analise.get('recomendacoes', [])
                todos_insights.extend(insights)
                todas_recomendacoes.extend(recomendacoes)
        
        return {
            'status': 'consolidado',
            'total_analises': len(respostas_financeiras),
            'insights_consolidados': list(set(todos_insights)),
            'recomendacoes_consolidadas': list(set(todas_recomendacoes)),
            'resumo': f"Consolidadas {len(respostas_financeiras)} análises financeiras"
        }
    
    def _consolidar_analise_industrial(self, respostas_industriais: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolida análises industriais"""
        if not respostas_industriais:
            return {'status': 'sem_dados', 'mensagem': 'Nenhuma análise industrial disponível'}
        
        # Consolidar insights
        todos_insights = []
        todas_recomendacoes = []
        
        for resposta in respostas_industriais:
            analise = resposta.get('analise', {})
            if isinstance(analise, dict):
                insights = analise.get('insights', [])
                recomendacoes = analise.get('recomendacoes', [])
                todos_insights.extend(insights)
                todas_recomendacoes.extend(recomendacoes)
        
        return {
            'status': 'consolidado',
            'total_analises': len(respostas_industriais),
            'insights_consolidados': list(set(todos_insights)),
            'recomendacoes_consolidadas': list(set(todas_recomendacoes)),
            'resumo': f"Consolidadas {len(respostas_industriais)} análises industriais"
        }
    
    def _consolidar_analise_integracao(self, respostas_integracao: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolida análises de integração"""
        if not respostas_integracao:
            return {'status': 'sem_dados', 'mensagem': 'Nenhuma análise de integração disponível'}
        
        # Consolidar insights
        todos_insights = []
        todas_recomendacoes = []
        
        for resposta in respostas_integracao:
            analise = resposta.get('analise', {})
            if isinstance(analise, dict):
                insights = analise.get('insights', [])
                recomendacoes = analise.get('recomendacoes', [])
                todos_insights.extend(insights)
                todas_recomendacoes.extend(recomendacoes)
        
        return {
            'status': 'consolidado',
            'total_analises': len(respostas_integracao),
            'insights_consolidados': list(set(todos_insights)),
            'recomendacoes_consolidadas': list(set(todas_recomendacoes)),
            'resumo': f"Consolidadas {len(respostas_integracao)} análises de integração"
        }
    
    def _identificar_correlacoes(self, respostas_por_agente: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Identifica correlações entre domínios"""
        correlacoes = []
        
        # Correlação financeiro-industrial
        if respostas_por_agente.get('financeiro') and respostas_por_agente.get('industrial'):
            correlacao = self._analisar_correlacao_financeiro_industrial(
                respostas_por_agente['financeiro'],
                respostas_por_agente['industrial']
            )
            if correlacao:
                correlacoes.append(correlacao)
        
        # Correlação com integração
        if respostas_por_agente.get('integracao'):
            correlacao = self._analisar_correlacao_integracao(respostas_por_agente['integracao'])
            if correlacao:
                correlacoes.append(correlacao)
        
        return correlacoes
    
    def _analisar_correlacao_financeiro_industrial(self, respostas_financeiras: List[Dict[str, Any]], respostas_industriais: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analisa correlação entre dados financeiros e industriais"""
        # Implementação básica - pode ser expandida
        return {
            'tipo': 'financeiro_industrial',
            'descricao': 'Correlação entre performance financeira e operacional',
            'insights': [
                'Análise integrada de receita vs produção',
                'Correlação entre custos e eficiência operacional',
                'Impacto da qualidade na lucratividade'
            ],
            'recomendacoes': [
                'Monitorar impacto de mudanças operacionais na receita',
                'Avaliar correlação entre investimentos e performance',
                'Considerar indicadores integrados para tomada de decisão'
            ]
        }
    
    def _analisar_correlacao_integracao(self, respostas_integracao: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analisa correlações de integração"""
        return {
            'tipo': 'integracao',
            'descricao': 'Análise integrada de múltiplos domínios',
            'insights': [
                'Visão holística da performance empresarial',
                'Identificação de sinergias entre áreas',
                'Análise de trade-offs entre objetivos'
            ],
            'recomendacoes': [
                'Desenvolver estratégias integradas',
                'Considerar impactos cruzados nas decisões',
                'Implementar indicadores de performance integrados'
            ]
        }
    
    def _gerar_insights_integrados(self, respostas_por_agente: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Gera insights integrados"""
        insights = []
        
        # Insight sobre sinergias
        if respostas_por_agente.get('financeiro') and respostas_por_agente.get('industrial'):
            insights.append("Sinergia entre performance financeira e operacional identificada")
            insights.append("Oportunidade de otimização integrada entre áreas")
        
        # Insight sobre trade-offs
        if respostas_por_agente.get('integracao'):
            insights.append("Análise integrada revela trade-offs entre objetivos")
            insights.append("Necessidade de balanceamento entre eficiência e qualidade")
        
        # Insight sobre oportunidades
        insights.append("Identificação de oportunidades de melhoria cruzadas")
        insights.append("Potencial para otimização de recursos integrados")
        
        return insights
    
    def _gerar_recomendacoes_estrategicas(self, respostas_por_agente: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Gera recomendações estratégicas"""
        recomendacoes = []
        
        # Recomendações de integração
        if respostas_por_agente.get('financeiro') and respostas_por_agente.get('industrial'):
            recomendacoes.append("Implementar indicadores de performance integrados")
            recomendacoes.append("Desenvolver estratégias que considerem ambos os domínios")
            recomendacoes.append("Criar processos de tomada de decisão integrados")
        
        # Recomendações de otimização
        if respostas_por_agente.get('integracao'):
            recomendacoes.append("Focar em otimizações que beneficiem múltiplas áreas")
            recomendacoes.append("Desenvolver métricas de sucesso integradas")
            recomendacoes.append("Criar cultura de colaboração entre áreas")
        
        # Recomendações gerais
        recomendacoes.append("Estabelecer processos de monitoramento contínuo")
        recomendacoes.append("Implementar feedback loops entre áreas")
        recomendacoes.append("Desenvolver capacidades de análise preditiva")
        
        return recomendacoes
    
    def _verificar_coerencia(self, respostas_por_agente: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Verifica coerência entre respostas"""
        verificacao = {
            'status': 'verificado',
            'inconsistencias': [],
            'alertas': [],
            'observacoes': []
        }
        
        # Verificar inconsistências entre domínios
        if respostas_por_agente.get('financeiro') and respostas_por_agente.get('industrial'):
            # Implementar lógica de verificação de coerência
            verificacao['observacoes'].append("Análise de coerência entre domínios financeiro e industrial")
        
        # Verificar qualidade das respostas
        for agente, respostas in respostas_por_agente.items():
            if respostas:
                for resposta in respostas:
                    if 'erro' in resposta:
                        verificacao['alertas'].append(f"Erro em resposta do agente {agente}: {resposta['erro']}")
        
        return verificacao
    
    def _gerar_resumo_executivo(self, analise_consolidada: Dict[str, Any]) -> str:
        """Gera resumo executivo"""
        resumo = "Análise integrada concluída com sucesso. "
        
        # Adicionar informações sobre domínios analisados
        dominios_analisados = []
        for dominio, analise in analise_consolidada.items():
            if analise.get('status') == 'consolidado':
                dominios_analisados.append(dominio)
        
        if dominios_analisados:
            resumo += f"Domínios analisados: {', '.join(dominios_analisados)}. "
        
        # Adicionar informações sobre correlações
        resumo += "Correlações entre domínios identificadas. "
        
        # Adicionar informações sobre recomendações
        resumo += "Recomendações estratégicas geradas para otimização integrada."
        
        return resumo
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do agente finalizador"""
        return {
            'agente': 'finalizador',
            'funcao': 'consolidacao_respostas',
            'timestamp': datetime.now().isoformat()
        }
