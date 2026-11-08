"""Stateless OpenAI Responses turns for the explicit Bancada provider."""
import json
import os
import re
import socket
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import Request

from inference_api import models

ENDPOINT = "https://api.openai.com/v1/responses"
MODEL = "gpt-6-luna"
API_SURFACE = "responses/v1"
DEFAULT_MAX_OUTPUT_TOKENS = 4096
MAX_OUTPUT_TOKENS = 8192
MAX_STREAM_BYTES = 8 * 1024 * 1024
_SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_SAFE_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
_SAFE_KEY = re.compile(r"[A-Za-z0-9_-]{10,512}\Z")
_BILLING_CODES = {"credit_balance_exhausted", "organization_spend_limit_exceeded",
                  "project_spend_limit_exceeded", "organization_usage_limit_exceeded",
                  "insufficient_quota"}


class OpenAIError(RuntimeError):
    def __init__(self, status: str, message: str, retry_after: str | None = None,
                 metadata: dict | None = None):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after
        self.metadata = metadata or {}


def configuration() -> dict:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    valid = bool(_SAFE_KEY.fullmatch(key))
    return {"model": MODEL, "available": valid,
            "dw_enabled": valid and os.getenv("INFERENCE_OPENAI_DW_ENABLED") == "1",
            "reason": None if valid else
            "OPENAI_API_KEY deve ser configurada no servidor"}


def _usage(value: object) -> dict | None:
    if not isinstance(value, dict):
        return None
    result = {key: value[key] for key in ("input_tokens", "output_tokens", "total_tokens")
              if type(value.get(key)) is int and value[key] >= 0}
    for key, fields in (("input_tokens_details", ("cached_tokens",)),
                        ("output_tokens_details", ("reasoning_tokens",))):
        details = value.get(key)
        if isinstance(details, dict):
            kept = {field: details[field] for field in fields
                    if type(details.get(field)) is int and details[field] >= 0}
            if kept:
                result[key] = kept
    return result or None


def _safe_id(value: object) -> str | None:
    return value if isinstance(value, str) and _SAFE_ID.fullmatch(value) else None


def _response_metadata(value: object) -> dict:
    if not isinstance(value, dict):
        return {}
    model = value.get("model")
    return {"response_id": _safe_id(value.get("id")),
            "served_model": model if isinstance(model, str) and _SAFE_MODEL.fullmatch(model) else None,
            "usage": _usage(value.get("usage"))}


def _read_stream(response) -> dict:
    size = 0
    completed = None
    try:
        for line in response:
            size += len(line)
            if size > MAX_STREAM_BYTES:
                raise OpenAIError("stream_incomplete", "OpenAI stream exceeded size limit")
            if not line.startswith(b"data: "):
                continue
            event = json.loads(line[6:])
            if not isinstance(event, dict):
                raise ValueError("Invalid stream event")
            kind = event.get("type")
            if kind == "response.completed":
                if completed is not None:
                    raise ValueError("Duplicate response completion")
                completed = event.get("response")
            elif kind == "response.incomplete":
                partial = event.get("response")
                details = partial.get("incomplete_details") if isinstance(partial, dict) else None
                reason = details.get("reason") if isinstance(details, dict) else None
                raise OpenAIError("context_limit" if reason == "max_output_tokens" else
                                  "response_incomplete", "OpenAI response incomplete",
                                  metadata={**_response_metadata(partial),
                                            "finish_reason": reason if reason in
                                            {"max_output_tokens", "content_filter"} else None})
            elif kind in {"response.failed", "error"}:
                failed = event.get("response")
                detail = failed.get("error") if kind == "response.failed" and isinstance(failed, dict) else event
                code = detail.get("code") if isinstance(detail, dict) else None
                status = "provider_quota_exhausted" if code in _BILLING_CODES else "provider_error"
                raise OpenAIError(status, "OpenAI response failed",
                                  metadata=_response_metadata(failed))
        if not isinstance(completed, dict):
            raise OpenAIError("stream_incomplete", "OpenAI stream ended before completion")
        return completed
    except (ValueError, UnicodeError, TypeError) as exc:
        raise OpenAIError("stream_incomplete", "OpenAI stream incomplete or invalid") from exc


def _message(response: dict) -> dict:
    if response.get("status") != "completed":
        detail = response.get("incomplete_details")
        reason = detail.get("reason") if isinstance(detail, dict) else None
        status = "context_limit" if reason == "max_output_tokens" else "response_incomplete"
        raise OpenAIError(status, "OpenAI response incomplete",
                          metadata={**_response_metadata(response),
                                    "finish_reason": reason if reason in {"max_output_tokens", "content_filter"} else None})
    if response.get("model") != MODEL:
        raise OpenAIError("provider_model_mismatch", "OpenAI served a different model",
                          metadata=_response_metadata(response))
    output = response.get("output")
    if not isinstance(output, list):
        raise OpenAIError("response_error", "OpenAI output shape is invalid")
    calls = []
    text = []
    for item in output:
        if not isinstance(item, dict):
            raise OpenAIError("response_error", "OpenAI output item is invalid")
        if item.get("type") == "function_call":
            if not all(isinstance(item.get(key), str) and item[key] for key in
                       ("call_id", "name", "arguments")):
                raise OpenAIError("response_error", "OpenAI function call is invalid")
            calls.append({"id": item["call_id"], "type": "function",
                          "function": {"name": item["name"], "arguments": item["arguments"]}})
        elif item.get("type") == "message":
            for part in item.get("content", []):
                if isinstance(part, dict) and part.get("type") == "output_text":
                    if not isinstance(part.get("text"), str):
                        raise OpenAIError("response_error", "OpenAI text is invalid")
                    text.append(part["text"])
    if calls and text:
        raise OpenAIError("response_error", "OpenAI mixed answer and tool call")
    return {"role": "assistant", "content": "".join(text), **({"tool_calls": calls} if calls else {})}


