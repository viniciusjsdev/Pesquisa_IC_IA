"""Small invented fixture for M1; never reads the research databases."""
from __future__ import annotations

import json
from datetime import date
from jsonschema import Draft202012Validator

from . import run, Limits
from .engine import INPUT_SCHEMAS
from .. import config, groq  # config loads the ignored local .env without printing it


QUESTION = ("Na linha fictícia L1 em 2020, quantos minutos de parada houve "
            "e qual foi o lucro líquido observado no mesmo ano? "
            "Isso prova que a parada causou a variação do lucro?")
PROTOCOL_PROMPT = ("Siga apenas o papel e o contrato JSON desta chamada. Use somente "
                   "os mapas e resultados sintéticos recebidos; não conclua causalidade por coincidência temporal.")

MAPS = {
    "dw": {"domain": "dw", "version": "fixture-1", "synthetic": True,
           "description": "Agregados fictícios por linha e ano",
           "sources": {"dw_paradas": {"fields": ["linha", "ano", "minutos_parada"],
                                      "grain": "linha/ano", "coverage": "2020"}}},
    "financeiro": {"domain": "financeiro", "version": "fixture-1", "synthetic": True,
                   "description": "Observações financeiras fictícias por data",
                   "sources": {"fin_resultado": {"fields": ["data", "lucro_liquido"],
                                              "grain": "observacao/data", "coverage": "2020"}}},
    "industrial": {"domain": "industrial", "version": "fixture-1", "synthetic": True,
                   "description": "Parada industrial fictícia individual",
                   "sources": {"ind_parada": {"fields": ["evento_id", "linha", "ano", "minutos_parada"],
                                              "grain": "parada/evento", "coverage": "2020"}}},
}

# Fixture maps obey the same Specialist interface as real maps. Their grammar
# is explicit and is also used by the fixture executor below.
_date_range = {"type": "object", "additionalProperties": False,
               "required": ["from", "to"],
               "properties": {"from": {"type": "string"}, "to": {"type": "string"}},
               "description": "ISO-8601 date; from < to; intervalo [from,to)"}
_filter_properties = {
    "dw_paradas": {"linha": {"type": "string"}, "ano": {"type": "integer"}},
    "ind_parada": {"evento_id": {"type": "integer", "minimum": 1},
                   "linha": {"type": "string"}, "ano": {"type": "integer"}},
    "fin_resultado": {"ano": {"type": "integer"}, "data": _date_range},
}
for _domain_map in MAPS.values():
    _domain_map["version"] = "fixture-2"
    for _source_id, _source in _domain_map["sources"].items():
        _source["field_types"] = {field: ("text" if field == "linha" else
                                           "date" if field == "data" else "integer")
                                   for field in _source["fields"]}
        _source["filter_contracts"] = {"type": "object", "additionalProperties": False,
                                       "properties": _filter_properties[_source_id]}


