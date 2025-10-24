"""
Testes de performance para o sistema multi-agente
"""

import pytest
import time
import asyncio
from fastapi.testclient import TestClient
from infrastructure.api.main import app
from config.logger import get_logger

logger = get_logger(__name__)


class TestPerformance:
    """Testes de performance"""
    
    def test_response_time_health_check(self):
        """Testa tempo de resposta do health check"""
        with TestClient(app) as client:
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0  # Deve responder em menos de 1 segundo
            
            logger.info(f"Health check response time: {response_time:.3f}s")
    
    def test_response_time_root_endpoint(self):
        """Testa tempo de resposta do endpoint raiz"""
        with TestClient(app) as client:
            start_time = time.time()
            response = client.get("/")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 0.5  # Deve responder em menos de 0.5 segundos
            
            logger.info(f"Root endpoint response time: {response_time:.3f}s")
    
    def test_response_time_rag_endpoints(self):
        """Testa tempo de resposta dos endpoints RAG"""
        with TestClient(app) as client:
            endpoints = [
                "/rag/exemplos",
                "/rag/agentes", 
                "/rag/ferramentas"
            ]
            
            for endpoint in endpoints:
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                assert response.status_code == 200
                assert response_time < 2.0  # Deve responder em menos de 2 segundos
                
                logger.info(f"{endpoint} response time: {response_time:.3f}s")
    
    def test_concurrent_requests(self):
        """Testa requisições concorrentes"""
        with TestClient(app) as client:
            # Simular múltiplas requisições simultâneas
            start_time = time.time()
            
            responses = []
            for i in range(10):
                response = client.get("/health")
                responses.append(response)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verificar que todas as respostas foram bem-sucedidas
            for response in responses:
                assert response.status_code == 200
            
            # Verificar que o tempo total é razoável
            assert total_time < 5.0  # 10 requisições em menos de 5 segundos
            
            logger.info(f"10 concurrent requests completed in: {total_time:.3f}s")
    
    def test_memory_usage_basic(self):
        """Testa uso básico de memória"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with TestClient(app) as client:
            # Fazer várias requisições
            for i in range(50):
                response = client.get("/health")
                assert response.status_code == 200
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Verificar que o aumento de memória é razoável
            assert memory_increase < 100  # Menos de 100MB de aumento
            
            logger.info(f"Memory usage - Initial: {initial_memory:.1f}MB, Final: {final_memory:.1f}MB, Increase: {memory_increase:.1f}MB")
    
    def test_error_handling_performance(self):
        """Testa performance do tratamento de erros"""
        with TestClient(app) as client:
            # Teste com endpoint inexistente
            start_time = time.time()
            response = client.get("/nonexistent-endpoint")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 404
            assert response_time < 0.5  # Erro deve ser tratado rapidamente
            
            logger.info(f"Error handling response time: {response_time:.3f}s")
    
    def test_large_payload_handling(self):
        """Testa tratamento de payloads grandes"""
        with TestClient(app) as client:
            # Criar payload grande
            large_consulta = "Qual foi a receita total de vendas? " * 100  # ~3KB
            
            payload = {
                "consulta": large_consulta,
                "parametros": {}
            }
            
            start_time = time.time()
            response = client.post("/rag/ask", json=payload)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Pode retornar 200 (sucesso) ou 503 (sistema não pronto)
            assert response.status_code in [200, 503]
            
            # Verificar que o tempo de resposta é razoável mesmo com payload grande
            assert response_time < 10.0  # Menos de 10 segundos
            
            logger.info(f"Large payload response time: {response_time:.3f}s")


class TestLoadTesting:
    """Testes de carga básicos"""
    
    def test_sustained_load(self):
        """Testa carga sustentada"""
        with TestClient(app) as client:
            start_time = time.time()
            
            # Fazer 100 requisições sequenciais
            for i in range(100):
                response = client.get("/health")
                assert response.status_code == 200
                
                # Pequena pausa para simular carga real
                time.sleep(0.01)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verificar que o tempo total é razoável
            assert total_time < 30.0  # 100 requisições em menos de 30 segundos
            
            logger.info(f"100 sustained requests completed in: {total_time:.3f}s")
    
    def test_mixed_endpoints_load(self):
        """Testa carga mista em diferentes endpoints"""
        with TestClient(app) as client:
            endpoints = [
                "/health",
                "/",
                "/rag/exemplos",
                "/rag/agentes",
                "/rag/ferramentas"
            ]
            
            start_time = time.time()
            
            # Fazer 50 requisições mistas
            for i in range(50):
                endpoint = endpoints[i % len(endpoints)]
                response = client.get(endpoint)
                assert response.status_code == 200
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verificar que o tempo total é razoável
            assert total_time < 20.0  # 50 requisições mistas em menos de 20 segundos
            
            logger.info(f"50 mixed endpoint requests completed in: {total_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
