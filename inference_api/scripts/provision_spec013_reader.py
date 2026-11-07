"""Provision and verify a local SELECT-only role for the SPEC-013 pilot.

Only the isolated PostgreSQL cluster at 127.0.0.1:5544 is supported. The
password is written to ignored `.local/`; no data rows or secrets are printed.
No application mode is activated by this script.
"""

import argparse
import json
from pathlib import Path
import secrets
import sys

import psycopg2
from psycopg2 import sql


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "BancoModeloUse"))
from scripts import bootstrap_local  # noqa: E402


ROLE = "spec013_reader"
HBA_MARKER = "# SPEC-013 pilot reader database boundary"
HBA_RULES = (HBA_MARKER + "\n"
             "host db_pesquisa_dw,db_industrial,db_financeiro spec013_reader 127.0.0.1/32 scram-sha-256\n"
             "host all spec013_reader 127.0.0.1/32 reject\n")
SECRET_PATH = ROOT / "inference_api/.local/spec013_reader_credentials.json"
CATALOG_PATH = ROOT / "specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json"
GRANTS = {
    "db_pesquisa_dw": ("dw", {"dim_machine", "dim_material", "dim_product",
                            "fact_downtime", "fact_financial_observation",
                            "fact_material_consumption", "fact_material_price_observation",
                            "fact_operation", "fact_quality_inspection", "fact_sale",
                            "source_file", "schema_migrations"}),
    "db_industrial": ("public", {"paradas_maquinas", "paradas_maquinas_geradas",
                                "registros_operacao", "canonical_source_file"}),
    "db_financeiro": ("public", {"resultados_financeiros", "vendas",
                                "canonical_source_file"}),
}


def _check_catalog() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if catalog.get("status") != "candidate_not_enabled":
        raise RuntimeError("Expected the pilot catalog to remain disabled")
    for domain, database in (("industrial", "db_industrial"),
                             ("financeiro", "db_financeiro")):
        expected = set(catalog["domains"][domain]["sources"]) | {"canonical_source_file"}
        if catalog["domains"][domain]["database"] != database or expected != GRANTS[database][1]:
            raise RuntimeError("Pilot source list changed; review grants before provisioning")
    dw_sources = catalog["domains"]["dw"]["sources"]
    expected_dw = {table for source in dw_sources.values()
                   for table in source.get("physical_tables", [])} | {"schema_migrations"}
    if expected_dw != GRANTS["db_pesquisa_dw"][1]:
        raise RuntimeError("DW physical table list changed; review grants")


def _restrict_database_connections() -> None:
    connection = bootstrap_local.connect("industrial", "postgres")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW listen_addresses")
            if cursor.fetchone() != ("127.0.0.1",):
                raise RuntimeError("Pilot role requires the isolated IPv4 loopback listener")
            cursor.execute("SHOW hba_file")
            hba_file = Path(cursor.fetchone()[0]).resolve()
            cluster = (ROOT / "BancoModeloUse/.local/postgres").resolve()
            if not hba_file.is_relative_to(cluster) or hba_file.name != "pg_hba.conf":
                raise RuntimeError("Unexpected PostgreSQL HBA file; refusing to edit")
            existing = hba_file.read_text(encoding="utf-8")
            if HBA_MARKER not in existing:
                hba_file.write_text(HBA_RULES + existing, encoding="utf-8")
            elif not existing.startswith(HBA_RULES):
                raise RuntimeError("Pilot HBA rules differ; inspect before retry")
            cursor.execute("SELECT pg_reload_conf()")
            if cursor.fetchone() != (True,):
                raise RuntimeError("PostgreSQL configuration reload failed")
            cursor.execute("SELECT count(*) FROM pg_hba_file_rules WHERE error IS NOT NULL")
            if cursor.fetchone()[0]:
                raise RuntimeError("PostgreSQL reports an invalid HBA rule")
        connection.commit()
    finally:
        connection.close()


