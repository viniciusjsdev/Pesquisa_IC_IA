#!/usr/bin/env python3
"""
Carrega CSVs financeiros para o banco financeiro.

Uso:
  python scripts/load_financeiro.py --base "BancoModeloUse/dados_simulados" --periodo "2021_2025" --chunksize 5000

- Lê os CSVs em BancoModeloUse/dados_simulados/dados_financeiros_<periodo>/
- Mapeia para as tabelas ORM em BancoModeloUse/core/models/financeiro/
- Insere via SQLAlchemy, com upsert simples por PK quando aplicável
"""
from __future__ import annotations
import argparse
import os
import sys
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import inspect

# Permite imports relativos ao projeto
ROOT = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(ROOT)
sys.path.append(WORKSPACE_ROOT)

from BancoModeloUse.infrastructure.database.connections.financeiro_connection import (  # type: ignore  # noqa: E402
    financeiro_connection,
)
from BancoModeloUse.core.models.financeiro.contabil import (  # type: ignore  # noqa: E402
    ContaContabil,
    LancamentoFinanceiro,
    CategoriaContabilPadrao,
    SubcategoriaContabilPadrao,
    ContaContabilDetalhe,
)
from BancoModeloUse.core.models.financeiro.custos import (  # type: ignore  # noqa: E402
    CustoPadrao,
    CustoIndiretoRateio,
    MaterialCustoHistorico,
    CustoMaoObraHistorico,
    CustoOperacionalVariavel,
    CustoProducao,
    ResultadoFinanceiro,
    AnaliseFinanceira,
)
from BancoModeloUse.core.models.financeiro.kpis import KPIGerencial  # type: ignore  # noqa: E402
from BancoModeloUse.core.models.financeiro.vendas import (  # type: ignore  # noqa: E402
    Venda,
    Orcamento,
)


def _read_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df


def _bulk_upsert(session: Session, model, df: pd.DataFrame, pk_column: str) -> int:
    count = 0
    mapper = inspect(model)
    model_cols = {c.key for c in mapper.columns}
    df = df[[c for c in df.columns if c in model_cols]]

    for _, row in df.iterrows():
        payload = row.dropna().to_dict()
        pk_value = payload.get(pk_column)
        if pk_value is None:
            obj = model(**payload)
            session.add(obj)
            count += 1
            continue
        existing = session.get(model, pk_value)
        if existing is None:
            obj = model(**payload)
            session.add(obj)
        else:
            for k, v in payload.items():
                setattr(existing, k, v)
        count += 1
    session.flush()
    return count


# --------- Funções de importação por tabela ---------

def import_contas_contabeis(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "contas_contabeis.csv")
    if not os.path.exists(path):
        print(f"[financeiro] contas_contabeis.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, ContaContabil, df, "conta_id")
    print(f"[financeiro] Contas contábeis importadas/atualizadas: {inserted}")
    return inserted


def import_lancamentos_financeiros(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "lancamentos_financeiros.csv")
    if not os.path.exists(path):
        print(f"[financeiro] lancamentos_financeiros.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, LancamentoFinanceiro, df, "lancamento_id")
    print(f"[financeiro] Lançamentos financeiros importados/atualizados: {inserted}")
    return inserted


def import_custos(session: Session, base_dir: str) -> int:
    total = 0
    mapping = [
        (CustoPadrao, "custos_padrao.csv", "custo_padrao_id"),
        (CustoIndiretoRateio, "custos_indiretos_rateio.csv", "rateio_id"),
        (MaterialCustoHistorico, "materiais_custo_historico.csv", "custo_material_id"),
        (CustoMaoObraHistorico, "custo_mao_obra_historico.csv", "custo_mo_id"),
        (CustoOperacionalVariavel, "custos_operacionais_variaveis.csv", "custo_operacional_id"),
        (CustoProducao, "custos_producao.csv", "id"),
        (ResultadoFinanceiro, "resultados_financeiros.csv", "id"),
        (AnaliseFinanceira, "analises_financeiras.csv", "id"),
    ]
    for model, filename, pk in mapping:
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            print(f"[financeiro] {filename} não encontrado em {base_dir}")
            continue
        df = _read_csv(path)
        total += _bulk_upsert(session, model, df, pk)
    print(f"[financeiro] Tabelas de custos importadas/atualizadas: {total}")
    return total


def import_kpis(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "kpis_gerenciais.csv")
    if not os.path.exists(path):
        print(f"[financeiro] kpis_gerenciais.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, KPIGerencial, df, "kpi_id")
    print(f"[financeiro] KPIs importados/atualizados: {inserted}")
    return inserted


def import_vendas_orcamentos(session: Session, base_dir: str) -> int:
    total = 0
    mapping = [
        (Venda, "vendas.csv", "venda_id"),
        (Orcamento, "orcamentos.csv", "orcamento_id"),
    ]
    for model, filename, pk in mapping:
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            print(f"[financeiro] {filename} não encontrado em {base_dir}")
            continue
        df = _read_csv(path)
        total += _bulk_upsert(session, model, df, pk)
    print(f"[financeiro] Vendas/Orçamentos importados/atualizados: {total}")
    return total


def build_base_path(base: str, periodo: Optional[str]) -> str:
    if periodo:
        return os.path.join(
            base,
            f"dados_financeiros_{periodo}",
        )
    # fallback: usa 2021_2025 por padrão
    return os.path.join(base, "dados_financeiros_2021_2025")


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga de CSVs para o banco financeiro")
    parser.add_argument("--base", default="BancoModeloUse/dados_simulados", help="Diretório base dos dados simulados")
    parser.add_argument("--periodo", default=None, help="Sufixo de período, ex: 2015_2016, 2017_2020, 2021_2025")
    parser.add_argument("--commit", action="store_true", help="Efetiva commit no final (senão faz rollback)")
    args = parser.parse_args()

    data_dir = build_base_path(args.base, args.periodo)
    print(f"[financeiro] Lendo dados de: {data_dir}")

    engine = financeiro_connection.get_engine()
    # Garante que as tabelas existam
    from BancoModeloUse.infrastructure.database.connections.financeiro_connection import Base as FinanceiroBase  # noqa: E402

    FinanceiroBase.metadata.create_all(bind=engine)

    session: Session = financeiro_connection.get_session()
    try:
        total = 0
        total += import_contas_contabeis(session, data_dir)
        total += import_lancamentos_financeiros(session, data_dir)
        total += import_custos(session, data_dir)
        total += import_kpis(session, data_dir)
        total += import_vendas_orcamentos(session, data_dir)

        if args.commit:
            session.commit()
            print(f"[financeiro] Commit realizado. Registros processados: {total}")
        else:
            session.rollback()
            print(f"[financeiro] Rollback realizado (use --commit para gravar). Registros processados: {total}")
    except Exception as exc:
        session.rollback()
        print(f"[financeiro] ERRO durante a carga: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
