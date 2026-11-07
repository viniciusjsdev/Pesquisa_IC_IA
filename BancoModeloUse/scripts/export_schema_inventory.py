"""Export only physical PostgreSQL schema metadata from the isolated cluster."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import bootstrap_local


DATABASES = (("industrial", "db_industrial", "public"),
             ("financeiro", "db_financeiro", "public"),
             ("dw", "db_pesquisa_dw", "dw"))


def inspect_database(domain: str, database: str, schema: str) -> dict:
    """Read names, types and physical constraints without reading user rows."""
    connection = bootstrap_local.connect("industrial" if domain == "dw" else domain, database)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("""SELECT table_name, column_name, ordinal_position,
                                     data_type, udt_name, is_nullable
                              FROM information_schema.columns
                              WHERE table_schema = %s
                              ORDER BY table_name, ordinal_position""", (schema,))
            tables = {}
            for table, column, position, data_type, udt_name, nullable in cursor.fetchall():
                tables.setdefault(table, {"columns": [], "constraints": []})["columns"].append({
                    "name": column, "position": position, "data_type": data_type,
                    "udt_name": udt_name, "nullable": nullable == "YES"})
            cursor.execute("""SELECT c.relname, p.conname, p.contype,
                                     pg_get_constraintdef(p.oid, true)
                              FROM pg_constraint p
                              JOIN pg_class c ON c.oid = p.conrelid
                              JOIN pg_namespace n ON n.oid = c.relnamespace
                              WHERE n.nspname = %s AND c.relkind IN ('r','p')
                                AND p.contype IN ('p','f','u')
                              ORDER BY c.relname, p.conname""", (schema,))
            for table, name, kind, definition in cursor.fetchall():
                tables[table]["constraints"].append({
                    "name": name, "kind": kind, "definition": definition})
            migration = None
            if domain == "dw":
                cursor.execute("SELECT version, source_fingerprint FROM dw.schema_migrations")
                migration = [{"version": version, "source_fingerprint": fingerprint}
                             for version, fingerprint in cursor.fetchall()]
        connection.rollback()
        return {"database": database, "schema": schema, "tables": tables,
                "migration": migration}
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Output already exists; refusing to overwrite")
    databases = {domain: inspect_database(domain, name, schema)
                 for domain, name, schema in DATABASES}
    body = {"inventory_version": 1, "scope": "physical_schema_only", "databases": databases}
    digest = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True,
                                       separators=(",", ":")).encode("utf-8")).hexdigest()
    document = {**body, "inventory_sha256": digest}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True,
                                     indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"inventory_sha256": digest,
                      "table_counts": {domain: len(item["tables"])
                                       for domain, item in databases.items()},
                      "dw_migration": databases["dw"]["migration"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
