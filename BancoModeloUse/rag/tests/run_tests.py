"""
Script para executar todos os testes do sistema multi-agente
"""

import subprocess
import sys
import os
from config.logger import get_logger

logger = get_logger(__name__)


def run_tests():
    """Executa todos os testes"""
    logger.info("Iniciando execução de testes...")
    
    # Diretório de testes
    test_dir = os.path.dirname(__file__)
    
    # Comandos de teste
    test_commands = [
        # Testes unitários
        ["python", "-m", "pytest", f"{test_dir}/test_multi_agent_system.py", "-v"],
        
        # Testes de integração
        ["python", "-m", "pytest", f"{test_dir}/test_integration.py", "-v"],
        
        # Testes de performance
        ["python", "-m", "pytest", f"{test_dir}/test_performance.py", "-v"],
        
        # Todos os testes juntos
        ["python", "-m", "pytest", f"{test_dir}", "-v", "--tb=short"]
    ]
    
    results = []
    
    for i, cmd in enumerate(test_commands):
        logger.info(f"Executando comando {i+1}/{len(test_commands)}: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            results.append({
                "command": " ".join(cmd),
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            })
            
            if result.returncode == 0:
                logger.info(f"✅ Comando {i+1} executado com sucesso")
            else:
                logger.error(f"❌ Comando {i+1} falhou com código {result.returncode}")
                logger.error(f"Stderr: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Comando {i+1} expirou após 5 minutos")
            results.append({
                "command": " ".join(cmd),
                "returncode": -1,
                "stdout": "",
                "stderr": "Timeout expired"
            })
        except Exception as e:
            logger.error(f"💥 Erro ao executar comando {i+1}: {str(e)}")
            results.append({
                "command": " ".join(cmd),
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            })
    
    # Resumo dos resultados
    logger.info("\n" + "="*50)
    logger.info("RESUMO DOS TESTES")
    logger.info("="*50)
    
    successful = 0
    failed = 0
    
    for i, result in enumerate(results):
        if result["returncode"] == 0:
            successful += 1
            status = "✅ SUCESSO"
        else:
            failed += 1
            status = "❌ FALHA"
        
        logger.info(f"{i+1}. {status} - {result['command']}")
    
    logger.info(f"\nTotal: {len(results)} comandos")
    logger.info(f"Sucessos: {successful}")
    logger.info(f"Falhas: {failed}")
    
    if failed == 0:
        logger.info("🎉 Todos os testes passaram!")
        return 0
    else:
        logger.error(f"💥 {failed} teste(s) falharam!")
        return 1


def run_specific_test(test_file):
    """Executa um teste específico"""
    logger.info(f"Executando teste específico: {test_file}")
    
    cmd = ["python", "-m", "pytest", test_file, "-v", "--tb=short"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info("✅ Teste executado com sucesso")
            print(result.stdout)
        else:
            logger.error(f"❌ Teste falhou com código {result.returncode}")
            print(result.stderr)
            
        return result.returncode
        
    except subprocess.TimeoutExpired:
        logger.error("⏰ Teste expirou após 5 minutos")
        return -1
    except Exception as e:
        logger.error(f"💥 Erro ao executar teste: {str(e)}")
        return -1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Executar teste específico
        test_file = sys.argv[1]
        exit_code = run_specific_test(test_file)
    else:
        # Executar todos os testes
        exit_code = run_tests()
    
    sys.exit(exit_code)
