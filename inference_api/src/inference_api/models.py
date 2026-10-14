"""Explicit candidate catalog; serving availability is verified against vLLM."""
from base64 import b64encode
import json
from urllib.request import Request, urlopen

from .config import vllm_url

BASE = "Qwen/Qwen2.5-7B-Instruct"
MODELS = {
    "qwen-base": {"battery": "base", "kind": "base"},
    "ft-finqa-a": {"battery": "A", "kind": "adapter"},
    "ft-failure-a": {"battery": "A", "kind": "adapter"},
    "ft-hibrido-a": {"battery": "A", "kind": "adapter"},
    "ft-finqa-b": {"battery": "B", "kind": "adapter"},
    "ft-failure-b": {"battery": "B", "kind": "adapter"},
    "ft-hibrido-b": {"battery": "B", "kind": "adapter"},
}


class ModelResponseError(RuntimeError):
    """A server replied, but did not provide the expected chat response shape."""

    def __init__(self, message: str, serving: dict):
        super().__init__(message)
        self.serving = serving


def _serving_record(endpoint: str, response, *, parsed: bool,
                    raw_body: bytes | None = None) -> dict:
    record = {
        "endpoint": endpoint,
        "served_model": response.get("model") if isinstance(response, dict) else None,
        "usage": response.get("usage") if isinstance(response, dict) else None,
        "raw_response": response,
        "raw_response_format": "json" if parsed else "text",
        "base": BASE,
        "base_revision": None,
        "adapter_run": None,
        "adapter_hash": None,
    }
    if raw_body is not None:
        record["raw_response_bytes_b64"] = b64encode(raw_body).decode("ascii")
    return record


def available_models() -> dict:
    endpoint = vllm_url()
    if not endpoint:
        return {alias: {**details, "available": False} for alias, details in MODELS.items()}
    request = Request(endpoint + "/v1/models", headers=_headers())
    with urlopen(request, timeout=8) as response:
        payload = json.load(response)
    served = {item["id"] for item in payload["data"]}
    return {alias: {**details, "available": alias in served} for alias, details in MODELS.items()}


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
    if not available_models()[alias]["available"]:
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
        raw_body = response.read()
    try:
        result = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ModelResponseError(
            "Invalid chat completion JSON",
            _serving_record(endpoint, raw_body.decode("utf-8", errors="replace"),
                            parsed=False, raw_body=raw_body),
        ) from exc
    try:
        content = result["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError("Chat completion content is not text")
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelResponseError(
            "Invalid chat completion shape",
            _serving_record(endpoint, result, parsed=True, raw_body=raw_body),
        ) from exc
    serving = _serving_record(endpoint, result, parsed=True)
    serving["served_model"] = result.get("model", alias)
    return content, serving
