"""Read-only RunPod balance display, separate from the manual session ceiling."""
from datetime import datetime, timezone
import json
import math
import os
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

GRAPHQL = "https://api.runpod.io/graphql"
QUERY = "query SessionBudget { myself { clientBalance currentSpendPerHr } }"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        raise HTTPError(request.full_url, code, "RunPod redirect refused", headers, fp)


def _open(request):
    return build_opener(_NoRedirect).open(request, timeout=5)


def status() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    result = {
        "currency": "USD",
        "session_ceiling_usd": 10.0,
        "session_ceiling_kind": "manual_target_not_provider_enforced",
        "runpod_source": "RunPod GraphQL myself.clientBalance",
        "runpod_balance_usd": None,
        "runpod_spend_per_hour_usd": None,
        "runpod_status": "not_configured",
        "status_checked_at": now,
        "checked_at": None,
    }
    key = os.getenv("RUNPOD_BALANCE_READ_KEY", "").strip()
    if not key:
        result["reason"] = "RunPod balance read key is not configured"
        return result
    result["runpod_status"] = "read_failed"
    result["checked_at"] = now
    request = Request(
        GRAPHQL, data=json.dumps({"query": QUERY}).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with _open(request) as response:
            payload = json.load(response)
        if payload.get("errors"):
            raise ValueError("RunPod GraphQL returned an error")
        account = payload["data"]["myself"]
        balance = account["clientBalance"]
        spend = account["currentSpendPerHr"]
        if (not isinstance(balance, (int, float)) or isinstance(balance, bool)
                or not math.isfinite(balance)):
            raise ValueError("Invalid balance response")
        if spend is not None and (not isinstance(spend, (int, float))
                                  or isinstance(spend, bool) or not math.isfinite(spend)):
            raise ValueError("Invalid spend response")
        result.update({
            "runpod_balance_usd": float(balance),
            "runpod_spend_per_hour_usd": float(spend) if spend is not None else None,
            "runpod_status": "confirmed_read",
        })
    except Exception:
        result["reason"] = "RunPod balance read failed"
    return result
