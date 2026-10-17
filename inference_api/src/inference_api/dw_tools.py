"""Allowlisted read-only access to the five DW v1 fixed queries."""
import hashlib
from contextlib import closing
from pathlib import Path
import re
import sys

import psycopg2

from .config import ROOT, dw_db_params

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from BancoModeloUse.dw import fixed_queries  # noqa: E402
from model_evaluation.export import canonical  # noqa: E402

NAMES = ("machine", "product", "financial", "quality", "material")
MAX_CALLS = 5
MAX_TURNS = 6
MAX_ROWS = 200
MAX_BYTES = 16 * 1024


class DWFingerprintError(ValueError):
    """The DW version changed after availability was recorded."""


class DWResultLimitError(ValueError):
    """A fixed query exceeded the Bancada's operational result budget."""


def catalog() -> list[dict]:
    result = []
    for name in NAMES:
        properties = {"year": {"type": "integer", "minimum": 2015, "maximum": 2026}}
        required = ["year"]
        if name != "financial":
            properties["id"] = {"type": "integer", "minimum": 1}
            required.append("id")
        result.append({"type": "function", "function": {
            "name": name,
            "description": f"Consulta fixa de leitura da DW para {name}; preserva cobertura, grão, fórmula, unidades e ressalvas. Sem SQL livre.",
            "parameters": {"type": "object", "properties": properties,
                           "required": required, "additionalProperties": False}}})
    return result


def validate_call(name: str, arguments: object) -> dict:
    if name not in NAMES or not isinstance(arguments, dict):
        raise ValueError("Unknown or malformed DW tool")
    required = {"year"} if name == "financial" else {"year", "id"}
    if set(arguments) != required:
        raise ValueError("DW tool arguments differ from fixed contract")
    year = arguments["year"]
    if type(year) is not int or not 2015 <= year <= 2026:
        raise ValueError("DW tool year outside 2015..2026")
    if name != "financial" and (type(arguments["id"]) is not int or arguments["id"] <= 0):
        raise ValueError("DW tool id must be positive")
    return arguments


def availability() -> dict:
    try:
        with closing(psycopg2.connect(**dw_db_params())) as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SET TRANSACTION READ ONLY")
                    cur.execute("SELECT version, source_fingerprint FROM dw.schema_migrations")
                    rows = cur.fetchall()
        if (len(rows) != 1 or rows[0][0] != 1 or not isinstance(rows[0][1], str)
                or not re.fullmatch(r"[0-9a-f]{64}", rows[0][1].strip())):
            raise ValueError("DW migration or fingerprint unavailable")
        return {"available": True, "database": "db_pesquisa_dw", "schema_version": 1,
                "query_contract_version": 1, "source_fingerprint": rows[0][1].strip(),
                "query_code_sha256": hashlib.sha256(Path(fixed_queries.__file__).read_bytes()).hexdigest()}
    except (psycopg2.Error, ValueError, OSError):
        return {"available": False, "reason": "DW isolada indisponível ou sem migração v1"}


def execute(name: str, arguments: dict, *, expected_fingerprint: str | None = None) -> dict:
    args = validate_call(name, arguments)
    with closing(psycopg2.connect(**dw_db_params())) as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute("SELECT version, source_fingerprint FROM dw.schema_migrations")
                rows = cur.fetchall()
            if (len(rows) != 1 or rows[0][0] != 1 or
                    not isinstance(rows[0][1], str) or
                    expected_fingerprint is not None and rows[0][1].strip() != expected_fingerprint):
                raise DWFingerprintError("DW fingerprint changed or migration unavailable")
            result = fixed_queries.query(name, args["year"], args.get("id"),
                                         connection=conn, readonly_already=True)
    if len(result["rows"]) > MAX_ROWS or len(canonical(result)) > MAX_BYTES:
        raise DWResultLimitError("DW tool result exceeds operational limits")
    return result
