"""Version 3 Bancada modes; historical snapshots remain read-only in storage."""
from datetime import datetime, timezone
from copy import deepcopy
import json


from . import config, criteria, dw_tools, evidence_packets, models, storage
from .dw_tools import canonical
from .auth import Principal


def _options(payload: dict) -> tuple[float, int]:
    temperature = payload.get("temperature", 0)
    max_tokens = payload.get("max_tokens", 256)
    if type(temperature) not in (float, int) or not 0 <= temperature <= 2:
        raise ValueError("Temperature must be between 0 and 2")
    if type(max_tokens) is not int or not 1 <= max_tokens <= 1024:
        raise ValueError("max_tokens must be between 1 and 1024")
    return temperature, max_tokens


def _prompt(payload: dict) -> dict:
    prompt_id = payload.get("prompt_revision_id")
    draft = payload.get("system_prompt")
    if (prompt_id is None) == (draft is None):
        raise ValueError("Provide exactly one prompt_revision_id or system_prompt")
    if prompt_id is not None:
        prompt = storage.get_prompt(prompt_id)
        if prompt is None:
            raise ValueError("Prompt revision not found")
        return {"schema_version": 1, "revision_id": prompt_id, "revision": prompt["revision"],
                "system_prompt": prompt["system_prompt"]}
    if not isinstance(draft, str) or not draft.strip() or len(draft) > 20000:
        raise ValueError("System prompt is required and limited to 20000 characters")
    return {"schema_version": 1, "revision_id": None, "revision": None, "system_prompt": draft}


def _criteria(payload: dict) -> dict:
    criteria_id = payload.get("criteria_revision_id")
    draft = payload.get("criteria")
    if criteria_id is not None and draft is not None:
        raise ValueError("Provide criteria_revision_id or criteria, not both")
    if criteria_id is not None:
        if not isinstance(criteria_id, str):
            raise ValueError("criteria_revision_id must be a UUID string")
        from uuid import UUID
        criteria_id = str(UUID(criteria_id))
        saved = storage.get_criteria(criteria_id)
        if saved is None:
            raise ValueError("Criteria revision not found")
        return {"schema_version": criteria.CRITERIA_VERSION, "revision_id": criteria_id,
                "revision": saved["revision"], "config": criteria.validate(saved["config"])}
    return {"schema_version": criteria.CRITERIA_VERSION, "revision_id": None,
            "revision": None,
            "config": criteria.validate(draft if draft is not None else criteria.DEFAULT)}



COMMON = {"evidence_mode", "model_alias", "temperature", "max_tokens",
          "prompt_revision_id", "system_prompt", "criteria_revision_id", "criteria"}
GUIDANCE = ("Use somente a evidência entregue. Ausência de observação não é zero. "
            "Associação temporal não estabelece causalidade. A tool financeira devolve "
            "linhas observadas, nunca um total anual. Declare cobertura e ressalvas.")


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_input(payload: dict) -> tuple[str, str, float, int]:
    mode = payload.get("evidence_mode")
    if not isinstance(mode, str) or mode not in {"dw_snapshot", "dw_tools"}:
        raise ValueError("evidence_mode must be dw_snapshot or dw_tools")
    allowed = COMMON | ({"case_id", "packet_sha256"} if mode == "dw_snapshot" else {"question"})
    if set(payload) - allowed:
        raise ValueError("Unexpected or cross-mode run parameters")
    alias = payload.get("model_alias")
    if not isinstance(alias, str) or alias not in models.MODELS:
        raise ValueError("Unknown model alias")
    if mode == "dw_snapshot":
        if not isinstance(payload.get("case_id"), str) or not isinstance(payload.get("packet_sha256"), str):
            raise ValueError("case_id and packet_sha256 required")
    else:
        question = payload.get("question")
        if not isinstance(question, str) or not question.strip() or len(question) > 4000:
            raise ValueError("Question is required and limited to 4000 characters")
    temperature, max_tokens = _options(payload)
    return mode, alias, temperature, max_tokens


def _checks(evidence_items: list[dict], answer: str, config: dict) -> list[dict]:
    """Literal checks only. They never assert numerical truth or causality."""
    results = []
    def add(name, result, detail):
        results.append({"schema_version": 3, "check": name, "result": result, "detail": detail})
    observed = any(item.get("coverage", {}).get("state") == "observed" for item in evidence_items)
    if config["require_evidence"]:
        add("criteria_evidence_presence", "passed" if observed else "failed", "At least one DW observation delivered.")
    if config["require_period"]:
        add("criteria_period", "passed" if all(type(item.get("year")) is int for item in evidence_items) and evidence_items else "failed", "DW evidence contains an explicit year.")
    for unit in config["required_units"]:
        add("criteria_unit", "passed" if any(unit in item.get("units", {}).values() for item in evidence_items) else "failed", unit)
    if config["require_cited_ids"]:
        add("criteria_cited_ids", "not_checked", "Version 3 DW results have no stable per-row citation IDs.")
    for phrase in config["required_caveats"]:
        add("criteria_caveat_literal", "passed" if phrase.casefold() in answer.casefold() else "failed", phrase)
    add("numerical_truth", "not_checked", "No independent gold set in exploratory execution.")
    add("causality", "not_checked", "Temporal association does not establish causality.")
    return results


