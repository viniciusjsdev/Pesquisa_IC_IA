"""Bounded, on-Pod diagnostic of the base and two FT-FinQA adapters.

This command never creates a Pod or a tunnel. `plan` only reads local files.
`execute` requires a fresh verification receipt and an explicit CLI flag.
Raw requests and responses stay in the caller-selected private output folder.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from time import monotonic
from urllib.error import HTTPError
from urllib.request import Request, build_opener, urlopen

from serving import REPO, command, load_manifest, manifest_digest, validate
from verify_remote import NoRedirect, _call


ALIASES = ("qwen-base", "ft-finqa-a", "ft-finqa-b")
DELIMITER = "\n\nEvidência JSON exata:\n"
LOOPBACK = "http://127.0.0.1:8002"
GATEWAY = "http://127.0.0.1:8000"
EXPECTED_REQUEST_SHA256 = "6e9a758d222182d60cc8b11ff0463f562b67e953fa4e9433a3380c2473da039a"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_case(path: Path) -> tuple[list[dict], dict]:
    """Read the two preserved, paired Bancada request bodies without printing them."""
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or len(entries) != 2:
        raise ValueError("Expected exactly the preserved A and B requests")
    bodies = {item["body"]["model"]: item["body"] for item in entries}
    if set(bodies) != {"ft-finqa-a", "ft-finqa-b"}:
        raise ValueError("Request aliases must be ft-finqa-a and ft-finqa-b")
    a, b = bodies["ft-finqa-a"], bodies["ft-finqa-b"]
    if (a["messages"] != b["messages"] or a.get("temperature") != b.get("temperature") or
            a.get("tools") or b.get("tools") or len(a["messages"]) != 2 or
            [item.get("role") for item in a["messages"]] != ["system", "user"]):
        raise ValueError("Preserved requests are not a paired, tool-free system/user case")
    if DELIMITER not in a["messages"][1]["content"]:
        raise ValueError("The preserved user message has no evidence delimiter")
    return a["messages"], {"source_run_ids": [item["source_run_id"] for item in entries],
                           "source_sha256": digest(path.read_bytes())}


def conditions(messages: list[dict], chat_rendered: str | None = None) -> list[dict]:
    """Each adjacent condition changes one declared factor or checks API equivalence."""
    question, evidence = messages[1]["content"].split(DELIMITER, 1)
    finqa = ("### Instruction: " + messages[0]["content"] + "\n" + question +
             " ### Context: " + evidence + " ### Response:")
    plans = [
        {"id": "C1_chat_02", "endpoint": "chat", "temperature": 0.2,
         "max_tokens": 128, "input": messages, "comparison": "C2: temperature"},
        {"id": "C2_chat_00", "endpoint": "chat", "temperature": 0.0,
         "max_tokens": 128, "input": messages, "comparison": "C3: route equivalence control"},
        {"id": "C3_chat_serialized_00", "endpoint": "completion", "temperature": 0.0,
         "max_tokens": 128, "input": chat_rendered,
         "comparison": "C4: prompt serialization"},
        {"id": "C4_finqa_format_00", "endpoint": "completion", "temperature": 0.0,
         "max_tokens": 128, "input": finqa, "comparison": "C5: output cap"},
        {"id": "C5_finqa_format_32", "endpoint": "completion", "temperature": 0.0,
         "max_tokens": 32, "input": finqa, "comparison": None},
    ]
    return plans


def request_body(alias: str, condition: dict) -> dict:
    if alias not in ALIASES:
        raise ValueError("Unexpected alias")
    payload = {"model": alias, "temperature": condition["temperature"],
               "top_p": 0.9, "repetition_penalty": 1.0, "stop": [],
               "max_tokens": condition["max_tokens"], "stream": False}
    if condition["endpoint"] == "chat":
        payload["messages"] = condition["input"]
    elif condition["endpoint"] == "completion":
        if not isinstance(condition["input"], str) or not condition["input"]:
            raise ValueError("A rendered prompt is required for completion")
        payload["prompt"] = condition["input"]
    else:
        raise ValueError("Unexpected endpoint")
    return payload


def classify(response: dict) -> dict:
    choice = response["choices"][0]
    finish = choice.get("finish_reason")
    if finish not in {"stop", "length", "tool_calls"}:
        raise ValueError("Missing or unexpected finish_reason")
    message = choice.get("message") or {}
    tool_calls = message.get("tool_calls") or []
    text = message.get("content") if "message" in choice else choice.get("text")
    if text is None and tool_calls:
        text = ""
    if not isinstance(text, str):
        raise ValueError("Missing response text")
    chunks = [text[i:i + 80] for i in range(0, len(text) - 79, 80)]
    top_repeat = max((chunks.count(chunk) for chunk in set(chunks)), default=0)
    return {"finish_reason": finish, "complete": finish == "stop" and not tool_calls,
            "response_chars": len(text), "usage": response.get("usage"),
            "tool_call_count": len(tool_calls), "max_repeat_of_80_char_block": top_repeat,
            "raw_text_sha256": digest(text.encode("utf-8"))}


def checked_receipt(path: Path, manifest: dict, base_revision: str, session_path: Path) -> dict:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    session = json.loads(session_path.read_text(encoding="utf-8"))
    if (receipt.get("status") != "passed" or
            receipt.get("manifest_sha256") != manifest_digest(manifest) or
            receipt.get("base_revision") != base_revision or
            receipt.get("session_id") != session.get("session_id") or
            session.get("base_revision") != base_revision or
            not all(receipt.get("generations", {}).get(alias, {}).get("confirmed")
                    for alias in [manifest["base_alias"],
                                  *(item["alias"] for item in manifest["adapters"]) ])):
        raise ValueError("Verification receipt does not match this seven-alias serving session")
    return receipt


def live_identity(receipt: dict, manifest: dict, token: str) -> dict:
    """Tie the direct vLLM port to the authenticated, currently live gateway."""
    if len(token) < 32:
        raise ValueError("INFERENCE_VLLM_TOKEN is missing or too short")
    listing, identity = _call(build_opener(NoRedirect()), GATEWAY + "/v1/models", token)
    expected = {key: receipt[key] for key in
                ("manifest_sha256", "base_revision", "session_id", "vllm_version")}
    served = {item.get("id") for item in listing.get("data", []) if isinstance(item, dict)}
    aliases = {manifest["base_alias"], *(item["alias"] for item in manifest["adapters"])}
    if identity != expected or served != aliases:
        raise ValueError("Live gateway identity or alias list differs from the verified session")
    lengths = {item.get("id"): item.get("max_model_len") for item in listing.get("data", [])
               if isinstance(item, dict)}
    return {"identity": identity, "reported_max_model_len": lengths}


def write_private(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_matrix(plan: list[dict], manifest: dict, receipt: dict, source: dict,
               output_dir: Path, max_wall_seconds: int, token: str) -> dict:
    """Persist each call and a rolling summary, including the first failure."""
    argv = command(manifest, REPO, receipt["base_revision"])
    configured_window = int(argv[argv.index("--max-model-len") + 1])
    deadline = monotonic() + max_wall_seconds
    results = []
    for condition in plan:
        for alias in ALIASES:
            started = datetime.now(timezone.utc).isoformat()
            began = monotonic()
            body = request_body(alias, condition)
            artifact = {"schema_version": 1, "status": "started", "condition": condition["id"],
                        "alias": alias, "started_at": started, "request": body,
                        "manifest_sha256": receipt["manifest_sha256"],
                        "base_revision": receipt["base_revision"],
                        "session_id": receipt["session_id"],
                        "vllm_version": receipt["vllm_version"],
                        "configured_max_model_len": configured_window,
                        "configured_window_source": "runpod/serving/serving.py command",
                        "serving_script_sha256": digest(Path(__file__).with_name("serving.py").read_bytes()),
                        "diagnostic_script_sha256": digest(Path(__file__).read_bytes()),
                        "source": source}
            try:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise TimeoutError("Diagnostic wall-time budget exhausted")
                before = live_identity(receipt, manifest, token)
                artifact["gateway_before"] = before
                endpoint = ("/v1/chat/completions" if condition["endpoint"] == "chat"
                            else "/v1/completions")
                req = Request(LOOPBACK + endpoint,
                              data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                              headers={"Content-Type": "application/json"}, method="POST")
                with urlopen(req, timeout=min(180, max(1, remaining))) as response:
                    raw = response.read(8 * 1024 * 1024 + 1)
                artifact["response_bytes_sha256"] = digest(raw)
                if len(raw) > 8 * 1024 * 1024:
                    raise ValueError("Diagnostic response exceeds 8 MiB")
                try:
                    answer = json.loads(raw)
                except ValueError:
                    artifact["raw_response_text"] = raw.decode("utf-8", errors="replace")
                    raise
                artifact["response"] = answer
                if answer.get("model") != alias:
                    raise ValueError("Direct vLLM response model differs from requested alias")
                after = live_identity(receipt, manifest, token)
                artifact["gateway_after"] = after
                if before["identity"] != after["identity"]:
                    raise ValueError("Gateway session changed during direct vLLM generation")
                artifact["summary"] = classify(answer)
                artifact["status"] = "completed"
            except HTTPError as exc:
                raw_error = exc.read(65537)
                artifact["status"] = "failed"
                artifact["error"] = {"type": "HTTPError", "http_status": exc.code,
                                     "body_truncated": len(raw_error) > 65536,
                                     "body_text": raw_error[:65536].decode("utf-8", errors="replace")}
            except Exception as exc:
                artifact["status"] = "failed"
                artifact["error"] = {"type": type(exc).__name__, "message": str(exc)}
            artifact["elapsed_seconds"] = round(monotonic() - began, 3)
            target = output_dir / f"{condition['id']}-{alias}.json"
            write_private(target, artifact)
            results.append({"condition": condition["id"], "alias": alias,
                            "status": artifact["status"], "artifact": str(target),
                            "elapsed_seconds": artifact["elapsed_seconds"],
                            **artifact.get("summary", {}),
                            **({"error": artifact["error"]} if "error" in artifact else {})})
            final = {"schema_version": 1,
                     "status": "partial_failed" if artifact["status"] == "failed" else "running",
                     "planned_calls": len(plan) * len(ALIASES), "completed_calls": len(results),
                     "results": results}
            write_private(output_dir / "summary.json", final)
            if artifact["status"] == "failed":
                return final
    final["status"] = "diagnostic_only"
    write_private(output_dir / "summary.json", final)
    return final


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "execute"))
    parser.add_argument("--request-file", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("manifest.json"))
    parser.add_argument("--base-revision")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--session-file", type=Path, default=Path(__file__).with_name(".local") / "session.json")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-wall-seconds", type=int)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        messages, source = load_case(args.request_file)
        manifest = load_manifest(args.manifest)
        validate(manifest)
        if args.action == "plan":
            plan = conditions(messages)
            print(json.dumps({"status": "plan_only", **source,
                              "aliases": ALIASES, "condition_ids": [item["id"] for item in plan],
                              "calls": len(ALIASES) * len(plan),
                              "needs_tokenizer_for_C3": True}, ensure_ascii=False))
            return 0
        if not args.execute or not args.base_revision or not args.receipt or not args.output_dir:
            raise ValueError("Execution requires --execute, --base-revision, --receipt and --output-dir")
        if source["source_sha256"] != EXPECTED_REQUEST_SHA256:
            raise ValueError("Preserved request file hash differs from the versioned diagnostic case")
        if not args.max_wall_seconds or not 1 <= args.max_wall_seconds <= 3600:
            raise ValueError("Explicit --max-wall-seconds must be between 1 and 3600")
        private_root = Path(__file__).with_name(".local").resolve()
        if not args.output_dir.resolve().is_relative_to(private_root):
            raise ValueError("Raw output must stay under runpod/serving/.local")
        args.output_dir.mkdir(parents=True, exist_ok=False)
        try:
            receipt = checked_receipt(args.receipt, manifest, args.base_revision, args.session_file)
            token = os.environ.get("INFERENCE_VLLM_TOKEN", "")
            live_identity(receipt, manifest, token)
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(manifest["base_model"],
                                                      revision=args.base_revision, local_files_only=True)
            rendered = tokenizer.apply_chat_template(messages, tokenize=False,
                                                     add_generation_prompt=True)
            plan = conditions(messages, rendered)
            final = run_matrix(plan, manifest, receipt, source, args.output_dir,
                               args.max_wall_seconds, token)
        except Exception as exc:
            final = {"schema_version": 1, "status": "preflight_failed",
                     "error": {"type": type(exc).__name__, "message": str(exc)},
                     "completed_calls": 0}
            write_private(args.output_dir / "summary.json", final)
        print(json.dumps({"status": final["status"], "completed_calls": final["completed_calls"],
                          "summary": str(args.output_dir / "summary.json")}, ensure_ascii=False))
        return 0 if final["status"] == "diagnostic_only" else 2
    except Exception as exc:
        print(f"SPEC-011 diagnostic stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
