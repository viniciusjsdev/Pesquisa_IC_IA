"""Offline structural check of a disabled SPEC-013 semantic catalog candidate.

This never connects to PostgreSQL and never enables a source. Semantic approval
is a separate research decision; a successful check proves only references.
"""

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path


DOMAINS = {"dw", "industrial", "financeiro"}
KINDS = {"existing_fixed_query", "existing_lineage_command", "typed_table_detail"}
ACTIVATION_BLOCKERS = [
    "semantic meaning, grain, units and temporal coverage require research review",
    "fixed-query output types and lineage output shapes need a versioned contract",
    "query filters, relations and budgets require DEC-001/002 approval",
    "local read-only access and external transmission gates require DEC-004",
]


def _fixed_query_fields(path: Path) -> dict[str, set[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    query = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "query")
    assignment = next(node for node in query.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "statements"
                              for target in node.targets))
    statements = ast.literal_eval(assignment.value)
    return {name: set(columns) for name, (_, columns) in statements.items()}


def _primary_key(table: dict) -> list[str]:
    keys = [item["definition"] for item in table.get("constraints", []) if item.get("kind") == "p"]
    if len(keys) != 1:
        return []
    match = re.fullmatch(r"PRIMARY KEY \(([^)]+)\)", keys[0])
    return [part.strip() for part in match.group(1).split(",")] if match else []


def _foreign_keys(table: dict) -> set[str]:
    relations = set()
    for item in table.get("constraints", []):
        if item.get("kind") != "f":
            continue
        match = re.fullmatch(
            r"FOREIGN KEY \(([^)]+)\) REFERENCES (?:public\.)?([\w]+)\(([^)]+)\).*",
            item["definition"])
        if match:
            relations.add(f"{match.group(1)} -> {match.group(2)}.{match.group(3)}")
    return relations


