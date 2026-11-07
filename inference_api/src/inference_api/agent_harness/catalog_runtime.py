"""Project an approved semantic catalog into bounded, per-domain model maps."""

from __future__ import annotations

import copy

from .local_queries import LINEAGE_FIELDS, LINEAGE_FACTS, TRACE_PKS, LocalQueryRejected
from .. import dw_tools


def filter_contract(source_id: str, source: dict) -> dict:
    """Expose the executor's filter grammar, without changing approved catalog bytes."""
    fixed = {item['function']['name']: item['function']['parameters']
             for item in dw_tools.catalog()}
    if source_id in fixed:
        return copy.deepcopy(fixed[source_id])
    positive = {"type": "integer", "minimum": 1}
    if source_id == "trace":
        return {"type": "object", "additionalProperties": False,
                "required": ["fact", "id"],
                "properties": {"fact": {"enum": sorted(TRACE_PKS)}, "id": positive},
                "description": "limite do plano deve ser 1; id é a chave mapeada do fato DW"}
    if source_id == "contributors":
        return {"type": "object", "additionalProperties": False,
                "required": ["kind", "year", "id", "fact", "after"],
                "properties": {"kind": {"enum": sorted(LINEAGE_FACTS)},
                    "year": {"type": "integer", "minimum": 2015, "maximum": 2026},
                    "id": positive, "fact": {"enum": sorted({x[0] for v in LINEAGE_FACTS.values() for x in v})},
                    "after": {"type": "integer", "minimum": 0}},
                "allOf": [{"if": {"properties": {"kind": {"const": kind}}},
                           "then": {"properties": {"fact": {"enum": [item[0] for item in facts]}}}}
                          for kind, facts in sorted(LINEAGE_FACTS.items())]}
    if source.get("kind") != "typed_table_detail":
        raise LocalQueryRejected("catalog_filter_contract_missing")
    properties = {}
    for candidate in source.get("filter_candidates", []):
        field, _, operator = candidate.partition(":")
        sql_type = source.get("field_types", {}).get(field)
        if operator == "range":
            if sql_type not in {"date", "timestamp without time zone", "timestamp with time zone"}:
                raise LocalQueryRejected("catalog_filter_contract_missing")
            properties[field] = {"type": "object", "additionalProperties": False,
                "required": ["from", "to"], "properties": {
                    "from": {"type": "string"}, "to": {"type": "string"}},
                "description": f"ISO-8601 {sql_type}; from < to; intervalo [from,to)"}
        else:
            if sql_type != "integer":
                raise LocalQueryRejected("catalog_filter_contract_missing")
            properties[field] = dict(positive)
    return {"type": "object", "minProperties": 1, "additionalProperties": False,
            "properties": properties}


def compile_maps(catalog: dict) -> dict:
    if not isinstance(catalog, dict) or catalog.get("status") != "approved_for_local_query":
        raise LocalQueryRejected("catalog_not_approved_for_local_query")
    if not isinstance(catalog.get("dw_source_fingerprint"), str) or not isinstance(
            catalog.get("physical_inventory_sha256"), str):
        raise LocalQueryRejected("catalog_version_missing")
    domains = catalog.get("domains", {})
    if not isinstance(domains, dict) or set(domains) != {"dw", "industrial", "financeiro"}:
        raise LocalQueryRejected("catalog_domains_invalid")
    maps = {}
    seen = set()
    for domain, domain_record in sorted(domains.items()):
        sources = {}
        for source_id, source in sorted(domain_record.get("sources", {}).items()):
            if source.get("enabled") is not True:
                continue
            if source_id in seen:
                raise LocalQueryRejected("duplicate_catalog_source")
            seen.add(source_id)
            projected = copy.deepcopy(source)
            if source_id in LINEAGE_FIELDS:
                projected["fields"] = LINEAGE_FIELDS[source_id]
            if not isinstance(projected.get("fields"), list) or not projected["fields"]:
                raise LocalQueryRejected("catalog_source_fields_missing")
            projected["description"] = projected.get("caveat", "")
            projected["coverage"] = projected.get("coverage", "piloto local; conferir por consulta")
            projected["filter_contracts"] = filter_contract(source_id, projected)
            sources[source_id] = projected
        if sources:
            maps[domain] = {"domain": domain,
                            "version": f"pilot-{catalog['version']}-{catalog['dw_source_fingerprint'][:12]}",
                            "synthetic": False,
                            "description": domain_record.get("overview", ""),
                            "sources": sources}
    if not maps:
        raise LocalQueryRejected("catalog_has_no_enabled_sources")
    return maps
