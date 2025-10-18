# core/services/etl/etl_scheduler.py
"""
Agendador ETL com APScheduler
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from core.services.etl.etl_service import ETLService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETLScheduler:
    """Agendador ETL com APScheduler"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.etl_service = ETLService()
        self.job_history = []
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Configura listeners para eventos do scheduler"""
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
    
    def _job_executed(self, event):
        """Callback para job executado com sucesso"""
        job_info = {
            'job_id': event.job_id,
            'timestamp': datetime.now(),
            'status': 'success',
            'return_value': event.return_value
        }
        self.job_history.append(job_info)
        logger.info(f"Job {event.job_id} executado com sucesso")
    
    def _job_error(self, event):
        """Callback para job com erro"""
        job_info = {
            'job_id': event.job_id,
            'timestamp': datetime.now(),
            'status': 'error',
            'exception': str(event.exception)
        }
        self.job_history.append(job_info)
        logger.error(f"Job {event.job_id} falhou: {event.exception}")
    
    def agendar_etl_diario(self, hora: str = "02:00"):
        """Agenda ETL diário"""
        trigger = CronTrigger(hour=int(hora.split(':')[0]), minute=int(hora.split(':')[1]))
        self.scheduler.add_job(
            func=self._executar_etl_diario,
            trigger=trigger,
            id='etl_diario',
            name='ETL Diário',
            replace_existing=True
        )
        logger.info(f"ETL diário agendado para {hora}")
    
    def agendar_etl_semanal(self, dia_semana: int = 1, hora: str = "03:00"):
        """Agenda ETL semanal (1=Segunda, 7=Domingo)"""
        trigger = CronTrigger(day_of_week=dia_semana, hour=int(hora.split(':')[0]), minute=int(hora.split(':')[1]))
        self.scheduler.add_job(
            func=self._executar_etl_semanal,
            trigger=trigger,
            id='etl_semanal',
            name='ETL Semanal',
            replace_existing=True
        )
        logger.info(f"ETL semanal agendado para {dia_semana} às {hora}")
    
    def agendar_etl_mensal(self, dia_mes: int = 1, hora: str = "04:00"):
        """Agenda ETL mensal"""
        trigger = CronTrigger(day=dia_mes, hour=int(hora.split(':')[0]), minute=int(hora.split(':')[1]))
        self.scheduler.add_job(
            func=self._executar_etl_mensal,
            trigger=trigger,
            id='etl_mensal',
            name='ETL Mensal',
            replace_existing=True
        )
        logger.info(f"ETL mensal agendado para dia {dia_mes} às {hora}")
    
    def agendar_etl_customizado(self, job_id: str, trigger, func, *args, **kwargs):
        """Agenda ETL customizado"""
        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            args=args,
            kwargs=kwargs,
            replace_existing=True
        )
        logger.info(f"ETL customizado {job_id} agendado")
    
    def executar_etl_imediato(self, tipo: str = 'diario') -> Dict[str, Any]:
        """Executa ETL imediatamente"""
        logger.info(f"Executando ETL {tipo} imediatamente")
        
        if tipo == 'diario':
            return self._executar_etl_diario()
        elif tipo == 'semanal':
            return self._executar_etl_semanal()
        elif tipo == 'mensal':
            return self._executar_etl_mensal()
        else:
            raise ValueError(f"Tipo de ETL inválido: {tipo}")
    
    def _executar_etl_diario(self) -> Dict[str, Any]:
        """Executa ETL diário"""
        try:
            resultado = self.etl_service.executar_etl_diario()
            logger.info("ETL diário executado com sucesso")
            return resultado
        except Exception as e:
            logger.error(f"Erro no ETL diário: {e}")
            raise
    
    def _executar_etl_semanal(self) -> Dict[str, Any]:
        """Executa ETL semanal"""
        try:
            resultado = self.etl_service.executar_etl_semanal()
            logger.info("ETL semanal executado com sucesso")
            return resultado
        except Exception as e:
            logger.error(f"Erro no ETL semanal: {e}")
            raise
    
    def _executar_etl_mensal(self) -> Dict[str, Any]:
        """Executa ETL mensal"""
        try:
            resultado = self.etl_service.executar_etl_mensal()
            logger.info("ETL mensal executado com sucesso")
            return resultado
        except Exception as e:
            logger.error(f"Erro no ETL mensal: {e}")
            raise
    
    def iniciar_scheduler(self):
        """Inicia o scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler ETL iniciado")
        else:
            logger.warning("Scheduler já está rodando")
    
    def parar_scheduler(self):
        """Para o scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler ETL parado")
        else:
            logger.warning("Scheduler já está parado")
    
    def obter_status_scheduler(self) -> Dict[str, Any]:
        """Retorna status do scheduler"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            })
        
        return {
            'running': self.scheduler.running,
            'jobs': jobs,
            'job_history': self.job_history[-10:],  # Últimos 10 jobs
            'timestamp': datetime.now()
        }
    
    def remover_job(self, job_id: str):
        """Remove job do scheduler"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job {job_id} removido")
        except Exception as e:
            logger.error(f"Erro ao remover job {job_id}: {e}")
    
    def pausar_job(self, job_id: str):
        """Pausa job do scheduler"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job {job_id} pausado")
        except Exception as e:
            logger.error(f"Erro ao pausar job {job_id}: {e}")
    
    def retomar_job(self, job_id: str):
        """Retoma job do scheduler"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job {job_id} retomado")
        except Exception as e:
            logger.error(f"Erro ao retomar job {job_id}: {e}")
    
    def configurar_etl_padrao(self):
        """Configura ETL com agendamentos padrão"""
        # ETL diário às 2:00
        self.agendar_etl_diario("02:00")
        
        # ETL semanal às segundas às 3:00
        self.agendar_etl_semanal(1, "03:00")
        
        # ETL mensal no dia 1 às 4:00
        self.agendar_etl_mensal(1, "04:00")
        
        logger.info("ETL padrão configurado")
    
    def executar_etl_periodo(self, data_inicio: date, data_fim: date) -> Dict[str, Any]:
        """Executa ETL para período específico"""
        logger.info(f"Executando ETL para período: {data_inicio} a {data_fim}")
        return self.etl_service.executar_etl_completo(data_inicio, data_fim)
    
    def obter_estatisticas_etl(self) -> Dict[str, Any]:
        """Retorna estatísticas do ETL"""
        return {
            'scheduler_status': self.obter_status_scheduler(),
            'etl_stats': self.etl_service.obter_estatisticas_etl(),
            'timestamp': datetime.now()
        }
