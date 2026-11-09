"""Append-only experiment records in a separate local PostgreSQL database."""
import json
import os
from contextlib import closing
from pathlib import Path
import subprocess
from uuid import uuid4

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from inference_api.config import app_db_params, db_params

SCHEMA = """
CREATE TABLE IF NOT EXISTS prompt_revisions (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    revision integer NOT NULL CHECK (revision > 0),
    author text NOT NULL,
    system_prompt text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (name, revision)
);
CREATE TABLE IF NOT EXISTS runs (
    id uuid PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    author text NOT NULL,
    snapshot jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
    id uuid PRIMARY KEY,
    run_id uuid NOT NULL REFERENCES runs(id),
    author text NOT NULL,
    text text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
"""

MIGRATION = Path(__file__).resolve().parents[3] / "migrations" / "001_identity_up.sql"
CRITERIA_MIGRATION = Path(__file__).resolve().parents[3] / "migrations" / "002_criteria_up.sql"
JOBS_MIGRATION = Path(__file__).resolve().parents[3] / "migrations" / "003_run_jobs_up.sql"
OBSERVABILITY_MIGRATION = Path(__file__).resolve().parents[3] / "migrations" / "004_observability_up.sql"

def migrate_observability(backup_path: Path,pg_dump: str='pg_dump') -> None:
    """Explicit, additive application-DB migration; never invoked on startup."""
    params=app_db_params()
    if params['dbname']!='db_inference_app':raise ValueError('observability_application_database_required')
    backup_path=backup_path.resolve()
    if backup_path.exists():raise ValueError('Backup path already exists')
    backup_path.parent.mkdir(parents=True,exist_ok=True)
    with closing(psycopg2.connect(**params)) as conn,conn,conn.cursor() as cur:
        cur.execute('SELECT version FROM inference_schema_migrations')
        if not {1,2,3}<={row[0] for row in cur.fetchall()}:raise ValueError('Application migrations 1-3 required')
    result=subprocess.run([pg_dump,'--format=custom','--file',str(backup_path),'--host',params['host'],
        '--port',str(params['port']),'--username',params['user'],'--dbname',params['dbname']],
        env=dict(os.environ,PGPASSWORD=params['password']),capture_output=True,check=False)
    if result.returncode or not backup_path.is_file() or not backup_path.stat().st_size:
        raise RuntimeError('Logical backup failed; observability migration not applied')
    with closing(psycopg2.connect(**params)) as conn,conn,conn.cursor() as cur:
        cur.execute(OBSERVABILITY_MIGRATION.read_text(encoding='utf-8'))


class RevisionConflict(Exception):
    def __init__(self, kind: str, current: dict | None):
        super().__init__(f"{kind} revision conflict")
        self.kind = kind
        self.current = current


def initialize() -> None:
    """Explicit one-time setup; never runs implicitly on service startup."""
    params = db_params("FINANCEIRO")
    connection = psycopg2.connect(**params)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", ("db_inference_app",))
            if not cursor.fetchone():
                cursor.execute("CREATE DATABASE db_inference_app")
    finally:
        connection.close()
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA)


def migrate_identity(backup_path: Path, pg_dump: str = "pg_dump") -> None:
    """Explicit backup and one-way application; down SQL is kept for manual rollback."""
    backup_path = backup_path.resolve()
    if backup_path.exists():
        raise ValueError("Backup path already exists")
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    params = app_db_params()
    env = dict(os.environ, PGPASSWORD=params["password"])
    result = subprocess.run(
        [pg_dump, "--format=custom", "--file", str(backup_path),
         "--host", params["host"], "--port", str(params["port"]),
         "--username", params["user"], "--dbname", params["dbname"]],
        env=env, capture_output=True, text=True, check=False,
    )
    if result.returncode or not backup_path.is_file() or backup_path.stat().st_size == 0:
        raise RuntimeError("Logical backup failed; identity migration was not applied")
    with psycopg2.connect(**params) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.inference_schema_migrations')")
            if cursor.fetchone()[0] is not None:
                raise ValueError("Identity migration already applied")
            cursor.execute(MIGRATION.read_text(encoding="utf-8"))


def migrate_criteria(backup_path: Path, pg_dump: str = "pg_dump") -> None:
    """Apply version 2 only after a logical backup of the application database."""
    backup_path = backup_path.resolve()
    if backup_path.exists():
        raise ValueError("Backup path already exists")
    params = app_db_params()
    with psycopg2.connect(**params) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.inference_schema_migrations')")
            if cursor.fetchone()[0] is None:
                raise ValueError("Identity migration is required before criteria migration")
            cursor.execute("SELECT version FROM inference_schema_migrations ORDER BY version")
            versions = {row[0] for row in cursor.fetchall()}
            if 1 not in versions or 2 in versions:
                raise ValueError("Criteria migration requires version 1 and no version 2")
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PGPASSWORD=params["password"])
    result = subprocess.run(
        [pg_dump, "--format=custom", "--file", str(backup_path),
         "--host", params["host"], "--port", str(params["port"]),
         "--username", params["user"], "--dbname", params["dbname"]],
        env=env, capture_output=True, text=True, check=False,
    )
    if result.returncode or not backup_path.is_file() or backup_path.stat().st_size == 0:
        raise RuntimeError("Logical backup failed; criteria migration was not applied")
    with psycopg2.connect(**params) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM inference_schema_migrations WHERE version = 2")
            if cursor.fetchone():
                raise ValueError("Criteria migration already applied")
            cursor.execute(CRITERIA_MIGRATION.read_text(encoding="utf-8"))


