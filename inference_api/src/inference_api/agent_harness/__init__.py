"""Experimental, synthetic-only execution core for SPEC-013 M1."""

from .engine import HarnessError, Limits, run

__all__ = ["HarnessError", "Limits", "run"]
