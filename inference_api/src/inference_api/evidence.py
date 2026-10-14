"""Deterministic read-only data agents and evidence assembly."""
from contextlib import closing

import psycopg2

from .config import db_params
from .contracts import EvidenceBundle, EvidenceItem, RoutePlan, SCHEMA_VERSION


# This backend allowlist is the only source of SQL for exploratory requests.
QUERIES = {
    "financeiro_vendas_ano": {
        "domain": "FINANCEIRO", "table": "public.vendas",
        "fields": ("data_venda", "quantidade_vendida", "preco_unitario_venda"),
        "statement": "SELECT count(*) AS registros, coalesce(sum(quantidade_vendida * preco_unitario_venda), 0) AS valor FROM public.vendas WHERE data_venda >= make_date(%s, 1, 1) AND data_venda < make_date(%s + 1, 1, 1)",
        "unit": "BRL", "formula": "sum(quantidade_vendida * preco_unitario_venda)",
        "limitation": "Soma de vendas disponíveis; não equivale necessariamente à receita contábil.",
    },
    "industrial_operacoes_ano": {
        "domain": "INDUSTRIAL", "table": "public.registros_operacao",
        "fields": ("hora_inicio", "quantidade_produzida_real"),
        "statement": "SELECT count(*) AS registros, coalesce(sum(quantidade_produzida_real), 0) AS valor FROM public.registros_operacao WHERE hora_inicio >= make_date(%s, 1, 1) AND hora_inicio < make_date(%s + 1, 1, 1)",
        "unit": "unidades registradas", "formula": "sum(quantidade_produzida_real)",
        "limitation": "Soma de registros de operação; pode duplicar etapas de produção.",
    },
}


class SourceQueryError(RuntimeError):
    def __init__(self, tool: str, cause: Exception):
        super().__init__(f"Source query failed for {tool}: {type(cause).__name__}")
        self.tool = tool
        self.cause_type = type(cause).__name__


def _query(tool: str, year: int) -> EvidenceItem:
    if tool not in QUERIES or type(year) is not int or not 2015 <= year <= 2026:
        raise ValueError("Unknown tool or invalid year")
    spec = QUERIES[tool]
    try:
        with closing(psycopg2.connect(**db_params(spec["domain"]))) as connection, connection:
            connection.set_session(readonly=True, autocommit=False)
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = '5s'")
                cursor.execute(spec["statement"], (year, year))
                row = cursor.fetchone()
    except Exception as exc:
        raise SourceQueryError(tool, exc) from exc
    if row is None:
        raise SourceQueryError(tool, RuntimeError("Missing aggregate row"))
    count, value = row
    return EvidenceItem(
        schema_version=SCHEMA_VERSION, id=f"{tool}:{year}", tool=tool,
        source_database="db_" + spec["domain"].lower(), source_table=spec["table"],
        source_fields=spec["fields"], filters={"year": year}, period={"year": year},
        granularity="annual aggregate of source records", unit=spec["unit"],
        value=str(value if value is not None else 0), record_count=int(count),
        formula=spec["formula"], query_template=spec["statement"],
        query_parameters=(year, year), quality="available" if count else "absent",
        limitation=spec["limitation"],
    )


def financial_agent(year: int) -> EvidenceItem:
    return _query("financeiro_vendas_ano", year)


def industrial_agent(year: int) -> EvidenceItem:
    return _query("industrial_operacoes_ano", year)


AGENTS = {
    "financeiro_vendas_ano": financial_agent,
    "industrial_operacoes_ano": industrial_agent,
}


def assemble(plan: RoutePlan) -> EvidenceBundle:
    items = tuple(AGENTS[tool](plan.year) for tool in plan.tools)
    return EvidenceBundle(
        schema_version=SCHEMA_VERSION, route=plan, items=items,
        quality="available" if all(item.record_count > 0 for item in items) else "insufficient_evidence",
        limitations=tuple(item.limitation for item in items) +
                    ((plan.limitation,) if plan.limitation else ()),
    )