class Conversation:
    """Keep opaque reasoning only in memory; never put it in a run snapshot."""

    def __init__(self):
        self._history = None

    def chat_turn(self, messages: list[dict], temperature: float, max_tokens: int | None,
                  *, tools: list[dict] | None,
                  omit_output_token_limit: bool = False,
                  max_request_bytes: int | None = None) -> tuple[dict, dict]:
        if omit_output_token_limit and max_tokens is not None:
            raise ValueError("Cannot omit and set an output token limit together")
        settings = configuration()
        if not settings["available"]:
            raise OpenAIError("provider_unavailable", settings["reason"])
        if self._history is None:
            if len(messages) != 2 or [item.get("role") for item in messages] != ["system", "user"]:
                raise OpenAIError("response_error", "Invalid initial OpenAI conversation")
            history = [{"role": "developer", "content": messages[0]["content"]}, messages[1]]
        else:
            tool_message = messages[-1]
            if tool_message.get("role") != "tool" or not isinstance(tool_message.get("tool_call_id"), str):
                raise OpenAIError("response_error", "Missing OpenAI function result")
            history = [*self._history, {"type": "function_call_output",
                                         "call_id": tool_message["tool_call_id"],
                                         "output": tool_message["content"]}]
        payload = {"model": MODEL, "input": history, "store": False, "stream": True,
                   "include": ["reasoning.encrypted_content"],
                   "reasoning": {"effort": "medium"}}
        if not omit_output_token_limit:
            payload["max_output_tokens"] = max_tokens or DEFAULT_MAX_OUTPUT_TOKENS
        if tools is not None:
            payload["tools"] = [{"type": "function", **tool["function"]} for tool in tools]
            payload.update({"tool_choice": "auto", "parallel_tool_calls": False})
        from inference_api.model_service.request_budget import encode_request
        body, request_budget = encode_request(payload, max_request_bytes)
        request = Request(ENDPOINT, data=body,
                          headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY'].strip()}",
                                   "Content-Type": "application/json", "User-Agent": "PesquisaICIA/1.0"},
                          method="POST")
        request_id = None
        try:
            with models.urlopen(request, timeout=600) as response:
                request_id = _safe_id(response.headers.get("x-request-id"))
                if response.headers.get("Content-Type", "").split(";")[0].strip() != "text/event-stream":
                    raise OpenAIError("response_error", "OpenAI did not return a Responses stream")
                result = _read_stream(response)
        except HTTPError as exc:
            error_request_id = _safe_id(exc.headers.get("x-request-id"))
            retry_after = exc.headers.get("Retry-After") if exc.code == 429 else None
            retry_after = retry_after if isinstance(retry_after, str) and len(retry_after) <= 80 and all(
                character.isalnum() or character in " ,:-" for character in retry_after) else None
            status = ({400: "provider_bad_request", 401: "provider_auth_error",
                       403: "provider_auth_error", 429: "provider_rate_limited"}.get(exc.code)
                      or ("provider_error" if exc.code >= 500 else "provider_request_error"))
            if exc.code in {400, 402, 429}:
                try:
                    body = json.loads(exc.read(4097))
                    code = body.get("error", {}).get("code") if isinstance(body, dict) else None
                    if code in {"context_length_exceeded", "context_window_exceeded"}:
                        status = "context_limit"
                    elif code in _BILLING_CODES:
                        status = "provider_quota_exhausted"
                except (ValueError, OSError, AttributeError):
                    pass
            raise OpenAIError(status, f"OpenAI HTTP {exc.code}", retry_after,
                              metadata={"request_id": error_request_id, "http_status": exc.code,
                                        "request_budget": request_budget}) from None
        except OpenAIError as exc:
            exc.metadata.setdefault("request_id", request_id)
            exc.metadata["request_budget"] = request_budget
            raise
        except (TimeoutError, socket.timeout):
            raise OpenAIError("provider_timeout", "OpenAI timed out",
                              metadata={"request_budget": request_budget}) from None
        except (URLError, OSError, HTTPException):
            raise OpenAIError("provider_connection_error", "OpenAI connection failed",
                              metadata={"request_budget": request_budget}) from None
        try:
            message = _message(result)
        except OpenAIError as exc:
            exc.metadata.setdefault("request_id", request_id)
            exc.metadata["request_budget"] = request_budget
            raise
        output = result["output"]
        self._history = [*history, *output]
        record = {"provider": "openai", "api_surface": API_SURFACE, "endpoint": ENDPOINT,
                  "model_id": MODEL, "served_model": result["model"], "usage": _usage(result.get("usage")),
                  "response_id": _safe_id(result.get("id")),
                  "request_id": request_id, "finish_reason": "tool_calls" if message.get("tool_calls") else "stop",
                  "raw_response_format": "sse", "store": False,
                  "reasoning_effort": "medium", "max_output_tokens": payload.get("max_output_tokens"),
                  "request_budget": request_budget}
        return message, record