def migrate_run_jobs(backup_path: Path, pg_dump: str = "pg_dump") -> None:
    """Add durable async job receipts after a logical application DB backup."""
    backup_path = backup_path.resolve()
    if backup_path.exists():
        raise ValueError("Backup path already exists")
    params = app_db_params()
    with closing(psycopg2.connect(**params)) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version FROM inference_schema_migrations ORDER BY version")
            if {row[0] for row in cursor.fetchall()} != {1, 2}:
                raise ValueError("Run job migration requires schema versions 1 and 2 only")
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PGPASSWORD=params["password"])
    result = subprocess.run(
        [pg_dump, "--format=custom", "--file", str(backup_path),
         "--host", params["host"], "--port", str(params["port"]),
         "--username", params["user"], "--dbname", params["dbname"]],
        env=env, capture_output=True, text=True, check=False,
    )
    if result.returncode or not backup_path.is_file() or backup_path.stat().st_size == 0:
        raise RuntimeError("Logical backup failed; run job migration was not applied")
    with closing(psycopg2.connect(**params)) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version FROM inference_schema_migrations ORDER BY version")
            if {row[0] for row in cursor.fetchall()} != {1, 2}:
                raise ValueError("Run job migration already applied or prerequisite changed")
            cursor.execute(JOBS_MIGRATION.read_text(encoding="utf-8"))


def create_job(researcher_id: str, request_key: str, request: dict) -> tuple[dict, bool]:
    from inference_api.executions.limits import BusyError

    job_id = str(uuid4())
    with closing(psycopg2.connect(**app_db_params())) as connection, connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""INSERT INTO run_jobs (id, researcher_id, request_key, request, status)
                              VALUES (%s, %s, %s, %s, 'accepted')
                              ON CONFLICT DO NOTHING RETURNING id""",
                           (job_id, researcher_id, request_key, Json(request)))
            created = cursor.fetchone() is not None
            cursor.execute("""SELECT id, researcher_id, request_key, request, status,
                                     run_id, error, created_at, started_at, finished_at
                              FROM run_jobs WHERE researcher_id = %s AND request_key = %s""",
                           (researcher_id, request_key))
            row = cursor.fetchone()
            if row is None:
                raise BusyError("Another inference is running; try again after it finishes")
            if row["request"] != request:
                raise ValueError("Request key was already used for different parameters")
            return _public_job(row), created


def get_job(job_id: str, researcher_id: str) -> dict | None:
    with closing(psycopg2.connect(**app_db_params())) as connection, connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""SELECT id, researcher_id, request_key, request, status,
                                     run_id, error, created_at, started_at, finished_at
                              FROM run_jobs WHERE id = %s AND researcher_id = %s""",
                           (job_id, researcher_id))
            row = cursor.fetchone()
            return _public_job(row) if row else None


def get_job_by_key(request_key: str, researcher_id: str) -> dict | None:
    with closing(psycopg2.connect(**app_db_params())) as connection, connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""SELECT id, researcher_id, request_key, request, status,
                                     run_id, error, created_at, started_at, finished_at
                              FROM run_jobs WHERE request_key = %s AND researcher_id = %s""",
                           (request_key, researcher_id))
            row = cursor.fetchone()
            return _public_job(row) if row else None


def update_job(job_id: str, previous: str, status: str, *, run_id: str | None = None,
               error: str | None = None) -> None:
    with closing(psycopg2.connect(**app_db_params())) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute("""UPDATE run_jobs SET status = %s, run_id = %s, error = %s,
                              started_at = CASE WHEN %s = 'running' THEN now() ELSE started_at END,
                              finished_at = CASE WHEN %s IN ('completed', 'failed', 'interrupted', 'busy')
                                                 THEN now() ELSE finished_at END
                              WHERE id = %s AND status = %s""",
                           (status, run_id, error, status, status, job_id, previous))
            if cursor.rowcount != 1:
                raise RuntimeError("Run job state changed unexpectedly")


def interrupt_unfinished_jobs() -> None:
    """No automatic retry after an API process restart."""
    with closing(psycopg2.connect(**app_db_params())) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute("""UPDATE run_jobs SET status = 'interrupted', finished_at = now(),
                              error = 'API process restarted; inspect history before a new attempt'
                              WHERE status IN ('accepted', 'running')""")


def _public_job(row: dict) -> dict:
    return _jsonable({key: row[key] for key in (
        "id", "status", "run_id", "error", "created_at", "started_at", "finished_at")})


def create_prompt(name: str, author: str, system_prompt: str,
                  expected_revision: int) -> dict:
    if not all(isinstance(x, str) and x.strip() for x in (name, author, system_prompt)):
        raise ValueError("Name, author and system prompt are required")
    if len(name) > 100 or len(author) > 100 or len(system_prompt) > 20000:
        raise ValueError("Prompt field exceeds size limit")
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError("expected_revision must be a non-negative integer")
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (name,))
            cursor.execute("SELECT coalesce(max(revision), 0) AS n FROM prompt_revisions WHERE name = %s", (name,))
            current = cursor.fetchone()["n"]
            if current != expected_revision:
                cursor.execute("""SELECT id, name, revision, author, system_prompt, created_at
                                  FROM prompt_revisions WHERE name = %s
                                  ORDER BY revision DESC LIMIT 1""", (name,))
                row = cursor.fetchone()
                raise RevisionConflict("prompt", _jsonable(row) if row else None)
            prompt_id = str(uuid4())
            cursor.execute("""INSERT INTO prompt_revisions (id, name, revision, author, system_prompt)
                              VALUES (%s, %s, %s, %s, %s)
                              RETURNING id, name, revision, author, system_prompt, created_at""",
                           (prompt_id, name, current + 1, author, system_prompt))
            return _jsonable(cursor.fetchone())


def list_prompts() -> list:
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""SELECT id, name, revision, author, system_prompt, created_at
                              FROM prompt_revisions ORDER BY name, revision DESC LIMIT 200""")
            return [_jsonable(row) for row in cursor.fetchall()]


