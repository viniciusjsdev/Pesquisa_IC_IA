"""SPEC-005 session gates: local read-only preflight and explicit HTTP rehearsal.

The default action never calls an external URL or starts a service. The HTTP
rehearsal requires --execute and an existing, separately authorized session.
"""

import argparse
from contextlib import closing
from datetime import datetime, timedelta, timezone
from getpass import getpass
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

from inference_api import config, limits, orchestrator, serving_catalog  # noqa: E402
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


def _source(domain: str, table: str) -> dict:
    with closing(psycopg2.connect(**config.db_params(domain))) as connection:
        connection.set_session(readonly=True, autocommit=False)
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '5s'")
            cursor.execute(f"SELECT count(*) FROM {table}")
            count = cursor.fetchone()[0]
            cursor.execute("SHOW transaction_read_only")
            readonly = cursor.fetchone()[0]
    if count < 1 or readonly != "on":
        raise GateFailure("Existing source load is empty or connection is not read-only")
    return {"database": "db_" + domain.lower(), "table": table,
            "rows_in_existing_load": count, "transaction_read_only": True}


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
        _check("db_financeiro", lambda: _source("FINANCEIRO", "public.vendas")),
        _check("db_industrial", lambda: _source("INDUSTRIAL", "public.registros_operacao")),
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


class AppClient:
    def __init__(self, origin: str):
        self.origin = _origin(origin)
        self.opener = build_opener(_NoRedirect())

    def call(self, method: str, path: str, token: str = "", body: dict | None = None) -> tuple[int, dict | list]:
        if not path.startswith("/api/") or "?" in path:
            raise ValueError("Only application API paths are accepted")
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.origin + path, data=data, headers=headers, method=method)
        try:
            response = self.opener.open(request, timeout=120)
        except HTTPError as exc:
            if exc.code not in (400, 401, 403, 404, 409, 429):
                raise
            response = exc
        with closing(response):
            raw = response.read(2 * 1024 * 1024 + 1)
            status = response.status if hasattr(response, "status") else response.code
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Application response exceeded 2 MiB")
        return status, json.loads(raw)


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


