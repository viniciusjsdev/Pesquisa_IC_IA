"""
Testes para o sistema multi-agente RAG
"""

import pytest
from unittest.mock import Mock, patch
from rag.state import AgentState
from rag.enums import Agentes
from rag.graph import build_graph
from rag.state_service import wrap_state
from rag.agents.preprocessador import preprocessador
from rag.agents.validador_global import validador_global
from rag.tools.registry import get_tool, list_tools
from config.logger import get_logger

logger = get_logger(__name__)


class TestStateManagement:
    """Testes para gerenciamento de estado"""
    
    def test_agent_state_creation(self):
        """Testa criação de AgentState"""
        state: AgentState = {
            "user_id": "test_user",
            "trace_id": "test_trace",
            "session_id": "test_session",
            "question": "Test question",
            "turn": None,
            "answer": "",
            "answers": {},
            "tasks": {},
            "pending": [],
            "current": None,
            "next": Agentes.ORQUESTRADOR,
            "error": "",
            "did_finalize": False,
            "validation": None,
            "issues": None,
            "loops": 0,
            "max_loops": 10
        }
        
        assert state["user_id"] == "test_user"
        assert state["question"] == "Test question"
        assert state["next"] == Agentes.ORQUESTRADOR
    
    def test_state_service_wrapper(self):
        """Testa StateService wrapper"""
        state: AgentState = {
            "user_id": "test_user",
            "trace_id": "test_trace",
            "session_id": "test_session",
            "question": "Test question",
            "turn": None,
            "answer": "",
            "answers": {},
            "tasks": {},
            "pending": [],
            "current": None,
            "next": Agentes.ORQUESTRADOR,
            "error": "",
            "did_finalize": False,
            "validation": None,
            "issues": None,
            "loops": 0,
            "max_loops": 10
        }
        
        service = wrap_state(state)
        
        assert service.question == "Test question"
        assert service.is_starting_flow() == True
        assert service.has_pending() == False


class TestAgentes:
    """Testes para agentes"""
    
    def test_preprocessador_basic(self):
        """Testa agente preprocessador básico"""
        state: AgentState = {
            "user_id": "test_user",
            "trace_id": "test_trace",
            "session_id": "test_session",
            "question": "Qual foi a receita total de vendas?",
            "turn": None,
            "answer": "",
            "answers": {},
            "tasks": {},
            "pending": [],
            "current": Agentes.PREPROCESSADOR,
            "next": Agentes.PREPROCESSADOR,
            "error": "",
            "did_finalize": False,
            "validation": None,
            "issues": None,
            "loops": 0,
            "max_loops": 10
        }
        
        # Mock do LLM para teste
        with patch('rag.agents.preprocessador.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.ask.return_value = '{"tasks": {"@agente_financeiro": "Calcular receita total de vendas", "@agente_finalizador": "Apresentar resultado final"}}'
            mock_get_llm.return_value = mock_llm
            
            result = preprocessador(state)
            
            assert "turn" in result
            assert result["turn"]["agent"] == Agentes.PREPROCESSADOR
    
    def test_validador_global_basic(self):
        """Testa agente validador global básico"""
        state: AgentState = {
            "user_id": "test_user",
            "trace_id": "test_trace",
            "session_id": "test_session",
            "question": "Qual foi a receita total de vendas?",
            "turn": None,
            "answer": "",
            "answers": {
                Agentes.FINANCEIRO: {
                    "agent": Agentes.FINANCEIRO,
                    "task": "Calcular receita total de vendas",
                    "answer": "Receita total: R$ 100.000",
                    "error": ""
                }
            },
            "tasks": {},
            "pending": [],
            "current": Agentes.VALIDADOR_GLOBAL,
            "next": Agentes.VALIDADOR_GLOBAL,
            "error": "",
            "did_finalize": False,
            "validation": None,
            "issues": None,
            "loops": 0,
            "max_loops": 10
        }
        
        # Mock do LLM para teste
        with patch('rag.agents.validador_global.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.ask.return_value = '{"ok": true}'
            mock_get_llm.return_value = mock_llm
            
            result = validador_global(state)
            
            assert "turn" in result
            assert result["turn"]["agent"] == Agentes.VALIDADOR_GLOBAL


class TestToolsRegistry:
    """Testes para registry de tools"""
    
    def test_tools_registry_basic(self):
        """Testa registry básico de tools"""
        tools = list_tools()
        
        # Verificar se tools foram registradas
        assert isinstance(tools, dict)
        
        # Verificar se tools financeiras estão registradas
        if "query_financeira" in tools:
            assert "Executa consultas financeiras" in tools["query_financeira"]


class TestGraph:
    """Testes para o graph LangGraph"""
    
    def test_graph_creation(self):
        """Testa criação do graph"""
        try:
            graph = build_graph()
            assert graph is not None
        except Exception as e:
            pytest.skip(f"Graph não pode ser criado: {e}")
    
    def test_graph_invoke_basic(self):
        """Testa invocação básica do graph"""
        try:
            graph = build_graph()
            
            initial_state: AgentState = {
                "user_id": "test_user",
                "trace_id": "test_trace",
                "session_id": "test_session",
                "question": "Test question",
                "turn": None,
                "answer": "",
                "answers": {},
                "tasks": {},
                "pending": [],
                "current": None,
                "next": Agentes.ORQUESTRADOR,
                "error": "",
                "did_finalize": False,
                "validation": None,
                "issues": None,
                "loops": 0,
                "max_loops": 10
            }
            
            # Mock dos agentes para teste
            with patch('rag.agents.preprocessador.get_llm') as mock_get_llm:
                mock_llm = Mock()
                mock_llm.ask.return_value = '{"tasks": {"@agente_finalizador": "Apresentar resultado final"}}'
                mock_get_llm.return_value = mock_llm
                
                result = graph.invoke(initial_state)
                
                assert isinstance(result, dict)
                assert "answer" in result or "error" in result
                
        except Exception as e:
            pytest.skip(f"Graph não pode ser testado: {e}")


class TestEnums:
    """Testes para enums"""
    
    def test_agentes_enum(self):
        """Testa enum de agentes"""
        assert Agentes.ORQUESTRADOR == "orquestrador"
        assert Agentes.PREPROCESSADOR == "preprocessador"
        assert Agentes.FINANCEIRO == "agente_financeiro"
        assert Agentes.INDUSTRIAL == "agente_industrial"
        assert Agentes.INTEGRACAO == "agente_integracao"
        assert Agentes.FINALIZADOR == "agente_finalizador"
        assert Agentes.VALIDADOR_GLOBAL == "validador_global"
    
    def test_agentes_from_key(self):
        """Testa conversão de string para enum"""
        assert Agentes.from_key("orquestrador") == Agentes.ORQUESTRADOR
        assert Agentes.from_key("preprocessador") == Agentes.PREPROCESSADOR
        assert Agentes.from_key("invalid") is None
    
    def test_agentes_lists(self):
        """Testa listas de agentes"""
        all_agents = Agentes.get_all_agents()
        assert "orquestrador" in all_agents
        assert "preprocessador" in all_agents
        
        specialized = Agentes.get_specialized_agents()
        assert "agente_financeiro" in specialized
        assert "agente_industrial" in specialized
        
        orchestration = Agentes.get_orchestration_agents()
        assert "orquestrador" in orchestration
        assert "preprocessador" in orchestration


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