def provision() -> dict:
    _check_catalog()
    SECRET_PATH.parent.mkdir(parents=True, exist_ok=True)
    preflight = bootstrap_local.connect("industrial", "postgres")
    try:
        with preflight.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (ROLE,))
            role_already_exists = cursor.fetchone() is not None
        preflight.rollback()
    finally:
        preflight.close()
    if role_already_exists and not SECRET_PATH.exists():
        raise RuntimeError("Role exists without saved credential; inspect before retry")
    if SECRET_PATH.exists():
        credentials = json.loads(SECRET_PATH.read_text(encoding="utf-8"))
        if credentials.get("user") != ROLE:
            raise RuntimeError("Existing credential file does not belong to pilot role")
        created_secret = False
    else:
        credentials = {"host": "127.0.0.1", "port": 5544,
                       "user": ROLE, "password": secrets.token_urlsafe(32)}
        with SECRET_PATH.open("x", encoding="utf-8") as stream:
            json.dump(credentials, stream)
        created_secret = True
    admin = bootstrap_local.connect("industrial", "postgres")
    try:
        with admin.cursor() as cursor:
            cursor.execute("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
            if cursor.fetchone() != (True,):
                raise RuntimeError("Local cluster administrator is required")
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (ROLE,))
            exists = cursor.fetchone() is not None
            if not exists and not created_secret:
                raise RuntimeError("Credential file exists but role does not; inspect before retry")
            if exists and created_secret:
                raise RuntimeError("Role exists without saved credential; inspect before retry")
            if not exists:
                cursor.execute(sql.SQL("""CREATE ROLE {} LOGIN NOINHERIT NOSUPERUSER
                                   NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
                                   PASSWORD %s""").format(sql.Identifier(ROLE)),
                               (credentials["password"],))
                cursor.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on")
                               .format(sql.Identifier(ROLE)))
            for database in GRANTS:
                cursor.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}")
                               .format(sql.Identifier(database), sql.Identifier(ROLE)))
        admin.commit()
    finally:
        admin.close()
    for database, (schema, tables) in GRANTS.items():
        connection = bootstrap_local.connect("industrial", database)
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}")
                               .format(sql.Identifier(schema), sql.Identifier(ROLE)))
                for table in sorted(tables):
                    cursor.execute(sql.SQL("GRANT SELECT ON TABLE {}.{} TO {}")
                                   .format(sql.Identifier(schema), sql.Identifier(table),
                                           sql.Identifier(ROLE)))
            connection.commit()
        finally:
            connection.close()
    _restrict_database_connections()
    verified = {}
    for database, (schema, tables) in GRANTS.items():
        connection = psycopg2.connect(**credentials, dbname=database)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(), current_user, "
                               "current_setting('default_transaction_read_only')")
                identity = cursor.fetchone()
                if identity != (database, ROLE, "on"):
                    raise RuntimeError("Pilot role identity or read-only default mismatch")
                cursor.execute("SET TRANSACTION READ ONLY")
                for table in sorted(tables):
                    cursor.execute(sql.SQL("SELECT 1 FROM {}.{} LIMIT 0")
                                   .format(sql.Identifier(schema), sql.Identifier(table)))
                cursor.execute("SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
                               "FROM pg_roles WHERE rolname = current_user")
                if cursor.fetchone() != (False, False, False, False, False):
                    raise RuntimeError("Pilot role has elevated privileges")
                cursor.execute("SELECT has_schema_privilege(current_user, %s, 'CREATE')",
                               (schema,))
                if cursor.fetchone()[0]:
                    raise RuntimeError("Pilot role can create in approved schema")
                cursor.execute("""SELECT count(*) FROM pg_class c
                                  JOIN pg_namespace n ON n.oid = c.relnamespace
                                  WHERE n.nspname = %s
                                    AND c.relkind IN ('r', 'p', 'v', 'm')
                                    AND c.relname <> ALL(%s)
                                    AND has_table_privilege(current_user, c.oid, 'SELECT')""",
                               (schema, list(tables)))
                if cursor.fetchone()[0]:
                    raise RuntimeError("Pilot role can SELECT outside approved table list")
                cursor.execute("""SELECT count(*) FROM pg_class c
                                  JOIN pg_namespace n ON n.oid = c.relnamespace
                                  WHERE n.nspname = %s AND c.relname = ANY(%s)
                                    AND (has_table_privilege(current_user, c.oid, 'INSERT')
                                      OR has_table_privilege(current_user, c.oid, 'UPDATE')
                                      OR has_table_privilege(current_user, c.oid, 'DELETE')
                                      OR has_table_privilege(current_user, c.oid, 'TRUNCATE'))""",
                               (schema, list(tables)))
                if cursor.fetchone()[0]:
                    raise RuntimeError("Pilot role has write privilege on approved tables")
            connection.rollback()
            verified[database] = {"approved_tables_selectable": len(tables),
                                  "outside_tables_selectable": 0,
                                  "write_privileges": 0,
                                  "default_read_only": True, "schema_create": False}
        finally:
            connection.close()
    try:
        unexpected = psycopg2.connect(**credentials, dbname="postgres", connect_timeout=3)
    except psycopg2.OperationalError:
        outside_database_rejected = True
    else:
        unexpected.close()
        outside_database_rejected = False
    if not outside_database_rejected:
        raise RuntimeError("Pilot role can connect to a non-approved database")
    return {"cluster": "127.0.0.1:5544", "role": ROLE,
            "credential_file_ignored": True, "catalog_file_unchanged": True,
            "outside_database_connection_rejected": True,
            "databases": verified, "provider_called": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = provision()
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.open("x", encoding="utf-8").write(rendered)
    else:
        print(rendered, end="")
