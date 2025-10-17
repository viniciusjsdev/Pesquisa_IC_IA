#!/usr/bin/env python3
"""
Script de configuração para novas máquinas
Executa automaticamente o setup completo do projeto
"""
import sys
import os
import subprocess
import logging

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 ou superior é necessário!")
        return False
    logger.info(f"Python {sys.version_info.major}.{sys.version_info.minor} detectado")
    return True

def install_dependencies():
    """Instala as dependências do projeto"""
    logger.info("Instalando dependências...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        logger.info("Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao instalar dependências: {e}")
        return False

def setup_database():
    """Configura o banco de dados"""
    logger.info("Configurando banco de dados...")
    try:
        from infrastructure.database.manager import db_manager
        if db_manager.ensure_database_ready():
            logger.info("Banco de dados configurado com sucesso!")
            return True
        else:
            logger.error("Falha na configuração do banco!")
            return False
    except Exception as e:
        logger.error(f"Erro na configuração do banco: {e}")
        return False

def start_application():
    """Inicia a aplicação"""
    logger.info("Iniciando aplicação...")
    try:
        from scripts.build import main
        return main()
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {e}")
        return 1

def main():
    """Função principal de setup"""
    logger.info("=== SETUP PARA NOVA MÁQUINA ===")
    logger.info("Configurando projeto automaticamente...")
    
    # 1. Verificar Python
    if not check_python_version():
        return 1
    
    # 2. Instalar dependências
    if not install_dependencies():
        return 1
    
    # 3. Configurar banco
    if not setup_database():
        return 1
    
    # 4. Iniciar aplicação
    logger.info("Setup concluído! Iniciando aplicação...")
    return start_application()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
