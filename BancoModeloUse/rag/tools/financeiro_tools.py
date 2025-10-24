# rag/tools/financeiro_tools.py
"""
Ferramentas RAG para consultas financeiras
"""
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from pydantic import BaseModel
from infrastructure.database.sessions import get_financeiro_db
from core.repositories.financeiro import CustosRepository, VendasRepository, ContabilRepository
from .base import BaseTool, ToolInput, ToolResult
from .registry import register_tool
import json

class FinanceiroQueryInput(ToolInput):
    """Input para consulta financeira"""
    consulta: str
    parametros: Optional[Dict[str, Any]] = None

class MargemContribuicaoInput(ToolInput):
    """Input para cálculo de margem de contribuição"""
    produto_id: int
    data_inicio: str
    data_fim: str

class IndicadoresFinanceirosInput(ToolInput):
    """Input para indicadores financeiros"""
    data_inicio: str
    data_fim: str

class FinanceiroQueryTool(BaseTool):
    """Tool para consultas financeiras genéricas"""
    
    name = "query_financeira"
    description = "Executa consultas financeiras (vendas, custos, lançamentos, orçamentos)"
    
    def __init__(self):
        self.custos_repo = None
        self.vendas_repo = None
        self.contabil_repo = None
    
    def _get_repositories(self, db_session):
        """Inicializa repositórios com sessão"""
        if not self.custos_repo:
            self.custos_repo = CustosRepository(db_session)
        if not self.vendas_repo:
            self.vendas_repo = VendasRepository(db_session)
        if not self.contabil_repo:
            self.contabil_repo = ContabilRepository(db_session)
    
    def run(self, payload: FinanceiroQueryInput) -> ToolResult:
        """
        Executa consulta financeira genérica
        
        Args:
            payload: Dados de entrada validados
        
        Returns:
            Resultado da consulta
        """
        if not payload.parametros:
            payload.parametros = {}
        
        data_inicio = payload.parametros.get('data_inicio')
        data_fim = payload.parametros.get('data_fim')
        
        with get_financeiro_db() as db:
            self._get_repositories(db)
            
            if payload.consulta == 'vendas':
                result = self._consultar_vendas(data_inicio, data_fim, payload.parametros)
            elif payload.consulta == 'custos':
                result = self._consultar_custos(data_inicio, data_fim, payload.parametros)
            elif payload.consulta == 'lancamentos':
                result = self._consultar_lancamentos(data_inicio, data_fim, payload.parametros)
            elif payload.consulta == 'orcamentos':
                result = self._consultar_orcamentos(data_inicio, data_fim, payload.parametros)
            else:
                result = {'erro': f'Tipo de consulta não suportado: {payload.consulta}'}
            
            return ToolResult(
                data=result,
                meta={"tool": self.name, "consulta": payload.consulta}
            )
    
    def _consultar_vendas(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta vendas"""
        try:
            if data_inicio and data_fim:
                vendas = self.vendas_repo.get_vendas_by_periodo(data_inicio, data_fim)
            else:
                vendas = self.vendas_repo.get_all_vendas()
            
            # Filtrar por produto se especificado
            produto_id = parametros.get('produto_id')
            if produto_id:
                vendas = [v for v in vendas if v.produto_id == produto_id]
            
            # Filtrar por cliente se especificado
            cliente_id = parametros.get('cliente_id')
            if cliente_id:
                vendas = [v for v in vendas if v.cliente_id == cliente_id]
            
            # Calcular totais
            total_quantidade = sum(v.quantidade_vendida for v in vendas)
            total_valor = sum(v.quantidade_vendida * v.preco_unitario_venda for v in vendas)
            
            return {
                'tipo': 'vendas',
                'total_registros': len(vendas),
                'total_quantidade': total_quantidade,
                'total_valor': float(total_valor),
                'dados': [
                    {
                        'venda_id': v.venda_id,
                        'produto_id': v.produto_id,
                        'cliente_id': v.cliente_id,
                        'quantidade_vendida': v.quantidade_vendida,
                        'preco_unitario': float(v.preco_unitario_venda),
                        'data_venda': v.data_venda.isoformat() if v.data_venda else None
                    } for v in vendas
                ]
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar vendas: {str(e)}'}
    
    def _consultar_custos(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta custos"""
        try:
            if data_inicio and data_fim:
                custos = self.custos_repo.get_custos_producao_by_periodo(data_inicio, data_fim)
            else:
                custos = self.custos_repo.get_custos_producao()
            
            # Calcular totais
            total_materia_prima = sum(float(c.materia_prima) for c in custos)
            total_mao_obra = sum(float(c.mao_obra_direta) for c in custos)
            total_indiretos = sum(float(c.custos_indiretos) for c in custos)
            total_custos = sum(float(c.custo_total) for c in custos if c.custo_total)
            
            return {
                'tipo': 'custos',
                'total_registros': len(custos),
                'total_materia_prima': total_materia_prima,
                'total_mao_obra': total_mao_obra,
                'total_indiretos': total_indiretos,
                'total_custos': total_custos,
                'dados': [
                    {
                        'custo_id': c.id,
                        'materia_prima': float(c.materia_prima),
                        'mao_obra_direta': float(c.mao_obra_direta),
                        'custos_indiretos': float(c.custos_indiretos),
                        'custo_total': float(c.custo_total) if c.custo_total else 0,
                        'custo_unitario': float(c.custo_unitario) if c.custo_unitario else 0,
                        'data_registro': c.data_registro.isoformat() if c.data_registro else None
                    } for c in custos
                ]
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar custos: {str(e)}'}
    
    def _consultar_lancamentos(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta lançamentos financeiros"""
        try:
            if data_inicio and data_fim:
                lancamentos = self.contabil_repo.get_lancamentos_by_periodo(data_inicio, data_fim)
            else:
                lancamentos = self.contabil_repo.get_all_lancamentos_financeiros()
            
            # Filtrar por conta se especificado
            conta_id = parametros.get('conta_id')
            if conta_id:
                lancamentos = [l for l in lancamentos if l.conta_id == conta_id]
            
            # Calcular totais
            total_valor = sum(float(l.valor) for l in lancamentos if l.valor)
            
            return {
                'tipo': 'lancamentos',
                'total_registros': len(lancamentos),
                'total_valor': total_valor,
                'dados': [
                    {
                        'lancamento_id': l.lancamento_id,
                        'conta_id': l.conta_id,
                        'data_lancamento': l.data_lancamento.isoformat() if l.data_lancamento else None,
                        'valor': float(l.valor) if l.valor else 0,
                        'descricao': l.descricao
                    } for l in lancamentos
                ]
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar lançamentos: {str(e)}'}
    
    def _consultar_orcamentos(self, data_inicio: date, data_fim: date, parametros: Dict) -> Dict[str, Any]:
        """Consulta orçamentos"""
        try:
            if data_inicio and data_fim:
                orcamentos = self.vendas_repo.get_orcamentos_by_periodo(data_inicio, data_fim)
            else:
                orcamentos = self.vendas_repo.get_all_orcamentos()
            
            # Filtrar por conta se especificado
            conta_id = parametros.get('conta_id')
            if conta_id:
                orcamentos = [o for o in orcamentos if o.conta_id == conta_id]
            
            # Calcular totais
            total_orcado = sum(float(o.valor_orcado) for o in orcamentos if o.valor_orcado)
            
            return {
                'tipo': 'orcamentos',
                'total_registros': len(orcamentos),
                'total_orcado': total_orcado,
                'dados': [
                    {
                        'orcamento_id': o.orcamento_id,
                        'conta_id': o.conta_id,
                        'valor_orcado': float(o.valor_orcado) if o.valor_orcado else 0,
                        'periodo': o.periodo.isoformat() if o.periodo else None
                    } for o in orcamentos
                ]
            }
        except Exception as e:
            return {'erro': f'Erro ao consultar orçamentos: {str(e)}'}
    
    def calcular_margem_contribuicao(self, produto_id: int, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """Calcula margem de contribuição para um produto"""
        try:
            with get_financeiro_db() as db:
                self._get_repositories(db)
                
                # Buscar vendas do produto
                vendas = self.vendas_repo.get_vendas_by_produto(produto_id)
                vendas_periodo = [v for v in vendas if data_inicio <= v.data_venda <= data_fim]
                
                # Buscar custos do produto
                custos = self.custos_repo.get_custos_producao_by_periodo(data_inicio, data_fim)
                
                # Calcular receita
                receita_total = sum(v.quantidade_vendida * v.preco_unitario_venda for v in vendas_periodo)
                
                # Calcular custos
                custo_total = sum(float(c.custo_total) for c in custos if c.custo_total)
                
                # Calcular margem
                margem_contribuicao = receita_total - custo_total
                percentual_margem = (margem_contribuicao / receita_total * 100) if receita_total > 0 else 0
                
                return {
                    'produto_id': produto_id,
                    'periodo': {'inicio': data_inicio.isoformat(), 'fim': data_fim.isoformat()},
                    'receita_total': float(receita_total),
                    'custo_total': custo_total,
                    'margem_contribuicao': float(margem_contribuicao),
                    'percentual_margem': percentual_margem
                }
        except Exception as e:
            return {'erro': f'Erro ao calcular margem de contribuição: {str(e)}'}
    
    def obter_indicadores_financeiros(self, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """Obtém indicadores financeiros consolidados"""
        try:
            with get_financeiro_db() as db:
                self._get_repositories(db)
                
                # Vendas
                vendas = self.vendas_repo.get_vendas_by_periodo(data_inicio, data_fim)
                receita_total = sum(v.quantidade_vendida * v.preco_unitario_venda for v in vendas)
                
                # Custos
                custos = self.custos_repo.get_custos_producao_by_periodo(data_inicio, data_fim)
                custo_total = sum(float(c.custo_total) for c in custos if c.custo_total)
                
                # Análises financeiras
                analises = self.custos_repo.get_analises_financeiras_by_periodo(data_inicio, data_fim)
                
                # Calcular indicadores
                lucro_bruto = receita_total - custo_total
                margem_bruta = (lucro_bruto / receita_total * 100) if receita_total > 0 else 0
                
                return {
                    'periodo': {'inicio': data_inicio.isoformat(), 'fim': data_fim.isoformat()},
                    'receita_total': float(receita_total),
                    'custo_total': custo_total,
                    'lucro_bruto': float(lucro_bruto),
                    'margem_bruta_percent': margem_bruta,
                    'total_vendas': len(vendas),
                    'total_custos': len(custos),
                    'analises_disponiveis': len(analises)
                }
        except Exception as e:
            return {'erro': f'Erro ao obter indicadores financeiros: {str(e)}'}


class MargemContribuicaoTool(BaseTool):
    """Tool para cálculo de margem de contribuição"""
    
    name = "calcular_margem_contribuicao"
    description = "Calcula margem de contribuição para um produto"
    
    def __init__(self):
        self.custos_repo = None
        self.vendas_repo = None
    
    def _get_repositories(self, db_session):
        """Inicializa repositórios com sessão"""
        if not self.custos_repo:
            self.custos_repo = CustosRepository(db_session)
        if not self.vendas_repo:
            self.vendas_repo = VendasRepository(db_session)
    
    def run(self, payload: MargemContribuicaoInput) -> ToolResult:
        """
        Calcula margem de contribuição
        
        Args:
            payload: Dados de entrada validados
        
        Returns:
            Resultado do cálculo
        """
        try:
            data_inicio = datetime.fromisoformat(payload.data_inicio).date()
            data_fim = datetime.fromisoformat(payload.data_fim).date()
            
            with get_financeiro_db() as db:
                self._get_repositories(db)
                
                # Buscar vendas do produto
                vendas = self.vendas_repo.get_vendas_by_produto(payload.produto_id)
                vendas_periodo = [v for v in vendas if data_inicio <= v.data_venda <= data_fim]
                
                # Buscar custos do produto
                custos = self.custos_repo.get_custos_producao_by_periodo(data_inicio, data_fim)
                
                # Calcular receita
                receita_total = sum(v.quantidade_vendida * v.preco_unitario_venda for v in vendas_periodo)
                
                # Calcular custos
                custo_total = sum(float(c.custo_total) for c in custos if c.custo_total)
                
                # Calcular margem
                margem_contribuicao = receita_total - custo_total
                percentual_margem = (margem_contribuicao / receita_total * 100) if receita_total > 0 else 0
                
                result = {
                    'produto_id': payload.produto_id,
                    'periodo': {'inicio': data_inicio.isoformat(), 'fim': data_fim.isoformat()},
                    'receita_total': float(receita_total),
                    'custo_total': custo_total,
                    'margem_contribuicao': float(margem_contribuicao),
                    'percentual_margem': percentual_margem
                }
                
                return ToolResult(
                    data=result,
                    meta={"tool": self.name, "produto_id": payload.produto_id}
                )
                
        except Exception as e:
            return ToolResult(
                data={'erro': f'Erro ao calcular margem de contribuição: {str(e)}'},
                meta={"tool": self.name, "erro": True}
            )


class IndicadoresFinanceirosTool(BaseTool):
    """Tool para indicadores financeiros"""
    
    name = "obter_indicadores_financeiros"
    description = "Obtém indicadores financeiros consolidados"
    
    def __init__(self):
        self.custos_repo = None
        self.vendas_repo = None
    
    def _get_repositories(self, db_session):
        """Inicializa repositórios com sessão"""
        if not self.custos_repo:
            self.custos_repo = CustosRepository(db_session)
        if not self.vendas_repo:
            self.vendas_repo = VendasRepository(db_session)
    
    def run(self, payload: IndicadoresFinanceirosInput) -> ToolResult:
        """
        Obtém indicadores financeiros
        
        Args:
            payload: Dados de entrada validados
        
        Returns:
            Resultado dos indicadores
        """
        try:
            data_inicio = datetime.fromisoformat(payload.data_inicio).date()
            data_fim = datetime.fromisoformat(payload.data_fim).date()
            
            with get_financeiro_db() as db:
                self._get_repositories(db)
                
                # Vendas
                vendas = self.vendas_repo.get_vendas_by_periodo(data_inicio, data_fim)
                receita_total = sum(v.quantidade_vendida * v.preco_unitario_venda for v in vendas)
                
                # Custos
                custos = self.custos_repo.get_custos_producao_by_periodo(data_inicio, data_fim)
                custo_total = sum(float(c.custo_total) for c in custos if c.custo_total)
                
                # Análises financeiras
                analises = self.custos_repo.get_analises_financeiras_by_periodo(data_inicio, data_fim)
                
                # Calcular indicadores
                lucro_bruto = receita_total - custo_total
                margem_bruta = (lucro_bruto / receita_total * 100) if receita_total > 0 else 0
                
                result = {
                    'periodo': {'inicio': data_inicio.isoformat(), 'fim': data_fim.isoformat()},
                    'receita_total': float(receita_total),
                    'custo_total': custo_total,
                    'lucro_bruto': float(lucro_bruto),
                    'margem_bruta_percent': margem_bruta,
                    'total_vendas': len(vendas),
                    'total_custos': len(custos),
                    'analises_disponiveis': len(analises)
                }
                
                return ToolResult(
                    data=result,
                    meta={"tool": self.name, "periodo": f"{data_inicio} a {data_fim}"}
                )
                
        except Exception as e:
            return ToolResult(
                data={'erro': f'Erro ao obter indicadores financeiros: {str(e)}'},
                meta={"tool": self.name, "erro": True}
            )


class FinanceiroTools:
    """Classe wrapper para todas as ferramentas financeiras"""
    
    def __init__(self):
        self.query_tool = FinanceiroQueryTool()
        self.margem_tool = MargemContribuicaoTool()
        self.indicadores_tool = IndicadoresFinanceirosTool()
    
    def query_financeira(self, consulta: str, parametros: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executa consulta financeira genérica"""
        return self.query_tool.execute(
            FinanceiroQueryInput(consulta=consulta, parametros=parametros)
        )
    
    def calcular_margem_contribuicao(self, produto_id: int, data_inicio: str, data_fim: str) -> Dict[str, Any]:
        """Calcula margem de contribuição"""
        return self.margem_tool.execute(
            MargemContribuicaoInput(produto_id=produto_id, data_inicio=data_inicio, data_fim=data_fim)
        )
    
    def obter_indicadores_financeiros(self, data_inicio: str, data_fim: str) -> Dict[str, Any]:
        """Obtém indicadores financeiros"""
        return self.indicadores_tool.execute(
            IndicadoresFinanceirosInput(data_inicio=data_inicio, data_fim=data_fim)
        )

# Registrar tools
register_tool(FinanceiroQueryTool())
register_tool(MargemContribuicaoTool())
register_tool(IndicadoresFinanceirosTool())
