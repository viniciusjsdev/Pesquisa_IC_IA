"""Local, read-only SPEC-013 query adapter for an approved pilot catalog.

The model supplies a typed plan, never SQL. This adapter is intentionally not
reachable from the Bancada provider mode while semantic approval is pending.
"""

from __future__ import annotations

from contextlib import closing
import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import re

import psycopg2
from psycopg2 import sql

from .typed_detail import DetailRejected, execute as execute_detail
from .. import dw_tools


ROOT = Path(__file__).resolve().parents[4]
READER_CREDENTIALS = ROOT / "inference_api/.local/spec013_reader_credentials.json"
CATALOG_PATH = ROOT / "specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json"
DATA_CONTRACT_PATH = Path(__file__).parent / "data_contracts.json"
DATA_CONTRACT_BYTES = DATA_CONTRACT_PATH.read_bytes()
DATA_CONTRACT = json.loads(DATA_CONTRACT_BYTES)
DATA_CONTRACT_SHA256 = hashlib.sha256(DATA_CONTRACT_BYTES).hexdigest()
FIXED = set(DATA_CONTRACT["fixed_output_fields"])
LINEAGE_FACTS = {
    "machine": (("fact_operation", "operation_id", "machine_id", "operation_day"),
                ("fact_downtime", "downtime_id", "machine_id", "start_day")),
    "product": (("fact_operation", "operation_id", "product_id", "operation_day"),
                ("fact_sale", "sale_id", "product_id", "sale_day")),
    "quality": (("fact_quality_inspection", "inspection_id", "product_id", "inspection_day"),),
    "material": (("fact_material_consumption", "consumption_id", "material_id", "registered_day"),
                 ("fact_material_price_observation", "price_observation_id", "material_id", "purchase_day")),
}
TRACE_PKS = {"fact_operation": "operation_id", "fact_downtime": "downtime_id",
             "fact_sale": "sale_id", "fact_financial_observation": "observation_id",
             "fact_quality_inspection": "inspection_id",
             "fact_material_consumption": "consumption_id",
             "fact_material_price_observation": "price_observation_id"}
LINEAGE_FIELDS = {name: item["fields"] for name, item in DATA_CONTRACT["lineage"].items()}
PLAN_KEYS = {"fonte_id", "campos", "filtros", "limite", "grao"}


class LocalQueryRejected(ValueError):
    """A typed plan, catalog, privilege, or physical version was rejected."""


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise LocalQueryRejected(reason)


def _reader() -> dict:
    path = READER_CREDENTIALS.resolve()
    _require(path.is_relative_to((ROOT / "inference_api/.local").resolve()) and
             path.is_file(), "reader_credentials_unavailable")
    credentials = json.loads(path.read_text(encoding="utf-8"))
    _require(credentials.get("user") == "spec013_reader" and
             credentials.get("host") == "127.0.0.1" and
             credentials.get("port") == 5544 and
             isinstance(credentials.get("password"), str) and
             bool(credentials["password"]), "reader_credentials_invalid")
    return credentials


def _connect(database: str):
    _require(database in {"db_pesquisa_dw", "db_industrial", "db_financeiro"},
             "source_database_not_allowed")
    return psycopg2.connect(**_reader(), dbname=database, connect_timeout=3)


