"""Conservative post-run scoring for SPEC-013.

Gold material is passed only to this offline evaluator, never to a model role.
Automatic checks establish route and reference integrity. A reviewer must
adjudicate calculation and conclusion before the four-part card is scored.
"""

from __future__ import annotations

import hashlib
import json


class ScoreContractError(ValueError):
    """The run, approved case, or adjudication is internally inconsistent."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ScoreContractError(reason)


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _not_scored(run_id: str | None, case_id: str | None, reason: str) -> dict:
    return {"status": "not_scored", "run_id": run_id, "case_id": case_id,
            "reason": reason, "scores": None}


def evaluate(run: dict, case: dict | None, adjudication: dict | None = None) -> dict:
    """Score one finished run; no aggregate ranking or provider calls.

    A case requires an explicit human review receipt. An adjudication is a
    separate review of this specific run. Neither may be inferred from a
    fixture or from the model's own answer.
    """
    _require(isinstance(run, dict) and isinstance(run.get("run_id"), str),
             "invalid_run")
    run_id = run["run_id"]
    if run.get("protocol") == "scenarios_v1":
        # SPEC-014 has no scientifically approved case bindings yet. Never inherit v6 gates.
        return _not_scored(run_id, case.get("case_id") if isinstance(case, dict) else None,
                           "scenario_case_binding_pending")
    if not isinstance(case, dict) or case.get("status") != "approved":
        return _not_scored(run_id, case.get("case_id") if isinstance(case, dict) else None,
                           "case_not_approved")
    case_id = case.get("case_id")
    _require(isinstance(case_id, str) and case_id and
             isinstance(case.get("prepared_by"), str) and case["prepared_by"] and
             isinstance(case.get("question_sha256"), str) and
             isinstance(case.get("map_sha256"), dict) and
             isinstance(case.get("accepted_routes"), list) and
             bool(case["accepted_routes"]) and
             isinstance(case.get("required_evidence_sources"), list) and
             all(isinstance(source, str) and source
                 for source in case["required_evidence_sources"]) and
             isinstance(case.get("review"), dict) and
             all(isinstance(case["review"].get(key), str) and case["review"][key]
                 for key in ("reviewer", "reviewed_at", "evidence_receipt")),
             "invalid_approved_case")
    _require(case["prepared_by"] != case["review"]["reviewer"],
             "case_reviewer_must_be_independent")
    _require(isinstance(run.get("question"), str) and
             _digest(run["question"]) == case["question_sha256"],
             "question_fingerprint_mismatch")
    _require(run.get("map_sha256") == case["map_sha256"],
             "map_fingerprint_mismatch")
    routes = case["accepted_routes"]
    _require(all(isinstance(route, list) and route and
                 all(isinstance(source, str) and source for source in route)
                 for route in routes), "invalid_accepted_routes")
    if run.get("status") not in {"answered_unverified", "insufficient_evidence"}:
        return _not_scored(run_id, case_id, "run_incomplete")
    response = run.get("response")
    _require(isinstance(response, dict), "missing_response")
    evidence = run.get("evidence")
    _require(isinstance(evidence, list) and
             all(isinstance(item, dict) and isinstance(item.get("result_id"), str)
                 and isinstance(item.get("source_id"), str) and
                 isinstance(item.get("coverage"), dict) for item in evidence),
             "invalid_evidence")
    ids = [item["result_id"] for item in evidence]
    _require(len(set(ids)) == len(ids), "duplicate_evidence_id")
    refs = response.get("evidencias_utilizadas")
    _require(isinstance(refs, list) and len(set(refs)) == len(refs) and
             all(isinstance(ref, str) for ref in refs), "invalid_answer_references")
    source_route = [item["source_id"] for item in evidence]
    route_score = int(source_route in routes)
    by_id = {item["result_id"]: item for item in evidence}
    cited_sources = {by_id[ref]["source_id"] for ref in refs if ref in by_id}
    expected_states = case.get("expected_evidence_states", {})
    _require(isinstance(expected_states, dict) and
             set(expected_states) <= set(case["required_evidence_sources"]) and
             all(state in {"observed", "no_observation"}
                 for state in expected_states.values()),
             "invalid_expected_evidence_states")
    def valid_cited_reference(ref: str) -> bool:
        if ref not in by_id:
            return False
        item = by_id[ref]
        expected = expected_states.get(item["source_id"], "observed")
        actual = item["coverage"].get("state")
        rows = item.get("rows")
        return (actual == expected and isinstance(rows, list) and
                item["coverage"].get("rows") == len(rows) and
                (bool(rows) if expected == "observed" else not rows))
    evidence_score = int(bool(refs) and
                         set(case["required_evidence_sources"]) <= cited_sources and all(
        valid_cited_reference(ref) for ref in refs))
    automatic = {"route": route_score, "evidence_reference": evidence_score}
    if not isinstance(adjudication, dict) or adjudication.get("status") != "reviewed":
        return {"status": "awaiting_run_review", "run_id": run_id,
                "run_sha256": _digest(run),
                "case_id": case_id, "case_sha256": _digest(case),
                "automatic_checks": automatic, "scores": None}
    _require(adjudication.get("run_id") == run_id and
             adjudication.get("run_sha256") == _digest(run) and
             adjudication.get("case_id") == case_id and
             adjudication.get("case_sha256") == _digest(case) and
             all(isinstance(adjudication.get(key), str) and adjudication[key]
                 for key in ("reviewer", "reviewed_at", "rationale")) and
             type(adjudication.get("calculation")) is int and
             type(adjudication.get("conclusion")) is int and
             adjudication["calculation"] in {0, 1} and
             adjudication["conclusion"] in {0, 1},
             "invalid_run_adjudication")
    return {"status": "scored", "run_id": run_id, "case_id": case_id,
            "run_sha256": _digest(run),
            "case_sha256": _digest(case),
            "scores": {**automatic, "calculation": adjudication["calculation"],
                       "conclusion": adjudication["conclusion"]},
            "review": {"reviewer": adjudication["reviewer"],
                       "reviewed_at": adjudication["reviewed_at"],
                       "rationale": adjudication["rationale"]}}
