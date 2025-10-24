from __future__ import annotations
from typing import Any, Optional, Dict, List, cast
from collections.abc import MutableMapping

from rag.enums import Agentes
from rag.state import AgentState, AgentTurn, ValidationResult
from config.logger import get_logger

logger = get_logger(__name__)

MAX_LOOPS = 10  # Configurável via settings


class StateService(MutableMapping[str, Any]):
    """
    Wrapper fino sobre AgentState (dict) com conveniências de leitura/escrita e
    métodos de domínio para reduzir a lógica espalhada no orquestrador.
    """
    def __init__(self, data: Optional[AgentState] = None):
        self._data: AgentState = cast(AgentState, data or {})

    # ========= MutableMapping boilerplate =========
    def __getitem__(self, k: str) -> Any: return self._data[k]
    def __setitem__(self, k: str, v: Any) -> None: self._data[k] = v
    def __delitem__(self, k: str) -> None: del self._data[k]
    def __iter__(self): return iter(self._data)
    def __len__(self) -> int: return len(self._data)

    # Acesso ao dict cru (se precisar devolver para o fluxo externo)
    @property
    def state_data(self) -> AgentState:
        return self._data

    # ========= Propriedades convenientes =========
    @property
    def turn(self) -> AgentTurn | None:
        return cast(AgentTurn, self._data.get("turn", None))

    @property
    def question(self) -> str:
        return cast(str, self._data.get("question", ""))

    @property
    def tasks(self) -> Dict[Agentes, str]:
        return cast(Dict[Agentes, str], self._data.get("tasks", {}))

    @property
    def answers(self) -> Dict[Agentes, AgentTurn]:
        return cast(Dict[Agentes, AgentTurn], self._data.get("answers", {}))

    @property
    def pending(self) -> List[Agentes]:
        return cast(List[Agentes], self._data.get("pending", []))

    @property
    def current(self) -> Optional[Agentes]:
        return cast(Optional[Agentes], self._data.get("current"))

    @property
    def validation(self) -> ValidationResult | None:
        return self._data.get("validation", None)

    @property
    def next(self) -> Agentes | str:
        return cast(Agentes | str, self._data.get("next", "END"))

    # ========= Métodos de domínio (orquestração) =========
    def is_starting_flow(self) -> bool:
        return not bool(self.tasks)

    def has_agent_turn(self) -> bool:
        return self.current is not None and self.turn

    def has_agent_turn_error(self) -> bool:
        return bool(self.turn.get("error", None))

    def is_not_validators_turn(self) -> bool:
        return self.current is not None \
            and self.current != Agentes.VALIDADOR_GLOBAL

    def has_pending(self) -> bool:
        return bool(self.pending)

    def is_validation_ok(self):
        validation = self.validation or {}
        return bool(validation.get("ok", False))

    def has_validation_issues(self):
        validation = self.validation or {}
        issues: Dict[Agentes, str] = validation.get("issues", {})
        return bool(issues)

    def increase_loop(self):
        self._data["loops"] += 1

    def pop_next_pending(self) -> Optional[Agentes]:
        if not self.pending:
            return None
        agent = self.pending.pop(0)
        self._data["pending"] = self.pending
        return agent

    def max_loops_reached(self) -> bool:
        loops = int(self._data.get("loops", 0) or 0)
        max_loops = int(self._data.get("max_loops", 0) or 0)
        return max_loops > 0 and loops >= max_loops

    def should_call_validador_global(self) -> bool:
        return self._data.get("validation") is None

    def route_to(self, agent: Agentes) -> None:
        """Define current/next de forma explícita."""
        self._data["current"] = agent
        self._data["next"] = agent

    def route_to_end(self) -> None:
        """Define current/next de forma explícita."""
        self._data["current"] = None
        self._data["next"] = "END"

    def mark_finalized(self, is_finalized: bool):
        self._data["did_finalize"] = is_finalized

    def push_answer(self) -> None:
        """Registra/atualiza answers do agente do turno atual."""
        turn: AgentTurn = self.turn
        agent = cast(Agentes, turn.get("agent") or self.current)
        if agent is None:
            return
        ans = self.answers.copy()
        ans[agent] = turn
        self._data["answers"] = ans

    def increment_loops(self) -> int:
        loops = int(self._data.get("loops", 0)) + 1
        self._data["loops"] = loops
        return loops

    def needs_finalizer(self) -> bool:
        """
        Regra comum: chamou todos os agentes (pending vazio)
        e ainda não finalizou.
        """
        did_finalize = bool(self._data.get("did_finalize", False))
        return (not self.has_pending()) and (not did_finalize)

    # ========= Estados de state (orquestracao) =========
    def state_first_step(self) -> AgentState:
        self.route_to(Agentes.PREPROCESSADOR)
        return {
            **self._data,
            "loops": 1,
            "max_loops": MAX_LOOPS,
        }

    def state_retry_agent_turn(self) -> AgentState:
        self.push_answer()
        agent = self.current
        self.increase_loop()
        self.route_to(agent)
        return self._data

    def state_next_agent_turn(self) -> AgentState:
        nxt = self.pending[0]
        self.route_to(nxt)
        return {
            **self._data,
            "turn": None,
        }

    def state_call_finalizador(self) -> AgentState:
        self.route_to(Agentes.FINALIZADOR)
        self.mark_finalized(False)
        return {
            **self._data,
            "turn": None,
        }

    def state_call_validador_global(self) -> AgentState:
        self.route_to(Agentes.VALIDADOR_GLOBAL)
        return {
            **self._data,
            "turn": None,
        }

    def state_end(self) -> AgentState:
        self.route_to_end()
        final_turn = self._data.get("answers", {}).get(Agentes.FINALIZADOR)
        return {
            **self._data,
            "turn": None,
            "pending": [],
            "answer": final_turn["answer"]
        }

    def state_validation_issues(self) -> AgentState:
        validation = self.validation
        issues: Dict[Agentes, str] = validation.get("issues", {})
        new_pending = list(issues)
        current = new_pending[0]
        self.increase_loop()
        self.route_to(current)
        self.mark_finalized(False)
        return {
            **self._data,
            "pending": list(issues),
            "issues": issues,
            "validation": None,
            "turn": None,
        }

    def state_back_to_preprocessador(self) -> AgentState:
        self.increase_loop()
        self.route_to(Agentes.PREPROCESSADOR)
        self.mark_finalized(False)
        return {
            **self._data,
            "pending": [],
            "issues": None,
            "validation": None,
            "turn": None,
        }


def wrap_state(state: AgentState | None) -> StateService:
    return StateService(state or cast(AgentState, {}))
