#!/usr/bin/env python3
"""
ETL de integração entre bancos Industrial e Financeiro para o Data Warehouse (DW).

Uso:
  python scripts/etl_dw.py --acao build

Ações:
- build: cria/atualiza dimensões e fatos a partir dos bancos origem

Notas:
- Conecta nos bancos Industrial e Financeiro para extrair dados normalizados
- Conecta na DW para criar/atualizar tabelas de dimensões e fatos
- Foca em DimTempo, DimProduto, DimMaquina e fatos básicos (Vendas, Produção)
"""
from __future__ import annotations
import argparse
import os
import sys
from datetime import datetime
from typing import Iterable, Optional

import pandas as pd
from sqlalchemy.orm import Session

ROOT = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(ROOT)
sys.path.append(WORKSPACE_ROOT)

# Conexões
from BancoModeloUse.infrastructure.database.connections.industrial_connection import (  # type: ignore  # noqa: E402
    industrial_connection,
)
from BancoModeloUse.infrastructure.database.connections.financeiro_connection import (  # type: ignore  # noqa: E402
    financeiro_connection,
)
from BancoModeloUse.infrastructure.database.connections.dw_connection import (  # type: ignore  # noqa: E402
    dw_connection,
)

# Modelos DW
from BancoModeloUse.core.models.dw.dimensoes import (  # type: ignore  # noqa: E402
    DimTempo,
    DimProduto,
    DimMaquina,
)
from BancoModeloUse.core.models.dw.fatos import (  # type: ignore  # noqa: E402
    FatoVendas,
    FatoProducao,
)

# Modelos origem
from BancoModeloUse.core.models.industrial.cadastros import Produto as IndProduto, Maquina as IndMaquina  # type: ignore  # noqa: E402
from BancoModeloUse.core.models.financeiro.vendas import Venda as FinVenda  # type: ignore  # noqa: E402
from BancoModeloUse.core.models.industrial.producao import (  # type: ignore  # noqa: E402
    RegistroOperacao as IndRegistroOperacao,
    OrdemProducao as IndOrdemProducao,
)


# --------- Utilitários ---------

def _ensure_dw_schema() -> None:
    from BancoModeloUse.infrastructure.database.connections.dw_connection import Base as DWBase  # type: ignore  # noqa: E402

    engine = dw_connection.get_engine()
    DWBase.metadata.create_all(bind=engine)


def _df_dates_range(min_date: pd.Timestamp, max_date: pd.Timestamp) -> pd.DataFrame:
    idx = pd.date_range(start=min_date.normalize(), end=max_date.normalize(), freq="D")
    return pd.DataFrame({"data": idx})


def _populate_dim_tempo(session: Session, min_date: pd.Timestamp, max_date: pd.Timestamp) -> int:
    df = _df_dates_range(min_date, max_date)
    df["dia"] = df["data"].dt.day
    df["mes"] = df["data"].dt.month
    df["trimestre"] = df["data"].dt.quarter
    df["ano"] = df["data"].dt.year
    df["dia_semana"] = df["data"].dt.weekday + 1
    df["nome_dia_semana"] = df["data"].dt.day_name()
    df["nome_mes"] = df["data"].dt.month_name()
    df["nome_trimestre"] = "T" + df["trimestre"].astype(str)
    df["feriado"] = False
    df["periodo_fiscal"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)
    df["semana_ano"] = df["data"].dt.isocalendar().week.astype(int)
    df["dia_ano"] = df["data"].dt.dayofyear

    # usa data como surrogate key simples (YYYYMMDD)
    df["tempo_sk"] = df["data"].dt.strftime("%Y%m%d").astype(int)

    inserted = 0
    for _, row in df.iterrows():
        payload = row.to_dict()
        sk = payload["tempo_sk"]
        existing = session.get(DimTempo, sk)
        if existing is None:
            obj = DimTempo(**payload)
            session.add(obj)
            inserted += 1
    session.flush()
    print(f"[dw] DimTempo linhas novas: {inserted}")
    return inserted


def _populate_dim_produto(session: Session, ind_session: Session) -> int:
    inserted = 0
    produtos: Iterable[IndProduto] = ind_session.query(IndProduto).all()
    for p in produtos:
        # SK simples = id industrial
        sk = p.produto_id
        existing = session.get(DimProduto, sk)
        payload = {
            "produto_sk": sk,
            "produto_id_financeiro": None,
            "produto_id_industrial": p.produto_id,
            "nome_produto": p.nome_produto,
            "categoria": None,
            "unidade_medida": p.unidade_medida,
            "preco_unitario": None,
            "data_inicio_vigencia": None,
            "data_fim_vigencia": None,
            "ativo": True,
        }
        if existing is None:
            session.add(DimProduto(**payload))
            inserted += 1
        else:
            for k, v in payload.items():
                setattr(existing, k, v)
    session.flush()
    print(f"[dw] DimProduto upserts: {inserted}")
    return inserted


