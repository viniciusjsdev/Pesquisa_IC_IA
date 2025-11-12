#!/usr/bin/env python3
"""
Script temporário para limpar todos os bancos de dados
ATENÇÃO: Este script apaga TODOS os dados dos bancos!
"""
import os
import sys
import logging

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa conexões
from infrastructure.database.connections.industrial_connection import industrial_connection
from infrastructure.database.connections.financeiro_connection import financeiro_connection
from infrastructure.database.connections.dw_connection import dw_connection

# Importa modelos industriais
from core.models.industrial.cadastros import (
    Produto, Material, Maquina, Fornecedor
)
from core.models.industrial.producao import (
    OrdemProducao, RoteiroProducao, OperacaoRoteiro, RegistroOperacao,
    ParadaMaquina, ConsumoMaterial, LoteMaterial, LoteProducao
)
from core.models.industrial.equipamentos import (
    Equipamento, ProcessoIndustrial
)
from core.models.industrial.qualidade import (
    ControleQualidade, Defeito, RegistroDefeito
)

# Importa modelos financeiros
from core.models.financeiro.custos import (
    CustoPadrao, CustoIndiretoRateio, MaterialCustoHistorico,
    CustoMaoObraHistorico, CustoOperacionalVariavel, CustoProducao,
    ResultadoFinanceiro, AnaliseFinanceira
)
from core.models.financeiro.contabil import (
    ContaContabil, LancamentoFinanceiro, CategoriaContabilPadrao,
    SubcategoriaContabilPadrao, ContaContabilDetalhe
)
from core.models.financeiro.vendas import (
    Venda, Orcamento
)
from core.models.financeiro.kpis import (
    KPIGerencial
)

