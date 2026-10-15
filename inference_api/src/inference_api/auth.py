"""Two named local researchers, password verification and revocable sessions."""
import hashlib
import hmac
import secrets
from collections import deque
from contextlib import closing, contextmanager
from dataclasses import dataclass
from threading import BoundedSemaphore, Lock
from time import monotonic
from uuid import UUID, uuid4

import psycopg2
from psycopg2.extras import RealDictCursor

from .config import app_db_params

ALLOWED_USERS = frozenset({"Nicoli", "Vinicius"})
ITERATIONS = 600_000
SESSION_HOURS = 12
MIN_PASSWORD_LENGTH = 12


class LoginBusy(Exception):
    pass


class LoginGate:
    """Bound PBKDF2 work per local API process without trusting proxy IP headers."""

    def __init__(self, max_attempts: int = 12, window_seconds: int = 60,
                 max_concurrent: int = 2):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._slots = BoundedSemaphore(max_concurrent)
        self._guard = Lock()
        self._attempts = deque()

    @contextmanager
    def attempt(self):
        if not self._slots.acquire(blocking=False):
            raise LoginBusy("Login is busy; try again shortly")
        try:
            now = monotonic()
            with self._guard:
                while self._attempts and now - self._attempts[0] >= self.window_seconds:
                    self._attempts.popleft()
                if len(self._attempts) >= self.max_attempts:
                    raise LoginBusy("Login rate limit reached; try again shortly")
                self._attempts.append(now)
            yield
        finally:
            self._slots.release()


LOGIN_GATE = LoginGate()


@dataclass(frozen=True)
class Principal:
    id: str
    username: str


def _digest(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)


def set_password(username: str, password: str) -> None:
    if username not in ALLOWED_USERS:
        raise ValueError("Only the two approved researchers can be registered")
    if not isinstance(password, str) or not MIN_PASSWORD_LENGTH <= len(password) <= 128:
        raise ValueError("Password must contain 12 to 128 characters")
    salt = secrets.token_bytes(32)
    digest = _digest(password, salt)
    with closing(psycopg2.connect(**app_db_params())) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO researchers (id, username, password_salt, password_digest, active)
                VALUES (%s, %s, %s, %s, true)
                ON CONFLICT (username) DO UPDATE SET
                  password_salt = excluded.password_salt,
                  password_digest = excluded.password_digest,
                  active = true,
                  failed_attempts = 0,
                  locked_until = NULL
                RETURNING id
            """, (str(uuid4()), username, psycopg2.Binary(salt), psycopg2.Binary(digest)))
            researcher_id = cursor.fetchone()[0]
            cursor.execute("DELETE FROM researcher_sessions WHERE researcher_id = %s",
                           (researcher_id,))


def revoke(username: str) -> None:
    if username not in ALLOWED_USERS:
        raise ValueError("Unknown researcher")
    with closing(psycopg2.connect(**app_db_params())) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE researchers SET active = false WHERE username = %s",
                           (username,))
            if cursor.rowcount != 1:
                raise ValueError("Researcher has not been registered")
            cursor.execute("""
                DELETE FROM researcher_sessions
                WHERE researcher_id = (SELECT id FROM researchers WHERE username = %s)
            """, (username,))


def login(username: str, password: str) -> dict | None:
    if (not isinstance(username, str) or not isinstance(password, str)
            or len(username) > 100 or len(password) > 128):
        return None
    with LOGIN_GATE.attempt():
        return _login_verified(username, password)


def _login_verified(username: str, password: str) -> dict | None:
    with closing(psycopg2.connect(**app_db_params())) as connection, connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, username, password_salt, password_digest, active
                FROM researchers WHERE username = %s FOR UPDATE
            """, (username if username in ALLOWED_USERS else "",))
            row = cursor.fetchone()
            salt = bytes(row["password_salt"]) if row else bytes(32)
            expected = bytes(row["password_digest"]) if row else bytes(32)
            valid = hmac.compare_digest(_digest(password, salt), expected)
            if not row or not row["active"] or not valid:
                if row and row["active"]:
                    cursor.execute("""
                        UPDATE researchers
                        SET failed_attempts = failed_attempts + 1
                        WHERE id = %s
                    """, (row["id"],))
                return None
            cursor.execute("""
                UPDATE researchers SET failed_attempts = 0, locked_until = NULL
                WHERE id = %s
            """, (row["id"],))
            session_id = uuid4()
            secret = secrets.token_urlsafe(32)
            session_salt = secrets.token_bytes(32)
            session_digest = hashlib.sha256(session_salt + secret.encode("ascii")).digest()
            cursor.execute("""
                INSERT INTO researcher_sessions
                  (id, researcher_id, token_salt, token_digest, expires_at)
                VALUES (%s, %s, %s, %s, now() + interval '12 hours')
            """, (str(session_id), row["id"], psycopg2.Binary(session_salt),
                  psycopg2.Binary(session_digest)))
            return {"username": row["username"], "token": f"{session_id}.{secret}",
                    "expires_in_seconds": SESSION_HOURS * 3600}


def authenticate(header: str) -> Principal | None:
    if not isinstance(header, str) or not header.startswith("Bearer "):
        return None
    token = header[len("Bearer "):]
    parts = token.split(".", 1)
    if len(parts) != 2 or len(parts[1]) > 128:
        return None
    try:
        session_id = str(UUID(parts[0]))
        secret = parts[1].encode("ascii")
    except (ValueError, UnicodeEncodeError):
        return None
    with closing(psycopg2.connect(**app_db_params())) as connection, connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT s.token_salt, s.token_digest, r.id, r.username
                FROM researcher_sessions s JOIN researchers r ON r.id = s.researcher_id
                WHERE s.id = %s AND s.expires_at > now() AND r.active
            """, (session_id,))
            row = cursor.fetchone()
    if not row:
        return None
    candidate = hashlib.sha256(bytes(row["token_salt"]) + secret).digest()
    if not hmac.compare_digest(candidate, bytes(row["token_digest"])):
        return None
    return Principal(str(row["id"]), row["username"])


def logout(header: str) -> None:
    principal = authenticate(header)
    if principal is None:
        return
    token = header[len("Bearer "):]
    session_id = str(UUID(token.split(".", 1)[0]))
    with closing(psycopg2.connect(**app_db_params())) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM researcher_sessions WHERE id = %s AND researcher_id = %s",
                           (session_id, principal.id))
