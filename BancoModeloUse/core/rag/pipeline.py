# core/rag/pipeline.py
"""
Pipeline RAG principal
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.rag.agents import AgenteOrquestrador, AgenteFinanceiro, AgenteIndustrial, AgenteFinalizador
from core.rag.tools import FinanceiroTools, IndustrialTools, IntegracaoTools

class RAGPipeline:
    """Pipeline RAG principal"""
    
    def __init__(self):
        self.orquestrador = AgenteOrquestrador()
        self.agente_financeiro = AgenteFinanceiro()
        self.agente_industrial = AgenteIndustrial()
        self.agente_finalizador = AgenteFinalizador()
        self.tools_financeiro = FinanceiroTools()
        self.tools_industrial = IndustrialTools()
        self.tools_integracao = IntegracaoTools()
    
    def processar_consulta(self, consulta: str) -> Dict[str, Any]:
        """
        Processa consulta do usuário através do pipeline RAG
        
        Args:
            consulta: Consulta do usuário em linguagem natural
        
        Returns:
            Dict com resultado da consulta
        """
        try:
            # 1. Interpretar consulta
            interpretacao = self.orquestrador.interpretar_consulta(consulta)
            
            # 2. Processar com agentes especializados
            respostas = self._processar_com_agentes(interpretacao)
            
            # 3. Consolidar respostas
            resultado_final = self.agente_finalizador.consolidar_respostas(respostas)
            
            # 4. Adicionar metadados
            resultado_final['consulta_original'] = consulta
            resultado_final['interpretacao'] = interpretacao
            resultado_final['pipeline_metadata'] = {
                'versao': '1.0',
                'timestamp': datetime.now().isoformat(),
                'agentes_utilizados': self._obter_agentes_utilizados(respostas)
            }
            
            return resultado_final
            
        except Exception as e:
            return {
                'erro': f'Erro no pipeline RAG: {str(e)}',
                'consulta_original': consulta,
                'timestamp': datetime.now().isoformat()
            }
    
    def _processar_com_agentes(self, interpretacao: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Processa consulta com agentes especializados"""
        respostas = []
        
        agente_destino = interpretacao.get('agente_destino')
        tipo_consulta = interpretacao.get('tipo_consulta')
        parametros = interpretacao.get('parametros', {})
        
        # Processar com agente financeiro
        if agente_destino == 'financeiro':
            resposta = self.agente_financeiro.processar_consulta(tipo_consulta, parametros)
            respostas.append(resposta)
        
        # Processar com agente industrial
        elif agente_destino == 'industrial':
            resposta = self.agente_industrial.processar_consulta(tipo_consulta, parametros)
            respostas.append(resposta)
        
        # Processar com agente de integração
        elif agente_destino == 'integracao':
            resposta = self._processar_integracao(tipo_consulta, parametros)
            respostas.append(resposta)
        
        # Processar com múltiplos agentes se necessário
        elif agente_destino == 'multiplos':
            respostas.extend(self._processar_multiplos_agentes(interpretacao))
        
        return respostas
    
    def _processar_integracao(self, tipo_consulta: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Processa consulta de integração"""
        try:
            # Executar consulta integrada
            resultado = self.tools_integracao.join_financeiro_industrial(tipo_consulta, parametros)
            
            # Gerar análise integrada
            analise = self._gerar_analise_integrada(tipo_consulta, resultado)
            
            return {
                'agente': 'integracao',
                'tipo_consulta': tipo_consulta,
                'parametros': parametros,
                'resultado': resultado,
                'analise': analise,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'agente': 'integracao',
                'erro': f'Erro ao processar integração: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _processar_multiplos_agentes(self, interpretacao: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Processa consulta com múltiplos agentes"""
        respostas = []
        
        # Processar com agente financeiro
        if 'financeiro' in interpretacao.get('agente_destino', ''):
            resposta_financeiro = self.agente_financeiro.processar_consulta(
                interpretacao.get('tipo_consulta'), 
                interpretacao.get('parametros', {})
            )
            respostas.append(resposta_financeiro)
        
        # Processar com agente industrial
        if 'industrial' in interpretacao.get('agente_destino', ''):
            resposta_industrial = self.agente_industrial.processar_consulta(
                interpretacao.get('tipo_consulta'),
                interpretacao.get('parametros', {})
            )
            respostas.append(resposta_industrial)
        
        return respostas
    
    def _gerar_analise_integrada(self, tipo_consulta: str, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """Gera análise integrada"""
        if 'erro' in resultado:
            return {'erro': resultado['erro']}
        
        analise = {
            'resumo': self._gerar_resumo_integrado(tipo_consulta, resultado),
            'insights': self._gerar_insights_integrados(tipo_consulta, resultado),
            'correlacoes': self._identificar_correlacoes_integradas(tipo_consulta, resultado),
            'recomendacoes': self._gerar_recomendacoes_integradas(tipo_consulta, resultado)
        }
        
        return analise
    
    def _gerar_resumo_integrado(self, tipo_consulta: str, resultado: Dict[str, Any]) -> str:
        """Gera resumo integrado"""
        if tipo_consulta == 'vendas_producao':
            total_vendas = resultado.get('total_vendas', 0)
            total_producao = resultado.get('total_producao', 0)
            eficiencia = resultado.get('eficiencia_vendas_percent', 0)
            return f"Análise integrada vendas vs produção: {total_vendas} vendas, {total_producao} produção, eficiência {eficiencia:.1f}%"
        
        elif tipo_consulta == 'custos_eficiencia':
            total_custos = resultado.get('total_custos', 0)
            total_producao = resultado.get('total_producao', 0)
            custo_por_unidade = resultado.get('custo_por_unidade', 0)
            return f"Análise integrada custos vs eficiência: R$ {total_custos:,.2f} custos, {total_producao} produção, R$ {custo_por_unidade:.2f} por unidade"
        
        elif tipo_consulta == 'qualidade_lucratividade':
            taxa_defeitos = resultado.get('taxa_defeitos_percent', 0)
            total_receita = resultado.get('total_receita', 0)
            impacto_defeitos = resultado.get('impacto_defeitos', 0)
            return f"Análise integrada qualidade vs lucratividade: {taxa_defeitos:.1f}% defeitos, R$ {total_receita:,.2f} receita, R$ {impacto_defeitos:,.2f} impacto"
        
        else:
            return "Análise integrada concluída com sucesso"
    
    def _gerar_insights_integrados(self, tipo_consulta: str, resultado: Dict[str, Any]) -> List[str]:
        """Gera insights integrados"""
        insights = []
        
        if tipo_consulta == 'vendas_producao':
            eficiencia = resultado.get('eficiencia_vendas_percent', 0)
            if eficiencia >= 90:
                insights.append("Excelente eficiência vendas vs produção")
            elif eficiencia >= 80:
                insights.append("Boa eficiência vendas vs produção")
            else:
                insights.append("Eficiência vendas vs produção precisa melhorar")
        
        elif tipo_consulta == 'custos_eficiencia':
            custo_por_unidade = resultado.get('custo_por_unidade', 0)
            if custo_por_unidade < 10:
                insights.append("Custo por unidade baixo - operação eficiente")
            elif custo_por_unidade > 50:
                insights.append("Custo por unidade alto - revisar eficiência")
        
        elif tipo_consulta == 'qualidade_lucratividade':
            taxa_defeitos = resultado.get('taxa_defeitos_percent', 0)
            if taxa_defeitos <= 2:
                insights.append("Taxa de defeitos baixa - qualidade excelente")
            elif taxa_defeitos > 10:
                insights.append("Taxa de defeitos alta - impacto na lucratividade")
        
        return insights
    
    def _identificar_correlacoes_integradas(self, tipo_consulta: str, resultado: Dict[str, Any]) -> List[str]:
        """Identifica correlações integradas"""
        correlacoes = []
        
        if tipo_consulta == 'vendas_producao':
            correlacoes.append("Correlação positiva entre produção e vendas")
            correlacoes.append("Oportunidade de otimização da eficiência")
        
        elif tipo_consulta == 'custos_eficiencia':
            correlacoes.append("Correlação entre custos e eficiência operacional")
            correlacoes.append("Impacto da eficiência nos custos unitários")
        
        elif tipo_consulta == 'qualidade_lucratividade':
            correlacoes.append("Correlação entre qualidade e lucratividade")
            correlacoes.append("Impacto dos defeitos na receita")
        
        return correlacoes
    
    def _gerar_recomendacoes_integradas(self, tipo_consulta: str, resultado: Dict[str, Any]) -> List[str]:
        """Gera recomendações integradas"""
        recomendacoes = []
        
        if tipo_consulta == 'vendas_producao':
            eficiencia = resultado.get('eficiencia_vendas_percent', 0)
            if eficiencia < 80:
                recomendacoes.append("Focar em aumentar a eficiência vendas vs produção")
                recomendacoes.append("Revisar processos de vendas e produção")
        
        elif tipo_consulta == 'custos_eficiencia':
            custo_por_unidade = resultado.get('custo_por_unidade', 0)
            if custo_por_unidade > 30:
                recomendacoes.append("Implementar melhorias na eficiência operacional")
                recomendacoes.append("Revisar estrutura de custos")
        
        elif tipo_consulta == 'qualidade_lucratividade':
            taxa_defeitos = resultado.get('taxa_defeitos_percent', 0)
            if taxa_defeitos > 5:
                recomendacoes.append("Implementar controles de qualidade adicionais")
                recomendacoes.append("Revisar processos de inspeção")
        
        return recomendacoes
    
    def _obter_agentes_utilizados(self, respostas: List[Dict[str, Any]]) -> List[str]:
        """Obtém lista de agentes utilizados"""
        agentes = []
        for resposta in respostas:
            agente = resposta.get('agente')
            if agente and agente not in agentes:
                agentes.append(agente)
        return agentes
    
    def obter_estatisticas_pipeline(self) -> Dict[str, Any]:
        """Retorna estatísticas do pipeline"""
        return {
            'pipeline': 'RAG',
            'versao': '1.0',
            'agentes_disponiveis': [
                'orquestrador',
                'financeiro',
                'industrial',
                'finalizador'
            ],
            'tools_disponiveis': [
                'financeiro_tools',
                'industrial_tools',
                'integracao_tools'
            ],
            'timestamp': datetime.now().isoformat()
        }
    
    def testar_pipeline(self) -> Dict[str, Any]:
        """Testa o pipeline com consultas de exemplo"""
        consultas_teste = [
            "Quais foram as vendas do último mês?",
            "Como está a produção da máquina 1?",
            "Qual a correlação entre custos e eficiência?",
            "Mostre o dashboard executivo"
        ]
        
        resultados_teste = []
        for consulta in consultas_teste:
            try:
                resultado = self.processar_consulta(consulta)
                resultados_teste.append({
                    'consulta': consulta,
                    'status': 'sucesso' if 'erro' not in resultado else 'erro',
                    'resultado': resultado
                })
            except Exception as e:
                resultados_teste.append({
                    'consulta': consulta,
                    'status': 'erro',
                    'erro': str(e)
                })
        
        return {
            'teste_pipeline': True,
            'consultas_testadas': len(consultas_teste),
            'resultados': resultados_teste,
            'timestamp': datetime.now().isoformat()
        }