def validate(catalog: dict, inventory: dict, fixed_queries_path: Path,
             lineage_cli_path: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    checks = {"sources": 0, "typed_fields": 0, "fixed_outputs": 0,
              "physical_tables": 0, "foreign_keys": 0}
    if catalog.get("status") != "candidate_not_enabled":
        errors.append("catalog must remain candidate_not_enabled in M0")
    if catalog.get("physical_inventory_sha256") != inventory.get("inventory_sha256"):
        errors.append("physical inventory SHA-256 mismatch")
    inventory_body = {key: value for key, value in inventory.items() if key != "inventory_sha256"}
    actual_inventory_hash = hashlib.sha256(json.dumps(inventory_body, sort_keys=True,
        ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    if inventory.get("inventory_sha256") != actual_inventory_hash:
        errors.append("physical inventory contents differ from their declared SHA-256")
    migration = inventory.get("databases", {}).get("dw", {}).get("migration", [])
    if len(migration) != 1 or catalog.get("dw_source_fingerprint") != migration[0].get("source_fingerprint"):
        errors.append("DW fingerprint mismatch")
    domains = catalog.get("domains")
    if not isinstance(domains, dict) or set(domains) != DOMAINS:
        errors.append("catalog must contain exactly the three domains")
        return {"valid_structurally": False, "eligible_for_activation": False,
                "activation_blockers": ACTIVATION_BLOCKERS,
                "errors": errors, "warnings": warnings, "checks": checks}
    fixed = _fixed_query_fields(fixed_queries_path)
    lineage = {node.name for node in ast.parse(lineage_cli_path.read_text(encoding="utf-8")).body
               if isinstance(node, ast.FunctionDef)}
    if catalog.get("cross_domain_relations"):
        errors.append("cross-domain relations require a separate semantic review")

    index_bytes = {}
    max_detail_bytes = {}
    physical_table_counts = {}

    for domain, domain_map in sorted(domains.items()):
        physical = inventory.get("databases", {}).get(domain, {})
        if domain_map.get("database") != physical.get("database") or domain_map.get("schema") != physical.get("schema"):
            errors.append(f"{domain}: database/schema mismatch")
        tables = physical.get("tables", {})
        sources = domain_map.get("sources", {})
        physical_table_counts[domain] = len(tables)
        if not isinstance(sources, dict):
            errors.append(f"{domain}: sources must be an object")
            continue
        index = [{"id": source_id, "grain": source.get("grain"),
                  "caveat": source.get("caveat")}
                 for source_id, source in sorted(sources.items())]
        index_bytes[domain] = len(json.dumps(index, ensure_ascii=False,
            separators=(",", ":")).encode("utf-8"))
        max_detail_bytes[domain] = max((len(json.dumps(source, ensure_ascii=False,
            separators=(",", ":")).encode("utf-8")) for source in sources.values()), default=0)
        for source_id, source in sorted(sources.items()):
            ref = f"{domain}.{source_id}"
            checks["sources"] += 1
            if source.get("enabled") is not False:
                errors.append(f"{ref}: source must stay disabled during M0")
            kind = source.get("kind")
            if kind not in KINDS:
                errors.append(f"{ref}: unknown source kind")
                continue
            if not source.get("grain") or not source.get("caveat"):
                warnings.append(f"{ref}: grain/caveat incomplete")
            fields = source.get("fields", [])
            if any(field not in fields for field in source.get("units", {})):
                errors.append(f"{ref}: units reference a field outside the source")
            if kind == "typed_table_detail":
                table = tables.get(source_id)
                if table is None:
                    errors.append(f"{ref}: typed table absent from physical inventory")
                    continue
                actual = {column["name"] for column in table.get("columns", [])}
                actual_types = {column["name"]: column["data_type"]
                                for column in table.get("columns", [])}
                if not isinstance(fields, list) or not fields or len(fields) != len(set(fields)):
                    errors.append(f"{ref}: fields missing or duplicated")
                else:
                    for field in fields:
                        if field not in actual:
                            errors.append(f"{ref}.{field}: column absent from physical inventory")
                        else:
                            checks["typed_fields"] += 1
                if source.get("field_types") != {field: actual_types[field]
                                                  for field in fields if field in actual_types}:
                    errors.append(f"{ref}: field types differ from physical inventory")
                if source.get("primary_key") != _primary_key(table):
                    errors.append(f"{ref}: primary key differs from physical inventory")
                declared = source.get("physical_relations", [])
                actual_relations = _foreign_keys(table)
                for relation in declared:
                    if relation not in actual_relations:
                        errors.append(f"{ref}: FK not present: {relation}")
                    else:
                        checks["foreign_keys"] += 1
                for candidate in source.get("filter_candidates", []):
                    if candidate.split(":", 1)[0] not in actual:
                        errors.append(f"{ref}: filter column absent: {candidate}")
                if not source.get("units"):
                    warnings.append(f"{ref}: units not specified for selected measures")
            elif kind == "existing_fixed_query":
                if domain != "dw" or source_id not in fixed:
                    errors.append(f"{ref}: fixed query not present in code")
                    continue
                fields = source.get("fields", [])
                if not isinstance(fields, list) or not fields or not set(fields) <= fixed[source_id]:
                    errors.append(f"{ref}: output fields not in fixed query")
                else:
                    checks["fixed_outputs"] += len(fields)
                physical_tables = source.get("physical_tables", [])
                if not physical_tables or len(physical_tables) != len(set(physical_tables)):
                    errors.append(f"{ref}: physical tables missing or duplicated")
                for table_name in physical_tables:
                    if table_name not in tables:
                        errors.append(f"{ref}: physical table absent: {table_name}")
                    else:
                        checks["physical_tables"] += 1
            elif domain != "dw" or source_id not in {"contributors", "trace"} or source_id not in lineage:
                errors.append(f"{ref}: lineage command not present in code")

    return {"valid_structurally": not errors, "eligible_for_activation": False,
            "activation_blockers": ACTIVATION_BLOCKERS,
            "errors": errors, "warnings": warnings, "checks": checks,
            "physical_table_counts": physical_table_counts,
            "index_bytes_by_domain": index_bytes,
            "largest_source_detail_bytes_by_domain": max_detail_bytes,
            "catalog_sha256": hashlib.sha256(json.dumps(catalog, sort_keys=True,
                ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest(),
            "inventory_sha256": inventory.get("inventory_sha256"),
            "fixed_query_source_sha256": hashlib.sha256(fixed_queries_path.read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--fixed-queries", type=Path, required=True)
    parser.add_argument("--lineage-cli", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate(json.loads(args.catalog.read_text(encoding="utf-8")),
                      json.loads(args.inventory.read_text(encoding="utf-8")),
                      args.fixed_queries, args.lineage_cli)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.open("x", encoding="utf-8").write(rendered)
    else:
        print(rendered, end="")
    return 0 if report["valid_structurally"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
