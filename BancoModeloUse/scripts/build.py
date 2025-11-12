#!/usr/bin/env python3
"""
Script de build do projeto
Cria e configura todos os bancos de dados (industrial, financeiro e DW)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.database.multi_db_manager import multi_db_manager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    """Executa a migração de todos os bancos de dados"""
    logger.info("Executando migração dos bancos de dados...")
    
    try:
        if multi_db_manager.ensure_all_databases_ready():
            logger.info("Migração concluída com sucesso!")
            return True
        else:
            logger.error("Falha na migração!")
            return False
    except Exception as e:
        logger.error(f"Erro durante a migração: {e}")
        return False


def main():
    """Função principal do build"""
    logger.info("Iniciando build do projeto...")
    logger.info("Configurando bancos: industrial, financeiro e DW")
    
    # Executa migração de todos os bancos
    if not run_migration():
        logger.error("Build falhou na migração!")
        return 1
    
    logger.info("Build concluído! Todos os bancos estão prontos.")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

