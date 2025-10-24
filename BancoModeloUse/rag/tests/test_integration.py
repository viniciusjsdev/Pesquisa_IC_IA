"""
Testes de integração para o sistema multi-agente
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from infrastructure.api.main import app
from config.logger import get_logger

logger = get_logger(__name__)


class TestAPIIntegration:
    """Testes de integração da API"""
    
    def test_health_check(self):
        """Testa endpoint de health check"""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "graph_ready" in data
            assert "langfuse_enabled" in data
    
    def test_root_endpoint(self):
        """Testa endpoint raiz"""
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            
            data = response.json()
            assert "service" in data
            assert "modules" in data
            assert "multi-agent" in data["modules"]
    
    def test_rag_ask_endpoint_basic(self):
        """Testa endpoint RAG básico"""
        with TestClient(app) as client:
            # Teste com pergunta simples
            payload = {
                "consulta": "Qual foi a receita total de vendas?",
                "parametros": {}
            }
            
            response = client.post("/rag/ask", json=payload)
            
            # Pode retornar 200 (sucesso) ou 503 (sistema não pronto)
            assert response.status_code in [200, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert "consulta_original" in data
                assert "resultado" in data
                assert "timestamp" in data
                assert "status" in data
    
    def test_rag_exemplos_endpoint(self):
        """Testa endpoint de exemplos"""
        with TestClient(app) as client:
            response = client.get("/rag/exemplos")
            assert response.status_code == 200
            
            data = response.json()
            assert "exemplos" in data
            assert "financeiro" in data["exemplos"]
            assert "industrial" in data["exemplos"]
            assert "integracao" in data["exemplos"]
    
    def test_rag_agentes_endpoint(self):
        """Testa endpoint de agentes"""
        with TestClient(app) as client:
            response = client.get("/rag/agentes")
            assert response.status_code == 200
            
            data = response.json()
            assert "agentes" in data
            assert "total_agentes" in data
            assert "orquestrador" in data["agentes"]
            assert "financeiro" in data["agentes"]
            assert "industrial" in data["agentes"]
            assert "finalizador" in data["agentes"]
    
    def test_rag_ferramentas_endpoint(self):
        """Testa endpoint de ferramentas"""
        with TestClient(app) as client:
            response = client.get("/rag/ferramentas")
            assert response.status_code == 200
            
            data = response.json()
            assert "ferramentas" in data
            assert "total_ferramentas" in data
            assert "financeiro_tools" in data["ferramentas"]
            assert "industrial_tools" in data["ferramentas"]
            assert "integracao_tools" in data["ferramentas"]


class TestDatabaseIntegration:
    """Testes de integração com banco de dados"""
    
    def test_database_status(self):
        """Testa status do banco de dados"""
        with TestClient(app) as client:
            response = client.get("/database-status")
            assert response.status_code == 200
            
            data = response.json()
            assert "database_exists" in data
            assert "tables_exist" in data
            assert "status" in data
            assert "message" in data
    
    def test_create_tables_endpoint(self):
        """Testa endpoint de criação de tabelas"""
        with TestClient(app) as client:
            response = client.post("/create-tables")
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert "status" in data
    
    def test_update_tables_endpoint(self):
        """Testa endpoint de atualização de tabelas"""
        with TestClient(app) as client:
            response = client.post("/update-tables")
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert "status" in data


class TestTraceIDIntegration:
    """Testes de integração com Trace ID"""
    
    def test_trace_id_propagation(self):
        """Testa propagação de Trace ID"""
        with TestClient(app) as client:
            # Teste sem Trace ID (deve gerar um)
            response = client.get("/health")
            assert response.status_code == 200
            assert "X-Trace-ID" in response.headers
            
            # Teste com Trace ID customizado
            custom_trace_id = "custom-trace-123"
            response = client.get(
                "/health",
                headers={"X-Trace-ID": custom_trace_id}
            )
            assert response.status_code == 200
            assert response.headers["X-Trace-ID"] == custom_trace_id
    
    def test_user_id_propagation(self):
        """Testa propagação de User ID"""
        with TestClient(app) as client:
            custom_user_id = "user-123"
            response = client.get(
                "/health",
                headers={"X-User-ID": custom_user_id}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["user_id"] == custom_user_id
    
    def test_session_id_propagation(self):
        """Testa propagação de Session ID"""
        with TestClient(app) as client:
            custom_session_id = "session-123"
            response = client.get(
                "/health",
                headers={"X-Session-ID": custom_session_id}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["session_id"] == custom_session_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
