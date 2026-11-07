"""One bounded OpenAI provider audit of the synthetic SPEC-013 role chain.

This is a direct diagnostic entry point. It does not register a Bancada mode,
read PostgreSQL, or evaluate model quality scientifically.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import Limits, run
from .synthetic_demo import MAPS, PROTOCOL_PROMPT, QUESTION, fixture_query, role_messages
from .. import config, openai_provider  # config loads ignored local credentials


MAX_CALLS = 16
MAX_OUTPUT_TOKENS = 4096


def model_call(role: str, envelope: dict, contract: dict) -> tuple[str, dict]:
    # A fresh conversation per role keeps hidden provider context out of the next role.
    conversation = openai_provider.Conversation()
    message, receipt = conversation.chat_turn(
        role_messages(envelope, contract, PROTOCOL_PROMPT), 0,
        MAX_OUTPUT_TOKENS, tools=None,
        max_request_bytes=envelope.get("request_byte_limit", Limits().input_bytes))
    return message.get("content") or "", {
        key: receipt[key] for key in ("provider", "model_id", "api_surface", "usage",
                                      "finish_reason", "request_id", "response_id", "request_budget")
        if key in receipt}


def main() -> None:
    parser = argparse.ArgumentParser(description="One synthetic-only OpenAI audit")
    parser.add_argument("--output", type=Path, required=True,
                        help="Local JSON trace; never a database path")
    args = parser.parse_args()
    if not openai_provider.configuration()["available"]:
        raise SystemExit("OpenAI API key is not configured; no call sent")
    result = run(QUESTION, MAPS, model_call, fixture_query,
                 limits=Limits(calls=MAX_CALLS))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(json.dumps({"run_id": result["run_id"], "status": result["status"],
                      "model_calls": result["model_calls"], "queries": result["queries"],
                      "roles": [event["role"] for event in result["trace"]],
                      "error": result["final_state"].get("error") if result["final_state"] else None},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
