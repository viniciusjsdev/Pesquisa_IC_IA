"""Small invented fixture for M1; never reads the research databases."""
from __future__ import annotations

import json
from datetime import date
from jsonschema import Draft202012Validator



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