def source_fingerprints(catalog: dict) -> dict:
    """Read route-independent manifests; never expose credentials or file paths."""
    try:
        _validate_catalog_base(catalog)
        domains = {}
        for domain in ('industrial', 'financeiro'):
            definition = catalog['domains'][domain]
            tables = sorted(name for name, source in definition['sources'].items()
                            if source.get('enabled'))
            with closing(_connect(definition['database'])) as connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute('SET TRANSACTION READ ONLY')
                        cursor.execute("SELECT set_config('statement_timeout', '10000', true)")
                        cursor.execute('SELECT current_database()')
                        _require(cursor.fetchone()[0] == definition['database'], 'source_database_mismatch')
                        cursor.execute('SELECT table_name, period_index, sha256 FROM public.canonical_source_file '
                                       'WHERE table_name = ANY(%s) ORDER BY table_name, period_index', (tables,))
                        files = [{'table': table, 'period': period, 'sha256': digest.strip()}
                                 for table, period, digest in cursor.fetchall()]
                        _require({item['table'] for item in files} == set(tables), 'source_files_unavailable')
                    domains[domain] = {'database': definition['database'], 'files': files,
                        'sha256': hashlib.sha256(json.dumps(files, sort_keys=True,
                                                           separators=(',', ':')).encode()).hexdigest()}
                finally:
                    connection.rollback()
        return {'status': 'recorded', 'policy': 'canonical_source_file_v1', 'domains': domains}
    except Exception as exc:
        # Diagnostic metadata must not erase a completed model run or authorize a retry.
        return {'status': 'unavailable', 'error_type': type(exc).__name__}


def _validate_catalog_base(catalog: dict) -> None:
    if hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest() != DATA_CONTRACT["catalog_sha256"]:
        raise LocalQueryRejected("catalog_file_hash_mismatch")
    if (hashlib.sha256(Path(dw_tools.fixed_queries.__file__).read_bytes()).hexdigest() !=
            DATA_CONTRACT["dw_query_code_sha256"]):
        raise LocalQueryRejected("dw_query_code_hash_mismatch")
    original = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    comparison = copy.deepcopy(catalog)
    comparison["status"] = "candidate_not_enabled"
    for domain in comparison.get("domains", {}).values():
        for source in domain.get("sources", {}).values():
            source["enabled"] = False
    if comparison != original:
        raise LocalQueryRejected("catalog_content_drift")


def _validate(plan: dict, catalog: dict) -> tuple[str, dict]:
    _require(isinstance(catalog, dict) and
             catalog.get("status") == "approved_for_local_query",
             "catalog_not_approved_for_local_query")
    _validate_catalog_base(catalog)
    _require(isinstance(plan, dict) and set(plan) == PLAN_KEYS,
             "invalid_typed_plan")
    source_id = plan["fonte_id"]
    matches = [(domain, source) for domain, domain_map in catalog.get("domains", {}).items()
               for candidate, source in domain_map.get("sources", {}).items()
               if candidate == source_id]
    _require(len(matches) == 1 and matches[0][1].get("enabled") is True,
             "source_not_enabled")
    domain, source = matches[0]
    fields = source.get("fields", LINEAGE_FIELDS.get(source_id, []))
    if source_id in FIXED:
        _require(fields == DATA_CONTRACT["fixed_output_fields"][source_id],
                 "fixed_output_contract_mismatch")
    _require(isinstance(fields, list) and fields and
             isinstance(plan["campos"], list) and bool(plan["campos"]) and
             all(isinstance(field, str) for field in plan["campos"]) and
             len(set(plan["campos"])) == len(plan["campos"]) and
             set(plan["campos"]) <= set(fields), "fields_outside_catalog")
    _require(plan["grao"] == source.get("grain"), "plan_source_or_grain_mismatch")
    _require(type(plan["limite"]) is int and 1 <= plan["limite"] <= 20,
             "row_limit_invalid")
    _require(isinstance(plan["filtros"], dict), "filters_outside_catalog")
    _require(not {"join", "relation", "cross_source"} & set(plan["filtros"]),
             "relation_not_approved")
    return domain, source


