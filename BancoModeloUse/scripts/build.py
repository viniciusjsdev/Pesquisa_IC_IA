#!/usr/bin/env python3
"""
Script de build do projeto
Sempre executa migração do banco antes de iniciar a aplicação
"""
import sys
import os
import subprocess
import webbrowser
import time
import threading
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.database.manager import db_manager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    """Executa a migração do banco de dados"""
    logger.info("Executando migração do banco de dados...")
    
    try:
        if db_manager.ensure_database_ready():
            logger.info("Migração concluída com sucesso!")
            return True
        else:
            logger.error("Falha na migração!")
            return False
    except Exception as e:
        logger.error(f"Erro durante a migração: {e}")
        return False

def check_port_available(port):
    """Verifica se uma porta está disponível"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def find_available_port():
    """Encontra uma porta disponível usando configurações"""
    from infrastructure.config.app_config import SERVER_CONFIG
    start_port, end_port = SERVER_CONFIG["port_range"]
    max_attempts = end_port - start_port + 1
    
    for port in range(start_port, start_port + max_attempts):
        if check_port_available(port):
            return port
    return None

def open_swagger_in_browser(port, delay=3):
    """Abre o Swagger no navegador após um delay"""
    def open_browser():
        time.sleep(delay)  # Aguarda o servidor inicializar
        swagger_url = f"http://localhost:{port}/docs"
        logger.info(f"Abrindo Swagger no navegador: {swagger_url}")
        try:
            webbrowser.open(swagger_url)
            logger.info("Swagger aberto no navegador!")
        except Exception as e:
            logger.error(f"Erro ao abrir navegador: {e}")
            logger.info(f"Acesse manualmente: {swagger_url}")
    
    # Executa em thread separada para não bloquear
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

def start_application():
    """Inicia a aplicação FastAPI"""
    logger.info("Iniciando aplicação...")
    
    # Encontra uma porta disponível
    port = find_available_port()
    if not port:
        logger.error("Nenhuma porta disponível encontrada!")
        return
    
    logger.info(f"Usando porta: {port}")
    
    # Inicia thread para abrir Swagger automaticamente
    open_swagger_in_browser(port)
    
    try:
        # Comando para iniciar o uvicorn
        from infrastructure.config.app_config import SERVER_CONFIG
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "infrastructure.api.main:app", 
            "--host", SERVER_CONFIG["host"], 
            "--port", str(port),
            "--reload" if SERVER_CONFIG["reload"] else "--no-reload"
        ]
        
        logger.info(f"Executando: {' '.join(cmd)}")
        logger.info(f"Aplicação disponível em: http://localhost:{port}")
        logger.info(f"Swagger será aberto automaticamente em: http://localhost:{port}/docs")
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {e}")

def main():
    """Função principal do build"""
    logger.info("Iniciando build do projeto...")
    
    # 1. Executa migração
    if not run_migration():
        logger.error("Build falhou na migração!")
        return 1
    
    # 2. Inicia aplicação
    logger.info("Build concluído! Iniciando aplicação...")
    start_application()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

