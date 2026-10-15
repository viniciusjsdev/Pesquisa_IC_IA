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


def infer(alias: str, system_prompt: str, question: str, evidence: dict,
          temperature: float, max_tokens: int) -> tuple[str, dict]:
    if alias not in MODELS:
        raise ValueError("Unknown model alias")
    endpoint = vllm_url()
    if not endpoint:
        raise RuntimeError("vLLM endpoint is not configured")
    listed = available_models()[alias]
    if not listed["available"]:
        raise RuntimeError("Selected model is not served by vLLM")
    payload = {
        "model": alias,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question + "\n\nEvidências JSON:\n" + json.dumps(evidence, ensure_ascii=False)},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    headers = {"Content-Type": "application/json", **_headers()}
    request = Request(endpoint + "/v1/chat/completions", data=json.dumps(payload).encode(),
                      headers=headers, method="POST")
    with urlopen(request, timeout=120) as response:
        identity = serving_catalog.response_identity(response)
        raw_body = response.read()
    if listed.get("session_id") and (identity is None or
                                     identity["session_id"] != listed["session_id"]):
        raise ModelResponseError(
            "Serving session changed between catalog and generation",
            _serving_record(endpoint, raw_body.decode("utf-8", errors="replace"),
                            parsed=False, raw_body=raw_body),
        )
    attested = serving_catalog.provenance(alias, identity, endpoint)
    try:
        result = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ModelResponseError(
            "Invalid chat completion JSON",
            _serving_record(endpoint, raw_body.decode("utf-8", errors="replace"),
                            parsed=False, raw_body=raw_body, provenance=attested),
        ) from exc
    try:
        content = result["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError("Chat completion content is not text")
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelResponseError(
            "Invalid chat completion shape",
            _serving_record(endpoint, result, parsed=True, raw_body=raw_body,
                            provenance=attested),
        ) from exc
    if result.get("model", alias) != alias:
        raise ModelResponseError(
            "Chat completion model differs from requested alias",
            _serving_record(endpoint, result, parsed=True, raw_body=raw_body,
                            provenance=attested),
        )
    serving = _serving_record(endpoint, result, parsed=True, provenance=attested)
    serving["served_model"] = result.get("model", alias)
    return content, serving
