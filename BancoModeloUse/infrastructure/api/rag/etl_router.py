# infrastructure/api/rag/etl_router.py
"""
Router para endpoints ETL
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel
from core.services.etl.etl_service import ETLService
from core.services.etl.etl_scheduler import ETLScheduler

router = APIRouter(prefix="/etl", tags=["ETL"])

# Inicializar serviços ETL
etl_service = ETLService()
etl_scheduler = ETLScheduler()

class ETLRequest(BaseModel):
    """Modelo para requisição de ETL"""
    data_inicio: date
    data_fim: date
    tipo: Optional[str] = "completo"  # completo, incremental

class ETLResponse(BaseModel):
    """Modelo para resposta de ETL"""
    status: str
    resultado: Dict[str, Any]
    timestamp: str

@router.post("/executar", response_model=ETLResponse)
async def executar_etl(request: ETLRequest):
    """
    Executa ETL para período especificado
    
    Args:
        request: Requisição com período e tipo de ETL
    
    Returns:
        Resultado da execução do ETL
    """
    try:
        if request.tipo == "completo":
            resultado = etl_service.executar_etl_completo(request.data_inicio, request.data_fim)
        elif request.tipo == "incremental":
            resultado = etl_service.executar_etl_incremental(request.data_inicio, request.data_fim)
        else:
            raise HTTPException(status_code=400, detail="Tipo de ETL inválido")
        
        return ETLResponse(
            status="sucesso",
            resultado=resultado,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar ETL: {str(e)}")

@router.post("/executar-diario")
async def executar_etl_diario():
    """
    Executa ETL diário para o dia anterior
    
    Returns:
        Resultado da execução do ETL diário
    """
    try:
        resultado = etl_service.executar_etl_diario()
        return {
            "status": "sucesso",
            "resultado": resultado,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar ETL diário: {str(e)}")

@router.post("/executar-semanal")
async def executar_etl_semanal():
    """
    Executa ETL semanal para a semana anterior
    
    Returns:
        Resultado da execução do ETL semanal
    """
    try:
        resultado = etl_service.executar_etl_semanal()
        return {
            "status": "sucesso",
            "resultado": resultado,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar ETL semanal: {str(e)}")

@router.post("/executar-mensal")
async def executar_etl_mensal():
    """
    Executa ETL mensal para o mês anterior
    
    Returns:
        Resultado da execução do ETL mensal
    """
    try:
        resultado = etl_service.executar_etl_mensal()
        return {
            "status": "sucesso",
            "resultado": resultado,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar ETL mensal: {str(e)}")

@router.get("/status")
async def obter_status_etl():
    """
    Retorna status do sistema ETL
    
    Returns:
        Status do ETL e agendamentos
    """
    try:
        status = etl_scheduler.obter_status_scheduler()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status ETL: {str(e)}")

@router.post("/agendar-diario")
async def agendar_etl_diario(hora: str = "02:00"):
    """
    Agenda ETL diário
    
    Args:
        hora: Hora para execução (formato HH:MM)
    
    Returns:
        Confirmação do agendamento
    """
    try:
        etl_scheduler.agendar_etl_diario(hora)
        return {
            "status": "sucesso",
            "mensagem": f"ETL diário agendado para {hora}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao agendar ETL diário: {str(e)}")

@router.post("/agendar-semanal")
async def agendar_etl_semanal(dia_semana: int = 1, hora: str = "03:00"):
    """
    Agenda ETL semanal
    
    Args:
        dia_semana: Dia da semana (1=Segunda, 7=Domingo)
        hora: Hora para execução (formato HH:MM)
    
    Returns:
        Confirmação do agendamento
    """
    try:
        etl_scheduler.agendar_etl_semanal(dia_semana, hora)
        return {
            "status": "sucesso",
            "mensagem": f"ETL semanal agendado para {dia_semana} às {hora}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao agendar ETL semanal: {str(e)}")

@router.post("/agendar-mensal")
async def agendar_etl_mensal(dia_mes: int = 1, hora: str = "04:00"):
    """
    Agenda ETL mensal
    
    Args:
        dia_mes: Dia do mês
        hora: Hora para execução (formato HH:MM)
    
    Returns:
        Confirmação do agendamento
    """
    try:
        etl_scheduler.agendar_etl_mensal(dia_mes, hora)
        return {
            "status": "sucesso",
            "mensagem": f"ETL mensal agendado para dia {dia_mes} às {hora}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao agendar ETL mensal: {str(e)}")

@router.post("/iniciar-scheduler")
async def iniciar_scheduler():
    """
    Inicia o scheduler ETL
    
    Returns:
        Confirmação da inicialização
    """
    try:
        etl_scheduler.iniciar_scheduler()
        return {
            "status": "sucesso",
            "mensagem": "Scheduler ETL iniciado",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar scheduler: {str(e)}")

@router.post("/parar-scheduler")
async def parar_scheduler():
    """
    Para o scheduler ETL
    
    Returns:
        Confirmação da parada
    """
    try:
        etl_scheduler.parar_scheduler()
        return {
            "status": "sucesso",
            "mensagem": "Scheduler ETL parado",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao parar scheduler: {str(e)}")

@router.get("/estatisticas")
async def obter_estatisticas_etl():
    """
    Retorna estatísticas do ETL
    
    Returns:
        Estatísticas do sistema ETL
    """
    try:
        estatisticas = etl_scheduler.obter_estatisticas_etl()
        return estatisticas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas ETL: {str(e)}")

@router.get("/historico")
async def obter_historico_etl():
    """
    Retorna histórico de execuções ETL
    
    Returns:
        Histórico de execuções
    """
    try:
        status = etl_scheduler.obter_status_scheduler()
        historico = status.get('job_history', [])
        return {
            "historico": historico,
            "total_execucoes": len(historico),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter histórico ETL: {str(e)}")
