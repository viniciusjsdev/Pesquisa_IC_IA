#!/usr/bin/env python3
"""
Script para executar ETL manualmente
"""
import sys
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from core.services.etl.etl_service import ETLService
from core.services.etl.etl_scheduler import ETLScheduler

def executar_etl_manual():
    """Executa ETL manualmente"""
    print("=== Executando ETL Manual ===")
    
    # Inicializar serviços
    etl_service = ETLService()
    etl_scheduler = ETLScheduler()
    
    # Obter período (último mês por padrão)
    hoje = date.today()
    primeiro_dia_mes_anterior = date(hoje.year, hoje.month - 1, 1) if hoje.month > 1 else date(hoje.year - 1, 12, 1)
    ultimo_dia_mes_anterior = date(hoje.year, hoje.month, 1) - timedelta(days=1)
    
    print(f"Período: {primeiro_dia_mes_anterior} a {ultimo_dia_mes_anterior}")
    
    try:
        # Executar ETL
        resultado = etl_service.executar_etl_completo(primeiro_dia_mes_anterior, ultimo_dia_mes_anterior)
        
        print("✅ ETL executado com sucesso!")
        print(f"📊 Dados extraídos:")
        for dominio, dados in resultado.get('dados_extraidos', {}).items():
            print(f"  - {dominio}: {dados}")
        
        print(f"📈 Dimensões carregadas: {resultado.get('dimensoes_carregadas', {})}")
        print(f"📈 Fatos carregados: {resultado.get('fatos_carregados', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar ETL: {e}")
        return False

def executar_etl_diario():
    """Executa ETL diário"""
    print("=== Executando ETL Diário ===")
    
    etl_service = ETLService()
    
    try:
        resultado = etl_service.executar_etl_diario()
        print("✅ ETL diário executado com sucesso!")
        print(f"📊 Resultado: {resultado}")
        return True
    except Exception as e:
        print(f"❌ Erro ao executar ETL diário: {e}")
        return False

def executar_etl_semanal():
    """Executa ETL semanal"""
    print("=== Executando ETL Semanal ===")
    
    etl_service = ETLService()
    
    try:
        resultado = etl_service.executar_etl_semanal()
        print("✅ ETL semanal executado com sucesso!")
        print(f"📊 Resultado: {resultado}")
        return True
    except Exception as e:
        print(f"❌ Erro ao executar ETL semanal: {e}")
        return False

def executar_etl_mensal():
    """Executa ETL mensal"""
    print("=== Executando ETL Mensal ===")
    
    etl_service = ETLService()
    
    try:
        resultado = etl_service.executar_etl_mensal()
        print("✅ ETL mensal executado com sucesso!")
        print(f"📊 Resultado: {resultado}")
        return True
    except Exception as e:
        print(f"❌ Erro ao executar ETL mensal: {e}")
        return False

def configurar_agendamentos():
    """Configura agendamentos ETL"""
    print("=== Configurando Agendamentos ETL ===")
    
    etl_scheduler = ETLScheduler()
    
    try:
        # Configurar agendamentos padrão
        etl_scheduler.configurar_etl_padrao()
        print("✅ Agendamentos configurados com sucesso!")
        
        # Iniciar scheduler
        etl_scheduler.iniciar_scheduler()
        print("✅ Scheduler iniciado!")
        
        # Mostrar status
        status = etl_scheduler.obter_status_scheduler()
        print(f"📊 Status do scheduler: {status['running']}")
        print(f"📊 Jobs agendados: {len(status['jobs'])}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao configurar agendamentos: {e}")
        return False

def mostrar_status():
    """Mostra status do ETL"""
    print("=== Status do ETL ===")
    
    etl_scheduler = ETLScheduler()
    
    try:
        status = etl_scheduler.obter_status_scheduler()
        print(f"🔄 Scheduler rodando: {status['running']}")
        print(f"📊 Jobs agendados: {len(status['jobs'])}")
        
        for job in status['jobs']:
            print(f"  - {job['name']}: {job['next_run_time']}")
        
        print(f"📈 Histórico: {len(status['job_history'])} execuções")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao obter status: {e}")
        return False

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python run_etl.py <comando>")
        print("Comandos disponíveis:")
        print("  manual     - Executa ETL manual para o último mês")
        print("  diario     - Executa ETL diário")
        print("  semanal    - Executa ETL semanal")
        print("  mensal     - Executa ETL mensal")
        print("  configurar - Configura agendamentos ETL")
        print("  status     - Mostra status do ETL")
        return
    
    comando = sys.argv[1].lower()
    
    if comando == "manual":
        executar_etl_manual()
    elif comando == "diario":
        executar_etl_diario()
    elif comando == "semanal":
        executar_etl_semanal()
    elif comando == "mensal":
        executar_etl_mensal()
    elif comando == "configurar":
        configurar_agendamentos()
    elif comando == "status":
        mostrar_status()
    else:
        print(f"❌ Comando inválido: {comando}")

if __name__ == "__main__":
    main()