def _dw_connection(catalog: dict, timeout_ms: int):
    connection = _connect("db_pesquisa_dw")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SELECT set_config('statement_timeout', %s, true)",
                           (str(timeout_ms),))
            cursor.execute("SELECT current_user, current_database()")
            _require(cursor.fetchone() == ("spec013_reader", "db_pesquisa_dw"),
                     "reader_identity_mismatch")
            cursor.execute("SELECT version, source_fingerprint FROM dw.schema_migrations")
            dw_tools._supported_migration(cursor.fetchall())
            cursor.execute("SELECT source_fingerprint FROM dw.schema_migrations")
            _require(cursor.fetchone()[0].strip() == catalog["dw_source_fingerprint"],
                     "dw_fingerprint_mismatch")
        return connection
    except Exception:
        connection.rollback()
        connection.close()
        raise


def _fixed_query(plan: dict, source: dict, catalog: dict, timeout_ms: int) -> dict:
    name = plan["fonte_id"]
    try:
        args = dw_tools.validate_call(name, plan["filtros"])
    except ValueError as exc:
        raise LocalQueryRejected("filters_outside_catalog") from exc
    with closing(_dw_connection(catalog, timeout_ms)) as connection:
        try:
            raw = dw_tools.fixed_queries.query(name, args["year"], args.get("id"),
                                               connection=connection,
                                               readonly_already=True)
        finally:
            connection.rollback()
    _require(len(raw["rows"]) <= plan["limite"], "row_limit_exceeded")
    _require(all(set(row) == set(DATA_CONTRACT["fixed_output_fields"][name])
                 for row in raw["rows"]), "fixed_output_contract_mismatch")
    _require(all(set(plan["campos"]) <= set(row) for row in raw["rows"]),
             "source_schema_mismatch")
    return {"rows": [{field: row[field] for field in plan["campos"]}
                     for row in raw["rows"]],
            "coverage": raw["coverage"],
            "units": {field: unit for field, unit in raw["units"].items()
                      if field in plan["campos"]},
            "formula": {field: formula for field, formula in raw["formula"].items()
                        if field in plan["campos"]},
            "interpretation": raw["interpretation"],
            "origin": {"database": "db_pesquisa_dw", "schema": "dw",
                       "query": name, "source_fingerprint": catalog["dw_source_fingerprint"],
                       "sources": raw["sources"]}}


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _contributors(plan: dict, catalog: dict, timeout_ms: int) -> dict:
    filters = plan["filtros"]
    _require(set(filters) == {"kind", "year", "id", "fact", "after"},
             "filters_outside_catalog")
    kind, year, dimension_id, fact, after = (filters[key] for key in
                                             ("kind", "year", "id", "fact", "after"))
    _require(kind in LINEAGE_FACTS and type(year) is int and 2015 <= year <= 2026
             and _positive(dimension_id) and type(after) is int and after >= 0,
             "invalid_lineage_filter")
    candidate = [item for item in LINEAGE_FACTS[kind] if item[0] == fact]
    _require(len(candidate) == 1, "lineage_fact_not_allowed")
    table, pk, dimension, day = candidate[0]
    start, end = date(year, 1, 1), date(year + 1, 1, 1)
    with closing(_dw_connection(catalog, timeout_ms)) as connection:
        try:
            with connection.cursor() as cursor:
                predicate = sql.SQL("{} = %s AND {} >= %s AND {} < %s").format(
                    sql.Identifier(dimension), sql.Identifier(day), sql.Identifier(day))
                cursor.execute(sql.SQL("SELECT count(*) FROM dw.{} WHERE {}").format(
                    sql.Identifier(table), predicate), (dimension_id, start, end))
                total = cursor.fetchone()[0]
                cursor.execute(sql.SQL("SELECT {} FROM dw.{} WHERE {} AND {} > %s "
                                       "ORDER BY {} LIMIT %s").format(
                    sql.Identifier(pk), sql.Identifier(table), predicate,
                    sql.Identifier(pk), sql.Identifier(pk)),
                    (dimension_id, start, end, after, plan["limite"] + 1))
                fetched = [row[0] for row in cursor.fetchall()]
        finally:
            connection.rollback()
    ids = fetched[:plan["limite"]]
    row = {"fact": fact, "total": total, "ids": ids,
           "next_after": ids[-1] if len(fetched) > plan["limite"] else None}
    return {"rows": [{field: row[field] for field in plan["campos"]}] if ids else [],
            "coverage": {"rows": 1 if ids else 0,
                         "state": "observed" if ids else "no_observation"},
            "units": {}, "origin": {"database": "db_pesquisa_dw", "schema": "dw",
                                   "query": "contributors", "source_fingerprint": catalog["dw_source_fingerprint"]},
            "interpretation": "IDs de fatos da DW; paginar se next_after existir. Não prova causalidade."}


