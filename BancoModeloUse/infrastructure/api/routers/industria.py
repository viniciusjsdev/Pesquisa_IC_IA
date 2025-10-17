# app/api/industria_router.py
from fastapi import APIRouter, Depends, HTTPException
from app.db import get_db
from sqlalchemy.orm import Session
from app.services.kpi_service import KPIService
from datetime import datetime, timedelta

router = APIRouter(prefix="/industria", tags=["Industria"])

def get_kpi_service(db: Session = Depends(get_db)):
    return KPIService(db)

@router.get("/ordem/{ordem_id}/kpis")
def ordem_kpis(ordem_id: int, svc: KPIService = Depends(get_kpi_service)):
    res = svc.ordem_kpis(ordem_id)
    if not res:
        raise HTTPException(status_code=404, detail="Ordem não encontrada ou sem registros")
    return res

@router.get("/maquina/{maquina_id}/kpis")
def maquina_kpis(maquina_id: int, start: str = None, end: str = None, svc: KPIService = Depends(get_kpi_service)):
    # start/end no formato ISO 'YYYY-MM-DD' ou 'YYYY-MM-DDTHH:MM:SS'
    if not start:
        start_dt = datetime.utcnow() - timedelta(days=7)
    else:
        start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end) if end else datetime.utcnow()
    return svc.maquina_kpis_periodo(maquina_id, start_dt, end_dt)
