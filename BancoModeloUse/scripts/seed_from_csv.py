#!/usr/bin/env python3
"""
Carrega dados simulados a partir de arquivos CSV para as tabelas do banco,
assumindo que os nomes das colunas do CSV correspondem aos nomes das colunas
no ORM/SQLAlchemy.

- Descobre as tabelas pelo Base.metadata
- Ordena inserções respeitando dependências de chaves estrangeiras
- Lê um CSV por tabela (nome do arquivo igual ao __tablename__, ex.: produtos.csv)
- Faz coerção básica de tipos (int, Decimal, date, datetime)
- Suporta limpeza prévia das tabelas em ordem segura

Uso:
  python BancoModeloUse/scripts/seed_from_csv.py --data-dir ./data --truncate

Requisitos dos CSVs:
  - Um arquivo CSV por tabela com nome "<__tablename__>.csv"
  - Cabeçalho com nomes de colunas iguais aos das tabelas
  - Delimitador padrão ',', encoding UTF-8 (configuráveis)
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable, List, Optional, Set, Tuple

# Ajusta o PYTHONPATH para permitir imports relativos ao projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

# SQLAlchemy
from sqlalchemy import Table
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Infra do projeto
from infrastructure.database.session import Base, SessionLocal, engine  # type: ignore

# Tipos do SQLAlchemy
from sqlalchemy import Integer as SAInteger
from sqlalchemy import String as SAString
from sqlalchemy import Text as SAText
from sqlalchemy import Date as SADate
from sqlalchemy import DateTime as SADateTime
from sqlalchemy import DECIMAL as SADECIMAL
from sqlalchemy import Boolean as SABoolean


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("seed_from_csv")


@dataclass(frozen=True)
class LoadPlan:
    ordered_table_names: List[str]
    reverse_ordered_table_names: List[str]


def _detect_dependencies(metadata_tables: Dict[str, Table]) -> Dict[str, Set[str]]:
    """Retorna um grafo de dependências: {tabela: {tabelas_das_quais_depende}}.

    Usa chaves estrangeiras declaradas nas colunas. Tabelas sem FKs terão dependência vazia.
    """
    dependencies: Dict[str, Set[str]] = {name: set() for name in metadata_tables.keys()}
    for table_name, table in metadata_tables.items():
        for column in table.columns:
            for fk in column.foreign_keys:
                parent_table = fk.column.table.name
                if parent_table != table_name:
                    dependencies[table_name].add(parent_table)
    return dependencies


def _topological_order(dependencies: Dict[str, Set[str]]) -> List[str]:
    """Ordena as tabelas para inserção (pais antes de filhos)."""
    # Kahn's algorithm
    deps_copy: Dict[str, Set[str]] = {k: set(v) for k, v in dependencies.items()}
    all_tables: Set[str] = set(dependencies.keys())
    dependents: Dict[str, Set[str]] = {t: set() for t in all_tables}
    for child, parents in dependencies.items():
        for parent in parents:
            dependents.setdefault(parent, set()).add(child)

    order: List[str] = []
    ready: List[str] = sorted([t for t, parents in deps_copy.items() if not parents])

    while ready:
        current = ready.pop(0)
        order.append(current)
        for child in sorted(dependents.get(current, [])):
            if current in deps_copy[child]:
                deps_copy[child].remove(current)
                if not deps_copy[child]:
                    ready.append(child)

    if len(order) != len(all_tables):
        # Ciclos (não esperado se FKs estiverem corretas). Ainda assim, adiciona o restante de forma estável.
        missing = list(all_tables - set(order))
        logger.warning("Ciclo detectado ou dependências faltantes; anexando tabelas restantes: %s", missing)
        order.extend(sorted(missing))

    return order


def build_load_plan() -> LoadPlan:
    """Constroi o plano de carga com base nas tabelas do metadata."""
    metadata_tables: Dict[str, Table] = dict(Base.metadata.tables)
    dependencies = _detect_dependencies(metadata_tables)
    ordered = _topological_order(dependencies)
    reverse_ordered = list(reversed(ordered))
    return LoadPlan(ordered_table_names=ordered, reverse_ordered_table_names=reverse_ordered)


def _coerce_value(value: str, column_type) -> Optional[object]:
    """Converte string para o tipo Python adequado conforme o tipo da coluna."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
    if value == "" or value.lower() in {"null", "none", "na", "n/a"}:
        return None

    # Integer
    if isinstance(column_type, SAInteger):
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Valor inválido para Integer: {value!r}")

    # Boolean
    if isinstance(column_type, SABoolean):
        if isinstance(value, bool):
            return value
        lowered = str(value).lower()
        if lowered in {"true", "t", "1", "yes", "y"}:
            return True
        if lowered in {"false", "f", "0", "no", "n"}:
            return False
        raise ValueError(f"Valor inválido para Boolean: {value!r}")

    # Decimal
    if isinstance(column_type, SADECIMAL):
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(f"Valor inválido para Decimal: {value!r}")

    # Date
    if isinstance(column_type, SADate):
        # Suporta formatos comuns
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(str(value), fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Valor inválido para Date: {value!r}. Formatos aceitos: YYYY-MM-DD, DD/MM/YYYY")

    # DateTime
    if isinstance(column_type, SADateTime):
        # Formatos comuns com/sem segundos
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        # ISO 8601
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            pass
        raise ValueError(
            f"Valor inválido para DateTime: {value!r}. Use ISO 8601 ou formatos comuns (YYYY-MM-DD HH:MM[:SS])"
        )

    # String/Text – mantém como está
    if isinstance(column_type, (SAString, SAText)):
        return str(value)

    # Fallback: retorna a string original
    return value


def _read_csv_rows(csv_path: str, delimiter: str, encoding: str) -> Tuple[List[str], Iterable[Dict[str, str]]]:
    with open(csv_path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = reader.fieldnames or []
        return headers, reader


def _find_csv_for_table(data_dir: str, table_name: str) -> Optional[str]:
    """Procura arquivo CSV cujo nome base case-insensitive seja o nome da tabela."""
    candidates = []
    for entry in os.listdir(data_dir):
        if not entry.lower().endswith(".csv"):
            continue
        name_no_ext = os.path.splitext(entry)[0].lower()
        if name_no_ext == table_name.lower():
            candidates.append(os.path.join(data_dir, entry))
    if not candidates:
        return None
    # Se houver múltiplos com o mesmo nome base (diferenças de case), pega o primeiro ordenado
    return sorted(candidates)[0]


def _filter_and_coerce_row(table: Table, row: Dict[str, str]) -> Dict[str, object]:
    """Mantém apenas colunas existentes na tabela e faz coerção de tipos."""
    result: Dict[str, object] = {}
    for column in table.columns:
        col_name = column.name
        if col_name in row:
            value = row[col_name]
            result[col_name] = _coerce_value(value, column.type)
    return result


def insert_rows_for_table(session: Session, table: Table, rows: Iterable[Dict[str, str]]) -> int:
    """Insere linhas usando INSERT em bloco. Retorna número de linhas inseridas.

    Linhas com todos os campos vazios/None são ignoradas.
    """
    prepared: List[Dict[str, object]] = []
    for row in rows:
        mapped = _filter_and_coerce_row(table, row)
        if not mapped:
            continue
        # Se todas as colunas estão None/vazias, ignora
        if all(v is None or (isinstance(v, str) and v.strip() == "") for v in mapped.values()):
            continue
        prepared.append(mapped)

    if not prepared:
        return 0

    session.execute(table.insert(), prepared)
    return len(prepared)


def truncate_tables(engine: Engine, plan: LoadPlan) -> None:
    """Limpa as tabelas em ordem reversa para respeitar FKs.

    Usa DELETE por compatibilidade. Se quiser TRUNCATE CASCADE, adapte para Postgres.
    """
    with engine.begin() as connection:
        for table_name in plan.reverse_ordered_table_names:
            table = Base.metadata.tables[table_name]
            logger.info("Limpando tabela: %s", table_name)
            connection.execute(table.delete())


def load_from_directory(data_dir: str, delimiter: str, encoding: str, truncate: bool, only_tables: Optional[List[str]]) -> None:
    plan = build_load_plan()

    # Se limitar por tabelas, filtra e mantém ordem relativa
    ordered_tables = plan.ordered_table_names
    if only_tables:
        only_set = {t.lower() for t in only_tables}
        ordered_tables = [t for t in ordered_tables if t.lower() in only_set]
        if not ordered_tables:
            logger.warning("Nenhuma tabela do filtro foi encontrada no metadata: %s", only_tables)

    if truncate:
        logger.info("--truncate habilitado: iniciando limpeza das tabelas")
        truncate_plan = LoadPlan(ordered_table_names=ordered_tables, reverse_ordered_table_names=list(reversed(ordered_tables)))
        truncate_tables(engine, truncate_plan)

    total_inserted = 0
    not_found: List[str] = []

    with SessionLocal() as session:
        try:
            for table_name in ordered_tables:
                csv_path = _find_csv_for_table(data_dir, table_name)
                if not csv_path:
                    not_found.append(table_name)
                    logger.info("CSV não encontrado para a tabela '%s' (esperado: %s/<tabela>.csv)", table_name, data_dir)
                    continue

                table = Base.metadata.tables[table_name]
                logger.info("Carregando %s de %s", table_name, csv_path)
                headers, reader = _read_csv_rows(csv_path, delimiter, encoding)

                # Log de diagnóstico de colunas que não existem na tabela
                extra_headers = [h for h in headers if h not in table.columns]
                missing_headers = [c.name for c in table.columns if c.name not in headers]
                if extra_headers:
                    logger.warning("CSV '%s' possui colunas não mapeadas (serão ignoradas): %s", csv_path, extra_headers)
                if missing_headers:
                    logger.info("CSV '%s' está sem algumas colunas da tabela (serão None/default): %s", csv_path, missing_headers)

                inserted = insert_rows_for_table(session, table, reader)
                total_inserted += inserted
                logger.info("Inseridas %d linhas em %s", inserted, table_name)

            session.commit()
            logger.info("Carga concluída com sucesso. Total inserido: %d", total_inserted)

            if not_found:
                logger.info("Sem CSV para %d tabela(s): %s", len(not_found), not_found)

        except SQLAlchemyError as e:
            session.rollback()
            logger.exception("Erro de banco ao inserir dados: %s", e)
            raise
        except Exception as e:
            session.rollback()
            logger.exception("Erro inesperado: %s", e)
            raise


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Carrega dados de CSVs para o banco, por tabela.")
    parser.add_argument("--data-dir", default=os.path.join(PROJECT_ROOT, "data"), help="Diretório com CSVs (<tabela>.csv)")
    parser.add_argument("--delimiter", default=",", help="Delimitador do CSV (padrão: ',')")
    parser.add_argument("--encoding", default="utf-8", help="Encoding do CSV (padrão: utf-8)")
    parser.add_argument("--truncate", action="store_true", help="Limpa as tabelas antes de inserir")
    parser.add_argument("--tables", nargs="*", help="Lista de tabelas a carregar (opcional)")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        logger.error("Diretório de dados não encontrado: %s", data_dir)
        return 2

    logger.info("Usando data-dir: %s", data_dir)
    try:
        load_from_directory(
            data_dir=data_dir,
            delimiter=args.delimiter,
            encoding=args.encoding,
            truncate=bool(args.truncate),
            only_tables=args.tables,
        )
        return 0
    except Exception:
        # Logs já emitidos
        return 1


if __name__ == "__main__":
    sys.exit(main())
