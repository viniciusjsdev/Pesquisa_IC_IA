"""Local read-only preflight and explicit tunnel HTTP check.

The SPEC-005 scope-based rehearsal was retired by SPEC-009. No generation runs
from this script; a future paid rehearsal needs a new explicit contract.
"""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "inference_api" / "src"))
sys.path.insert(0, str(ROOT / "runpod" / "serving"))

from inference_api import config, limits  # noqa: E402
import serving  # noqa: E402


class GateFailure(ValueError):
    """A short, safe gate reason intended for an operator report."""


def _check(name: str, operation) -> dict:
    try:
        evidence = operation()
        return {"component": name, "state": "CONFIRMED", "evidence": evidence}
    except Exception as exc:
        # Operational error strings can contain connection details. Report type
        # and component only; keep credentials and server bodies out of logs.
        result = {"component": name, "state": "BLOCKED", "reason": type(exc).__name__}
        if isinstance(exc, GateFailure):
            result["detail"] = str(exc)
        return result


def _git() -> dict:
    result = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                            cwd=ROOT, capture_output=True, text=True, check=True)
    changes = [line for line in result.stdout.splitlines() if line]
    if changes:
        raise GateFailure(f"Checkout has {len(changes)} changed paths requiring review")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()
    return {"head": head, "working_tree": "clean"}


def _dw() -> dict:
    with closing(psycopg2.connect(**config.dw_db_params())) as connection:
        connection.set_session(readonly=True, autocommit=False)
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '5s'")
            cursor.execute("SELECT version, source_fingerprint FROM dw.schema_migrations")
            rows = cursor.fetchall()
            cursor.execute("SHOW transaction_read_only")
            readonly = cursor.fetchone()[0]
    if len(rows) != 1 or rows[0][0] != 1 or readonly != "on":
        raise GateFailure("DW v1 migration or read-only transaction unavailable")
    return {"database": "db_pesquisa_dw", "schema_version": 1,
            "source_fingerprint": rows[0][1].strip(), "transaction_read_only": True}


def _app() -> dict:
    with closing(psycopg2.connect(**config.app_db_params())) as connection:
        connection.set_session(readonly=True, autocommit=False)
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '5s'")
            cursor.execute("SELECT version FROM inference_schema_migrations ORDER BY version")
            versions = [row[0] for row in cursor.fetchall()]
            cursor.execute("SELECT username, active FROM researchers ORDER BY username")
            users = cursor.fetchall()
            cursor.execute("SHOW transaction_read_only")
            readonly = cursor.fetchone()[0]
    if versions != [1, 2] or users != [("Nicoli", True), ("Vinicius", True)] or readonly != "on":
        raise GateFailure("Application migrations, approved identities or read-only connection are incomplete")
    return {"database": "db_inference_app", "schema_versions": versions,
            "active_researchers": [row[0] for row in users], "transaction_read_only": True}


def _artifacts() -> dict:
    try:
        return serving.validate(serving.load_manifest(), ROOT)
    except (OSError, ValueError, KeyError) as exc:
        raise GateFailure("Adapter manifest, file path or SHA-256 validation failed") from exc


def _serving_config() -> dict:
    revision = os.getenv("INFERENCE_BASE_REVISION", "").strip()
    endpoint = config.vllm_url()
    token = os.getenv("INFERENCE_VLLM_TOKEN", "")
    if not serving.REVISION.fullmatch(revision):
        raise GateFailure("INFERENCE_BASE_REVISION needs an exact 40-character commit")
    if not endpoint:
        raise GateFailure("INFERENCE_VLLM_URL is not configured")
    if len(token) < 32:
        raise GateFailure("INFERENCE_VLLM_TOKEN is missing or too short")
    return {"base_revision": revision, "endpoint": endpoint,
            "gateway_credential": "configured", "network_call": False}


