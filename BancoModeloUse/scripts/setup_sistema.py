#!/usr/bin/env python3
"""
Script para configurar o sistema completo
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from infrastructure.database.manager import db_manager
from core.services.etl.etl_scheduler import ETLScheduler
from core.rag.pipeline import RAGPipeline

def configurar_bancos():
    """Configura os bancos de dados"""
    print("=== Configurando Bancos de Dados ===")
    
    try:
        # Verificar se bancos existem
        print("🔍 Verificando bancos de dados...")
        
        # Banco financeiro
        if db_manager.check_database_exists("db_financeiro"):
            print("✅ Banco financeiro existe")
        else:
            print("❌ Banco financeiro não encontrado")
            return False
        
        # Banco industrial
        if db_manager.check_database_exists("db_industrial"):
            print("✅ Banco industrial existe")
        else:
            print("❌ Banco industrial não encontrado")
            return False
        
        # Banco DW
        if db_manager.check_database_exists("db_datamind_dw"):
            print("✅ Banco DW existe")
        else:
            print("❌ Banco DW não encontrado")
            return False
        
        # Criar tabelas
        print("🔧 Criando tabelas...")
        if db_manager.create_tables():
            print("✅ Tabelas criadas com sucesso")
        else:
            print("❌ Erro ao criar tabelas")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar bancos: {e}")
        return False

def configurar_etl():
    """Configura o sistema ETL"""
    print("=== Configurando Sistema ETL ===")
    
    try:
        etl_scheduler = ETLScheduler()
        
        # Configurar agendamentos padrão
        print("📅 Configurando agendamentos ETL...")
        etl_scheduler.configurar_etl_padrao()
        print("✅ Agendamentos configurados")
        
        # Iniciar scheduler
        print("🚀 Iniciando scheduler ETL...")
        etl_scheduler.iniciar_scheduler()
        print("✅ Scheduler iniciado")
        
        # Mostrar status
        status = etl_scheduler.obter_status_scheduler()
        print(f"📊 Status: {status['running']}")
        print(f"📊 Jobs: {len(status['jobs'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar ETL: {e}")
        return False

def configurar_rag():
    """Configura o sistema RAG"""
    print("=== Configurando Sistema RAG ===")
    
    try:
        pipeline = RAGPipeline()
        
        # Testar pipeline
        print("🧪 Testando pipeline RAG...")
        resultado_teste = pipeline.testar_pipeline()
        
        if resultado_teste.get('sucesso'):
            print("✅ Pipeline RAG funcionando")
            print(f"📊 Testes executados: {resultado_teste.get('total_testes', 0)}")
            print(f"📊 Taxa de sucesso: {resultado_teste.get('taxa_sucesso', 0)}%")
        else:
            print("❌ Pipeline RAG com problemas")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar RAG: {e}")
        return False

def verificar_sistema():
    """Verifica se o sistema está funcionando"""
    print("=== Verificando Sistema ===")
    
    try:
        # Verificar bancos
        print("🔍 Verificando bancos de dados...")
        bancos_ok = all([
            db_manager.check_database_exists("db_financeiro"),
            db_manager.check_database_exists("db_industrial"),
            db_manager.check_database_exists("db_datamind_dw")
        ])
        
        if bancos_ok:
            print("✅ Todos os bancos estão funcionando")
        else:
            print("❌ Alguns bancos não estão funcionando")
            return False
        
        # Verificar ETL
        print("🔍 Verificando sistema ETL...")
        etl_scheduler = ETLScheduler()
        status_etl = etl_scheduler.obter_status_scheduler()
        
        if status_etl.get('running'):
            print("✅ Sistema ETL funcionando")
        else:
            print("❌ Sistema ETL não está funcionando")
            return False
        
        # Verificar RAG
        print("🔍 Verificando sistema RAG...")
        pipeline = RAGPipeline()
        resultado_teste = pipeline.testar_pipeline()
        
        if resultado_teste.get('sucesso'):
            print("✅ Sistema RAG funcionando")
        else:
            print("❌ Sistema RAG com problemas")
            return False
        
        print("🎉 Sistema completamente funcional!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar sistema: {e}")
        return False

def executar_etl_inicial():
    """Executa ETL inicial para popular a DW"""
    print("=== Executando ETL Inicial ===")
    
    try:
        from core.services.etl.etl_service import ETLService
        from datetime import date, timedelta
        
        etl_service = ETLService()
        
        # Executar ETL para último mês
        hoje = date.today()
        primeiro_dia_mes_anterior = date(hoje.year, hoje.month - 1, 1) if hoje.month > 1 else date(hoje.year - 1, 12, 1)
        ultimo_dia_mes_anterior = date(hoje.year, hoje.month, 1) - timedelta(days=1)
        
        print(f"📅 Período: {primeiro_dia_mes_anterior} a {ultimo_dia_mes_anterior}")
        
        resultado = etl_service.executar_etl_completo(primeiro_dia_mes_anterior, ultimo_dia_mes_anterior)
        
        print("✅ ETL inicial executado com sucesso!")
        print(f"📊 Dados extraídos: {resultado.get('dados_extraidos', {})}")
        print(f"📊 Dimensões carregadas: {resultado.get('dimensoes_carregadas', {})}")
        print(f"📊 Fatos carregados: {resultado.get('fatos_carregados', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar ETL inicial: {e}")
        return False

def mostrar_status_completo():
    """Mostra status completo do sistema"""
    print("=== Status Completo do Sistema ===")
    
    try:
        # Status dos bancos
        print("\n📊 Status dos Bancos:")
        bancos = ["db_financeiro", "db_industrial", "db_datamind_dw"]
        for banco in bancos:
            if db_manager.check_database_exists(banco):
                print(f"  ✅ {banco}: OK")
            else:
                print(f"  ❌ {banco}: ERRO")
        
        # Status do ETL
        print("\n📊 Status do ETL:")
        etl_scheduler = ETLScheduler()
        status_etl = etl_scheduler.obter_status_scheduler()
        print(f"  🔄 Scheduler: {'Rodando' if status_etl.get('running') else 'Parado'}")
        print(f"  📅 Jobs: {len(status_etl.get('jobs', []))}")
        
        # Status do RAG
        print("\n📊 Status do RAG:")
        pipeline = RAGPipeline()
        estatisticas = pipeline.obter_estatisticas_pipeline()
        print(f"  🧠 Pipeline: Funcionando")
        print(f"  📊 Consultas: {estatisticas.get('total_consultas', 0)}")
        print(f"  📊 Taxa de sucesso: {estatisticas.get('taxa_sucesso', 0)}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao obter status: {e}")
        return False

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python setup_sistema.py <comando>")
        print("Comandos disponíveis:")
        print("  configurar    - Configura o sistema completo")
        print("  bancos        - Configura apenas os bancos")
        print("  etl           - Configura apenas o ETL")
        print("  rag           - Configura apenas o RAG")
        print("  verificar     - Verifica se o sistema está funcionando")
        print("  etl-inicial   - Executa ETL inicial")
        print("  status        - Mostra status completo")
        return
    
    comando = sys.argv[1].lower()
    
    if comando == "configurar":
        print("🚀 Configurando sistema completo...")
        sucesso = True
        sucesso &= configurar_bancos()
        sucesso &= configurar_etl()
        sucesso &= configurar_rag()
        
        if sucesso:
            print("🎉 Sistema configurado com sucesso!")
        else:
            print("❌ Erro na configuração do sistema")
    
    elif comando == "bancos":
        configurar_bancos()
    
    elif comando == "etl":
        configurar_etl()
    
    elif comando == "rag":
        configurar_rag()
    
    elif comando == "verificar":
        verificar_sistema()
    
    elif comando == "etl-inicial":
        executar_etl_inicial()
    
    elif comando == "status":
        mostrar_status_completo()
    
    else:
        print(f"❌ Comando inválido: {comando}")

if __name__ == "__main__":
    main()
