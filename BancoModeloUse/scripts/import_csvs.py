#!/usr/bin/env python3
"""
Importador automático de CSVs para PostgreSQL usando SQLAlchemy e pandas.

- Detecta todos os CSVs no repositório
- Mapeia arquivo -> tabela por nome do arquivo
- Lê cabeçalho e confere com colunas do modelo ORM
- Sugere mapeamentos quando os nomes são semelhantes
- Insere no banco alvo (financeiro, industrial, dw) com deduplicação por PK
- Gera logs e relatório final (JSON e Markdown)

Uso (exemplos):
  python scripts/import_csvs.py --dry-run                 # Apenas valida e gera relatório
  python scripts/import_csvs.py --execute                 # Executa inserções de fato
  python scripts/import_csvs.py --root /workspace         # Define a raiz a escanear
  python scripts/import_csvs.py --include BancoModeloUse/dados_simulados  

Requisitos: pandas, SQLAlchemy, psycopg2-binary
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import logging
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
import unicodedata

# Terceiros
import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Permite imports relativos ao projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
sys.path.append(PROJECT_ROOT)

# Infraestrutura de bancos e modelos
from infrastructure.config.database_config import (
    FINANCEIRO_DB_CONFIG,
    INDUSTRIAL_DB_CONFIG,
    DW_DB_CONFIG,
)

# Conexões (cada uma define seu Base distinto)
from infrastructure.database.connections.financeiro_connection import Base as FinanceiroBase, financeiro_connection
from infrastructure.database.connections.industrial_connection import Base as IndustrialBase, industrial_connection
from infrastructure.database.connections.dw_connection import Base as DWBase, dw_connection

# Importa todos os modelos para registrar no metadata de cada Base
import core.models.financeiro.custos  # noqa: F401
import core.models.financeiro.contabil  # noqa: F401
import core.models.financeiro.vendas  # noqa: F401
import core.models.financeiro.kpis  # noqa: F401

import core.models.industrial.cadastros  # noqa: F401
import core.models.industrial.producao  # noqa: F401
import core.models.industrial.equipamentos  # noqa: F401
import core.models.industrial.qualidade  # noqa: F401

import core.models.dw.dimensoes  # noqa: F401
import core.models.dw.fatos  # noqa: F401
import core.models.dw.agregados  # noqa: F401


# --------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------

def setup_logging(log_dir: str) -> None:
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "import_csvs.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def normalize_name(name: str) -> str:
    # minusculo, sem acentos, somente letras/numeros/underscore
    nfkd = unicodedata.normalize("NFKD", name.strip().lower())
    only_ascii = nfkd.encode("ASCII", "ignore").decode("ASCII")
    cleaned = re.sub(r"[^a-z0-9_]+", "_", only_ascii)
    return re.sub(r"_+", "_", cleaned).strip("_")


def detect_delimiter(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sample = f.read(4096)
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except Exception:
        return ","


# --------------------------------------------------------------------------------------
# ORM / Metadata
# --------------------------------------------------------------------------------------

class DBContext:
    def __init__(self, name: str, base, engine: Engine):
        self.name = name
        self.base = base
        self.engine = engine
        self.metadata: MetaData = base.metadata

    def table_info(self) -> Dict[str, Dict]:
        info = {}
        for table_name, table in self.metadata.tables.items():
            columns = [col.name for col in table.columns]
            pk_cols = [col.name for col in table.primary_key.columns]
            nullable_map = {col.name: bool(col.nullable) for col in table.columns}
            fks = []
            for col in table.columns:
                for fk in col.foreign_keys:
                    try:
                        # form: <ForeignKey at 0x..; table.column>
                        ref_table = fk.column.table.name
                        ref_col = fk.column.name
                        fks.append({"column": col.name, "ref_table": ref_table, "ref_column": ref_col})
                    except Exception:
                        pass
            info[table_name] = {
                "db": self.name,
                "columns": columns,
                "pk": pk_cols,
                "nullable": nullable_map,
                "foreign_keys": fks,
                "table_obj": table,
            }
        return info


def build_db_contexts() -> Dict[str, DBContext]:
    contexts: Dict[str, DBContext] = {
        "financeiro": DBContext("financeiro", FinanceiroBase, financeiro_connection.get_engine()),
        "industrial": DBContext("industrial", IndustrialBase, industrial_connection.get_engine()),
        "dw": DBContext("dw", DWBase, dw_connection.get_engine()),
    }
    return contexts


# --------------------------------------------------------------------------------------
# CSV Scanning & Matching
# --------------------------------------------------------------------------------------

CSV_IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
}


def find_csv_files(root: str, include_path: Optional[str] = None) -> List[str]:
    files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # filtra diretorios ignorados
        dirnames[:] = [d for d in dirnames if d not in CSV_IGNORE_DIRS]
        rel = os.path.relpath(dirpath, root)
        if include_path and include_path not in os.path.join(rel, ""):  # substring
            continue
        for fn in filenames:
            if fn.lower().endswith(".csv"):
                files.append(os.path.join(dirpath, fn))
    files.sort()
    return files


def suggest_mappings(csv_cols: List[str], model_cols: List[str]) -> List[Tuple[str, str, float]]:
    suggestions: List[Tuple[str, str, float]] = []
    norm_model = {normalize_name(c): c for c in model_cols}
    for c in csv_cols:
        nc = normalize_name(c)
        if nc in norm_model:
            continue
        # procura o mais parecido
        matches = difflib.get_close_matches(nc, list(norm_model.keys()), n=1, cutoff=0.75)
        if matches:
            best = matches[0]
            ratio = difflib.SequenceMatcher(None, nc, best).ratio()
            suggestions.append((c, norm_model[best], ratio))
    return suggestions


def columns_compatible(csv_cols: List[str], model_info: Dict) -> Tuple[bool, List[str], List[str]]:
    model_cols = model_info["columns"]
    model_nullable = model_info["nullable"]
    csv_set = {normalize_name(c) for c in csv_cols}
    model_set = {normalize_name(c) for c in model_cols}

    exact = csv_set == model_set
    if exact:
        return True, [], []

    # Subconjunto (permitido se colunas ausentes forem nulas ou default)
    missing_in_csv = [c for c in model_cols if normalize_name(c) not in csv_set]
    extra_in_csv = [c for c in csv_cols if normalize_name(c) not in model_set]

    # checa nulabilidade dos faltantes
    missing_blockers = []
    for c in missing_in_csv:
        if not model_nullable.get(c, True):
            missing_blockers.append(c)

    compatible = len(missing_blockers) == 0
    return compatible, missing_in_csv, extra_in_csv


# --------------------------------------------------------------------------------------
# Inserção
# --------------------------------------------------------------------------------------

class InsertResult:
    def __init__(self):
        self.rows_total: int = 0
        self.rows_inserted: int = 0
        self.rows_skipped_duplicates: int = 0


def insert_dataframe(
    df: pd.DataFrame,
    model_info: Dict,
    engine: Engine,
    dry_run: bool,
) -> InsertResult:
    result = InsertResult()
    result.rows_total = len(df)

    table: Table = model_info["table_obj"]
    pk_cols: List[str] = model_info["pk"]

    if result.rows_total == 0:
        return result

    # Reordena colunas e adiciona ausentes como None
    desired_cols = [c.name for c in table.columns]
    for c in desired_cols:
        if c not in df.columns:
            df[c] = None
    df = df[desired_cols]

    if dry_run:
        # Em dry-run, não insere, apenas sinaliza que poderia inserir
        return result

    try:
        with engine.begin() as conn:
            if pk_cols:
                # Usa upsert DO NOTHING para evitar duplicatas por PK
                chunk_size = 1000
                for start in range(0, len(df), chunk_size):
                    chunk = df.iloc[start : start + chunk_size]
                    payload = chunk.to_dict(orient="records")
                    if not payload:
                        continue
                    stmt = pg_insert(table).values(payload)
                    stmt = stmt.on_conflict_do_nothing(index_elements=pk_cols)
                    res = conn.execute(stmt)
                    # res.rowcount pode ser -1 dependendo do driver; conta aproximada
                    # Reconsulta contagem inserida comparando tentativas vs afetadas não é trivial.
                    # Assumimos que conflitos são ignorados; para relatório, estimamos via checagem explícita abaixo (opcional).
                # Para estimar inseridos, contamos total - duplicados detectados por PK presentes
                # Estratégia: buscar PKs existentes do chunk e comparar
                # Para performance em datasets grandes, pular estimativa precisa e manter inserted desconhecido.
                # Aqui, manteremos inserted como desconhecido; usuário pode consultar no banco.
                # Como alternativa, poderíamos contar afetados se o driver suportar.
                result.rows_inserted = 0  # indeterminado
            else:
                df.to_sql(table.name, conn, if_exists="append", index=False, method="multi", chunksize=1000)
                result.rows_inserted = len(df)
    except Exception as e:
        logging.error(f"Falha ao inserir na tabela {table.name}: {e}")
        raise

    return result


# --------------------------------------------------------------------------------------
# Relatórios
# --------------------------------------------------------------------------------------

def save_reports(report: Dict, reports_dir: str) -> None:
    os.makedirs(reports_dir, exist_ok=True)
    # JSON
    json_path = os.path.join(reports_dir, "import_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    # Markdown
    md_path = os.path.join(reports_dir, "import_report.md")
    lines: List[str] = []
    lines.append(f"# Relatório de Importação - {datetime.utcnow().isoformat()} UTC\n")
    lines.append(f"- Modo: {'Dry-Run' if report.get('dry_run') else 'Execução'}\n")
    lines.append(f"- CSVs encontrados: {report.get('num_csvs_found', 0)}\n")
    lines.append(f"- CSVs processados: {len(report.get('files', []))}\n")
    ok = [f for f in report.get('files', []) if f.get('status') == 'ok']
    err = [f for f in report.get('files', []) if f.get('status') == 'error']
    skip = [f for f in report.get('files', []) if f.get('status') == 'skipped']
    lines.append(f"- Sucessos: {len(ok)} | Skips: {len(skip)} | Erros: {len(err)}\n")
    lines.append("\n## Detalhes por arquivo\n")
    for f in report.get("files", []):
        lines.append(f"### {f['file']}\n")
        lines.append(f"- Status: {f.get('status')}\n")
        if f.get("target_table"):
            lines.append(f"- Tabela alvo: `{f['target_table']}` ({f.get('target_db')})\n")
        if f.get("csv_columns"):
            lines.append(f"- Colunas CSV: {', '.join(f['csv_columns'])}\n")
        if f.get("model_columns"):
            lines.append(f"- Colunas modelo: {', '.join(f['model_columns'])}\n")
        if f.get("missing_in_csv"):
            lines.append(f"- Faltando no CSV: {', '.join(f['missing_in_csv'])}\n")
        if f.get("extra_in_csv"):
            lines.append(f"- Extras no CSV: {', '.join(f['extra_in_csv'])}\n")
        if f.get("suggestions"):
            lines.append("- Sugestões de mapeamento:\n")
            for s in f["suggestions"]:
                lines.append(f"  - '{s[0]}' -> '{s[1]}' (similaridade {s[2]:.2f})\n")
        if f.get("error"):
            lines.append(f"- Erro: {f['error']}\n")
        if f.get("rows_total") is not None:
            lines.append(f"- Linhas no CSV: {f['rows_total']}\n")
        if f.get("rows_inserted") is not None:
            lines.append(f"- Linhas inseridas: {f['rows_inserted']}\n")
        if f.get("rows_skipped_duplicates") is not None:
            lines.append(f"- Duplicatas ignoradas: {f['rows_skipped_duplicates']}\n")
        lines.append("\n")

    if report.get("tables_updated"):
        lines.append("## Tabelas atualizadas\n")
        for t, v in report["tables_updated"].items():
            lines.append(f"- `{t}`: +{v} linhas\n")
        lines.append("\n")

    if report.get("errors"):
        lines.append("## Erros gerais\n")
        for e in report["errors"]:
            lines.append(f"- {e}\n")
        lines.append("\n")

    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


# --------------------------------------------------------------------------------------
# Fluxo principal
# --------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Importador automático de CSVs para os bancos financeiro/industrial/dw")
    parser.add_argument("--root", default=REPO_ROOT, help="Raiz do repositório para busca de CSVs")
    parser.add_argument("--include", default=None, help="Substring de caminho para filtrar CSVs (opcional)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", dest="dry_run", action="store_true", help="Apenas valida e gera relatório (default)")
    mode.add_argument("--execute", dest="dry_run", action="store_false", help="Executa inserções")
    parser.set_defaults(dry_run=True)

    args = parser.parse_args()

    logs_dir = os.path.join(PROJECT_ROOT, "scripts", "logs")
    reports_dir = os.path.join(PROJECT_ROOT, "scripts", "reports")
    setup_logging(logs_dir)

    logging.info("Inicializando mapeamento de metadados ORM...")
    contexts = build_db_contexts()
    table_index: Dict[str, Dict] = {}
    for db_name, ctx in contexts.items():
        for tname, info in ctx.table_info().items():
            table_index[tname] = info

    logging.info("Buscando arquivos CSV...")
    csv_files = find_csv_files(args.root, include_path=args.include)

    report: Dict = {
        "started_at": datetime.utcnow().isoformat() + "Z",
        "dry_run": args.dry_run,
        "num_csvs_found": len(csv_files),
        "files": [],
        "tables_updated": defaultdict(int),
        "errors": [],
    }

    # Testa conexões apenas se não for dry-run
    engines_ok: Dict[str, bool] = {"financeiro": False, "industrial": False, "dw": False}
    if not args.dry_run:
        for db_name, ctx in contexts.items():
            try:
                with ctx.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                engines_ok[db_name] = True
            except Exception as e:
                logging.error(f"Sem conexão com banco {db_name}: {e}")
                report["errors"].append(f"Banco {db_name} indisponível: {e}")

    for fpath in csv_files:
        entry = {
            "file": os.path.relpath(fpath, REPO_ROOT),
            "status": None,
            "target_table": None,
            "target_db": None,
            "csv_columns": None,
            "model_columns": None,
            "missing_in_csv": None,
            "extra_in_csv": None,
            "suggestions": None,
            "rows_total": None,
            "rows_inserted": None,
            "rows_skipped_duplicates": None,
            "error": None,
        }

        try:
            base_name = os.path.basename(fpath)
            table_candidate = os.path.splitext(base_name)[0]
            table_candidate_norm = normalize_name(table_candidate)

            # Confere se existe tabela com mesmo nome (normalizado)
            # Preferência por nome exato primeiro
            if table_candidate in table_index:
                table_name = table_candidate
            else:
                # tenta normalizado
                matches = [t for t in table_index.keys() if normalize_name(t) == table_candidate_norm]
                table_name = matches[0] if matches else None

            if not table_name:
                entry["status"] = "skipped"
                entry["error"] = "Nenhuma tabela ORM correspondente encontrada pelo nome do arquivo"
                report["files"].append(entry)
                continue

            model_info = table_index[table_name]
            entry["target_table"] = table_name
            entry["target_db"] = model_info["db"]
            entry["model_columns"] = model_info["columns"]

            # Lê cabeçalho
            delimiter = detect_delimiter(fpath)
            df_head = pd.read_csv(fpath, delimiter=delimiter, nrows=0)
            csv_cols = list(df_head.columns)
            entry["csv_columns"] = csv_cols

            compatible, missing, extra = columns_compatible(csv_cols, model_info)
            entry["missing_in_csv"] = missing
            entry["extra_in_csv"] = extra
            entry["suggestions"] = suggest_mappings(csv_cols, model_info["columns"]) if not compatible else []

            if not compatible:
                entry["status"] = "skipped"
                entry["error"] = "Colunas incompatíveis entre CSV e modelo ORM"
                report["files"].append(entry)
                continue

            # Lê dados completos (com tipos automáticos do pandas)
            df = pd.read_csv(fpath, delimiter=delimiter)
            entry["rows_total"] = len(df)

            # Insere ou faz dry-run
            db_name = model_info["db"]
            engine = contexts[db_name].engine

            if not args.dry_run and not engines_ok.get(db_name, False):
                entry["status"] = "error"
                entry["error"] = f"Sem conexão com banco {db_name}"
                report["files"].append(entry)
                continue

            try:
                ins_res = insert_dataframe(df, model_info, engine, dry_run=args.dry_run)
                entry["rows_inserted"] = ins_res.rows_inserted
                entry["rows_skipped_duplicates"] = ins_res.rows_skipped_duplicates
                entry["status"] = "ok"
                if not args.dry_run:
                    report["tables_updated"][table_name] += entry["rows_inserted"] or 0
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)

            report["files"].append(entry)

        except Exception as e:
            entry["status"] = "error"
            entry["error"] = str(e)
            report["files"].append(entry)

    report["finished_at"] = datetime.utcnow().isoformat() + "Z"

    # Salva relatórios
    save_reports(report, reports_dir)

    # Sinaliza preparação da DW (criação de tabelas) se possível
    # Em dry-run apenas registra intenção
    try:
        if args.dry_run:
            logging.info("Dry-run: preparação da DW (db_datamind_dw) será realizada em execução real.")
        else:
            # Tenta criar/atualizar tabelas da DW
            DWBase.metadata.create_all(bind=contexts["dw"].engine)
            logging.info("DW preparada (tabelas criadas/atualizadas).")
    except Exception as e:
        logging.error(f"Falha na preparação da DW: {e}")
        report["errors"].append(f"Falha na preparação da DW: {e}")
        save_reports(report, reports_dir)

    logging.info("Relatórios gerados em scripts/reports/")


if __name__ == "__main__":
    sys.exit(main())