def fixture_query(plan: dict) -> dict:
    source_id = plan["fonte_id"]
    filters = plan["filtros"]
    if not isinstance(filters, dict):
        raise ValueError("invalid_synthetic_filters")
    source = next((m["sources"][source_id] for m in MAPS.values()
                   if source_id in m["sources"]), None)
    if source is None:
        raise ValueError("source_not_in_synthetic_fixture")
    if not Draft202012Validator(source["filter_contracts"]).is_valid(filters):
        raise ValueError("unsupported_synthetic_filter")
    if source_id == "dw_paradas":
        values = {"linha": "L1", "ano": 2020, "minutos_parada": 45}
        units = {"minutos_parada": "min"}
        if not set(filters) <= {"linha", "ano"}:
            raise ValueError("unsupported_synthetic_filter")
        matched = all(values[field] == value for field, value in filters.items())
    elif source_id == "fin_resultado":
        values = {"data": "2020-12-31", "lucro_liquido": 1200}
        units = {"lucro_liquido": "unidade monetaria ficticia"}
        if not set(filters) <= {"ano", "data"}:
            raise ValueError("unsupported_synthetic_filter")
        matched = filters.get("ano", 2020) == 2020
        selected_date = date.fromisoformat(values["data"])
        date_filter = filters.get("data")
        if date_filter is not None:
            try:
                start, end = date.fromisoformat(date_filter["from"]), date.fromisoformat(date_filter["to"])
                if start >= end:
                    raise ValueError()
            except ValueError as exc:
                raise ValueError("invalid_synthetic_date_filter") from exc
            matched = matched and start <= selected_date < end
    elif source_id == "ind_parada":
        values = {"evento_id": 7, "linha": "L1", "ano": 2020, "minutos_parada": 45}
        units = {"minutos_parada": "min"}
        if not set(filters) <= {"evento_id", "linha", "ano"}:
            raise ValueError("unsupported_synthetic_filter")
        matched = all(values[field] == value for field, value in filters.items())
    else:
        raise ValueError("source_not_in_synthetic_fixture")
    if not set(plan["campos"]) <= set(values):
        raise ValueError("field_not_in_synthetic_fixture")
    rows = [{field: values[field] for field in plan["campos"]}] if matched else []
    return {"rows": rows,
            "coverage": {"state": "observed" if rows else "no_observation",
                         "rows": len(rows), "synthetic": True},
            "units": units}


def make_groq_model_call(model_id: str, protocol_prompt: str = ""):
    """Pin the same non-GPT Groq model across every role call."""
    if not isinstance(model_id, str) or not model_id or "gpt" in model_id.casefold() or "openai" in model_id.casefold():
        raise ValueError("Synthetic harness requires a non-GPT model")
    def call(role: str, envelope: dict, contract: dict) -> tuple[str, dict]:
        message, metadata = groq.chat_turn(
            role_messages(envelope, contract, protocol_prompt),
            0, 900, tools=None, harness_model=model_id,
            max_request_bytes=envelope.get("request_byte_limit", Limits().input_bytes))
        return message.get("content") or "", {
            "provider": "groq", "model_id": metadata.get("served_model"),
            "usage": metadata.get("usage"), "finish_reason": metadata.get("finish_reason"),
            "request_budget": metadata.get("request_budget")}
    return call


def role_messages(envelope: dict, contract: dict, protocol_prompt: str = "") -> list[dict]:
    """Identical per-role prompt for the synthetic provider audit."""
    system = ("Você executa exatamente um papel de um teste sintético. "
              "Responda somente com um objeto JSON válido, sem markdown ou texto fora dele. "
              "Não inclua campos extras. Use null para valores não aplicáveis. "
              "Se a entrada contiver correction_feedback, corrija o mesmo papel usando o erro e a dica. "
              f"{protocol_prompt}\n"
              f"Tarefa: {contract['task']}\n"
              "Schema da entrada em input: " + json.dumps(
                  INPUT_SCHEMAS[envelope["role"]].schema, ensure_ascii=False) + "\n"
              "Schema JSON obrigatório da saída: " + json.dumps(
                  contract["schema"], ensure_ascii=False))
    return [{"role": "system", "content": system},
            {"role": "user", "content": json.dumps(envelope, ensure_ascii=False)}]


def main() -> None:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="SPEC-013 synthetic-only Groq smoke")
    parser.add_argument("--output", type=Path, help="Optional local trace JSON path")
    args = parser.parse_args()
    settings = groq.harness_configuration()
    if not settings["available"]:
        raise SystemExit("Groq is not configured; no call sent")
    result = run(QUESTION, MAPS, make_groq_model_call(settings["model"], PROTOCOL_PROMPT), fixture_query)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"run_id": result["run_id"], "status": result["status"],
                      "model_calls": result["model_calls"], "queries": result["queries"],
                      "roles": [event["role"] for event in result["trace"]],
                      "error": result["final_state"].get("error") if result["final_state"] else None},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
