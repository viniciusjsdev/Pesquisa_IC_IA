# infrastructure/api/rag/rag_router.py
"""
Router para endpoints RAG Multi-Agente
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel
from rag.state import AgentState
from rag.enums import Agentes
from core.context_vars import get_trace_id, get_user_id, get_session_id
from config.logger import get_logger
from rag.telemetry.langfuse import get_langfuse, is_langfuse_enabled

router = APIRouter(prefix="/rag", tags=["RAG Multi-Agente"])
logger = get_logger(__name__)

class ConsultaRequest(BaseModel):
    """Modelo para requisição de consulta RAG"""
    consulta: str
    parametros: Optional[Dict[str, Any]] = None

class ConsultaResponse(BaseModel):
    """Modelo para resposta de consulta RAG"""
    consulta_original: str
    resultado: Dict[str, Any]
    timestamp: str
    status: str

@router.post("/ask", response_model=ConsultaResponse)
async def processar_consulta(request: ConsultaRequest):
    """
    Processa consulta através do sistema multi-agente
    
    Args:
        request: Requisição com consulta e parâmetros opcionais
    
    Returns:
        Resposta processada pelo sistema multi-agente
    """
    try:
        # Obter contexto de rastreamento
        trace_id = get_trace_id()
        user_id = get_user_id()
        session_id = get_session_id()
        
        logger.info(f"Processando consulta - Trace ID: {trace_id}, User ID: {user_id}")
        
        # Criar estado inicial
        initial_state: AgentState = {
            "user_id": user_id or "anonymous",
            "trace_id": trace_id or "no-trace",
            "session_id": session_id or "no-session",
            "question": request.consulta,
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
        
        # Obter graph (importado do main.py)
        from infrastructure.api.main import graph, graph_ready
        
        if not graph_ready:
            raise HTTPException(status_code=503, detail="Sistema multi-agente não está pronto")
        
        # Executar graph com telemetria
        if is_langfuse_enabled():
            lf = get_langfuse()
            with lf.start_as_current_span(name="rag_multi_agent_query") as span:
                span.update(
                    input=request.consulta,
                    metadata={
                        "user_id": user_id,
                        "session_id": session_id,
                        "trace_id": trace_id
                    }
                )
                
                # Executar graph
                final_state = graph.invoke(initial_state)
                
                span.update(
                    output=final_state.get("answer", ""),
                    metadata={
                        "loops": final_state.get("loops", 0),
                        "agents_executed": list(final_state.get("answers", {}).keys()),
                        "validation_ok": final_state.get("validation", {}).get("ok", False)
                    }
                )
        else:
            # Executar graph sem telemetria
            final_state = graph.invoke(initial_state)
        
        # Determinar status
        status = "sucesso" if not final_state.get("error") else "erro"
        
        return ConsultaResponse(
            consulta_original=request.consulta,
            resultado={
                "answer": final_state.get("answer", ""),
                "agents_executed": list(final_state.get("answers", {}).keys()),
                "loops": final_state.get("loops", 0),
                "validation": final_state.get("validation"),
                "trace_id": trace_id
            },
            timestamp=datetime.now().isoformat(),
            status=status
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar consulta: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar consulta: {str(e)}")

@router.get("/exemplos")
async def obter_exemplos_consulta():
    """
    Retorna exemplos de consultas que podem ser feitas
    
    Returns:
        Lista de exemplos de consultas
    """
    exemplos = {
        "financeiro": [
            "Quais foram as vendas do último mês?",
            "Como está a margem de contribuição do produto X?",
            "Mostre os custos de produção por período",
            "Qual o ROI do investimento Y?"
        ],
        "industrial": [
            "Como está a produção da máquina 1?",
            "Qual a eficiência (OEE) dos equipamentos?",
            "Mostre a taxa de defeitos por período",
            "Quantas paradas ocorreram hoje?"
        ],
        "integracao": [
            "Qual a correlação entre custos e eficiência?",
            "Mostre o dashboard executivo",
            "Como está a qualidade vs lucratividade?",
            "Quais são os KPIs integrados?"
        ]
    }
    
    return {
        "exemplos": exemplos,
        "descricao": "Exemplos de consultas por domínio",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/estatisticas")
async def obter_estatisticas_rag():
    """
    Retorna estatísticas do sistema RAG
    
    Returns:
        Estatísticas do pipeline RAG
    """
    try:
        estatisticas = rag_pipeline.obter_estatisticas_pipeline()
        return estatisticas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@router.post("/teste")
async def testar_pipeline():
    """
    Testa o pipeline RAG com consultas de exemplo
    
    Returns:
        Resultado dos testes
    """
    try:
        resultado_teste = rag_pipeline.testar_pipeline()
        return resultado_teste
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao testar pipeline: {str(e)}")

@router.get("/agentes")
async def obter_agentes_disponiveis():
    """
    Retorna informações sobre os agentes disponíveis
    
    Returns:
        Lista de agentes e suas capacidades
    """
    agentes = {
        "orquestrador": {
            "descricao": "Interpreta consultas e direciona para agentes especializados",
            "responsabilidades": [
                "Interpretar consultas em linguagem natural",
                "Classificar domínio da consulta",
                "Extrair parâmetros da consulta",
                "Direcionar para agente especializado"
            ]
        },
        "financeiro": {
            "descricao": "Especializado em consultas financeiras",
            "responsabilidades": [
                "Analisar dados financeiros",
                "Calcular indicadores financeiros",
                "Gerar insights sobre performance financeira",
                "Sugerir ações para otimização financeira"
            ],
            "tipos_consulta": ["vendas", "custos", "lancamentos", "orcamentos", "indicadores"]
        },
        "industrial": {
            "descricao": "Especializado em consultas operacionais",
            "responsabilidades": [
                "Analisar dados operacionais",
                "Calcular KPIs industriais",
                "Gerar insights sobre performance operacional",
                "Sugerir ações para melhoria operacional"
            ],
            "tipos_consulta": ["producao", "equipamentos", "qualidade", "paradas", "indicadores"]
        },
        "finalizador": {
            "descricao": "Consolida respostas e produz resultado final",
            "responsabilidades": [
                "Consolidar respostas de múltiplos agentes",
                "Identificar correlações entre domínios",
                "Gerar insights integrados",
                "Produzir recomendações estratégicas"
            ]
        }
    }
    
    return {
        "agentes": agentes,
        "total_agentes": len(agentes),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/ferramentas")
async def obter_ferramentas_disponiveis():
    """
    Retorna informações sobre as ferramentas disponíveis
    
    Returns:
        Lista de ferramentas e suas capacidades
    """
    ferramentas = {
        "financeiro_tools": {
            "descricao": "Ferramentas para consultas financeiras",
            "metodos": [
                "query_financeira",
                "calcular_margem_contribuicao",
                "obter_indicadores_financeiros"
            ]
        },
        "industrial_tools": {
            "descricao": "Ferramentas para consultas industriais",
            "metodos": [
                "query_operacional",
                "calcular_kpis_ordem",
                "obter_indicadores_operacionais"
            ]
        },
        "integracao_tools": {
            "descricao": "Ferramentas para consultas integradas",
            "metodos": [
                "join_financeiro_industrial",
                "obter_dashboard_executivo"
            ]
        }
    }
    
    return {
        "ferramentas": ferramentas,
        "total_ferramentas": len(ferramentas),
        "timestamp": datetime.now().isoformat()
    }
