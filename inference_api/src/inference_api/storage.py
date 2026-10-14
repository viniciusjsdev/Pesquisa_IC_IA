"""Append-only experiment records in a separate local PostgreSQL database."""
import json
from uuid import uuid4

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from .config import app_db_params, db_params

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
                raise ValueError(f"Prompt revision conflict: current revision is {current}")
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


def create_run(author: str, snapshot: dict) -> dict:
    run_id = str(uuid4())
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""INSERT INTO runs (id, author, snapshot) VALUES (%s, %s, %s)
                              RETURNING id, created_at, author, snapshot""",
                           (run_id, author, Json(snapshot)))
            return _jsonable(cursor.fetchone())


def get_run(run_id: str) -> dict | None:
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, created_at, author, snapshot FROM runs WHERE id = %s", (run_id,))
            row = cursor.fetchone()
            return _jsonable(row) if row else None


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
