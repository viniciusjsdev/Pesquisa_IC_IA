"""Validate researcher-declared scope and select only backend-owned tools."""
from .contracts import QuestionRequest, RoutePlan, SCHEMA_VERSION


TOOLS_BY_SCOPE = {
    "financeiro": ("financeiro_vendas_ano",),
    "industrial": ("industrial_operacoes_ano",),
    "integrado": ("financeiro_vendas_ano", "industrial_operacoes_ano"),
}
LEGACY_ROUTE_SCOPE = {tools[0]: scope for scope, tools in TOOLS_BY_SCOPE.items() if len(tools) == 1}
ALLOWED_FIELDS = {
    "author", "question", "model_alias", "prompt_revision_id", "system_prompt",
    "scope", "evidence_route", "year", "temperature", "max_tokens", "tools",
    "criteria_revision_id", "criteria",
}
ASSOCIATION_LIMIT = (
    "Agregados financeiro e industrial coincidem no ano; isso permite investigar "
    "associação, sem demonstrar causalidade ou atribuir receita a uma máquina."
)


def plan(payload: dict, alias: str, question: str, temperature: float,
         max_tokens: int) -> tuple[QuestionRequest, RoutePlan]:
    unknown = set(payload) - ALLOWED_FIELDS
    if unknown:
        raise ValueError("Unknown request parameters: " + ", ".join(sorted(unknown)))
    scope = payload.get("scope")
    legacy = payload.get("evidence_route")
    if scope is not None and legacy is not None:
        raise ValueError("Provide scope or legacy evidence_route, not both")
    if legacy is not None:
        if not isinstance(legacy, str):
            raise ValueError("Unknown evidence route")
        scope = LEGACY_ROUTE_SCOPE.get(legacy)
        if scope is None:
            raise ValueError("Unknown evidence route")
        origin = "legacy_evidence_route"
    else:
        origin = "researcher_declared_scope"
    if not isinstance(scope, str) or scope not in TOOLS_BY_SCOPE:
        raise ValueError("Scope must be financeiro, industrial or integrado")
    year = payload.get("year")
    if type(year) is not int or not 2015 <= year <= 2026:
        raise ValueError("Year must be an integer from 2015 through 2026")
    tools = TOOLS_BY_SCOPE[scope]
    if "tools" in payload and payload["tools"] != list(tools):
        raise ValueError("Requested tools must exactly match the scope allowlist")
    request = QuestionRequest(question, scope, year, alias, temperature, max_tokens, origin)
    route = RoutePlan(SCHEMA_VERSION, scope, year, tools, origin,
                      ASSOCIATION_LIMIT if scope == "integrado" else None)
    return request, route
