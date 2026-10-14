"""Version 2 exploratory contracts. The formal evaluation harness is separate."""
from dataclasses import asdict, dataclass
from typing import Any


SCHEMA_VERSION = 2


@dataclass(frozen=True)
class QuestionRequest:
    question: str
    scope: str
    year: int | None
    model_alias: str
    temperature: float
    max_tokens: int
    route_origin: str


@dataclass(frozen=True)
class RoutePlan:
    schema_version: int
    scope: str
    year: int
    tools: tuple[str, ...]
    choice_origin: str
    limitation: str | None


@dataclass(frozen=True)
class EvidenceItem:
    schema_version: int
    id: str
    tool: str
    source_database: str
    source_table: str
    source_fields: tuple[str, ...]
    filters: dict[str, Any]
    period: dict[str, int]
    granularity: str
    unit: str
    value: str
    record_count: int
    formula: str
    query_template: str
    query_parameters: tuple[int, ...]
    quality: str
    limitation: str


@dataclass(frozen=True)
class EvidenceBundle:
    schema_version: int
    route: RoutePlan
    items: tuple[EvidenceItem, ...]
    quality: str
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class ModelOutput:
    schema_version: int
    raw_text: str | None
    cited_evidence_ids: tuple[str, ...]
    serving: dict[str, Any]


@dataclass(frozen=True)
class CheckResult:
    schema_version: int
    check: str
    result: str
    detail: str


@dataclass(frozen=True)
class RunSnapshot:
    schema_version: int
    question_request: QuestionRequest
    prompt: dict[str, Any]
    model: dict[str, Any]
    route_plan: RoutePlan | None
    evidence_bundle: EvidenceBundle | None
    model_output: ModelOutput | None
    checks: tuple[CheckResult, ...]
    status: str
    error: dict[str, str] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
