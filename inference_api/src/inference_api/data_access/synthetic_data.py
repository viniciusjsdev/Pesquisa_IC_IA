"""Public, invented Bancada fixture. No research database or private packet access."""
import json

QUESTION = "Qual foi o valor fictício em 2020?"
PACKET = {"fixture": "synthetic-v1", "question": QUESTION, "year": 2020,
          "evidence_items": [{"year": 2020, "coverage": {"state": "observed"},
                              "units": {"value": "unidade fictícia"},
                              "rows": [{"value": 42, "label": "dado inventado"}]}]}
SOURCE = {"kind": "synthetic_fixture", "id": "synthetic-v1"}


def packet_json() -> str:
    return json.dumps(PACKET, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def catalog() -> list[dict]:
    return [{"type": "function", "function": {
        "name": "synthetic_metric",
        "description": "Consulta local à fixture inventada. Não acessa DW ou dados reais.",
        "parameters": {"type": "object", "properties": {
            "year": {"type": "integer", "enum": [2020]}},
            "required": ["year"], "additionalProperties": False}}}]


def validate_call(name: str, arguments: object) -> dict:
    if name != "synthetic_metric" or type(arguments) is not dict or arguments != {"year": 2020}:
        raise ValueError("Invalid synthetic tool call")
    return arguments


def execute(name: str, arguments: dict) -> dict:
    validate_call(name, arguments)
    return {"source": SOURCE, "year": 2020, "coverage": {"state": "observed"},
            "units": {"value": "unidade fictícia"},
            "rows": [{"value": 42, "label": "dado inventado"}]}
