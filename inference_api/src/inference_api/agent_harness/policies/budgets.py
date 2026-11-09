"""Frozen per-run limits; framework transitions do not consume model calls."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ScenarioLimits:
    model_calls: int = 48
    query_attempts: int = 3
    investigation_rounds: int = 3
    input_bytes: int = 32768
    output_bytes: int = 32768
    result_bytes: int = 32768
    timeout_seconds: int = 600

def remaining(s):
    limits = s['limits']
    return {'remaining_model_calls': limits['model_calls']-s['calls'],
            'remaining_queries': limits['query_attempts']-s['attempts'],
            'remaining_rounds': limits['investigation_rounds']-s['round_no']}

def recursion_limit(limits):
    # Each model call may require projection/tool/routing, including refused attempts.
    return 20 + 8 * (limits.model_calls + limits.query_attempts + limits.investigation_rounds)
