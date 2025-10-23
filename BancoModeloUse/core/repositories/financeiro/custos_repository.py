# core/repositories/financeiro/custos_repository.py
"""
Repositório para operações de custos financeiros
"""
from sqlalchemy.orm import Session
from core.models.financeiro.custos import (
    CustoPadrao, CustoIndiretoRateio, MaterialCustoHistorico,
    CustoMaoObraHistorico, CustoOperacionalVariavel, CustoProducao,
    ResultadoFinanceiro, AnaliseFinanceira
)
from core.repositories.base import BaseRepository

class CustosRepository(BaseRepository):
    """Repositório para operações de custos"""
    
    def get_all_custos_padrao(self):
        """Retorna todos os custos padrão"""
        return self.db.query(CustoPadrao).all()
    
    def get_custo_padrao_by_tipo(self, tipo_custo: str):
        """Busca custos padrão por tipo"""
        return self.db.query(CustoPadrao).filter(CustoPadrao.tipo_custo == tipo_custo).all()
    
    def get_custos_indiretos_rateio(self):
        """Retorna todos os custos indiretos de rateio"""
        return self.db.query(CustoIndiretoRateio).all()
    
    def get_custos_indiretos_by_periodo(self, data_inicio, data_fim):
        """Busca custos indiretos por período"""
        return self.db.query(CustoIndiretoRateio).filter(
            CustoIndiretoRateio.data_referencia.between(data_inicio, data_fim)
        ).all()
    
    def get_materiais_custo_historico(self):
        """Retorna histórico de custos de materiais"""
        return self.db.query(MaterialCustoHistorico).all()
    
    def get_materiais_custo_by_material(self, material_id: int):
        """Busca custos históricos por material"""
        return self.db.query(MaterialCustoHistorico).filter(
            MaterialCustoHistorico.material_id == material_id
        ).all()
    
    def get_custos_mao_obra(self):
        """Retorna custos de mão de obra"""
        return self.db.query(CustoMaoObraHistorico).all()
    
    def get_custos_operacionais_variaveis(self):
        """Retorna custos operacionais variáveis"""
        return self.db.query(CustoOperacionalVariavel).all()
    
    def get_custos_producao(self):
        """Retorna custos de produção"""
        return self.db.query(CustoProducao).all()
    
    def get_custos_producao_by_periodo(self, data_inicio, data_fim):
        """Busca custos de produção por período"""
        return self.db.query(CustoProducao).filter(
            CustoProducao.data_registro.between(data_inicio, data_fim)
        ).all()
    
    def get_resultados_financeiros(self):
        """Retorna resultados financeiros"""
        return self.db.query(ResultadoFinanceiro).all()
    
    def get_analises_financeiras(self):
        """Retorna análises financeiras"""
        return self.db.query(AnaliseFinanceira).all()
    
    def get_analises_financeiras_by_periodo(self, data_inicio, data_fim):
        """Busca análises financeiras por período"""
        return self.db.query(AnaliseFinanceira).filter(
            AnaliseFinanceira.data_registro.between(data_inicio, data_fim)
        ).all()
    
    def create_custo_padrao(self, custo_data: dict):
        """Cria novo custo padrão"""
        custo = CustoPadrao(**custo_data)
        self.db.add(custo)
        self.db.commit()
        self.db.refresh(custo)
        return custo
    
    def create_custo_producao(self, custo_data: dict):
        """Cria novo custo de produção"""
        custo = CustoProducao(**custo_data)
        self.db.add(custo)
        self.db.commit()
        self.db.refresh(custo)
        return custo
    
    def create_resultado_financeiro(self, resultado_data: dict):
        """Cria novo resultado financeiro"""
        resultado = ResultadoFinanceiro(**resultado_data)
        self.db.add(resultado)
        self.db.commit()
        self.db.refresh(resultado)
        return resultado
