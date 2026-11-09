"""One durable receipt per asynchronous Bancada submission; never auto-retry."""
from threading import Thread
from uuid import UUID

from inference_api import limits, service, storage
from inference_api.identity.auth import Principal


def submit(payload: dict, principal: Principal, request_key: str) -> dict:
    prepared = service.prepare(payload)
    if not isinstance(request_key, str):
        raise ValueError("request_key must be a UUID string")
    key = str(UUID(request_key))
    job, created = storage.create_job(principal.id, key, payload)
    if created:
        Thread(target=_execute, args=(job["id"], payload, principal, prepared), daemon=True,
               name=f"inference-job-{job['id'][:8]}").start()
    return job


def _execute(job_id: str, payload: dict, principal: Principal, prepared=None) -> None:
    try:
        with limits.reserve(principal.id):
            storage.update_job(job_id, "accepted", "running")
            run = service.execute_run(payload, principal, prepared=prepared,job_id=job_id)
            storage.update_job(job_id, "running", "completed", run_id=run["id"])
    except (limits.BusyError, limits.QuotaError) as exc:
        storage.update_job(job_id, "accepted", "busy", error=str(exc))
    except Exception as exc:
        # A run may already have been saved. Inspect history before manual retry.
        try:
            storage.update_job(job_id, "running", "failed", error=type(exc).__name__)
        except RuntimeError:
            storage.update_job(job_id, "accepted", "failed", error=type(exc).__name__)
