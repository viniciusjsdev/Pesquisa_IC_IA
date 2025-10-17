#!/usr/bin/env python3
"""
Script para abrir o Swagger no navegador
Verifica se o servidor está rodando e abre automaticamente
"""
import webbrowser
import requests
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_server_running(port=8000):
    """Verifica se o servidor está rodando na porta especificada"""
    try:
        response = requests.get(f"http://localhost:{port}/", timeout=2)
        return response.status_code == 200
    except:
        return False

def find_server_port():
    """Encontra em qual porta o servidor está rodando"""
    for port in range(8000, 8010):
        if check_server_running(port):
            return port
    return None

def open_swagger():
    """Abre o Swagger no navegador"""
    logger.info("Procurando servidor em execução...")
    
    # Encontra a porta do servidor
    port = find_server_port()
    
    if not port:
        logger.error("Servidor não encontrado!")
        logger.info("Execute primeiro: python build.py")
        return False
    
    logger.info(f"Servidor encontrado na porta {port}")
    
    # URL do Swagger
    swagger_url = f"http://localhost:{port}/docs"
    
    try:
        logger.info(f"Abrindo Swagger: {swagger_url}")
        webbrowser.open(swagger_url)
        logger.info("Swagger aberto no navegador!")
        
        # Mostra outras URLs úteis
        logger.info("\nURLs disponíveis:")
        logger.info(f"  • Swagger UI: http://localhost:{port}/docs")
        logger.info(f"  • ReDoc: http://localhost:{port}/redoc")
        logger.info(f"  • API Root: http://localhost:{port}/")
        logger.info(f"  • Database Status: http://localhost:{port}/database-status")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao abrir navegador: {e}")
        logger.info(f"Acesse manualmente: {swagger_url}")
        return False

def main():
    """Função principal"""
    logger.info("Abrindo Swagger...")
    
    if open_swagger():
        logger.info("Sucesso!")
    else:
        logger.error("Falha ao abrir Swagger!")

if __name__ == "__main__":
    main()