def _populate_dim_maquina(session: Session, ind_session: Session) -> int:
    inserted = 0
    maquinas: Iterable[IndMaquina] = ind_session.query(IndMaquina).all()
    for m in maquinas:
        sk = m.maquina_id
        existing = session.get(DimMaquina, sk)
        payload = {
            "maquina_sk": sk,
            "maquina_id_industrial": m.maquina_id,
            "nome_maquina": m.nome_maquina,
            "linha_producao": m.linha_producao,
            "capacidade_max": m.capacidade_producao_max,
            "centro_custo": None,
            "data_inicio_vigencia": None,
            "data_fim_vigencia": None,
            "ativo": True,
        }
        if existing is None:
            session.add(DimMaquina(**payload))
            inserted += 1
        else:
            for k, v in payload.items():
                setattr(existing, k, v)
    session.flush()
    print(f"[dw] DimMaquina upserts: {inserted}")
    return inserted


def _populate_fato_vendas(session: Session, fin_session: Session) -> int:
    inserted = 0
    vendas: Iterable[FinVenda] = fin_session.query(FinVenda).all()
    for v in vendas:
        tempo_sk = int(pd.to_datetime(v.data_venda).strftime("%Y%m%d")) if v.data_venda else None
        valor_total = None
        try:
            if v.preco_unitario_venda is not None and v.quantidade_vendida is not None:
                valor_total = float(v.preco_unitario_venda) * float(v.quantidade_vendida)
        except Exception:
            pass

        payload = {
            "venda_sk": v.venda_id,
            "produto_sk": v.produto_id,  # assumindo alinhamento 1:1
            "tempo_sk": tempo_sk,
            "cliente_sk": v.cliente_id if getattr(v, "cliente_id", None) is not None else None,
            "quantidade_vendida": v.quantidade_vendida,
            "valor_unitario": v.preco_unitario_venda,
            "valor_total": valor_total,
            "desconto": None,
            "margem_contribuicao": None,
            "data_venda": v.data_venda,
        }
        existing = session.get(FatoVendas, payload["venda_sk"])
        if existing is None:
            session.add(FatoVendas(**payload))
            inserted += 1
        else:
            for k, val in payload.items():
                setattr(existing, k, val)
    session.flush()
    print(f"[dw] FatoVendas upserts: {inserted}")
    return inserted


def _populate_fato_producao(session: Session, ind_session: Session) -> int:
    inserted = 0
    regs: Iterable[IndRegistroOperacao] = ind_session.query(IndRegistroOperacao).all()
    # Mapa de ordens para derivar produto e quantidade planejada
    ordens: Iterable[IndOrdemProducao] = ind_session.query(IndOrdemProducao).all()
    ordem_by_id = {o.ordem_producao_id: o for o in ordens}
    for r in regs:
        data_reg = pd.to_datetime(r.hora_inicio) if r.hora_inicio else None
        tempo_sk = int(data_reg.strftime("%Y%m%d")) if data_reg is not None else None
        tempo_producao_min = None
        if getattr(r, "hora_inicio", None) and getattr(r, "hora_fim", None):
            try:
                dt_i = pd.to_datetime(r.hora_inicio)
                dt_f = pd.to_datetime(r.hora_fim)
                tempo_producao_min = (dt_f - dt_i).total_seconds() / 60.0
            except Exception:
                tempo_producao_min = None

        produto_sk = None
        quantidade_planejada = None
        ordem = ordem_by_id.get(getattr(r, "ordem_producao_id", None))
        if ordem is not None:
            produto_sk = ordem.produto_id
            quantidade_planejada = ordem.quantidade_planejada
        payload = {
            "producao_sk": r.registro_id,
            "produto_sk": produto_sk,
            "maquina_sk": r.maquina_id,
            "tempo_sk": tempo_sk,
            "quantidade_produzida": r.quantidade_produzida_real,
            "quantidade_planejada": quantidade_planejada,
            "tempo_producao_min": tempo_producao_min,
            "tempo_setup_min": r.tempo_setup_real_min,
            "consumo_energia_kwh": r.consumo_energia_kwh,
            "eficiencia_percent": None,
            "defeitos_quantidade": None,
            "defeitos_percent": None,
            "data_producao": data_reg.date() if data_reg is not None else None,
        }
        existing = session.get(FatoProducao, payload["producao_sk"])
        if existing is None:
            session.add(FatoProducao(**payload))
            inserted += 1
        else:
            for k, val in payload.items():
                setattr(existing, k, val)
    session.flush()
    print(f"[dw] FatoProducao upserts: {inserted}")
    return inserted


def run_build() -> None:
    # Garante schema da DW
    _ensure_dw_schema()
    dw_sess: Session = dw_connection.get_session()
    ind_sess: Session = industrial_connection.get_session()
    fin_sess: Session = financeiro_connection.get_session()
    try:
        # Dimensão tempo: usa o range de datas dos dados fonte
        min_date = pd.Timestamp("2015-01-01")
        max_date = pd.Timestamp("2025-12-31")
        _populate_dim_tempo(dw_sess, min_date, max_date)
        _populate_dim_produto(dw_sess, ind_sess)
        _populate_dim_maquina(dw_sess, ind_sess)
        _populate_fato_vendas(dw_sess, fin_sess)
        _populate_fato_producao(dw_sess, ind_sess)
        dw_sess.commit()
        print("[dw] Build concluído com sucesso.")
    except Exception as exc:
        dw_sess.rollback()
        print(f"[dw] ERRO no build: {exc}")
        raise
    finally:
        dw_sess.close()
        ind_sess.close()
        fin_sess.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL para Data Warehouse")
    parser.add_argument("--acao", default="build", choices=["build"], help="Ação do processo de ETL")
    args = parser.parse_args()

    if args.acao == "build":
        run_build()


if __name__ == "__main__":
    main()
