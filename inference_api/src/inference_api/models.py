"""Explicit candidate catalog; serving availability is verified against vLLM."""
from base64 import b64encode
from http.client import HTTPException
from urllib.error import HTTPError
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


MAX_STREAM_BYTES = 8 * 1024 * 1024


def _read_chat_stream(response, endpoint: str, alias: str, provenance: dict) -> tuple[dict, bytes]:
    """Reassemble one OpenAI SSE turn while retaining the exact upstream bytes."""
    raw = bytearray()
    content = []
    calls: dict[int, dict] = {}
    usage = None
    finish = None
    done = False
    model = None
    try:
        for line in response:
            raw.extend(line)
            if len(raw) > MAX_STREAM_BYTES:
                raise ValueError("Stream exceeds size limit")
            if done:
                if line.strip():
                    raise ValueError("Data after stream completion")
                continue
            if not line.startswith(b"data: "):
                continue
            data = line[6:].strip()
            if data == b"[DONE]":
                done = True
                continue
            chunk = json.loads(data)
            if chunk.get("model") != alias:
                raise ValueError("Served model differs from alias")
            model = chunk["model"]
            if chunk.get("usage") is not None:
                usage = chunk["usage"]
            choices = chunk.get("choices") or []
            for choice in choices:
                if choice.get("index") != 0:
                    raise ValueError("Unexpected choice index")
                if choice.get("finish_reason") is not None:
                    finish = choice["finish_reason"]
                delta = choice.get("delta") or {}
                if delta.get("content") is not None:
                    if not isinstance(delta["content"], str):
                        raise ValueError("Invalid content delta")
                    content.append(delta["content"])
                for part in delta.get("tool_calls") or []:
                    index = part["index"]
                    if type(index) is not int or index < 0 or index > 20:
                        raise ValueError("Invalid tool index")
                    call = calls.setdefault(index, {"id": None, "type": None,
                                                    "function": {"name": "", "arguments": ""}})
                    if part.get("id") is not None:
                        if call["id"] is not None and call["id"] != part["id"]:
                            raise ValueError("Tool ID changed")
                        call["id"] = part["id"]
                    if part.get("type") is not None:
                        call["type"] = part["type"]
                    function = part.get("function") or {}
                    for field in ("name", "arguments"):
                        fragment = function.get(field)
                        if fragment is not None:
                            if not isinstance(fragment, str):
                                raise ValueError("Invalid tool delta")
                            call["function"][field] += fragment
        if not done or finish is None or model != alias:
            raise ValueError("Incomplete chat stream")
        if finish in {"stop", "tool_calls"} and bool(calls) != (finish == "tool_calls"):
            raise ValueError("Tool finish mismatch")
        if calls and (sorted(calls) != list(range(len(calls))) or any(
                call["type"] != "function" or not call["id"] or
                not call["function"]["name"] for call in calls.values())):
            raise ValueError("Incomplete tool call")
    except (ValueError, KeyError, TypeError, IndexError, OSError, HTTPException) as exc:
        raise ModelResponseError("Invalid or incomplete chat stream",
                                 _serving_record(endpoint, raw.decode("utf-8", errors="replace"),
                                                 parsed=False, raw_body=bytes(raw),
                                                 provenance=provenance)) from exc
    message = {"role": "assistant", "content": "".join(content),
               **({"tool_calls": [calls[i] for i in sorted(calls)]} if calls else {})}
    return {"model": model, "choices": [{"index": 0, "finish_reason": finish,
                                            "message": message}], "usage": usage}, bytes(raw)


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
    from . import groq
    groq_settings = groq.configuration()
    groq_entry = {"groq": {"provider": "groq", "kind": "hosted", "model_id": groq_settings["model"],
                           "available": groq_settings["available"], "reason": groq_settings["reason"],
                           "generation_confirmed": False}}
    try:
        endpoint = vllm_url()
    except ValueError:
        endpoint = ""
    if not endpoint:
        return {alias: {**details, "candidate": True, "available": False,
                        "provider": "runpod", "generation_confirmed": False,
                        "reason": "RunPod serving session not configured"} for alias, details in MODELS.items()} | groq_entry
    try:
        request = Request(endpoint + "/v1/models", headers=_headers())
        with urlopen(request, timeout=8) as response:
            payload = json.load(response)
            identity = serving_catalog.response_identity(response)
    except HTTPError as exc:
        if 300 <= exc.code < 400:
            raise
        return {alias: {**details, "candidate": True, "available": False,
                        "provider": "runpod", "generation_confirmed": False,
                        "reason": "RunPod serving session unavailable"} for alias, details in MODELS.items()} | groq_entry
    except Exception:
        return {alias: {**details, "candidate": True, "available": False,
                        "provider": "runpod", "generation_confirmed": False,
                        "reason": "RunPod serving session unavailable"} for alias, details in MODELS.items()} | groq_entry
    served = {item["id"] for item in payload["data"]}
    return {alias: {**details, "candidate": True, "provider": "runpod", "available": alias in served and identity is not None,
                    "generation_confirmed": alias in served and
                    serving_catalog.generation_confirmed(endpoint, identity, alias),
                    "session_id": identity["session_id"] if identity else None,
                    "reason": None if alias in served and identity else "RunPod serving session not attested"}
            for alias, details in MODELS.items()} | groq_entry


def _headers() -> dict:
    from os import getenv
    token = getenv("INFERENCE_VLLM_TOKEN", "").strip()
    headers = {"User-Agent": "PesquisaICIA/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def chat_turn(alias: str, messages: list[dict], temperature: float, max_tokens: int | None,
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
               "stream": True, "stream_options": {"include_usage": True}}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if tools is not None:
        payload.update({"tools": tools, "tool_choice": "auto", "parallel_tool_calls": False})
    request = Request(endpoint + "/v1/chat/completions",
                      data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                      headers={"Content-Type": "application/json", **_headers()}, method="POST")
    with urlopen(request, timeout=600) as response:
        identity = serving_catalog.response_identity(response)
        if identity is None or identity["session_id"] != listed["session_id"]:
            raise ModelResponseError("Serving session changed during turn",
                                     {"endpoint": endpoint, "session_id": listed["session_id"]})
        provenance = serving_catalog.provenance(alias, identity, endpoint)
        if response.headers.get("Content-Type", "").split(";")[0].strip() != "text/event-stream":
            raw_body = response.read(MAX_STREAM_BYTES + 1)
            raise ModelResponseError("Serving endpoint did not stream chat completion",
                                     _serving_record(endpoint, raw_body.decode("utf-8", errors="replace"),
                                                     parsed=False, raw_body=raw_body,
                                                     provenance=provenance))
        result, raw_body = _read_chat_stream(response, endpoint, alias, provenance)
    try:
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
        invalid = _serving_record(endpoint, result, parsed=True, raw_body=raw_body,
                                  provenance=provenance)
        invalid["raw_response_format"] = "sse"
        raise ModelResponseError("Invalid chat completion shape",
                                 invalid) from exc
    record = _serving_record(endpoint, result, parsed=True, raw_body=raw_body, provenance=provenance)
    record["raw_response_format"] = "sse"
    record["request"] = payload
    return message, record
