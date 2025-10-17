# app/services/kpi_service.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.repositories.industria_repo import IndustriaRepository
import math

class KPIService:
    def __init__(self, db: Session):
        self.repo = IndustriaRepository(db)

    def _calc_tempo_total_operacao_min(self, registros):
        total = 0.0
        for r in registros:
            if r.hora_inicio and r.hora_fim:
                total += (r.hora_fim - r.hora_inicio).total_seconds() / 60.0
        return total

    def ordem_kpis(self, ordem_id: int):
        ordem = self.repo.get_ordem(ordem_id)
        registros = self.repo.get_registros_por_ordem(ordem_id)
        if not ordem or not registros:
            return None

        # Quantidade produzida total
        total_produzida = sum((r.quantidade_produzida_real or 0) for r in registros)
        # Tempo total operação (min)
        tempo_total_min = self._calc_tempo_total_operacao_min(registros)
        # Tempo setup total
        tempo_setup_min = sum((r.tempo_setup_real_min or 0) for r in registros)
        # Energia total
        energia_total_kwh = sum((r.consumo_energia_kwh or 0) for r in registros)

        # Eficiência simples = produzido / planejado
        eficiencia_percent = (total_produzida / ordem.quantidade_planejada * 100.0) if ordem.quantidade_planejada else None

        # Taxa de defeitos por lotes associados (se existir)
        # Pesquisa controles de qualidade via lotes_producao relacionados à ordem
        lotes = ordem.__dict__.get("lotes")  # se você mapear relationship, ou buscar via query direta
        # Para simplicidade, buscar controles ligados a ordens via join seria ideal.
        # Aqui vamos simplificar: contar rejeições nos controles relacionados aos lotes (se existirem)
        # Implementação básica (melhorar conforme relationships):
        controles = []
        # (implementação ideal: query para controles onde lote.ordem_id == ordem_id)
        # Vou fazer uma consulta direta SQLAlchemy:
        from app import models
        db = self.repo.db
        controles = db.query(models.ControleQualidade).join(models.LoteProducao, models.ControleQualidade.lote_producao_id == models.LoteProducao.lote_producao_id).filter(models.LoteProducao.ordem_producao_id == ordem_id).all()

        unidades_rejeitadas = sum((c.unidades_rejeitadas or 0) for c in controles)
        unidades_inspecionadas = sum(((c.unidades_aprovadas or 0) + (c.unidades_rejeitadas or 0)) for c in controles)
        taxa_defeitos_percent = (unidades_rejeitadas / unidades_inspecionadas * 100.0) if unidades_inspecionadas else 0.0

        energia_por_unidade = (energia_total_kwh / total_produzida) if total_produzida else None

        return {
            "ordem_producao_id": ordem_id,
            "eficiencia_percent": round(eficiencia_percent, 2) if eficiencia_percent is not None else None,
            "taxa_defeitos_percent": round(taxa_defeitos_percent, 2),
            "energia_por_unidade_kwh": round(energia_por_unidade, 4) if energia_por_unidade else None,
            "tempo_total_min": round(tempo_total_min, 2),
            "tempo_setup_total_min": round(tempo_setup_min, 2),
            "quantidade_produzida": int(total_produzida)
        }

    def maquina_kpis_periodo(self, maquina_id: int, dt_inicio: datetime, dt_fim: datetime):
        registros = self.repo.get_registros_por_maquina_periodo(maquina_id, dt_inicio, dt_fim)
        paradas = self.repo.get_paradas_por_maquina_periodo(maquina_id, dt_inicio, dt_fim)

        total_produzida = sum((r.quantidade_produzida_real or 0) for r in registros)
        tempo_operacao_min = self._calc_tempo_total_operacao_min(registros)
        tempo_parada_min = sum(((p.hora_fim_parada - p.hora_inicio_parada).total_seconds() / 60.0) for p in paradas if p.hora_fim_parada and p.hora_inicio_parada)
        energia_total = sum((r.consumo_energia_kwh or 0) for r in registros)

        # Disponibilidade = tempo_operacao / (tempo_operacao + tempo_parada)
        disponibilidade = (tempo_operacao_min / (tempo_operacao_min + tempo_parada_min) * 100.0) if (tempo_operacao_min + tempo_parada_min) > 0 else None

        # MTBF e MTTR
        # MTBF = tempo_operacao_total / numero_de_falhas (considerando paradas como falhas)
        num_falhas = len(paradas)
        mtbf_h = (tempo_operacao_min / 60.0 / num_falhas) if num_falhas else None
        # MTTR = tempo_parada_total / numero_de_falhas
        mttr_h = (tempo_parada_min / 60.0 / num_falhas) if num_falhas else None

        taxa_defeitos = 0.0
        # se desejar, você pode agregar defeitos por registros associados

        energia_por_unidade = (energia_total / total_produzida) if total_produzida else None

        return {
            "maquina_id": maquina_id,
            "periodo_inicio": dt_inicio.isoformat(),
            "periodo_fim": dt_fim.isoformat(),
            "disponibilidade_percent": round(disponibilidade, 2) if disponibilidade is not None else None,
            "mtbf_h": round(mtbf_h, 2) if mtbf_h else None,
            "mttr_h": round(mttr_h, 2) if mttr_h else None,
            "energia_por_unidade_kwh": round(energia_por_unidade, 4) if energia_por_unidade else None,
            "quantidade_produzida": int(total_produzida)
        }











from math import sqrt

def calcular_oee(disponibilidade: float, performance: float, qualidade: float) -> float:
    return round(disponibilidade * performance * qualidade, 4)

def calcular_taxa_producao(producao_total: float, tempo: float) -> float:
    return round(producao_total / tempo, 4) if tempo > 0 else 0.0

def calcular_eficiencia_linha(saida_linha: float, smv: float, num_operadores: int, minutos_trabalhados: float) -> float:
    return round((saida_linha * smv * 100) / (num_operadores * minutos_trabalhados), 4) if num_operadores > 0 else 0.0

def calcular_produtividade_mao_obra(saida_total: float, mao_obra_total: float) -> float:
    return round(saida_total / mao_obra_total, 4) if mao_obra_total > 0 else 0.0

def calcular_vazao(area1: float, v1: float, area2: float) -> float:
    # A1 * v1 = A2 * v2 => v2 = (A1 * v1) / A2
    return round((area1 * v1) / area2, 4) if area2 > 0 else 0.0

def calcular_transferencia_calor(massa: float, c: float, delta_t: float) -> float:
    return round(massa * c * delta_t, 4)

def calcular_taxa_defeito(defeitos: int, unidades: int) -> float:
    return round((defeitos / unidades) * 100, 4) if unidades > 0 else 0.0