# Importa modelos DW
from core.models.dw.dimensoes import (
    DimProduto, DimTempo, DimMaquina, DimCliente, DimFornecedor
)
from core.models.dw.fatos import (
    FatoVendas, FatoProducao, FatoCustos, FatoQualidade, FatoEnergia
)
from core.models.dw.agregados import (
    KPIFinanceiro, KPIIndustrial, KPIIntegrado, DashboardExecutivo
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clear_table(session, model_class):
    """Limpa todos os registros de uma tabela"""
    try:
        count = session.query(model_class).count()
        session.query(model_class).delete()
        session.commit()
        logger.info(f"  ✓ {model_class.__tablename__}: {count} registros removidos")
        return count
    except Exception as e:
        session.rollback()
        logger.error(f"  ✗ Erro ao limpar {model_class.__tablename__}: {e}")
        return 0

def clear_industrial_database():
    """Limpa todas as tabelas do banco industrial"""
    logger.info("=" * 80)
    logger.info("LIMPANDO BANCO INDUSTRIAL")
    logger.info("=" * 80)
    
    session = industrial_connection.get_session()
    total_removed = 0
    
    try:
        # Limpa na ordem inversa das dependências
        logger.info("\nLimpando tabelas dependentes...")
        total_removed += clear_table(session, ControleQualidade)
        total_removed += clear_table(session, RegistroDefeito)
        total_removed += clear_table(session, Defeito)
        total_removed += clear_table(session, ConsumoMaterial)
        total_removed += clear_table(session, ParadaMaquina)
        total_removed += clear_table(session, RegistroOperacao)
        total_removed += clear_table(session, OperacaoRoteiro)
        total_removed += clear_table(session, LoteProducao)
        total_removed += clear_table(session, LoteMaterial)
        total_removed += clear_table(session, RoteiroProducao)
        total_removed += clear_table(session, OrdemProducao)
        
        logger.info("\nLimpando tabelas base...")
        total_removed += clear_table(session, ProcessoIndustrial)
        total_removed += clear_table(session, Equipamento)
        total_removed += clear_table(session, Fornecedor)
        total_removed += clear_table(session, Maquina)
        total_removed += clear_table(session, Material)
        total_removed += clear_table(session, Produto)
        
        logger.info(f"\n✓ Banco Industrial limpo! Total: {total_removed} registros removidos")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao limpar banco industrial: {e}")
        raise
    finally:
        session.close()
    
    return total_removed

def clear_financeiro_database():
    """Limpa todas as tabelas do banco financeiro"""
    logger.info("\n" + "=" * 80)
    logger.info("LIMPANDO BANCO FINANCEIRO")
    logger.info("=" * 80)
    
    session = financeiro_connection.get_session()
    total_removed = 0
    
    try:
        # Limpa na ordem inversa das dependências
        logger.info("\nLimpando tabelas dependentes...")
        total_removed += clear_table(session, KPIGerencial)
        total_removed += clear_table(session, Orcamento)
        total_removed += clear_table(session, Venda)
        total_removed += clear_table(session, ContaContabilDetalhe)
        total_removed += clear_table(session, SubcategoriaContabilPadrao)
        total_removed += clear_table(session, CategoriaContabilPadrao)
        total_removed += clear_table(session, LancamentoFinanceiro)
        total_removed += clear_table(session, AnaliseFinanceira)
        total_removed += clear_table(session, ResultadoFinanceiro)
        total_removed += clear_table(session, CustoProducao)
        total_removed += clear_table(session, CustoOperacionalVariavel)
        total_removed += clear_table(session, CustoMaoObraHistorico)
        total_removed += clear_table(session, MaterialCustoHistorico)
        total_removed += clear_table(session, CustoIndiretoRateio)
        
        logger.info("\nLimpando tabelas base...")
        total_removed += clear_table(session, ContaContabil)
        total_removed += clear_table(session, CustoPadrao)
        
        logger.info(f"\n✓ Banco Financeiro limpo! Total: {total_removed} registros removidos")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao limpar banco financeiro: {e}")
        raise
    finally:
        session.close()
    
    return total_removed

def clear_dw_database():
    """Limpa todas as tabelas do banco DW"""
    logger.info("\n" + "=" * 80)
    logger.info("LIMPANDO BANCO DATA WAREHOUSE (DW)")
    logger.info("=" * 80)
    
    session = dw_connection.get_session()
    total_removed = 0
    
    try:
        logger.info("\nLimpando tabelas agregadas...")
        total_removed += clear_table(session, DashboardExecutivo)
        total_removed += clear_table(session, KPIIntegrado)
        total_removed += clear_table(session, KPIIndustrial)
        total_removed += clear_table(session, KPIFinanceiro)
        
        logger.info("\nLimpando tabelas de fatos...")
        total_removed += clear_table(session, FatoEnergia)
        total_removed += clear_table(session, FatoQualidade)
        total_removed += clear_table(session, FatoCustos)
        total_removed += clear_table(session, FatoProducao)
        total_removed += clear_table(session, FatoVendas)
        
        logger.info("\nLimpando tabelas de dimensões...")
        total_removed += clear_table(session, DimFornecedor)
        total_removed += clear_table(session, DimCliente)
        total_removed += clear_table(session, DimMaquina)
        total_removed += clear_table(session, DimTempo)
        total_removed += clear_table(session, DimProduto)
        
        logger.info(f"\n✓ Banco DW limpo! Total: {total_removed} registros removidos")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao limpar banco DW: {e}")
        raise
    finally:
        session.close()
    
    return total_removed

def main():
    """Função principal"""
    print("=" * 80)
    print("⚠️  ATENÇÃO: Este script vai apagar TODOS os dados dos bancos!")
    print("=" * 80)
    
    response = input("\nTem certeza que deseja continuar? (digite 'SIM' para confirmar): ")
    
    if response != "SIM":
        print("\nOperação cancelada.")
        return 0
    
    print("\nIniciando limpeza dos bancos de dados...\n")
    
    try:
        total_removed = 0
        
        # Limpa cada banco
        total_removed += clear_industrial_database()
        total_removed += clear_financeiro_database()
        total_removed += clear_dw_database()
        
        print("\n" + "=" * 80)
        print("LIMPEZA CONCLUÍDA!")
        print("=" * 80)
        print(f"Total de registros removidos: {total_removed}")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ Erro durante limpeza: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

