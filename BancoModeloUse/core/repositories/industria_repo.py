# app/repositories/industria_repo.py
from app.repositories.base import BaseRepository
from app import models
from sqlalchemy import func
from datetime import datetime, date, timedelta

class IndustriaRepository(BaseRepository):

    def get_ordem(self, ordem_id: int):
        return self.db.query(models.OrdemProducao).filter_by(ordem_producao_id=ordem_id).first()

    def get_registros_por_ordem(self, ordem_id: int):
        return self.db.query(models.RegistroOperacao).filter_by(ordem_producao_id=ordem_id).all()

    def get_paradas_por_maquina_periodo(self, maquina_id: int, dt_inicio, dt_fim):
        return (
            self.db.query(models.ParadaMaquina)
            .filter(models.ParadaMaquina.maquina_id == maquina_id)
            .filter(models.ParadaMaquina.hora_inicio_parada >= dt_inicio)
            .filter(models.ParadaMaquina.hora_fim_parada <= dt_fim)
            .all()
        )

    def get_controles_por_lote(self, lote_id: int):
        return self.db.query(models.ControleQualidade).filter_by(lote_producao_id=lote_id).all()

    def get_registros_por_maquina_periodo(self, maquina_id: int, dt_inicio, dt_fim):
        return (
            self.db.query(models.RegistroOperacao)
            .filter(models.RegistroOperacao.maquina_id == maquina_id)
            .filter(models.RegistroOperacao.hora_inicio >= dt_inicio)
            .filter(models.RegistroOperacao.hora_fim <= dt_fim)
            .all()
        )

    def get_paradas_por_maquina(self, maquina_id: int):
        return self.db.query(models.ParadaMaquina).filter_by(maquina_id=maquina_id).all()

    # adicione mais métodos conforme necessário