def _limits() -> dict:
    if (os.getenv("INFERENCE_USER_DAILY_RUNS", "").strip() or
            os.getenv("INFERENCE_GLOBAL_DAILY_RUNS", "").strip() or
            not isinstance(limits.LOCK_KEY, int)):
        raise GateFailure("Session limits differ from one global inference and no daily quota")
    return {"global_concurrent_inferences": 1, "daily_quotas": "disabled",
            "evidence_kind": "configuration_only"}


def preflight() -> dict:
    """Read only checkout, artifacts and loopback databases; no external HTTP."""
    checks = [
        _check("git", _git),
        _check("db_pesquisa_dw", _dw),
        _check("db_inference_app", _app),
        _check("adapters", _artifacts),
        _check("serving_configuration", _serving_config),
        _check("limits", _limits),
    ]
    return {"schema_version": 1, "checked_at": datetime.now(timezone.utc).isoformat(),
            "kind": "local_preflight", "state": "CONFIRMED" if all(
                item["state"] == "CONFIRMED" for item in checks) else "BLOCKED",
            "checks": checks, "remote_generation": "not_run", "ngrok_http": "not_run",
            "scientific_evaluation": "not_run"}


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def _origin(value: str) -> str:
    parsed = urlsplit(value)
    loopback = parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and parsed.port == 8765
    if (not (parsed.scheme == "https" or loopback) or not parsed.hostname or
            parsed.username or parsed.password or parsed.query or parsed.fragment or
            parsed.path not in ("", "/")):
        raise ValueError("Application origin must be HTTPS or http://127.0.0.1:8765")
    return value.rstrip("/")



def tunnel_probe(origin: str) -> dict:
    """Probe only this HTTPS application origin; tunnel target still needs readback."""
    origin = _origin(origin)
    if urlsplit(origin).scheme != "https":
        raise ValueError("Tunnel probe requires a public HTTPS origin")
    opener = build_opener(_NoRedirect())
    expected = {"/": 200, "/api/me": 401, "/api/runs": 401,
                "/api/models": 401, "/v1/models": 404}
    checks = []
    for path, wanted in expected.items():
        request = Request(origin + path, method="GET")
        try:
            response = opener.open(request, timeout=10)
        except HTTPError as exc:
            response = exc
        except Exception as exc:
            checks.append({"path": path, "state": "BLOCKED",
                           "reason": type(exc).__name__})
            break
        with closing(response):
            status = response.status if hasattr(response, "status") else response.code
            response.read(1024)
        checks.append({"path": path, "http_status": status,
                       "state": "CONFIRMED" if status == wanted else "BLOCKED"})
        if status != wanted:
            break
    return {"schema_version": 1, "kind": "ngrok_http_probe", "checked_at":
            datetime.now(timezone.utc).isoformat(), "origin": origin,
            "state": "CONFIRMED" if len(checks) == len(expected) and all(
                item["state"] == "CONFIRMED" for item in checks) else "BLOCKED",
            "checks": checks, "tunnel_target_readback": "manual_required",
            "other_tunnels_readback": "manual_required"}



def _report_path(path: Path) -> Path:
    allowed = (ROOT / "inference_api" / ".local").resolve()
    destination = path.resolve()
    if not destination.is_relative_to(allowed):
        raise ValueError("Reports must stay under inference_api/.local")
    if destination.exists():
        raise ValueError("Report already exists; no overwrite")
    return destination



def _save_report(path: Path, report: dict) -> None:
    destination = _report_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preflight", "tunnel-check"))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--app-origin")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "preflight":
        if args.execute or args.app_origin:
            parser.error("preflight is local and accepts no HTTP execution flags")
        result = preflight()
        if args.output:
            _save_report(args.output, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["state"] == "CONFIRMED" else 2
    if not args.execute or not args.app_origin or not args.output:
        parser.error("tunnel-check requires --execute, --app-origin and --output")
    result = tunnel_probe(args.app_origin)
    _save_report(args.output, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["state"] == "CONFIRMED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
