"""State machine for the five SPEC-013 roles; data access is injected.

This module has no database connection and cannot execute SQL. Real local
queries require the separately gated query service and approved catalog.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Callable
from uuid import uuid4

from jsonschema import Draft202012Validator
from ..request_budget import RequestBudgetExceeded, POLICY as REQUEST_BUDGET_POLICY


CONTRACT_BYTES = (Path(__file__).parent / "contracts.json").read_bytes()
CONTRACT = json.loads(CONTRACT_BYTES)
CONTRACT_SHA256 = hashlib.sha256(CONTRACT_BYTES).hexdigest()
INPUT_CONTRACT_BYTES = (Path(__file__).parent / "input_contracts.json").read_bytes()
INPUT_CONTRACT = json.loads(INPUT_CONTRACT_BYTES)
INPUT_CONTRACT_SHA256 = hashlib.sha256(INPUT_CONTRACT_BYTES).hexdigest()
DEPENDENCY_POLICY = "direct_input_events_v1"
ENGINE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
CORRECTION_HINTS = {
    "analysis_domain_consistency": "Se dominios contem fontes para qualquer medida, tratavel deve ser true; causalidade nao comprovada e uma lacuna, nao bloqueia as medidas. Se tratavel=false, dominios deve ser [].",
    "invalid_consult_decision": "Se decisao=consultar, dominio_adicional deve ser null; escolha uma fonte por consulta.",
    "invalid_additional_domain": "Se decisao=pedir_dominio, fonte_id deve ser null e o dominio deve ser novo e permitido.",
    "invalid_no_source_decision": "Se decisao=sem_fonte, fonte_id e dominio_adicional devem ser null.",
    "route_not_in_selected_map": "Use fonte_id exatamente de available_source_ids e inclua esse ID em map_refs; nao use o nome do dominio.",
    "plan_outside_selected_map": "Use apenas fonte_id, campos, grao e evidencias do trecho e limites entregues.",
    "plan_unknown_evidence_refs": "evidence_refs aceita somente IDs de available_evidence_ids (result_01 etc.); use [] se a lista estiver vazia. Nao use IDs da fonte ou colunas.",
    "review_unknown_evidence": "evidencias_utilizadas deve conter apenas IDs exatos de available_evidence_ids (result_01 etc.), sem descricoes.",
    "review_missing_gap": "Se precisa_aprofundar, informe lacuna e proximo_dado_necessario.",
    "review_unknown_domain": "Sugira somente um dominio do indice.",
    "answer_unknown_evidence": "evidencias_utilizadas deve conter apenas IDs exatos de available_evidence_ids (result_01 etc.), sem descricoes.",
}


def _correction_hint(role: str, error: str, inputs: dict) -> str:
    return CORRECTION_HINTS.get(error, "Responda ao schema JSON do papel e ao contrato completo da fonte.")
BLOCKED_QUERY_ERRORS = {"catalog_not_approved_for_local_query", "source_not_enabled",
                        "source_database_mismatch", "source_schema_mismatch",
                        "source_files_unavailable", "dw_fingerprint_mismatch",
                        "reader_identity_mismatch", "provenance_key_unavailable",
                        "row_limit_exceeded", "result_byte_limit_exceeded"}
for _role in CONTRACT["roles"].values():
    Draft202012Validator.check_schema(_role["schema"])
if set(INPUT_CONTRACT["roles"]) != set(CONTRACT["roles"]):
    raise ValueError("Input and output role contracts differ")
INPUT_SCHEMAS = {}
for _name, _role in INPUT_CONTRACT["roles"].items():
    _schema = {"type": "object", "additionalProperties": False,
               "required": _role["required"],
               "properties": {**_role["properties"],
                              "correction_feedback": INPUT_CONTRACT["correction_feedback"]}}
    Draft202012Validator.check_schema(_schema)
    INPUT_SCHEMAS[_name] = Draft202012Validator(_schema)


class HarnessError(ValueError):
    """A visible protocol or fixture failure; never triggers a hidden fallback."""


@dataclass(frozen=True)
class Limits:
    """M1 fixture ceilings, not the final scientific policy of DEC-002."""

    calls: int = 16
    queries: int = 2
    corrections_per_role: int = 1
    input_bytes: int = 16_384
    output_bytes: int | None = 8_192
    result_bytes: int = 8_192


def _bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise HarnessError(code)


def _parse(raw: str, role: str) -> dict:
    if not isinstance(raw, str):
        raise HarnessError("model_output_not_text")
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=unique_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, TypeError) as exc:
        raise HarnessError("model_output_invalid_json") from exc
    errors = list(Draft202012Validator(CONTRACT["roles"][role]["schema"]).iter_errors(value))
    if errors:
        raise HarnessError("model_output_schema_error: " + errors[0].message[:180])
    return value


def _validate_maps(domain_maps: dict, *, synthetic: bool) -> tuple[list[dict], dict]:
    if not isinstance(domain_maps, dict) or not domain_maps:
        raise HarnessError("missing_domain_maps")
    index = []
    sources = {}
    for domain, domain_map in sorted(domain_maps.items()):
        if domain not in {"dw", "industrial", "financeiro"}:
            raise HarnessError("unknown_domain")
        if (not isinstance(domain_map, dict) or domain_map.get("domain") != domain or
                domain_map.get("synthetic") is not synthetic or
                not isinstance(domain_map.get("version"), str) or
                not isinstance(domain_map.get("sources"), dict)):
            raise HarnessError("real_or_invalid_domain_map_blocked")
        for source_id, source in domain_map["sources"].items():
            if (source_id in sources or not isinstance(source_id, str) or
                    not isinstance(source, dict) or
                    not isinstance(source.get("fields"), list) or
                    not source["fields"] or
                    not all(isinstance(field, str) and field for field in source["fields"]) or
                    len(set(source["fields"])) != len(source["fields"]) or
                    not isinstance(source.get("grain"), str)):
                raise HarnessError("invalid_source_map")
            sources[source_id] = {**source, "domain": domain}
        index.append({"domain": domain, "description": domain_map.get("description", "")})
    return index, sources


def _compact_index(domain_map: dict, map_sha256: str) -> dict:
    """The selector sees source summaries, never field definitions."""
    return {"domain": domain_map["domain"], "version": domain_map["version"],
            "map_sha256": map_sha256, "description": domain_map.get("description", ""),
            "sources": [{"id": source_id, "description": source.get("description", ""),
                         "grain": source["grain"], "coverage": source.get("coverage", "")}
                        for source_id, source in sorted(domain_map["sources"].items())]}


def run(question: str, domain_maps: dict,
        model_call: Callable[[str, dict, dict], tuple[str, dict]],
        synthetic_query: Callable[[dict], dict], *, limits: Limits = Limits(),
        protocol: str = "synthetic_fixture_m1") -> dict:
    """Execute a bounded run; return exact role/tool events and status.

    model_call receives (role, JSON envelope, role contract) and returns
    (raw JSON text, provider metadata). No model receives the full trace.
    """
    if not isinstance(question, str) or not question.strip() or len(question) > 4000:
        raise HarnessError("invalid_question")
    if protocol not in {"synthetic_fixture_m1", "local_readonly_pilot"}:
        raise HarnessError("unknown_protocol")
    synthetic = protocol == "synthetic_fixture_m1"
    domain_index, source_map = _validate_maps(domain_maps, synthetic=synthetic)
    run_id = str(uuid4())
    trace: list[dict] = []
    evidence: list[dict] = []
    model_calls = 0
    queries = 0
    query_attempts = 0
    gap = None
    analysis = None
    candidate = None
    evidence_events: dict[str, str] = {}
    gap_event_id = None
    map_hashes = {domain: hashlib.sha256(_bytes(domain_map)).hexdigest()
                  for domain, domain_map in domain_maps.items()}
    case_fingerprint = hashlib.sha256(_bytes({"question": question, "maps": map_hashes,
                                             "protocol": protocol,
                                             "dependency_policy": DEPENDENCY_POLICY,
                                             "request_budget_policy": REQUEST_BUDGET_POLICY,
                                             "contract": CONTRACT_SHA256,
                                             "input_contract": INPUT_CONTRACT_SHA256})).hexdigest()

    def dependencies(inputs: dict, source_event_ids: list[str]) -> list[str]:
        """Resolve actual input producers; never approximate by trace position."""
        refs = set(source_event_ids)
        items = list(inputs.get("evidence_state", []))
        if inputs.get("query_result") is not None:
            items.append(inputs["query_result"])
        for item in items:
            result_id = item["result_id"]
            _require(result_id in evidence_events, "internal_evidence_dependency_missing")
            refs.add(evidence_events[result_id])
        rejected_id = inputs.get("correction_feedback", {}).get("rejected_event_id")
        if rejected_id:
            refs.add(rejected_id)
        _require(refs <= {event["event_id"] for event in trace},
                 "internal_event_dependency_missing")
        return [event["event_id"] for event in trace if event["event_id"] in refs]

    def invoke(role: str, inputs: dict, round_no: int,
               semantic_check: Callable[[dict], None] | None = None, *,
               source_event_ids: list[str]) -> dict:
        nonlocal model_calls, candidate
        if role not in CONTRACT["roles"]:
            raise HarnessError("unknown_role")
        for attempt in range(limits.corrections_per_role + 1):
            if not INPUT_SCHEMAS[role].is_valid(inputs):
                raise HarnessError("internal_input_schema_error")
            if model_calls >= limits.calls:
                raise HarnessError("model_call_budget_exhausted")
            call_id = f"call_{model_calls + 1:02d}"
            envelope = {"schema_version": 1, "case_fingerprint": case_fingerprint,
                        "request_byte_limit": limits.input_bytes,
                        "call_id": call_id,
                        "role": role, "round": round_no,
                        "template_version": CONTRACT["version"],
                        "source_event_ids": dependencies(inputs, source_event_ids),
                        "input": inputs}
            event = {"event_id": call_id, "role": role, "round": round_no,
                     "attempt": attempt + 1, "input": envelope,
                     "contract_sha256": CONTRACT_SHA256,
                     "input_contract_sha256": INPUT_CONTRACT_SHA256,
                     "status": "started"}
            trace.append(event)
            event["input_envelope_bytes"] = len(_bytes(envelope))
            if event["input_envelope_bytes"] > limits.input_bytes:
                event.update(status="rejected", error="input_context_limit", request_dispatched=False)
                raise HarnessError("input_context_limit")
            model_calls += 1
            try:
                raw, metadata = model_call(role, envelope, CONTRACT["roles"][role])
                if not isinstance(metadata, dict):
                    raise HarnessError("missing_model_identity")
                identity = (metadata.get("provider"), metadata.get("model_id"))
                if not all(isinstance(item, str) and item for item in identity):
                    raise HarnessError("missing_model_identity")
                if candidate is None:
                    candidate = identity
                elif candidate != identity:
                    raise HarnessError("model_identity_changed")
                event["model"] = {key: metadata[key] for key in
                                  ("provider", "model_id", "api_surface", "usage",
                                   "finish_reason", "request_id", "response_id", "request_budget")
                                  if key in metadata}
                event["output_bytes"] = len(raw.encode("utf-8")) if isinstance(raw, str) else None
                if not isinstance(raw, str) or (limits.output_bytes is not None and
                                               event["output_bytes"] > limits.output_bytes):
                    raise HarnessError("model_output_limit")
                event["raw_output"] = raw
                output = _parse(raw, role)
                if semantic_check is not None:
                    semantic_check(output)
                event["output"] = output
                event["status"] = "validated"
                return output
            except RequestBudgetExceeded as exc:
                event.update(status="rejected", error="input_context_limit",
                             request_budget=exc.receipt, request_dispatched=False)
                raise HarnessError("input_context_limit") from exc
            except HarnessError as exc:
                event["status"] = "rejected"
                event["error"] = str(exc)
                if str(exc) in {"missing_model_identity", "model_identity_changed"} or attempt >= limits.corrections_per_role:
                    raise
                inputs = {**inputs, "correction_feedback": feedback(
                    str(exc), attempt + 1, event, _correction_hint(role, str(exc), inputs))}
                if "limits" in inputs:
                    inputs["limits"] = {**inputs["limits"], **budget()}
            except Exception as exc:
                # Provider errors remain visible in the trace and are never retried.
                event["status"] = "provider_error"
                event["error"] = getattr(exc, "status", type(exc).__name__)
                http_status = getattr(exc, "metadata", {}).get("http_status")
                request_receipt = getattr(exc, "metadata", {}).get("request_budget")
                if isinstance(request_receipt, dict):
                    event["request_budget"] = request_receipt
                    event["request_dispatched"] = True
                if type(http_status) is int:
                    event["http_status"] = http_status
                if getattr(exc, "retry_after", None):
                    event["retry_after"] = exc.retry_after
                raise HarnessError("provider_error: " + event["error"]) from exc

    def budget() -> dict:
        return {"rows": 20, "remaining_queries": limits.queries - query_attempts,
                "remaining_model_calls": limits.calls - model_calls}

    def feedback(error: str, attempt: int, event: dict, hint: str) -> dict:
        return {"error_code": error, "attempt": attempt,
                "remaining_attempts": max(0, limits.corrections_per_role - attempt + 1),
                "hint": hint, "rejected_output": event.get("raw_output"),
                "rejected_plan": event.get("input") if event["role"] in
                    {"data_query", "synthetic_query"} else None,
                "rejected_event_id": event["event_id"], "budget": budget()}

    try:
        def validate_analysis(output: dict) -> None:
            _require(set(output["dominios"]) <= set(domain_maps), "domain_outside_index")
            _require(output["tratavel"] == bool(output["dominios"]),
                     "analysis_domain_consistency")
        analysis = invoke("analista_pergunta", {
            "question": question, "domain_index": domain_index,
            "protocol": ("synthetic_fixture_m1" if synthetic else "local_readonly_pilot") +
                        "; partial measurable answers allowed; causal claims require separate evidence; no SQL; no scientific score"},
            1, validate_analysis, source_event_ids=[])
        analysis_event_id = trace[-1]["event_id"]
        round_no = 0
        pending_domains = None
        selector_feedback = None
        route_corrections = 0
        while analysis["tratavel"] and query_attempts < limits.queries:
            if pending_domains is None:
                round_no += 1
                domains = sorted(analysis["dominios"]) if gap is None else [gap["dominio"]]
                domain_event_ids = []
            else:
                domains = pending_domains
                pending_domains = None
            for _ in range(len(domain_maps) + 1):
                source_index = [_compact_index(domain_maps[d], map_hashes[d]) for d in domains]
                available = {item["id"] for index in source_index for item in index["sources"]}
                def validate_selection(value: dict) -> None:
                    _require(set(value["map_refs"]) <= available, "selector_ref_outside_index")
                    if value["decisao"] == "pedir_dominio":
                        _require(value["fonte_id"] is None and
                                 value["dominio_adicional"] in domain_maps and
                                 value["dominio_adicional"] not in domains,
                                 "invalid_additional_domain")
                    elif value["decisao"] == "sem_fonte":
                        _require(value["fonte_id"] is None and value["dominio_adicional"] is None,
                                 "invalid_no_source_decision")
                    else:
                        _require(value["dominio_adicional"] is None, "invalid_consult_decision")
                        _require(value["fonte_id"] in available and
                                 value["fonte_id"] in value["map_refs"], "route_not_in_selected_map")
                selector_input = {"question": question, "necessidade": analysis["necessidade"],
                    "source_index": source_index, "available_source_ids": sorted(available),
                    "evidence_state": evidence.copy(), "gap": gap, "limits": budget()}
                if selector_feedback is not None:
                    selector_input["correction_feedback"] = selector_feedback
                    selector_feedback = None
                selection = invoke("selecionador_fontes", selector_input, round_no, validate_selection,
                    source_event_ids=[analysis_event_id, *domain_event_ids,
                                      *([gap_event_id] if gap_event_id else [])])
                selection_event_id = trace[-1]["event_id"]
                if selection["decisao"] == "pedir_dominio":
                    domain_event_ids.append(selection_event_id)
                    domains.append(selection["dominio_adicional"])
                    continue
                break
            else:
                raise HarnessError("domain_discovery_budget_exhausted")
            if selection["decisao"] == "sem_fonte":
                gap = {"reason": selection["justificativa"]}
                gap_event_id = selection_event_id
                break
            source_id = selection["fonte_id"]
            source_contract = {**source_map[source_id], "source_id": source_id}
            domain = source_contract["domain"]
            projection_id = f"map_{sum(e['role'] == 'map_projection' for e in trace) + 1:02d}"
            trace.append({"event_id": projection_id, "role": "map_projection", "round": round_no,
                "source_event_ids": [selection_event_id],
                "status": "validated", "input": {"domain": domain, "selected_table_ids": [source_id],
                    "map_sha256": map_hashes[domain]},
                "output": {"selected_table_ids": [source_id], "source_count": 1,
                    "detail_sha256": hashlib.sha256(_bytes(source_contract)).hexdigest()}})
            specialist_input = {"question": question, "necessidade": analysis["necessidade"],
                "domain": domain, "rota": selection, "source_contract": source_contract,
                "evidence_state": evidence.copy(), "gap": gap,
                "available_evidence_ids": [e["result_id"] for e in evidence], "limits": budget()}
            def validate_plan(value: dict) -> None:
                plan = value["plano"]
                _require(plan["fonte_id"] == source_id and
                         set(plan["campos"]) <= set(source_contract["fields"]) and
                         plan["grao"] == source_contract["grain"] and plan["limite"] <= 20,
                         "plan_outside_selected_map")
                _require(set(value["evidence_refs"]) <= {e["result_id"] for e in evidence},
                         "plan_unknown_evidence_refs")
            route_retry = False
            for query_attempt in range(limits.corrections_per_role + 1):
                if query_attempts >= limits.queries:
                    raise HarnessError("query_attempt_budget_exhausted")
                specialist_input["limits"] = budget()
                planned = invoke("especialista_consulta", specialist_input, round_no, validate_plan,
                    source_event_ids=[analysis_event_id, selection_event_id, projection_id,
                                      *([gap_event_id] if gap_event_id else [])])
                plan_event_id = trace[-1]["event_id"]
                plan = planned["plano"]
                tool_role = "synthetic_query" if synthetic else "data_query"
                tool_event = {"event_id": f"tool_{sum(e['role'] == tool_role for e in trace) + 1:02d}",
                              "role": tool_role, "round": round_no,
                              "source_event_ids": [plan_event_id],
                              "status": "started", "input": plan}
                trace.append(tool_event)
                query_attempts += 1
                tool_event["query_attempt"] = query_attempts
                try:
                    result = synthetic_query(plan)
                    break
                except (ValueError, TypeError) as exc:
                    reason = str(exc) if str(exc) in {
                        "invalid_synthetic_filters", "unsupported_synthetic_filter",
                        "invalid_synthetic_date_filter", "field_not_in_synthetic_fixture",
                        "source_not_in_synthetic_fixture",
                        "invalid_typed_plan", "catalog_not_approved_for_local_query",
                        "source_not_enabled", "plan_source_or_grain_mismatch",
                        "fields_outside_catalog", "row_limit_invalid",
                        "filters_outside_catalog", "invalid_range_filter",
                        "invalid_id_filter", "provenance_key_unavailable",
                        "source_database_mismatch", "source_schema_mismatch",
                        "source_files_unavailable", "row_limit_exceeded",
                        "result_byte_limit_exceeded", "invalid_lineage_filter",
                        "lineage_fact_not_allowed", "dw_fingerprint_mismatch",
                        "reader_identity_mismatch", "relation_not_approved"} else "query_rejected"
                    tool_event["status"] = "rejected"
                    tool_event["error"] = reason
                    if not synthetic and reason == "relation_not_approved":
                        if route_corrections >= limits.corrections_per_role:
                            raise HarnessError("route_correction_budget_exhausted") from exc
                        route_corrections += 1
                        pending_domains = domains
                        selector_feedback = feedback(reason, route_corrections, tool_event,
                            "Escolha outra rota permitida sem relação entre fontes.")
                        route_retry = True
                        break
                    if not synthetic and reason in BLOCKED_QUERY_ERRORS:
                        raise HarnessError("query_blocked: " + reason) from exc
                    if query_attempt >= limits.corrections_per_role:
                        raise HarnessError("synthetic_query_error" if synthetic else "query_error") from exc
                    specialist_input = {**specialist_input, "limits": budget(),
                        "correction_feedback": feedback(reason, query_attempt + 1, tool_event,
                            "Corrija o plano recusado usando source_contract, inclusive tipos e filtros. "
                            "IDs são números JSON; intervalos usam from/to, início inclusivo e fim exclusivo.")}
                except Exception as exc:
                    tool_event["status"] = "rejected"
                    tool_event["error"] = type(exc).__name__
                    raise HarnessError("synthetic_query_error" if synthetic else "query_error") from exc
            if route_retry:
                continue
            route_corrections = 0
            allowed_result_keys = ({"rows", "coverage", "units"} if synthetic else
                                   {"rows", "coverage", "units", "origin", "formula", "interpretation"})
            if (not isinstance(result, dict) or
                    not {"rows", "coverage", "units"} <= set(result) or
                    not set(result) <= allowed_result_keys or
                    not isinstance(result["rows"], list) or
                    len(result["rows"]) > plan["limite"] or
                    not isinstance(result["coverage"], dict) or
                    result["coverage"].get("rows") != len(result["rows"]) or
                    result["coverage"].get("state") != ("observed" if result["rows"] else "no_observation") or
                    not isinstance(result["units"], dict) or
                    len(_bytes(result)) > limits.result_bytes):
                tool_event["status"] = "rejected"
                tool_event["error"] = ("synthetic_result_contract_error" if synthetic else
                                       "query_result_contract_error")
                raise HarnessError(tool_event["error"])
            queries += 1
            result_id = f"result_{queries:02d}"
            evidence_item = {"result_id": result_id, "source_id": source_id,
                             "grain": plan["grao"], "plan": plan, **result}
            evidence.append(evidence_item)
            tool_event["status"] = "validated"
            tool_event["output"] = evidence_item
            evidence_events[result_id] = tool_event["event_id"]
            def validate_review(value: dict) -> None:
                _require(set(value["evidencias_utilizadas"]) <= {e["result_id"] for e in evidence},
                         "review_unknown_evidence")
                if value["decisao"] == "precisa_aprofundar":
                    _require(bool(value["lacuna"]) and bool(value["proximo_dado_necessario"]),
                             "review_missing_gap")
                    _require(value["dominio_sugerido"] in domain_maps, "review_unknown_domain")
            review = invoke("revisor_evidencias", {
                "question": question, "domains_identified": analysis["dominios"],
                "necessidade": analysis["necessidade"], "query_result": evidence_item,
                "evidence_state": evidence[:-1],
                "available_evidence_ids": [e["result_id"] for e in evidence],
                "limits": {"remaining_queries": limits.queries - query_attempts}}, round_no,
                validate_review, source_event_ids=[analysis_event_id])
            gap_event_id = trace[-1]["event_id"]
            if review["decisao"] != "precisa_aprofundar":
                gap = {"review": review}
                break
            gap = {"reason": review["lacuna"], "need": review["proximo_dado_necessario"],
                   "dominio": review["dominio_sugerido"]}
        response = invoke("redator_resposta", {
            "question": question, "evidence_state": evidence,
            "available_evidence_ids": [e["result_id"] for e in evidence],
            "limits_and_errors": {"gap": gap, "queries_used": queries,
                                  "queries_limit": limits.queries, "query_attempts_used": query_attempts}}, round_no + 1,
            lambda value: _require(set(value["evidencias_utilizadas"]) <=
                                   {e["result_id"] for e in evidence}, "answer_unknown_evidence"),
            source_event_ids=[gap_event_id or analysis_event_id])
        status = "answered_unverified" if any(item["coverage"]["state"] == "observed"
                                                for item in evidence) else "insufficient_evidence"
    except HarnessError as exc:
        response = None
        status = "contract_error"
        gap = {"error": str(exc)}
    return {"run_id": run_id, "status": status, "question": question,
            "protocol": protocol, "case_fingerprint": case_fingerprint,
            "dependency_policy": DEPENDENCY_POLICY,
            "request_budget_policy": REQUEST_BUDGET_POLICY,
            "engine_sha256": ENGINE_SHA256,
            "contract_sha256": CONTRACT_SHA256,
            "input_contract_sha256": INPUT_CONTRACT_SHA256,
            "map_sha256": map_hashes, "candidate": candidate,
            "model_calls": model_calls, "queries": queries, "query_attempts": query_attempts,
            "limits": asdict(limits), "trace": trace,
            "evidence": evidence, "response": response, "final_state": gap}
