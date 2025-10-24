#!/usr/bin/env python3
"""
Carrega CSVs industriais para o banco industrial.

Uso:
  python scripts/load_industrial.py --base "BancoModeloUse/dados_simulados" --periodo "2015_2017" --chunksize 5000

- Lê os CSVs em BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_<periodo>/
- Mapeia para as tabelas ORM em BancoModeloUse/core/models/industrial/
- Insere via SQLAlchemy, com upsert simples por PK quando aplicável
"""
from __future__ import annotations
import argparse
import os
import sys
from typing import Callable, Dict, Iterable, List, Optional

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import inspect, Date, DateTime

# Permite imports relativos ao projeto
ROOT = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(ROOT)
sys.path.append(WORKSPACE_ROOT)

from BancoModeloUse.infrastructure.database.connections.industrial_connection import (  # type: ignore  # noqa: E402
    industrial_connection,
)
from BancoModeloUse.core.models.industrial.cadastros import (  # type: ignore  # noqa: E402
    Produto,
    Material,
    Maquina,
    Fornecedor,
)
from BancoModeloUse.core.models.industrial.equipamentos import (  # type: ignore  # noqa: E402
    Equipamento,
    ProcessoIndustrial,
)
from BancoModeloUse.core.models.industrial.producao import (  # type: ignore  # noqa: E402
    OrdemProducao,
    RoteiroProducao,
    OperacaoRoteiro,
    RegistroOperacao,
    ParadaMaquina,
    ConsumoMaterial,
    LoteMaterial,
    LoteProducao,
)
from BancoModeloUse.core.models.industrial.qualidade import (  # type: ignore  # noqa: E402
    ControleQualidade,
    Defeito,
    RegistroDefeito,
)


def _read_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normaliza nomes de colunas para snake_case já coerente com CSVs
    df.columns = [c.strip() for c in df.columns]
    return df


