"""Persist one synthetic SPEC-013 run/job locally, read it back and remove it.

No provider or research database is contacted. The script deletes only UUIDs it
created, and reports the cleanup result without exposing the fixture content.
"""

import argparse
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
from uuid import uuid4

import psycopg2


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inference_api" / "src"))
sys.path.insert(0, str(ROOT / "inference_api" / "tests"))
from inference_api import service, storage  # noqa: E402
from inference_api.identity.auth import Principal  # noqa: E402
from inference_api.config import app_db_params  # noqa: E402
from test_agent_harness import ScriptedModel, scripted_outputs  # noqa: E402


def verify() -> dict:
    with psycopg2.connect(**app_db_params()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SELECT id, username FROM researchers ORDER BY username LIMIT 1")
            researcher = cursor.fetchone()
            cursor.execute("SELECT count(*) FROM run_jobs WHERE status IN ('accepted', 'running')")
            active_jobs = cursor.fetchone()[0]
        connection.rollback()
    if researcher is None or active_jobs:
        raise RuntimeError("Existing researcher required and active jobs must be absent")
    principal = Principal(str(researcher[0]), researcher[1])
    payload = {"provider": "groq", "model_alias": "groq_harness",
               "evidence_mode": "agent_harness", "system_prompt": service.HARNESS_PROMPT}
    model = ScriptedModel(scripted_outputs())
    run_id = job_id = None
    report = {"provider_called": False, "research_database_queried": False,
              "run_readback": False, "job_readback": False,
              "idempotency_preserved": False, "cleanup_verified": False}
    try:
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture-key",
                                  "GROQ_HARNESS_MODEL": "qwen/qwen3.8-27b"}), \
             patch("inference_api.executions.service.synthetic_demo.make_groq_model_call",
                   return_value=model):
            run = service.execute_run(payload, principal)
        run_id = run["id"]
        saved = storage.get_run(run_id)
        report["run_readback"] = (saved is not None and
                                  saved["snapshot"]["harness_result"]["queries"] == 2 and
                                  saved["snapshot"]["schema_version"] == 6)
        report["model_calls"] = len(model.calls)
        key = str(uuid4())
        job, created = storage.create_job(principal.id, key, payload)
        job_id = job["id"]
        repeated, repeated_created = storage.create_job(principal.id, key, payload)
        report["idempotency_preserved"] = created and not repeated_created and repeated["id"] == job_id
        storage.update_job(job_id, "accepted", "running")
        storage.update_job(job_id, "running", "completed", run_id=run_id)
        saved_job = storage.get_job(job_id, principal.id)
        report["job_readback"] = saved_job["status"] == "completed" and saved_job["run_id"] == run_id
    finally:
        if run_id or job_id:
            with psycopg2.connect(**app_db_params()) as connection:
                with connection.cursor() as cursor:
                    if job_id:
                        cursor.execute("DELETE FROM run_jobs WHERE id = %s", (job_id,))
                    if run_id:
                        cursor.execute("DELETE FROM runs WHERE id = %s", (run_id,))
            with psycopg2.connect(**app_db_params()) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT count(*) FROM run_jobs WHERE id = %s", (job_id,))
                    jobs_remaining = cursor.fetchone()[0]
                    cursor.execute("SELECT count(*) FROM runs WHERE id = %s", (run_id,))
                    runs_remaining = cursor.fetchone()[0]
                connection.rollback()
            report["cleanup_verified"] = not jobs_remaining and not runs_remaining
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify()
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.open("x", encoding="utf-8").write(rendered)
    else:
        print(rendered, end="")
    return 0 if all(report[key] for key in
                    ("run_readback", "job_readback", "idempotency_preserved", "cleanup_verified")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
