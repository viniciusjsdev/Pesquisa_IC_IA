#!/usr/bin/env python3
"""
Script para verificar bancos de dados e tabelas
Verifica se os bancos existem e quais tabelas foram criadas
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os

# Adiciona o diretório raiz ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.config.database_config import (
    FINANCEIRO_DB_CONFIG, 
    INDUSTRIAL_DB_CONFIG, 
    DW_DB_CONFIG
)

def get_connection_params(config):
    """Extrai parâmetros de conexão de uma configuração"""
    return {
        'host': config['host'],
        'port': config['port'],
        'user': config['user'],
        'password': config['password'],
        'database': config['database']
    }

def check_database_exists(config):
    """Verifica se um banco específico existe"""
    try:
        params = get_connection_params(config)
        
        # Conecta ao PostgreSQL (banco padrão postgres)
        conn = psycopg2.connect(
            host=params['host'],
            port=params['port'],
            user=params['user'],
            password=params['password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (params['database'],))
        exists = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        
        return exists
        
    except Exception as e:
        print(f"Erro ao verificar banco {config['database']}: {e}")
        return False

def get_tables_in_database(config):
    """Lista todas as tabelas em um banco específico"""
    try:
        params = get_connection_params(config)
        
        # Conecta ao banco específico
        conn = psycopg2.connect(
            host=params['host'],
            port=params['port'],
            user=params['user'],
            password=params['password'],
            database=params['database']
        )
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return tables
        
    except Exception as e:
        print(f"Erro ao listar tabelas do banco {config['database']}: {e}")
        return []

def main():
    print("=" * 60)
    print("VERIFICACAO DE BANCOS DE DADOS E TABELAS")
    print("=" * 60)
    print()
    
    # Configurações dos bancos
    configs = {
        'Financeiro': FINANCEIRO_DB_CONFIG,
        'Industrial': INDUSTRIAL_DB_CONFIG,
        'Data Warehouse': DW_DB_CONFIG
    }
    
    total_banks = 0
    total_tables = 0
    
    for bank_name, config in configs.items():
        print(f"BANCO: {bank_name}")
        print(f"Database: {config['database']}")
        print(f"Host: {config['host']}:{config['port']}")
        print("-" * 40)
        
        # Verifica se o banco existe
        if check_database_exists(config):
            print(f"Status: EXISTE")
            
            # Lista as tabelas
            tables = get_tables_in_database(config)
            if tables:
                print(f"Tabelas encontradas ({len(tables)}):")
                for table in tables:
                    print(f"  - {table}")
                total_tables += len(tables)
            else:
                print("Nenhuma tabela encontrada")
            
            total_banks += 1
        else:
            print(f"Status: NAO EXISTE")
        
        print()
    
    # Resumo geral
    print("=" * 60)
    print("RESUMO GERAL")
    print("=" * 60)
    print(f"Bancos existentes: {total_banks}/3")
    print(f"Total de tabelas: {total_tables}")
    
    if total_banks == 3:
        print("Status: TODOS OS BANCOS EXISTEM")
    else:
        print("Status: ALGUNS BANCOS FALTANDO")
    
    if total_tables > 0:
        print("Status: TABELAS CRIADAS")
    else:
        print("Status: NENHUMA TABELA ENCONTRADA")
    
    print()
    print("Para criar os bancos e tabelas, execute:")
    print("python scripts/setup_machine.py")

if __name__ == '__main__':
    main()