def _coerce_df_types_for_model(model, df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte colunas do DataFrame para tipos esperados pelo modelo ORM
    (Date -> date, DateTime -> datetime) quando aplicável.
    """
    mapper = inspect(model)
    df_conv = df.copy()
    for col in mapper.columns:
        name = col.key
        if name not in df_conv.columns:
            continue
        try:
            if isinstance(col.type, DateTime):
                df_conv[name] = pd.to_datetime(df_conv[name], errors="coerce")
            elif isinstance(col.type, Date):
                df_conv[name] = pd.to_datetime(df_conv[name], errors="coerce").dt.date
        except Exception:
            # Mantém valor original se falhar conversão
            pass
    return df_conv


def _bulk_upsert(session: Session, model, df: pd.DataFrame, pk_column: str) -> int:
    """
    Upsert simples: tenta inserir; se PK existe, faz merge linha a linha.
    É seguro porém menos performático em PKs já existentes.
    """
    count = 0
    # Determina colunas válidas no modelo
    mapper = inspect(model)
    model_cols = {c.key for c in mapper.columns}
    df = df[[c for c in df.columns if c in model_cols]]
    df = _coerce_df_types_for_model(model, df)

    pk_series = df[pk_column] if pk_column in df.columns else pd.Series(dtype=df.dtypes[0])

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

def import_produtos(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "produtos.csv")
    if not os.path.exists(path):
        print(f"[industrial] produtos.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, Produto, df, "produto_id")
    print(f"[industrial] Produtos importados/atualizados: {inserted}")
    return inserted


def import_materiais(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "materiais.csv")
    if not os.path.exists(path):
        print(f"[industrial] materiais.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, Material, df, "material_id")
    print(f"[industrial] Materiais importados/atualizados: {inserted}")
    return inserted


def import_maquinas(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "maquinas.csv")
    if not os.path.exists(path):
        print(f"[industrial] maquinas.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, Maquina, df, "maquina_id")
    print(f"[industrial] Maquinas importadas/atualizadas: {inserted}")
    return inserted


def import_equipamentos(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "equipamentos.csv")
    if not os.path.exists(path):
        print(f"[industrial] equipamentos.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, Equipamento, df, "id")
    print(f"[industrial] Equipamentos importados/atualizados: {inserted}")
    return inserted


def import_processos_industriais(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "processo_industrial.csv")
    if not os.path.exists(path):
        print(f"[industrial] processo_industrial.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, ProcessoIndustrial, df, "id")
    print(f"[industrial] Processos industriais importados/atualizados: {inserted}")
    return inserted


def import_fornecedores(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "fornecedores.csv")
    if not os.path.exists(path):
        print(f"[industrial] fornecedores.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, Fornecedor, df, "fornecedor_id")
    print(f"[industrial] Fornecedores importados/atualizados: {inserted}")
    return inserted


def import_roteiros_producao(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "roteiros_producao.csv")
    if not os.path.exists(path):
        print(f"[industrial] roteiros_producao.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, RoteiroProducao, df, "roteiro_id")
    print(f"[industrial] Roteiros importados/atualizados: {inserted}")
    return inserted


def import_operacoes_roteiro(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "operacoes_roteiro.csv")
    if not os.path.exists(path):
        print(f"[industrial] operacoes_roteiro.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, OperacaoRoteiro, df, "operacao_roteiro_id")
    print(f"[industrial] Operações de roteiro importadas/atualizadas: {inserted}")
    return inserted


def import_ordens_producao(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "ordens_producao.csv")
    if not os.path.exists(path):
        print(f"[industrial] ordens_producao.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, OrdemProducao, df, "ordem_producao_id")
    print(f"[industrial] Ordens de produção importadas/atualizadas: {inserted}")
    return inserted


def import_registros_operacao(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "registros_operacao.csv")
    if not os.path.exists(path):
        print(f"[industrial] registros_operacao.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, RegistroOperacao, df, "registro_id")
    print(f"[industrial] Registros de operação importados/atualizados: {inserted}")
    return inserted


def import_paradas_maquinas(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "paradas_maquinas.csv")
    if not os.path.exists(path):
        print(f"[industrial] paradas_maquinas.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, ParadaMaquina, df, "parada_id")
    print(f"[industrial] Paradas de máquinas importadas/atualizadas: {inserted}")
    return inserted


def import_lotes_materiais(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "lotes_materiais.csv")
    if not os.path.exists(path):
        print(f"[industrial] lotes_materiais.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, LoteMaterial, df, "lote_id")
    print(f"[industrial] Lotes de materiais importados/atualizados: {inserted}")
    return inserted


def import_lotes_producao(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "lotes_producao.csv")
    if not os.path.exists(path):
        print(f"[industrial] lotes_producao.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, LoteProducao, df, "lote_producao_id")
    print(f"[industrial] Lotes de produção importados/atualizados: {inserted}")
    return inserted


def import_consumo_materiais(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "consumo_materiais.csv")
    if not os.path.exists(path):
        print(f"[industrial] consumo_materiais.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, ConsumoMaterial, df, "consumo_id")
    print(f"[industrial] Consumo de materiais importado/atualizado: {inserted}")
    return inserted


def import_controle_qualidade(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "controle_qualidade.csv")
    if not os.path.exists(path):
        print(f"[industrial] controle_qualidade.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, ControleQualidade, df, "controle_id")
    print(f"[industrial] Controle de qualidade importado/atualizado: {inserted}")
    return inserted


def import_defeitos(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "defeitos.csv")
    if not os.path.exists(path):
        print(f"[industrial] defeitos.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, Defeito, df, "defeito_id")
    print(f"[industrial] Defeitos importados/atualizados: {inserted}")
    return inserted


def import_registros_defeitos(session: Session, base_dir: str) -> int:
    path = os.path.join(base_dir, "registros_defeitos.csv")
    if not os.path.exists(path):
        print(f"[industrial] registros_defeitos.csv não encontrado em {base_dir}")
        return 0
    df = _read_csv(path)
    inserted = _bulk_upsert(session, RegistroDefeito, df, "registro_defeito_id")
    print(f"[industrial] Registros de defeitos importados/atualizados: {inserted}")
    return inserted


def build_base_path(base: str, periodo: Optional[str]) -> str:
    if periodo:
        return os.path.join(
            base,
            f"dados_industriais_automotivo_eletronica_{periodo}",
        )
    # fallback: usa 2015_2017 por padrão
    return os.path.join(base, "dados_industriais_automotivo_eletronica_2015_2017")


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga de CSVs para o banco industrial")
    parser.add_argument("--base", default="BancoModeloUse/dados_simulados", help="Diretório base dos dados simulados")
    parser.add_argument("--periodo", default=None, help="Sufixo de período, ex: 2015_2017, 2017_2020, 2021_2025")
    parser.add_argument("--commit", action="store_true", help="Efetiva commit no final (senão faz rollback)")
    args = parser.parse_args()

    data_dir = build_base_path(args.base, args.periodo)
    print(f"[industrial] Lendo dados de: {data_dir}")

    engine = industrial_connection.get_engine()
    # Garante que as tabelas existam
    from BancoModeloUse.infrastructure.database.connections.industrial_connection import Base as IndustrialBase  # noqa: E402

    IndustrialBase.metadata.create_all(bind=engine)

    session: Session = industrial_connection.get_session()
    try:
        total = 0
        total += import_produtos(session, data_dir)
        total += import_materiais(session, data_dir)
        total += import_maquinas(session, data_dir)
        total += import_equipamentos(session, data_dir)
        total += import_processos_industriais(session, data_dir)
        total += import_fornecedores(session, data_dir)
        total += import_roteiros_producao(session, data_dir)
        total += import_operacoes_roteiro(session, data_dir)
        total += import_ordens_producao(session, data_dir)
        total += import_registros_operacao(session, data_dir)
        total += import_paradas_maquinas(session, data_dir)
        total += import_lotes_materiais(session, data_dir)
        total += import_lotes_producao(session, data_dir)
        total += import_consumo_materiais(session, data_dir)
        total += import_controle_qualidade(session, data_dir)
        total += import_defeitos(session, data_dir)
        total += import_registros_defeitos(session, data_dir)

        if args.commit:
            session.commit()
            print(f"[industrial] Commit realizado. Registros processados: {total}")
        else:
            session.rollback()
            print(f"[industrial] Rollback realizado (use --commit para gravar). Registros processados: {total}")
    except Exception as exc:
        session.rollback()
        print(f"[industrial] ERRO durante a carga: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
