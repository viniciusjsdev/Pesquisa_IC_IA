# core/services/etl/extractors/financeiro_extractor.py
"""
Extrator de dados do banco financeiro
"""
from datetime import datetime, date
from typing import List, Dict, Any
from infrastructure.database.sessions import get_financeiro_db
from core.repositories.financeiro import CustosRepository, VendasRepository, ContabilRepository

class FinanceiroExtractor:
    """Extrator de dados financeiros"""
    
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
    
    def extrair_vendas(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Extrai dados de vendas do banco financeiro"""
        with get_financeiro_db() as db:
            self._get_repositories(db)
            vendas = self.vendas_repo.get_vendas_by_periodo(data_inicio, data_fim)
            
            vendas_data = []
            for venda in vendas:
                vendas_data.append({
                    'venda_id': venda.venda_id,
                    'produto_id': venda.produto_id,
                    'cliente_id': venda.cliente_id,
                    'quantidade_vendida': venda.quantidade_vendida,
                    'preco_unitario_venda': float(venda.preco_unitario_venda) if venda.preco_unitario_venda else 0,
                    'data_venda': venda.data_venda,
                    'valor_total': venda.quantidade_vendida * (venda.preco_unitario_venda or 0)
                })
            
            return vendas_data
    
    def extrair_custos(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Extrai dados de custos do banco financeiro"""
        with get_financeiro_db() as db:
            self._get_repositories(db)
            
            # Extrair custos de produção
            custos_producao = self.custos_repo.get_custos_producao_by_periodo(data_inicio, data_fim)
            
            custos_data = []
            for custo in custos_producao:
                custos_data.append({
                    'custo_id': custo.id,
                    'materia_prima': float(custo.materia_prima),
                    'mao_obra_direta': float(custo.mao_obra_direta),
                    'custos_indiretos': float(custo.custos_indiretos),
                    'custo_total': float(custo.custo_total) if custo.custo_total else 0,
                    'custo_unitario': float(custo.custo_unitario) if custo.custo_unitario else 0,
                    'data_registro': custo.data_registro
                })
            
            return custos_data
    
    def extrair_lancamentos_financeiros(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Extrai lançamentos financeiros do banco financeiro"""
        with get_financeiro_db() as db:
            self._get_repositories(db)
            lancamentos = self.contabil_repo.get_lancamentos_by_periodo(data_inicio, data_fim)
            
            lancamentos_data = []
            for lancamento in lancamentos:
                lancamentos_data.append({
                    'lancamento_id': lancamento.lancamento_id,
                    'conta_id': lancamento.conta_id,
                    'data_lancamento': lancamento.data_lancamento,
                    'valor': float(lancamento.valor) if lancamento.valor else 0,
                    'descricao': lancamento.descricao
                })
            
            return lancamentos_data
    
    def extrair_contas_contabeis(self) -> List[Dict[str, Any]]:
        """Extrai contas contábeis do banco financeiro"""
        with get_financeiro_db() as db:
            self._get_repositories(db)
            contas = self.contabil_repo.get_all_contas_contabeis()
            
            contas_data = []
            for conta in contas:
                contas_data.append({
                    'conta_id': conta.conta_id,
                    'numero_conta': conta.numero_conta,
                    'nome_conta': conta.nome_conta,
                    'tipo_conta': conta.tipo_conta
                })
            
            return contas_data
    
    def extrair_orcamentos(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Extrai orçamentos do banco financeiro"""
        with get_financeiro_db() as db:
            self._get_repositories(db)
            orcamentos = self.vendas_repo.get_orcamentos_by_periodo(data_inicio, data_fim)
            
            orcamentos_data = []
            for orcamento in orcamentos:
                orcamentos_data.append({
                    'orcamento_id': orcamento.orcamento_id,
                    'conta_id': orcamento.conta_id,
                    'valor_orcado': float(orcamento.valor_orcado) if orcamento.valor_orcado else 0,
                    'periodo': orcamento.periodo
                })
            
            return orcamentos_data
    
    def extrair_analises_financeiras(self, data_inicio: date, data_fim: date) -> List[Dict[str, Any]]:
        """Extrai análises financeiras do banco financeiro"""
        with get_financeiro_db() as db:
            self._get_repositories(db)
            analises = self.custos_repo.get_analises_financeiras_by_periodo(data_inicio, data_fim)
            
            analises_data = []
            for analise in analises:
                analises_data.append({
                    'analise_id': analise.id,
                    'vendas_totais': float(analise.vendas_totais),
                    'lucro_bruto': float(analise.lucro_bruto),
                    'margem_lucro_bruto': float(analise.margem_lucro_bruto),
                    'roi': float(analise.roi),
                    'ponto_equilibrio': float(analise.ponto_equilibrio),
                    'data_registro': analise.data_registro
                })
            
            return analises_data
    
    def extrair_todos_dados_financeiros(self, data_inicio: date, data_fim: date) -> Dict[str, List[Dict[str, Any]]]:
        """Extrai todos os dados financeiros do período"""
        return {
            'vendas': self.extrair_vendas(data_inicio, data_fim),
            'custos': self.extrair_custos(data_inicio, data_fim),
            'lancamentos': self.extrair_lancamentos_financeiros(data_inicio, data_fim),
            'contas': self.extrair_contas_contabeis(),
            'orcamentos': self.extrair_orcamentos(data_inicio, data_fim),
            'analises': self.extrair_analises_financeiras(data_inicio, data_fim)
        }
