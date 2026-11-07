"""Bounded, read-only detail queries for an explicitly approved catalog source.

No model SQL is accepted. The caller owns catalog approval and supplies a fresh
connection factory; the Bancada does not wire this module to providers yet.
"""

from datetime import date, datetime
from decimal import Decimal
import json
from typing import Callable

from psycopg2 import sql


STRIDE = 1_000_000
DOMAINS = {"industrial", "financeiro"}
PLAN_KEYS = {"fonte_id", "campos", "filtros", "limite", "grao"}


class DetailRejected(ValueError):
    """A plan or result failed the approved source contract."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise DetailRejected(reason)


def _normalize(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _validate_plan(domain: str, source_id: str, plan: dict, catalog: dict,
                   max_rows: int) -> tuple[dict, dict, list[str]]:
    _require(domain in DOMAINS and isinstance(plan, dict) and set(plan) == PLAN_KEYS,
             "invalid_typed_plan")
    _require(catalog.get("status") == "approved_for_local_query",
             "catalog_not_approved_for_local_query")
    domain_map = catalog.get("domains", {}).get(domain, {})
    source = domain_map.get("sources", {}).get(source_id)
    _require(domain_map.get("schema") == "public" and isinstance(source, dict)
             and source.get("kind") == "typed_table_detail" and source.get("enabled") is True,
             "source_not_enabled")
    _require(plan["fonte_id"] == source_id and plan["grao"] == source["grain"],
             "plan_source_or_grain_mismatch")
    fields = plan["campos"]
    _require(isinstance(fields, list) and fields and
             all(isinstance(item, str) for item in fields) and
             len(fields) == len(set(fields)) and set(fields) <= set(source["fields"]),
             "fields_outside_catalog")
    _require(type(plan["limite"]) is int and 1 <= plan["limite"] <= max_rows,
             "row_limit_invalid")
    filters = plan["filtros"]
    allowed_filters = {item.split(":", 1)[0]: item.endswith(":range")
                       for item in source.get("filter_candidates", [])}
    _require(isinstance(filters, dict) and bool(filters) and
             set(filters) <= set(allowed_filters), "filters_outside_catalog")
    field_types = source.get("field_types", {})
    clauses = []
    values = []
    for field, value in sorted(filters.items()):
        if allowed_filters[field]:
            _require(isinstance(value, dict) and set(value) == {"from", "to"}
                     and all(isinstance(item, str) for item in value.values()),
                     "invalid_range_filter")
            try:
                parse = date.fromisoformat if field_types[field] == "date" else datetime.fromisoformat
                start, end = parse(value["from"]), parse(value["to"])
            except (ValueError, KeyError) as exc:
                raise DetailRejected("invalid_range_filter") from exc
            _require(start < end, "invalid_range_filter")
            clauses.append(sql.SQL("{} >= %s AND {} < %s").format(
                sql.Identifier(field), sql.Identifier(field)))
            values.extend((start, end))
        else:
            _require(type(value) is int and value > 0 and field_types.get(field) == "integer",
                     "invalid_id_filter")
            clauses.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
            values.append(value)
    pk = source.get("primary_key", [])
    _require(len(pk) == 1 and pk[0] in source["fields"]
             and field_types.get(pk[0]) == "integer", "provenance_key_unavailable")
    return source, {"clauses": clauses, "values": values}, fields


def execute(domain: str, source_id: str, plan: dict, catalog: dict,
            connect: Callable[[], object], *, max_rows: int = 20,
            max_bytes: int = 8192, timeout_ms: int = 10_000) -> dict:
    """Execute one parameterized SELECT and return rows with source provenance."""
    _require(type(max_rows) is int and 1 <= max_rows <= 200,
             "invalid_backend_limits")
    source, where, fields = _validate_plan(domain, source_id, plan, catalog, max_rows)
    _require(type(max_bytes) is int and 1 <= max_bytes <= 65_536 and
             type(timeout_ms) is int and 1 <= timeout_ms <= 30_000,
             "invalid_backend_limits")
    pk = source["primary_key"][0]
    selected = [pk, *(field for field in fields if field != pk)]
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SELECT set_config('statement_timeout', %s, true)",
                           (str(timeout_ms),))
            cursor.execute("SELECT current_database()")
            _require(cursor.fetchone()[0] == catalog["domains"][domain]["database"],
                     "source_database_mismatch")
            cursor.execute("""SELECT column_name, data_type
                              FROM information_schema.columns
                              WHERE table_schema = 'public' AND table_name = %s""",
                           (source_id,))
            actual_types = dict(cursor.fetchall())
            _require(all(actual_types.get(field) == field_type for field, field_type
                         in source.get("field_types", {}).items()),
                     "source_schema_mismatch")
            cursor.execute("""SELECT period_index, source_path, sha256
                              FROM public.canonical_source_file
                              WHERE table_name = %s""", (source_id,))
            files = {period: {"source_path": path, "source_file_sha256": digest.strip()}
                     for period, path, digest in cursor.fetchall()}
            _require(files, "source_files_unavailable")
            statement = sql.SQL("SELECT {} FROM {} WHERE {} ORDER BY {} LIMIT %s").format(
                sql.SQL(", ").join(map(sql.Identifier, selected)),
                sql.Identifier("public", source_id),
                sql.SQL(" AND ").join(where["clauses"]), sql.Identifier(pk))
            cursor.execute(statement, (*where["values"], plan["limite"] + 1))
            records = cursor.fetchall()
            _require(len(records) <= plan["limite"], "row_limit_exceeded")
            rows = []
            for record in records:
                values = dict(zip(selected, record))
                row_id = values[pk]
                _require(type(row_id) is int and 0 < row_id < 3 * STRIDE,
                         "provenance_key_outside_periods")
                period = row_id // STRIDE
                _require(period in files, "row_source_file_unavailable")
                rows.append({"values": {field: _normalize(values[field]) for field in fields},
                             "provenance": {"database": catalog["domains"][domain]["database"],
                                            "schema": "public", "table": source_id,
                                            "primary_key": {pk: row_id},
                                            "period_index": period, **files[period]}})
        result = {"rows": rows,
                  "coverage": {"state": "observed" if rows else "no_observation",
                               "rows": len(rows)},
                  "units": {field: unit for field, unit in source.get("units", {}).items()
                            if field in fields},
                  "origin": {"database": catalog["domains"][domain]["database"],
                             "schema": "public", "table": source_id,
                             "catalog_version": catalog["version"]}}
        _require(len(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")).encode("utf-8")) <= max_bytes,
                 "result_byte_limit_exceeded")
        return result
    finally:
        connection.rollback()
        connection.close()
