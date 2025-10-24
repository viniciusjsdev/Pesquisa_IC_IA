from functools import wraps
from typing import Any, Dict
from config.logger import get_logger
from rag.utils.turns import make_turn

logger = get_logger(__name__)


def as_turn(*, extra: Dict[str, Any] | None = None):
    """
    Decorator que normaliza a saída do agente para formato {"turn": AgentTurn}.
    
    Aceita que o agente retorne:
    - {"answer": "..."}  -> sucesso
    - {"error": "..."}   -> erro  
    - {"answer": "...", "extra": {...}} -> adiciona campos extras
    - string             -> tratado como {"answer": string}
    """
    def deco(fn):
        @wraps(fn)
        def wrapper(state):
            try:
                result = fn(state)
                
                # Normalização mínima
                if isinstance(result, str):
                    payload = {"answer": result}
                elif isinstance(result, dict):
                    payload = result.copy()
                else:
                    # fallback seguro
                    payload = {
                        "error": f"Invalid agent return type: {type(result)}"
                    }
                
                ans = payload.get("answer")
                err = payload.get("error")
                ex = {}
                
                # merge extra do decorator + extra da função (se houver)
                if extra:
                    ex.update(extra)
                if "extra" in payload and isinstance(payload["extra"], dict):
                    ex.update(payload["extra"])
                
                turn = make_turn(state, answer=ans, error=err, extra=ex or None)
                return {"turn": turn}
                
            except Exception as e:
                logger.error(f"Erro no decorator as_turn: {str(e)}")
                turn = make_turn(state, error=str(e))
                return {"turn": turn}
                
        return wrapper
    return deco