def _expect(actual: int, expected: int, component: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{component} returned HTTP {actual}, expected {expected}")


def _report_path(path: Path) -> Path:
    allowed = (ROOT / "inference_api" / ".local").resolve()
    destination = path.resolve()
    if not destination.is_relative_to(allowed):
        raise ValueError("Reports must stay under inference_api/.local")
    if destination.exists():
        raise ValueError("Report already exists; no overwrite")
    return destination


def _tunnel_report(path: Path, origin: str) -> None:
    allowed = (ROOT / "inference_api" / ".local").resolve()
    source = path.resolve()
    if not source.is_relative_to(allowed):
        raise ValueError("Tunnel report must stay under inference_api/.local")
    report = json.loads(source.read_text(encoding="utf-8"))
    checked = datetime.fromisoformat(report["checked_at"])
    if checked.tzinfo is None:
        raise ValueError("Tunnel report timestamp must include a timezone")
    age = datetime.now(timezone.utc) - checked
    if (report.get("kind") != "ngrok_http_probe" or report.get("state") != "CONFIRMED" or
            report.get("origin") != origin or
            not timedelta(minutes=-2) <= age <= timedelta(minutes=30)):
        raise ValueError("Matching recent tunnel HTTP report is required")


def _save_report(path: Path, report: dict) -> None:
    destination = _report_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")


def _journal(path: Path, report: dict) -> None:
    """Keep exact created IDs even if a later HTTP gate fails."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def rehearsal(app: AppClient, aliases: list[str], year: int,
              passwords: dict[str, str], journal=None) -> dict:
    """One attempt per case; save each readback and stop at the first failed gate."""
    if len(aliases) != 2 or len(set(aliases)) != 2 or any(
            alias not in serving_catalog.MODELS for alias in aliases):
        raise ValueError("Select exactly two distinct catalog aliases")
    if type(year) is not int or not 2015 <= year <= 2026:
        raise ValueError("Year must be 2015 through 2026")
    report = {"schema_version": 1, "kind": "authorized_http_rehearsal",
              "started_at": datetime.now(timezone.utc).isoformat(),
              "application_origin": app.origin, "aliases": aliases, "year": year,
              "state": "UNCERTAIN", "runs": [], "created_run_ids": [],
              "revisions": [], "gates": [], "pending": None}
    if journal:
        journal(report)
    def mark_pending(component: str, details: dict) -> None:
        report["pending"] = {"component": component, **details}
        if journal:
            journal(report)

    def clear_pending() -> None:
        report["pending"] = None
        if journal:
            journal(report)

    sessions = {}
    stage = "unauthenticated_access"
    try:
        status, _ = app.call("GET", "/api/me")
        _expect(status, 401, "unauthenticated history gate")
        report["gates"].append({"component": "unauthenticated_access", "state": "CONFIRMED"})
        for username in ("Nicoli", "Vinicius"):
            stage = username + "_login"
            mark_pending(stage, {"author": username})
            status, result = app.call("POST", "/api/login", body={
                "username": username, "password": passwords[username]})
            _expect(status, 200, f"{username} login")
            sessions[username] = result["token"]
            status, me = app.call("GET", "/api/me", sessions[username])
            _expect(status, 200, f"{username} identity")
            if me.get("username") != username:
                raise RuntimeError("Application identity readback differs")
            clear_pending()
        report["gates"].append({"component": "two_verified_sessions", "state": "CONFIRMED"})
        stage = "model_catalog"
        status, catalog = app.call("GET", "/api/models", sessions["Nicoli"])
        _expect(status, 200, "model catalog")
        if not all(catalog.get(alias, {}).get("available") and
                   catalog[alias].get("generation_confirmed") for alias in aliases):
            raise RuntimeError("Selected aliases lack same-session generation receipts")
        report["gates"].append({"component": "model_catalog", "state": "CONFIRMED"})
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        name = "spec005-" + stamp
        prompts = []
        criteria = []
        config = {"schema_version": 1, "require_evidence": True, "require_period": True,
                  "required_units": [], "require_cited_ids": False, "required_caveats": []}
        for revision, username in enumerate(("Nicoli", "Vinicius")):
            token = sessions[username]
            revision_entry = {"author": username, "revision": revision + 1}
            report["revisions"].append(revision_entry)
            stage = username + "_prompt_revision"
            mark_pending(stage, {"name": name, "expected_revision": revision,
                                 "author": username})
            status, prompt = app.call("POST", "/api/prompts", token, {
                "name": name, "expected_revision": revision,
                "system_prompt": "Responda brevemente com os limites das evidências fornecidas."})
            _expect(status, 201, "prompt revision")
            revision_entry["prompt_id"] = prompt["id"]
            if journal:
                journal(report)
            clear_pending()
            stage = username + "_criteria_revision"
            mark_pending(stage, {"name": name, "expected_revision": revision,
                                 "author": username})
            status, criterion = app.call("POST", "/api/criteria", token, {
                "name": name, "expected_revision": revision, "config": config})
            _expect(status, 201, "criteria revision")
            revision_entry["criteria_id"] = criterion["id"]
            if journal:
                journal(report)
            clear_pending()
            if prompt.get("revision") != revision + 1 or criterion.get("revision") != revision + 1:
                raise RuntimeError("Revision readback differs")
            prompts.append(prompt["id"])
            criteria.append(criterion["id"])
        report["gates"].append({"component": "prompt_and_criteria_revisions", "state": "CONFIRMED"})
        for index, scope in enumerate(("financeiro", "industrial", "integrado")):
            for model_index, alias in enumerate(aliases):
                username = ("Nicoli", "Vinicius")[(index + model_index) % 2]
                stage = scope + "/" + alias + "_run"
                mark_pending(stage, {"scope": scope, "alias": alias, "year": year,
                                     "author": username, "prompt_id": prompts[model_index],
                                     "criteria_id": criteria[model_index]})
                status, created = app.call("POST", "/api/runs", sessions[username], {
                    "author": "forged-author", "question": "Que mostram os registros deste ano?",
                    "model_alias": alias, "prompt_revision_id": prompts[model_index],
                    "criteria_revision_id": criteria[model_index],
                    "scope": scope, "year": year, "temperature": 0, "max_tokens": 64})
                _expect(status, 201, f"{scope}/{alias} run")
                run_id = created["id"]
                report["created_run_ids"].append(run_id)
                stage = scope + "/" + alias + "_readback"
                mark_pending(stage, {"run_id": run_id, "scope": scope,
                                     "alias": alias, "author": username})
                status, readback = app.call("GET", "/api/runs/" + run_id, sessions[username])
                _expect(status, 200, "run readback")
                snapshot = readback["snapshot"]
                expected_tools = orchestrator.TOOLS_BY_SCOPE[scope]
                items = snapshot.get("evidence_bundle", {}).get("items", [])
                checks = snapshot.get("checks", [])
                if (readback.get("author") != username or
                        snapshot.get("identity", {}).get("author_verified") is not True or
                        snapshot.get("status") != "answered_unverified" or
                        snapshot.get("question_request", {}).get("scope") != scope or
                        snapshot.get("question_request", {}).get("year") != year or
                        snapshot.get("prompt", {}).get("revision_id") != prompts[model_index] or
                        snapshot.get("verification_criteria", {}).get("revision_id") != criteria[model_index] or
                        snapshot.get("model", {}).get("alias") != alias or
                        snapshot.get("model", {}).get("generation_confirmed") is not True or
                        snapshot.get("model", {}).get("provenance_status") != "session_manifest_checked" or
                        {item.get("tool") for item in items} != set(expected_tools) or
                        any(item.get("record_count", 0) < 1 for item in items) or
                        not checks or any(check.get("result") == "failed" for check in checks)):
                    raise RuntimeError(f"Run readback failed for {scope}/{alias}")
                report["runs"].append(readback)
                clear_pending()
        report["gates"].append({"component": "six_runs_three_scopes_two_models", "state": "CONFIRMED"})
        stage = "invalid_alias_rejected"
        mark_pending(stage, {"alias": "unknown-alias", "author": "Nicoli"})
        status, _ = app.call("POST", "/api/runs", sessions["Nicoli"], {
            "question": "Entrada inválida", "model_alias": "unknown-alias",
            "system_prompt": "Teste", "scope": "financeiro", "year": year})
        _expect(status, 400, "invalid alias gate")
        clear_pending()
        report["gates"].append({"component": "invalid_alias_rejected", "state": "CONFIRMED"})
        stage = "invalid_year_without_model"
        mark_pending(stage, {"alias": aliases[0], "scope": "financeiro",
                             "year": 2014, "author": "Vinicius"})
        status, invalid = app.call("POST", "/api/runs", sessions["Vinicius"], {
            "question": "Ano fora do contrato", "model_alias": aliases[0],
            "system_prompt": "Teste de rota", "scope": "financeiro", "year": 2014})
        _expect(status, 201, "invalid year snapshot")
        report["created_run_ids"].append(invalid["id"])
        stage += "_readback"
        mark_pending(stage, {"run_id": invalid["id"], "author": "Vinicius"})
        status, failed = app.call("GET", "/api/runs/" + invalid["id"], sessions["Vinicius"])
        _expect(status, 200, "invalid year readback")
        if failed["snapshot"].get("status") != "route_error" or failed.get("author") != "Vinicius":
            raise RuntimeError("Controlled route error readback differs")
        report["runs"].append(failed)
        clear_pending()
        report["gates"].append({"component": "invalid_year_without_model", "state": "CONFIRMED"})
        report["state"] = "CONFIRMED"
    except Exception as exc:
        report["state"] = "UNCERTAIN" if report["pending"] else "BLOCKED"
        report["gates"].append({"component": stage, "state": report["state"],
                                "reason": type(exc).__name__})
    finally:
        for username, token in sessions.items():
            try:
                status, _ = app.call("POST", "/api/logout", token)
                if status != 200:
                    report["gates"].append({"component": username + "_logout", "state": "UNCERTAIN"})
                    report["state"] = "UNCERTAIN"
            except Exception:
                report["gates"].append({"component": username + "_logout", "state": "UNCERTAIN"})
                report["state"] = "UNCERTAIN"
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        if journal:
            journal(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preflight", "rehearsal", "tunnel-check"))
    parser.add_argument("--execute", action="store_true", help="Permit existing-app HTTP calls and real generation")
    parser.add_argument("--app-origin")
    parser.add_argument("--aliases", nargs=2)
    parser.add_argument("--year", type=int, default=2020)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--tunnel-report", type=Path)
    parser.add_argument("--forwarding-reviewed", action="store_true")
    args = parser.parse_args()
    if args.action == "preflight":
        if args.execute or args.app_origin or args.aliases or args.tunnel_report or args.forwarding_reviewed:
            parser.error("preflight is local and accepts no HTTP execution flags")
        result = preflight()
        if args.output:
            _save_report(args.output, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["state"] == "CONFIRMED" else 2
    if args.action == "tunnel-check":
        if (not args.execute or not args.app_origin or not args.output or args.aliases or
                args.tunnel_report or args.forwarding_reviewed):
            parser.error("tunnel-check requires --execute, --app-origin and --output")
        destination = _report_path(args.output)
        result = tunnel_probe(args.app_origin)
        _save_report(destination, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["state"] == "CONFIRMED" else 2
    if not args.execute or not args.app_origin or not args.aliases or not args.output:
        parser.error("rehearsal requires --execute, --app-origin, two --aliases and --output")
    destination = _report_path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    gate = preflight()
    if gate["state"] != "CONFIRMED":
        print(json.dumps({"state": "BLOCKED", "preflight": gate}, ensure_ascii=False))
        return 2
    app = AppClient(args.app_origin)
    if urlsplit(app.origin).scheme == "https":
        if not args.tunnel_report or not args.forwarding_reviewed:
            parser.error("HTTPS rehearsal requires --tunnel-report and --forwarding-reviewed")
        _tunnel_report(args.tunnel_report, app.origin)
    passwords = {username: getpass(username + " password: ") for username in
                 ("Nicoli", "Vinicius")}
    result = rehearsal(app, args.aliases, args.year, passwords,
                       journal=lambda report: _journal(destination, report))
    print(json.dumps({"state": result["state"], "run_count": len(result["runs"]),
                      "report": str(args.output)}, ensure_ascii=False))
    return 0 if result["state"] == "CONFIRMED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