def execute_run(payload: dict, principal: Principal) -> dict:
    mode, alias, temperature, max_tokens = _validate_input(payload)
    prompt = _prompt(payload)
    verification_criteria = _criteria(payload)
    model = {"alias": alias, "base": models.BASE, "battery": models.MODELS[alias]["battery"],
             "parameters": {"temperature": temperature, "max_tokens": max_tokens},
             "endpoint": config.vllm_url() or None, "provenance_status": "unverified",
             "generation_confirmed": False}
    snapshot = {"schema_version": 3, "evidence_mode": mode,
                "prompt": prompt, "verification_criteria": verification_criteria,
                "model": model, "status": "preparing", "error": None,
                "checks": [], "model_output": None, "model_turns": [],
                "identity": {"principal_id": principal.id, "author_verified": True}}
    try:
        if mode == "dw_snapshot":
            packet, packet_bytes = evidence_packets.select_packet(payload["case_id"], payload["packet_sha256"])
            body = packet["body"]
            question = body["question"]
            snapshot["question_request"] = {"question": question, "domain": body["domain"], "model_alias": alias}
            snapshot["packet"] = {"case_id": body["case_id"], "sha256": packet["sha256"],
                                  "file_sha256": __import__("hashlib").sha256(packet_bytes).hexdigest(),
                                  "bytes_b64": __import__("base64").b64encode(packet_bytes).decode("ascii"),
                                  "source_snapshot": body["source_snapshot"],
                                  "schema_version": body["schema_version"],
                                  "query_contract_version": body["query_contract_version"],
                                  "query_code_sha256": body["query_code_sha256"]}
            evidence_items = body["evidence_items"]
            evidence_json = packet_bytes.decode("utf-8")
            messages = [{"role": "system", "content": prompt["system_prompt"] + "\n" + GUIDANCE},
                        {"role": "user", "content": question + "\n\nEvidência JSON exata:\n" + evidence_json}]
            snapshot["evidence_json_sent"] = evidence_json
            tools = None
        else:
            question = payload["question"]
            snapshot["question_request"] = {"question": question, "model_alias": alias}
            snapshot["tool_catalog"] = dw_tools.catalog()
            snapshot["tool_limits"] = {"calls": dw_tools.MAX_CALLS, "turns": dw_tools.MAX_TURNS,
                                       "rows": dw_tools.MAX_ROWS, "bytes": dw_tools.MAX_BYTES}
            snapshot["tool_trace"] = []
            availability = dw_tools.availability()
            snapshot["dw_source"] = availability
            if not availability["available"]:
                snapshot["status"] = "dw_unavailable"
                snapshot["error"] = {"stage": "dw", "type": "DWUnavailable", "message": availability["reason"]}
                return storage.create_run(principal.username, snapshot)
            evidence_items = []
            messages = [{"role": "system", "content": prompt["system_prompt"] + "\n" + GUIDANCE},
                        {"role": "user", "content": question}]
            tools = snapshot["tool_catalog"]
        session_id = None
        total_rows = total_bytes = 0
        for turn_number in range(1, dw_tools.MAX_TURNS + 1 if tools is not None else 2):
            started = _timestamp()
            turn_record = {"order": turn_number, "started_at": started,
                           "request": {"messages": deepcopy(messages), "tools": tools,
                                       "tool_choice": "auto" if tools is not None else None,
                                       "parallel_tool_calls": False if tools is not None else None,
                                       "temperature": temperature, "max_tokens": max_tokens}}
            snapshot["model_turns"].append(turn_record)
            try:
                message, serving = models.chat_turn(alias, messages, temperature, max_tokens,
                                                    tools=tools, session_id=session_id)
            except models.ModelResponseError as exc:
                snapshot["status"] = "response_error"
                snapshot["error"] = {"stage": "response", "type": type(exc).__name__, "message": str(exc)}
                turn_record.update({"finished_at": _timestamp(), "error": str(exc),
                                    "serving": exc.serving})
                break
            except Exception as exc:
                snapshot["status"] = "model_error"
                snapshot["error"] = {"stage": "model", "type": type(exc).__name__, "message": str(exc)}
                turn_record.update({"finished_at": _timestamp(), "error": str(exc)})
                break
            turn_record.update({"finished_at": _timestamp(), "serving": serving})
            session_id = serving["session_id"]
            model.update({key: serving.get(key) for key in
                          ("endpoint", "served_model", "base_revision", "adapter_run", "adapter_hash",
                           "provenance_status", "generation_confirmed", "session_id")})
            calls = message.get("tool_calls")
            if calls is not None:
                if tools is None or not isinstance(calls, list) or len(calls) != 1 or len(snapshot["tool_trace"]) >= dw_tools.MAX_CALLS or turn_number >= dw_tools.MAX_TURNS:
                    snapshot["status"] = "tool_protocol_error"
                    snapshot["error"] = {"stage": "tool", "type": "ToolCallLimitOrShape"}
                    break
                call = calls[0]
                trace = {"order": len(snapshot["tool_trace"]) + 1, "started_at": _timestamp(),
                         "raw_request": call, "status": "pending"}
                snapshot["tool_trace"].append(trace)
                try:
                    if not isinstance(call, dict) or call.get("type") != "function" or not isinstance(call.get("id"), str) or not call["id"]:
                        raise ValueError("Malformed tool call")
                    function = call["function"]
                    if not isinstance(function, dict) or not isinstance(function.get("arguments"), str):
                        raise ValueError("Malformed tool function")
                    def unique_pairs(pairs):
                        value = {}
                        for key, item in pairs:
                            if key in value:
                                raise ValueError("Duplicate DW tool argument")
                            value[key] = item
                        return value
                    args = json.loads(function["arguments"], object_pairs_hook=unique_pairs,
                                      parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("Invalid number")))
                    args = dw_tools.validate_call(function.get("name"), args)
                    trace["validated_arguments"] = args
                except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                    trace.update({"status": "failed", "error": {"stage": "tool_validation", "type": type(exc).__name__, "message": str(exc)}, "finished_at": _timestamp()})
                    snapshot["status"] = "tool_error"
                    snapshot["error"] = trace["error"]
                    break
                trace["name"] = function["name"]
                try:
                    result = dw_tools.execute(function["name"], args,
                                              expected_fingerprint=availability["source_fingerprint"])
                    result_bytes = canonical(result)
                    if total_rows + len(result["rows"]) > dw_tools.MAX_ROWS or total_bytes + len(result_bytes) > dw_tools.MAX_BYTES:
                        raise dw_tools.DWResultLimitError("Cumulative DW tool result limit exceeded")
                except dw_tools.DWResultLimitError as exc:
                    trace.update({"status": "failed", "error": {"stage": "limit", "type": type(exc).__name__, "message": str(exc)}, "finished_at": _timestamp()})
                    snapshot["status"] = "tool_limit_error"
                    snapshot["error"] = trace["error"]
                    break
                except Exception as exc:
                    trace.update({"status": "failed", "error": {"stage": "query", "type": type(exc).__name__}, "finished_at": _timestamp()})
                    snapshot["status"] = "query_error"
                    snapshot["error"] = trace["error"]
                    break
                total_rows += len(result["rows"])
                total_bytes += len(result_bytes)
                trace.update({"result": result, "result_bytes": len(result_bytes),
                              "status": "returned", "finished_at": _timestamp()})
                evidence_items.append(result)
                messages.append(message)
                messages.append({"role": "tool", "tool_call_id": call["id"],
                                 "content": result_bytes.decode("utf-8")})
                continue
            answer = message.get("content")
            if not isinstance(answer, str) or not answer.strip():
                snapshot["status"] = "response_error"
                snapshot["error"] = {"stage": "response", "type": "EmptyModelResponse"}
            elif not any(item.get("coverage", {}).get("state") == "observed" for item in evidence_items):
                snapshot["status"] = "insufficient_evidence"
                snapshot["error"] = {"stage": "evidence", "type": "NoDWObservation"}
                snapshot["model_output"] = {"raw_text": answer, "serving": serving}
            else:
                snapshot["status"] = "answered_unverified"
                snapshot["model_output"] = {"raw_text": answer, "serving": serving}
                snapshot["checks"] = _checks(evidence_items, answer, verification_criteria["config"])
            break
        else:
            snapshot["status"] = "tool_protocol_error"
            snapshot["error"] = {"stage": "tool", "type": "TurnLimit"}
    except Exception as exc:
        snapshot["status"] = "preparation_error"
        snapshot["error"] = {"stage": "preparation", "type": type(exc).__name__, "message": str(exc)}
    return storage.create_run(principal.username, snapshot)