def _trace(plan: dict, catalog: dict, timeout_ms: int) -> dict:
    filters = plan["filtros"]
    _require(set(filters) == {"fact", "id"} and filters["fact"] in TRACE_PKS
             and _positive(filters["id"]) and plan["limite"] == 1,
             "invalid_lineage_filter")
    fact, mapped_id = filters["fact"], filters["id"]
    with closing(_dw_connection(catalog, timeout_ms)) as connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("SELECT f.original_id, f.period_index, s.domain, "
                                       "s.table_name, s.source_path, s.sha256 "
                                       "FROM dw.{} f JOIN dw.source_file s USING (source_file_id) "
                                       "WHERE f.{} = %s").format(
                    sql.Identifier(fact), sql.Identifier(TRACE_PKS[fact])), (mapped_id,))
                found = cursor.fetchone()
        finally:
            connection.rollback()
    rows = []
    if found is not None:
        original_id, period, domain, table, path, digest = found
        _require(domain in {"industrial", "financeiro"} and
                 re.fullmatch(r"[0-9a-f]{64}", digest.strip()) is not None,
                 "lineage_provenance_invalid")
        full = {"mapped_id": mapped_id, "original_id": original_id,
                "period_index": period, "source_database": f"db_{domain}",
                "source_table": table, "source_csv": path,
                "source_sha256": digest.strip()}
        rows = [{field: full[field] for field in plan["campos"]}]
    return {"rows": rows,
            "coverage": {"rows": len(rows),
                         "state": "observed" if rows else "no_observation"},
            "units": {}, "origin": {"database": "db_pesquisa_dw", "schema": "dw",
                                   "query": "trace", "source_fingerprint": catalog["dw_source_fingerprint"]},
            "interpretation": "Proveniência do fato DW; não inclui valor bruto ou relação causal."}


def execute(plan: dict, catalog: dict, *, max_bytes: int = 32_768,
            timeout_ms: int = 10_000) -> dict:
    """Execute one allowed local plan using the dedicated reader role."""
    _require(type(max_bytes) is int and 1 <= max_bytes <= 32_768 and
             type(timeout_ms) is int and 1 <= timeout_ms <= 10_000,
             "invalid_backend_limits")
    domain, source = _validate(plan, catalog)
    name = plan["fonte_id"]
    if domain == "dw" and name in FIXED and source["kind"] == "existing_fixed_query":
        result = _fixed_query(plan, source, catalog, timeout_ms)
    elif domain == "dw" and name == "contributors" and source["kind"] == "existing_lineage_command":
        result = _contributors(plan, catalog, timeout_ms)
    elif domain == "dw" and name == "trace" and source["kind"] == "existing_lineage_command":
        result = _trace(plan, catalog, timeout_ms)
    elif domain in {"industrial", "financeiro"} and source["kind"] == "typed_table_detail":
        result = execute_detail(domain, name, plan, catalog,
                                lambda: _connect(catalog["domains"][domain]["database"]),
                                max_rows=20, max_bytes=max_bytes,
                                timeout_ms=timeout_ms)
    else:
        raise LocalQueryRejected("source_not_enabled")
    result["origin"]["data_contract_sha256"] = DATA_CONTRACT_SHA256
    _require(len(json.dumps(result, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":"), allow_nan=False).encode("utf-8")) <= max_bytes,
             "result_byte_limit_exceeded")
    return result
