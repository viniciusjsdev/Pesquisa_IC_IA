"""Groq Chat Completions for synthetic Bancada tests only."""
import json
import os
import re
import socket
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import Request

from . import models

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MODEL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")


class GroqError(RuntimeError):
    def __init__(self, status: str, message: str, retry_after: str | None = None,
                 metadata: dict | None = None):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after
        self.metadata = metadata or {}


def configuration() -> dict:
    key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", "").strip()
    valid = bool(key and MODEL_ID.fullmatch(model))
    return {"model": model if MODEL_ID.fullmatch(model) else None,
            "available": valid, "reason": None if valid else "GROQ_API_KEY e GROQ_MODEL válidos devem ser configurados no servidor"}


def chat_turn(messages: list[dict], temperature: float, max_tokens: int | None,
              *, tools: list[dict] | None) -> tuple[dict, dict]:
    """The production URL is fixed; local tests replace the transport."""
    settings = configuration()
    if not settings["available"]:
        raise GroqError("provider_unavailable", settings["reason"])
    model = settings["model"]
    payload = {"model": model, "messages": messages, "temperature": temperature,
               "stream": True, "stream_options": {"include_usage": True}}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if tools is not None:
        payload.update({"tools": tools, "tool_choice": "auto", "parallel_tool_calls": False})
    request = Request(ENDPOINT, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                      headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY'].strip()}",
                               "Content-Type": "application/json", "User-Agent": "PesquisaICIA/1.0"},
                      method="POST")
    provenance = {"provider": "groq", "model_id": model, "endpoint": ENDPOINT}
    try:
        with models.urlopen(request, timeout=600) as response:
            if response.headers.get("Content-Type", "").split(";")[0].strip() != "text/event-stream":
                raise GroqError("response_error", "Groq did not return a chat stream")
            result, _raw = models._read_chat_stream(response, ENDPOINT, model, provenance)
    except HTTPError as exc:
        retry_after = exc.headers.get("Retry-After") if exc.code == 429 else None
        retry_after = retry_after if retry_after and len(retry_after) <= 80 else None
        error_code = None
        invalid_tool_generation = False
        if exc.code == 400:
            try:
                body = json.loads(exc.read(4097))
                detail = body.get("error") if isinstance(body, dict) else None
                if isinstance(detail, dict):
                    error_code = detail.get("code")
                    invalid_tool_generation = detail.get("failed_generation") is not None
            except (ValueError, UnicodeDecodeError, OSError):
                pass
        status = ({400: "provider_bad_request", 401: "provider_auth_error",
                   403: "provider_auth_error", 429: "provider_rate_limited"}.get(exc.code)
                  or ("provider_error" if exc.code >= 500 else "provider_request_error"))
        if exc.code == 400 and error_code in {"context_length_exceeded", "context_window_exceeded"}:
            status = "context_limit"
        elif exc.code == 400 and invalid_tool_generation:
            status = "provider_tool_error"
        raise GroqError(status, f"Groq HTTP {exc.code}", retry_after) from None
    except (TimeoutError, socket.timeout):
        raise GroqError("provider_timeout", "Groq timed out") from None
    except (URLError, OSError, HTTPException):
        raise GroqError("provider_connection_error", "Groq connection failed") from None
    except models.ModelResponseError as exc:
        if isinstance(exc.__cause__, (TimeoutError, socket.timeout)):
            raise GroqError("provider_timeout", "Groq stream timed out") from None
        raise GroqError("stream_incomplete", "Groq stream incomplete or invalid") from exc
    choice = result["choices"][0]
    if choice["finish_reason"] not in {"stop", "tool_calls"}:
        status = "context_limit" if choice["finish_reason"] == "length" else "response_incomplete"
        raise GroqError(status, f"Groq finish_reason={choice['finish_reason']}", metadata={
            "usage": result.get("usage"), "finish_reason": choice["finish_reason"],
            "served_model": model})
    message = choice["message"]
    record = {**provenance, "served_model": model, "usage": result.get("usage"),
              "finish_reason": choice["finish_reason"], "raw_response_format": "sse"}
    return message, record
