"""Database-backed global concurrency and daily run budgets."""
from contextlib import contextmanager
import os

import psycopg2

from .config import app_db_params

LOCK_KEY = 773104003


class BusyError(Exception):
    pass


class QuotaError(Exception):
    pass


def _optional_positive_setting(name: str) -> int | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    value = int(raw)
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


@contextmanager
def reserve(principal_id: str):
    """Reject a second run across threads/processes before any source or model call."""
    connection = psycopg2.connect(**app_db_params())
    connection.autocommit = True
    locked = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s)", (LOCK_KEY,))
            locked = cursor.fetchone()[0]
        if not locked:
            raise BusyError("Another inference is running; try again after it finishes")
        user_limit = _optional_positive_setting("INFERENCE_USER_DAILY_RUNS")
        global_limit = _optional_positive_setting("INFERENCE_GLOBAL_DAILY_RUNS")
        if user_limit is not None or global_limit is not None:
            connection.autocommit = False
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT (now() AT TIME ZONE 'America/Sao_Paulo')::date")
                    today = cursor.fetchone()[0]
                    if global_limit is not None:
                        cursor.execute("""
                            INSERT INTO inference_usage (usage_day, researcher_id, attempts)
                            VALUES (%s, NULL, 1)
                            ON CONFLICT (usage_day) WHERE researcher_id IS NULL
                            DO UPDATE SET attempts = inference_usage.attempts + 1
                            RETURNING attempts
                        """, (today,))
                        if cursor.fetchone()[0] > global_limit:
                            raise QuotaError("Global daily inference limit reached")
                    if user_limit is not None:
                        cursor.execute("""
                            INSERT INTO inference_usage (usage_day, researcher_id, attempts)
                            VALUES (%s, %s, 1)
                            ON CONFLICT (usage_day, researcher_id) WHERE researcher_id IS NOT NULL
                            DO UPDATE SET attempts = inference_usage.attempts + 1
                            RETURNING attempts
                        """, (today, principal_id))
                        if cursor.fetchone()[0] > user_limit:
                            raise QuotaError("User daily inference limit reached")
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        yield
    finally:
        if locked:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", (LOCK_KEY,))
        connection.close()
