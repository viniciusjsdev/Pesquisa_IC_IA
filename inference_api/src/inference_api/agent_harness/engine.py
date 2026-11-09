"""Consumed SPEC-013 schema/limit compatibility only; execution uses scenarios.run."""
from dataclasses import dataclass
import json
from pathlib import Path
from jsonschema import Draft202012Validator

INPUT_CONTRACT_BYTES = (Path(__file__).parent / "input_contracts.json").read_bytes()
INPUT_CONTRACT = json.loads(INPUT_CONTRACT_BYTES)
INPUT_SCHEMAS = {}
for _name, _role in INPUT_CONTRACT["roles"].items():
    _schema = {"type": "object", "additionalProperties": False,
               "required": _role["required"],
               "properties": {**_role["properties"],
                              "correction_feedback": INPUT_CONTRACT["correction_feedback"]}}
    Draft202012Validator.check_schema(_schema)
    INPUT_SCHEMAS[_name] = Draft202012Validator(_schema)

class HarnessError(ValueError):
    """A visible protocol or fixture failure; never triggers a hidden fallback."""


@dataclass(frozen=True)
class Limits:
    """M1 fixture ceilings, not the final scientific policy of DEC-002."""

    calls: int = 16
    queries: int = 2
    corrections_per_role: int = 1
    input_bytes: int = 16_384
    output_bytes: int | None = 8_192
    result_bytes: int = 8_192
