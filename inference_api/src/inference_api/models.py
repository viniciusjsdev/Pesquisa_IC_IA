"""Explicit candidate catalog; serving availability is verified against vLLM."""
from base64 import b64encode
import json
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .config import vllm_url
from . import serving_catalog

BASE = serving_catalog.BASE
MODELS = serving_catalog.MODELS


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def urlopen(request, timeout):
    """Keep the backend bearer token on the configured serving origin."""
    return build_opener(_NoRedirect()).open(request, timeout=timeout)


class ModelResponseError(RuntimeError):
    """A server replied, but did not provide the expected chat response shape."""

    def __init__(self, message: str, serving: dict):
        super().__init__(message)
        self.serving = serving


def _serving_record(endpoint: str, response, *, parsed: bool,
                    raw_body: bytes | None = None, provenance: dict | None = None) -> dict:
    record = {
        "endpoint": endpoint,
        "served_model": response.get("model") if isinstance(response, dict) else None,
        "usage": response.get("usage") if isinstance(response, dict) else None,
        "raw_response": response,
        "raw_response_format": "json" if parsed else "text",
        "base": BASE,
        **(provenance or serving_catalog.provenance("qwen-base", None, endpoint)),
    }
    if raw_body is not None:
        record["raw_response_bytes_b64"] = b64encode(raw_body).decode("ascii")
    return record


def available_models() -> dict:
    endpoint = vllm_url()
    if not endpoint:
        return {alias: {**details, "candidate": True, "available": False,
                        "generation_confirmed": False} for alias, details in MODELS.items()}
    request = Request(endpoint + "/v1/models", headers=_headers())
    with urlopen(request, timeout=8) as response:
        payload = json.load(response)
        identity = serving_catalog.response_identity(response)
    served = {item["id"] for item in payload["data"]}
    return {alias: {**details, "candidate": True, "available": alias in served,
                    "generation_confirmed": alias in served and
                    serving_catalog.generation_confirmed(endpoint, identity, alias),
                    "session_id": identity["session_id"] if identity else None}
            for alias, details in MODELS.items()}


def _headers() -> dict:
    from os import getenv
    token = getenv("INFERENCE_VLLM_TOKEN", "").strip()
    return {"Authorization": f"Bearer {token}"} if token else {}


def chat_turn(alias: str, messages: list[dict], temperature: float, max_tokens: int,
              *, tools: list[dict] | None, session_id: str | None) -> tuple[dict, dict]:
    """One OpenAI chat turn; caller owns tool validation and conversation limits."""
    if alias not in MODELS:
        raise ValueError("Unknown model alias")
    endpoint = vllm_url()
    if not endpoint:
        raise RuntimeError("vLLM endpoint is not configured")
    listed = available_models()[alias]
    if not listed["available"] or not listed.get("session_id"):
        raise RuntimeError("Selected model has no attested serving session")
    if session_id is not None and listed["session_id"] != session_id:
        raise ModelResponseError("Serving session changed before turn", {"session_id": listed["session_id"]})
    payload = {"model": alias, "messages": messages, "temperature": temperature,
               "max_tokens": max_tokens, "stream": False}
    if tools is not None:
        payload.update({"tools": tools, "tool_choice": "auto", "parallel_tool_calls": False})
    request = Request(endpoint + "/v1/chat/completions",
                      data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                      headers={"Content-Type": "application/json", **_headers()}, method="POST")
    with urlopen(request, timeout=120) as response:
        identity = serving_catalog.response_identity(response)
        raw_body = response.read()
    if identity is None or identity["session_id"] != listed["session_id"]:
        raise ModelResponseError("Serving session changed during turn",
                                 _serving_record(endpoint, raw_body.decode("utf-8", errors="replace"),
                                                 parsed=False, raw_body=raw_body))
    provenance = serving_catalog.provenance(alias, identity, endpoint)
    try:
        result = json.loads(raw_body)
        choice = result["choices"][0]
        message = choice["message"]
        if not isinstance(message, dict) or message.get("role") != "assistant":
            raise TypeError("Invalid assistant message")
        finish = choice.get("finish_reason")
        if finish not in {"stop", "tool_calls"} or bool(message.get("tool_calls")) != (finish == "tool_calls"):
            raise TypeError("Invalid or incomplete chat turn")
        if result.get("model", alias) != alias:
            raise TypeError("Served model differs from alias")
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise ModelResponseError("Invalid chat completion shape",
                                 _serving_record(endpoint, raw_body.decode("utf-8", errors="replace"),
                                                 parsed=False, raw_body=raw_body, provenance=provenance)) from exc
    record = _serving_record(endpoint, result, parsed=True, raw_body=raw_body, provenance=provenance)
    record["request"] = payload
    return message, record
