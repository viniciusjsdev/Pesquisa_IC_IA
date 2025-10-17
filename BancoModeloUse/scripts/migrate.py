#!/usr/bin/env python3
"""
Script de migração do banco de dados
Executa automaticamente quando há mudanças nas tabelas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.database.manager import db_manager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Função principal de migração"""
    logger.info("Iniciando migração do banco de dados...")
    
    try:
        # Garante que o banco e tabelas estão prontos
        if db_manager.ensure_database_ready():
            logger.info("Migração concluída com sucesso!")
            return 0
        else:
            logger.error("Falha na migração!")
            return 1
            
    except Exception as e:
        logger.error(f"Erro durante a migração: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

