"""Explicit, refusal-based PostgreSQL 15 logical copy into an empty Compose volume.

No action occurs without --execute. The existing Windows cluster is read only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from datetime import datetime, timezone

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "inference_api" / "compose.yaml"
DATABASES = ("db_industrial", "db_financeiro", "db_inference_app")


def run(argv: list[str], *, env: dict[str, str] | None = None,
        stdin=None) -> str:
    result = subprocess.run(argv, env=env, stdin=stdin, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if result.returncode:
        # Never print tool stderr: libpq and Docker can include connection details.
        raise RuntimeError(f"Command failed ({Path(argv[0]).name}, exit {result.returncode})")
    return result.stdout.decode("utf-8", errors="replace").strip()


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def quoted(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def source_config(values: dict[str, str | None], database: str,
                  fixture: bool) -> tuple[dict[str, str], list[str]]:
    domain = "INDUSTRIAL" if database == "db_industrial" else "FINANCEIRO"
    prefix = domain + "_DB_"
    host, port = values.get(prefix + "HOST"), values.get(prefix + "PORT")
    name, user, password = (values.get(prefix + key) for key in ("NAME", "USER", "PASSWORD"))
    if not all((host, port, name, user, password)):
        raise ValueError(f"Incomplete {domain} source settings")
    if name != ("db_industrial" if domain == "INDUSTRIAL" else "db_financeiro"):
        raise ValueError(f"Unexpected {domain} source database")
    if host != "127.0.0.1" or (port == "5544") == fixture:
        raise ValueError("Source must be the isolated Windows port 5544, or an alternate fixture port with --fixture")
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        raise ValueError("Invalid source port")
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    flags = ["-h", host, "-p", port, "-U", user, "-d", database]
    return env, flags


def source_counts(psql: str, env: dict[str, str], flags: list[str]) -> dict[str, int]:
    query = "SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY 1,2"
    rows = run([psql, "-X", "-At", "-v", "ON_ERROR_STOP=1", *flags, "-c", query], env=env)
    counts: dict[str, int] = {}
    for row in rows.splitlines():
        schema, table = row.split("|", 1)
        sql = f"SELECT count(*) FROM {quoted(schema)}.{quoted(table)}"
        count = run([psql, "-X", "-At", "-v", "ON_ERROR_STOP=1", *flags, "-c", sql], env=env)
        counts[f"{schema}.{table}"] = int(count)
    return counts


def target_counts(compose: list[str], database: str) -> dict[str, int]:
    query = "SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY 1,2"
    rows = run([*compose, "exec", "-T", "db", "psql", "-X", "-At", "-v", "ON_ERROR_STOP=1",
                "-U", "pesquisa_local", "-d", database, "-c", query])
    counts: dict[str, int] = {}
    for row in rows.splitlines():
        schema, table = row.split("|", 1)
        sql = f"SELECT count(*) FROM {quoted(schema)}.{quoted(table)}"
        count = run([*compose, "exec", "-T", "db", "psql", "-X", "-At", "-v", "ON_ERROR_STOP=1",
                     "-U", "pesquisa_local", "-d", database, "-c", sql])
        counts[f"{schema}.{table}"] = int(count)
    return counts


def verify_target_volume(compose: list[str], project: str) -> None:
    container_id = run([*compose, "ps", "-q", "db"])
    if not container_id or len(container_id.splitlines()) != 1:
        raise ValueError("Expected one running Compose db container")
    container = json.loads(run(["docker", "inspect", container_id]))[0]
    labels = container["Config"].get("Labels") or {}
    expected_name = f"{project}_research_pgdata"
    mounts = [mount for mount in container.get("Mounts", [])
              if mount.get("Destination") == "/var/lib/postgresql/data"]
    if (not container["State"].get("Running") or
            labels.get("com.docker.compose.project") != project or
            labels.get("com.docker.compose.service") != "db" or
            len(mounts) != 1 or mounts[0].get("Type") != "volume" or
            mounts[0].get("Name") != expected_name):
        raise ValueError("Destination is not the expected running Compose db volume")
    volume = json.loads(run(["docker", "volume", "inspect", expected_name]))[0]
    volume_labels = volume.get("Labels") or {}
    if (volume_labels.get("com.docker.compose.project") != project or
            volume_labels.get("com.docker.compose.volume") != "research_pgdata"):
        raise ValueError("Destination volume identity could not be confirmed")


def verify_empty_target(compose: list[str]) -> None:
    existing = run([*compose, "exec", "-T", "db", "psql", "-X", "-At", "-v", "ON_ERROR_STOP=1",
                    "-U", "pesquisa_local", "-d", "postgres", "-c",
                    "SELECT datname || '|' || datistemplate || '|' || datallowconn "
                    "FROM pg_database ORDER BY datname"])
    if existing.splitlines() != ["postgres|false|true", "template0|true|false", "template1|true|true"]:
        raise ValueError("Target cluster database inventory differs from a fresh PostgreSQL 15 volume")
    # A full pg_dump also includes large objects and table data. Checking only
    # schema would miss blobs cloned from template1. Accept solely the
    # boilerplate from a newly initialized PostgreSQL 15 database.
    empty_schema_statements = {
        "SET statement_timeout = 0;", "SET lock_timeout = 0;",
        "SET idle_in_transaction_session_timeout = 0;", "SET client_encoding = 'UTF8';",
        "SET standard_conforming_strings = on;",
        "SELECT pg_catalog.set_config('search_path', '', false);",
        "SET check_function_bodies = false;", "SET xmloption = content;",
        "SET client_min_messages = warning;", "SET row_security = off;",
    }
    for database in ("postgres", "template1"):
        dump = run([*compose, "exec", "-T", "db", "pg_dump", "--format=plain",
                    "-U", "pesquisa_local", "-d", database])
        unexpected = [line.strip() for line in dump.splitlines()
                      if line.strip() and not line.startswith("--") and
                      not line.startswith("\\restrict ") and
                      not line.startswith("\\unrestrict ") and
                      line.strip() not in empty_schema_statements]
        if unexpected:
            raise ValueError(f"Target {database} database has user data or DDL; refusing all changes")
    roles = run([*compose, "exec", "-T", "db", "psql", "-X", "-At", "-v", "ON_ERROR_STOP=1",
                 "-U", "pesquisa_local", "-d", "postgres", "-c",
                 "SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%' ORDER BY rolname"])
    spaces = run([*compose, "exec", "-T", "db", "psql", "-X", "-At", "-v", "ON_ERROR_STOP=1",
                  "-U", "pesquisa_local", "-d", "postgres", "-c",
                  "SELECT spcname FROM pg_tablespace ORDER BY spcname"])
    if roles.splitlines() != ["pesquisa_local"] or spaces.splitlines() != ["pg_default", "pg_global"]:
        raise ValueError("Target cluster has unexpected roles or tablespaces; refusing all changes")


def copy(args: argparse.Namespace) -> dict:
    source_values = dotenv_values(args.source_env)
    if not args.compose_env.is_file() or not args.source_env.is_file():
        raise ValueError("Source and Compose environment files must exist")
    if not re.fullmatch(r"[a-z][a-z0-9_-]{2,50}", args.project):
        raise ValueError("Invalid Compose project name")
    if args.fixture and not args.project.startswith("spec008-test-"):
        raise ValueError("Fixture copy requires a spec008-test-* project")
    if args.inject_failure_after_first and not args.fixture:
        raise ValueError("Failure injection is fixture-only")

    pg_dump = str(args.pg_bin / ("pg_dump.exe" if os.name == "nt" else "pg_dump"))
    psql = str(args.pg_bin / ("psql.exe" if os.name == "nt" else "psql"))
    if not re.search(r"\b15\.\d+", run([pg_dump, "--version"])):
        raise ValueError("Host pg_dump must be PostgreSQL 15")
    compose = ["docker", "compose", "-p", args.project, "--env-file", str(args.compose_env), "-f", str(COMPOSE)]
    if not re.search(r"\b15\.\d+", run([*compose, "exec", "-T", "db", "pg_restore", "--version"])):
        raise ValueError("Target pg_restore must be PostgreSQL 15")
    verify_target_volume(compose, args.project)
    verify_empty_target(compose)
    if args.receipt.exists():
        raise ValueError("Receipt already exists; refusing to overwrite prior evidence")
    for database in DATABASES:
        source_config(source_values, database, args.fixture)

    receipt: dict = {"schema_version": 1, "spec_id": "SPEC-008", "state": "preparing",
                     "captured_at": datetime.now(timezone.utc).isoformat(),
                     "project": args.project, "source_mode": "fixture" if args.fixture else "isolated_windows_5544",
                     "databases": {}}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "inference_api" / ".local").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="spec008-dumps-", dir=ROOT / "inference_api" / ".local") as temp:
        dumps = {}
        for database in DATABASES:
            env, flags = source_config(source_values, database, args.fixture)
            path = Path(temp) / f"{database}.dump"
            run([pg_dump, *flags, "-Fc", "--no-owner", "--no-acl", "-f", str(path)], env=env)
            counts = source_counts(psql, env, flags)
            dumps[database] = (path, counts)
            receipt["databases"][database] = {"dump_sha256": digest(path), "dump_bytes": path.stat().st_size,
                                               "source_counts": counts, "state": "dumped"}
        args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for index, database in enumerate(DATABASES):
            path, counts = dumps[database]
            try:
                run([*compose, "exec", "-T", "db", "createdb", "-U", "pesquisa_local",
                     "--template=template1", database])
                with path.open("rb") as stream:
                    run([*compose, "exec", "-T", "db", "pg_restore", "-U", "pesquisa_local", "-d", database,
                         "--no-owner", "--no-acl", "--exit-on-error"], stdin=stream)
                target = target_counts(compose, database)
                if target != counts:
                    raise RuntimeError(f"Readback counts differ for {database}")
                receipt["databases"][database].update({"target_counts": target, "state": "confirmed"})
                if args.inject_failure_after_first and index == 0:
                    raise RuntimeError("Fixture-only injected failure after first database")
            except Exception:
                receipt["state"] = "partial_requires_manual_reconciliation"
                args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                raise
            args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt["state"] = "confirmed"
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="explicitly authorize this local Docker copy")
    parser.add_argument("--source-env", type=Path, default=ROOT / "BancoModeloUse" / ".env.local")
    parser.add_argument("--compose-env", type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--pg-bin", type=Path, default=Path(r"C:\Program Files\PostgreSQL\15\bin"))
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--fixture", action="store_true", help="allow only a disposable alternate source port")
    parser.add_argument("--inject-failure-after-first", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.execute:
        parser.error("--execute is required; no data copied")
    try:
        result = copy(args)
    except Exception as exc:
        parser.exit(1, f"Copy refused or incomplete: {exc}\n")
    print(f"Logical copy confirmed for {len(result['databases'])} databases; receipt: {args.receipt}")


if __name__ == "__main__":
    main()
