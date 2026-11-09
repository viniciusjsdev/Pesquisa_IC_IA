"""A view contains authorized inputs and semantic indexes, never runtime clients."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ContextView:
    inputs: dict
    domains: tuple
    source_ids: tuple
    evidence_ids: tuple
    scenario: str = 'data_access'
    known_domains: tuple = ()
    available_domains: tuple = ()
