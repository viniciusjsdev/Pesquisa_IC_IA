from typing import Dict, List, Literal, Optional, TypedDict
from rag.enums import Agentes


class AgentTurn(TypedDict, total=False):
    """Representa um turno de execução de um agente"""
    agent: Agentes          # quem respondeu
    task: str               # a subtarefa enviada a esse agente
    answer: str             # a resposta textual do agente
    error: str              # erro ocorrido, se houver

    @classmethod
    def from_state(cls, state: "AgentState") -> "AgentTurn":
        """Cria AgentTurn a partir do estado atual"""
        agent = state["current"]
        return cls(
            agent=agent,
            task=state["tasks"].get(agent, ""),
            answer=state.get("answer", ""),
            error=state.get("error", ""),
        )


class ValidationResult(TypedDict, total=False):
    """Resultado da validação global"""
    ok: bool
    issues: Dict[Agentes, str]


class AgentState(TypedDict, total=False):
    """Estado compartilhado entre todos os agentes"""
    # Identificação
    user_id: str
    trace_id: str
    session_id: str
    question: str

    # Controle de fluxo
    turn: AgentTurn | None
    answer: str
    answers: Dict[Agentes, AgentTurn]
    tasks: Dict[Agentes, str]
    pending: List[Agentes]
    current: Optional[Agentes]
    next: Agentes | Literal["END"]
    error: str

    # Validação e controle
    did_finalize: bool
    validation: ValidationResult | None
    issues: Dict[Agentes, str] | None
    loops: int
    max_loops: int


def is_starting_flow(state: AgentState) -> bool:
    """Verifica se é o início do fluxo (sem tarefas definidas)"""
    return not bool(state.get("tasks"))


def is_validation_ok(state: AgentState) -> bool:
    """Verifica se a validação está ok"""
    validation = state.get("validation") or {}
    return bool(validation.get("ok", False))


def has_validation_issues(state: AgentState) -> bool:
    """Verifica se há issues de validação"""
    validation = state.get("validation") or {}
    issues: Dict[Agentes, str] = validation.get("issues", {})
    return bool(issues)


def max_loops_reached(state: AgentState) -> bool:
    """Verifica se atingiu o limite máximo de loops"""
    loops = int(state.get("loops", 0) or 0)
    max_loops = int(state.get("max_loops", 0) or 0)
    return max_loops > 0 and loops >= max_loops
