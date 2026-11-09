"""Only serializable run data enters LangGraph state; clients live in RunContext."""
from dataclasses import dataclass
from typing import Callable
from typing_extensions import TypedDict

class RunState(TypedDict, total=False):
    run_id: str
    question: str
    scenario: str
    profile_id: str
    fixed: bool
    limits: dict
    roles: dict
    contract_sha: str
    maps: dict
    packet: dict | None
    sources: dict
    domains: list
    source_index: list
    packet_index: list
    available_domains: list
    examined_item_ids: list
    closure_reason: str | None
    evidence: list
    trace: list
    findings: list
    calls: int
    attempts: int
    queries: int
    round_no: int
    gap: dict | None
    candidate: tuple | None
    seen: list
    analysis: dict
    selection: dict
    source: dict
    specialist_input: dict
    planned: dict
    review: dict
    response: dict | None
    status: str
    next: str
    repair: int
    repair_feedback: dict | None
    call_input: dict
    correction: int

@dataclass
class RunContext:
    model_call: Callable
    query: Callable | None
    cancelled: Callable
    observer: object
    last_state: dict | None = None
