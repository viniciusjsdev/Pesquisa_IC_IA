"""Allowlisted read-only access to five fixed DW queries on known V1/V2 loads."""
import hashlib
from contextlib import closing
from pathlib import Path
import re
import sys

import psycopg2

from inference_api.config import ROOT, dw_db_params

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from BancoModeloUse.dw import fixed_queries  # noqa: E402
from model_evaluation.export import canonical  # noqa: E402

NAMES = ("machine", "product", "financial", "quality", "material")
KNOWN_V2_FINGERPRINT = "66f8808cf83902ff6c7fd277937bf8e0671482058f540f3ea9c1ec8c5a182800"
MAX_CALLS = 5
MAX_TURNS = 6
MAX_ROWS = 200
MAX_BYTES = 16 * 1024


class DWFingerprintError(ValueError):
    """The DW version changed after availability was recorded."""


class DWResultLimitError(ValueError):
    """A fixed query exceeded the Bancada's operational result budget."""


def _supported_migration(rows: list) -> tuple[int, str]:
    """Accept historical V1 and the reviewed, immutable canonical V2 load."""
    if len(rows) != 1 or type(rows[0][0]) is not int or not isinstance(rows[0][1], str):
        raise DWFingerprintError("DW migration unavailable")
    version, digest = rows[0][0], rows[0][1].strip()
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise DWFingerprintError("DW fingerprint invalid")
    if version != 1 and not (version == 2 and digest == KNOWN_V2_FINGERPRINT):
        raise DWFingerprintError("DW migration not in the reviewed allowlist")
    return version, digest


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
        version, digest = _supported_migration(rows)
        return {"available": True, "database": "db_pesquisa_dw", "schema_version": version,
                "query_contract_version": 1, "source_fingerprint": digest,
                "query_code_sha256": hashlib.sha256(Path(fixed_queries.__file__).read_bytes()).hexdigest()}
    except (psycopg2.Error, ValueError, OSError):
        return {"available": False, "reason": "DW isolada indisponível ou sem migração permitida"}


def execute(name: str, arguments: dict, *, expected_fingerprint: str | None = None) -> dict:
    args = validate_call(name, arguments)
    with closing(psycopg2.connect(**dw_db_params())) as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute("SELECT version, source_fingerprint FROM dw.schema_migrations")
                rows = cur.fetchall()
            _, digest = _supported_migration(rows)
            if expected_fingerprint is not None and digest != expected_fingerprint:
                raise DWFingerprintError("DW fingerprint changed or migration unavailable")
            result = fixed_queries.query(name, args["year"], args.get("id"),
                                         connection=conn, readonly_already=True)
    if len(result["rows"]) > MAX_ROWS or len(canonical(result)) > MAX_BYTES:
        raise DWResultLimitError("DW tool result exceeds operational limits")
    return result
