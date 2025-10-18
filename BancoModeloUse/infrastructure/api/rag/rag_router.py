# infrastructure/api/rag/rag_router.py
"""
Router para endpoints RAG
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel
from core.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/rag", tags=["RAG"])

# Inicializar pipeline RAG
rag_pipeline = RAGPipeline()

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

@router.post("/consulta", response_model=ConsultaResponse)
async def processar_consulta(request: ConsultaRequest):
    """
    Processa consulta através do pipeline RAG
    
    Args:
        request: Requisição com consulta e parâmetros opcionais
    
    Returns:
        Resposta processada pelo pipeline RAG
    """
    try:
        # Processar consulta através do pipeline
        resultado = rag_pipeline.processar_consulta(request.consulta)
        
        # Determinar status
        status = "sucesso" if "erro" not in resultado else "erro"
        
        return ConsultaResponse(
            consulta_original=request.consulta,
            resultado=resultado,
            timestamp=datetime.now().isoformat(),
            status=status
        )
    except Exception as e:
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
