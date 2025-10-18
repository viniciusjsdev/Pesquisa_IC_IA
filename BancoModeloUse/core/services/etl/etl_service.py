# core/services/etl/etl_service.py
"""
Serviço ETL principal
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from core.services.etl.extractors import FinanceiroExtractor, IndustrialExtractor
from core.services.etl.transformers import DimensoesTransformer, FatosTransformer, LookupService
from core.services.etl.loaders import DimensoesLoader, FatosLoader

class ETLService:
    """Serviço ETL principal"""
    
    def __init__(self):
        self.financeiro_extractor = FinanceiroExtractor()
        self.industrial_extractor = IndustrialExtractor()
        self.dimensoes_transformer = DimensoesTransformer()
        self.fatos_transformer = FatosTransformer(LookupService())
        self.dimensoes_loader = DimensoesLoader()
        self.fatos_loader = FatosLoader()
        self.lookup_service = LookupService()
    
    def executar_etl_completo(self, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """Executa ETL completo para o período especificado"""
        print(f"Iniciando ETL para período: {data_inicio} a {data_fim}")
        
        # 1. Extrair dados
        print("1. Extraindo dados...")
        dados_financeiros = self.financeiro_extractor.extrair_todos_dados_financeiros(data_inicio, data_fim)
        dados_industriais = self.industrial_extractor.extrair_todos_dados_industriais(data_inicio, data_fim)
        
        print(f"Dados financeiros extraídos: {len(dados_financeiros.get('vendas', []))} vendas, {len(dados_financeiros.get('custos', []))} custos")
        print(f"Dados industriais extraídos: {len(dados_industriais.get('ordens_producao', []))} ordens, {len(dados_industriais.get('registros_operacao', []))} registros")
        
        # 2. Transformar dimensões
        print("2. Transformando dimensões...")
        dimensoes_transformadas = self._transformar_dimensoes(dados_financeiros, dados_industriais, data_inicio, data_fim)
        
        # 3. Carregar dimensões
        print("3. Carregando dimensões...")
        resultados_dimensoes = self.dimensoes_loader.carregar_todas_dimensoes(dimensoes_transformadas)
        print(f"Dimensões carregadas: {resultados_dimensoes}")
        
        # 4. Limpar cache de lookup
        self.lookup_service.limpar_cache()
        
        # 5. Transformar fatos
        print("4. Transformando fatos...")
        fatos_transformados = self._transformar_fatos(dados_financeiros, dados_industriais)
        
        # 6. Carregar fatos
        print("5. Carregando fatos...")
        resultados_fatos = self.fatos_loader.carregar_todos_fatos(fatos_transformados)
        print(f"Fatos carregados: {resultados_fatos}")
        
        # 7. Resumo
        resumo = {
            'periodo': {'inicio': data_inicio, 'fim': data_fim},
            'dados_extraidos': {
                'financeiros': {k: len(v) for k, v in dados_financeiros.items()},
                'industriais': {k: len(v) for k, v in dados_industriais.items()}
            },
            'dimensoes_carregadas': resultados_dimensoes,
            'fatos_carregados': resultados_fatos,
            'timestamp': datetime.now()
        }
        
        print(f"ETL concluído: {resumo}")
        return resumo
    
    def executar_etl_incremental(self, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """Executa ETL incremental para o período especificado"""
        print(f"Iniciando ETL incremental para período: {data_inicio} a {data_fim}")
        
        # ETL incremental é similar ao completo, mas com otimizações
        return self.executar_etl_completo(data_inicio, data_fim)
    
    def executar_etl_diario(self) -> Dict[str, Any]:
        """Executa ETL diário para o dia anterior"""
        ontem = date.today() - timedelta(days=1)
        return self.executar_etl_incremental(ontem, ontem)
    
    def executar_etl_semanal(self) -> Dict[str, Any]:
        """Executa ETL semanal para a semana anterior"""
        hoje = date.today()
        inicio_semana = hoje - timedelta(days=hoje.weekday() + 7)
        fim_semana = inicio_semana + timedelta(days=6)
        return self.executar_etl_incremental(inicio_semana, fim_semana)
    
    def executar_etl_mensal(self) -> Dict[str, Any]:
        """Executa ETL mensal para o mês anterior"""
        hoje = date.today()
        primeiro_dia_mes_anterior = date(hoje.year, hoje.month - 1, 1) if hoje.month > 1 else date(hoje.year - 1, 12, 1)
        ultimo_dia_mes_anterior = date(hoje.year, hoje.month, 1) - timedelta(days=1)
        return self.executar_etl_incremental(primeiro_dia_mes_anterior, ultimo_dia_mes_anterior)
    
    def _transformar_dimensoes(self, dados_financeiros: Dict, dados_industriais: Dict, data_inicio: date, data_fim: date) -> Dict[str, List[Dict[str, Any]]]:
        """Transforma dados para dimensões"""
        dimensoes_transformadas = {}
        
        # Transformar produtos
        produtos = self.dimensoes_transformer.transformar_produtos(dados_financeiros, dados_industriais)
        dimensoes_transformadas['produtos'] = produtos
        
        # Transformar tempos
        tempos = self.dimensoes_transformer.transformar_tempo(data_inicio, data_fim)
        dimensoes_transformadas['tempos'] = tempos
        
        # Transformar máquinas
        maquinas = self.dimensoes_transformer.transformar_maquinas(dados_industriais)
        dimensoes_transformadas['maquinas'] = maquinas
        
        # Transformar clientes
        clientes = self.dimensoes_transformer.transformar_clientes(dados_financeiros)
        dimensoes_transformadas['clientes'] = clientes
        
        # Transformar fornecedores
        fornecedores = self.dimensoes_transformer.transformar_fornecedores(dados_industriais)
        dimensoes_transformadas['fornecedores'] = fornecedores
        
        return dimensoes_transformadas
    
    def _transformar_fatos(self, dados_financeiros: Dict, dados_industriais: Dict) -> Dict[str, List[Dict[str, Any]]]:
        """Transforma dados para fatos"""
        fatos_transformados = {}
        
        # Transformar vendas
        vendas = self.fatos_transformer.transformar_vendas(dados_financeiros, {})
        fatos_transformados['vendas'] = vendas
        
        # Transformar produção
        producao = self.fatos_transformer.transformar_producao(dados_industriais, {})
        fatos_transformados['producao'] = producao
        
        # Transformar custos
        custos = self.fatos_transformer.transformar_custos(dados_financeiros, {})
        fatos_transformados['custos'] = custos
        
        # Transformar qualidade
        qualidade = self.fatos_transformer.transformar_qualidade(dados_industriais, {})
        fatos_transformados['qualidade'] = qualidade
        
        # Transformar energia
        energia = self.fatos_transformer.transformar_energia(dados_industriais, {})
        fatos_transformados['energia'] = energia
        
        return fatos_transformados
    
    def obter_estatisticas_etl(self) -> Dict[str, Any]:
        """Retorna estatísticas do ETL"""
        return {
            'lookup_cache': self.lookup_service.obter_estatisticas_cache(),
            'timestamp': datetime.now()
        }