def get_prompt(prompt_id: str) -> dict | None:
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""SELECT id, name, revision, author, system_prompt, created_at
                              FROM prompt_revisions WHERE id = %s""", (prompt_id,))
            row = cursor.fetchone()
            return _jsonable(row) if row else None


def create_criteria(name: str, author: str, config: dict,
                    expected_revision: int) -> dict:
    from inference_api.executions.criteria import validate
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        raise ValueError("Criteria name is required and limited to 100 characters")
    if not isinstance(author, str) or not author.strip() or len(author) > 100:
        raise ValueError("Criteria author is required")
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError("expected_revision must be a non-negative integer")
    clean = validate(config)
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("criteria:" + name,))
            cursor.execute("""SELECT coalesce(max(revision), 0) AS n
                              FROM verification_criteria_revisions WHERE name = %s""", (name,))
            current = cursor.fetchone()["n"]
            if current != expected_revision:
                cursor.execute("""SELECT id, name, revision, author, config, created_at
                                  FROM verification_criteria_revisions WHERE name = %s
                                  ORDER BY revision DESC LIMIT 1""", (name,))
                row = cursor.fetchone()
                raise RevisionConflict("criteria", _jsonable(row) if row else None)
            criterion_id = str(uuid4())
            cursor.execute("""INSERT INTO verification_criteria_revisions
                              (id, name, revision, author, config) VALUES (%s, %s, %s, %s, %s)
                              RETURNING id, name, revision, author, config, created_at""",
                           (criterion_id, name, current + 1, author, Json(clean)))
            return _jsonable(cursor.fetchone())


def list_criteria() -> list:
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""SELECT id, name, revision, author, config, created_at
                              FROM verification_criteria_revisions
                              ORDER BY name, revision DESC LIMIT 200""")
            return [_jsonable(row) for row in cursor.fetchall()]


def get_criteria(criteria_id: str) -> dict | None:
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""SELECT id, name, revision, author, config, created_at
                              FROM verification_criteria_revisions WHERE id = %s""",
                           (criteria_id,))
            row = cursor.fetchone()
            return _jsonable(row) if row else None


def create_run(author: str, snapshot: dict) -> dict:
    run_id = str(uuid4())
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""INSERT INTO runs (id, author, snapshot) VALUES (%s, %s, %s)
                              RETURNING id, created_at, author, snapshot""",
                           (run_id, author, Json(snapshot)))
            return _jsonable(cursor.fetchone())


def get_run(run_id: str,principal_id=None) -> dict | None:
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, created_at, author, snapshot FROM runs WHERE id = %s", (run_id,))
            row = cursor.fetchone()
            result=_jsonable(row) if row else None
    if result:
        from inference_api.observability.receipts import current
        result['observability_current']=current(run_id,principal_id)
    return result


def list_runs() -> list:
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""SELECT id, created_at, author, snapshot FROM runs
                              ORDER BY created_at DESC LIMIT 100""")
            return [_jsonable(row) for row in cursor.fetchall()]


def add_feedback(run_id: str, author: str, text: str) -> dict:
    if (not isinstance(author, str) or not isinstance(text, str) or
            not author.strip() or not text.strip() or len(author) > 100 or len(text) > 10000):
        raise ValueError("Author and feedback text are required; text limit is 10000 characters")
    feedback_id = str(uuid4())
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""INSERT INTO feedback (id, run_id, author, text)
                              VALUES (%s, %s, %s, %s)
                              RETURNING id, run_id, author, text, created_at""",
                           (feedback_id, run_id, author, text))
            return _jsonable(cursor.fetchone())


def _jsonable(row: dict) -> dict:
    return json.loads(json.dumps(dict(row), default=str))
