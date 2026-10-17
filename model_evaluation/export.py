"""Exporta pacotes determinísticos das consultas fixas da DW local."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from functools import lru_cache
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from BancoModeloUse.dw import fixed_queries

SCHEMA_VERSION = 1
QUERY_CONTRACT_VERSION = 1
SCHEMA_PATH = "model_evaluation/schemas/evidence_packet.schema.json"
DEFAULT_OUTPUT = ROOT / "model_evaluation" / ".local" / "packets"
CASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
KINDS = frozenset(("machine", "product", "financial", "quality", "material"))
DOMAINS = frozenset(("financeiro", "industrial", "integrado"))
MAX_QUERIES = 5
MAX_ROWS = 200
MAX_BYTES = 512 * 1024


class ExportError(ValueError):
    """Manifesto, consulta, limite ou pacote existente inválido."""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ExportError(f"Chave JSON duplicada: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ExportError(f"Número JSON inválido: {value}")


@lru_cache(maxsize=1)
def _packet_validator():
    schema = json.loads((Path(__file__).parent / "schemas" / "evidence_packet.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _keys(value: object, required: set[str], optional: set[str], where: str) -> dict:
    if not isinstance(value, dict):
        raise ExportError(f"{where}: objeto JSON obrigatório")
    missing = required - value.keys()
    extra = value.keys() - required - optional
    if missing or extra:
        raise ExportError(f"{where}: campos ausentes {sorted(missing)}; desconhecidos {sorted(extra)}")
    return value


def validate_manifest(manifest: object) -> list[dict]:
    manifest = _keys(manifest, {"schema_version", "cases"}, set(), "manifesto")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != SCHEMA_VERSION:
        raise ExportError("schema_version do manifesto deve ser 1")
    cases = manifest["cases"]
    if not isinstance(cases, list) or not cases:
        raise ExportError("cases deve ser uma lista não vazia")
    seen = set()
    for case in cases:
        case = _keys(case, {"case_id", "question", "domain", "queries"}, set(), "caso")
        case_id = case["case_id"]
        if not isinstance(case_id, str) or CASE_ID.fullmatch(case_id) is None:
            raise ExportError(f"case_id inválido: {case_id!r}")
        if case_id in seen:
            raise ExportError(f"case_id duplicado: {case_id}")
        seen.add(case_id)
        question = case["question"]
        if not isinstance(question, str) or not question.strip() or len(question) > 2000:
            raise ExportError(f"{case_id}: question deve ter 1 a 2000 caracteres úteis")
        try:
            question.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ExportError(f"{case_id}: question contém Unicode inválido") from exc
        if not isinstance(case["domain"], str) or case["domain"] not in DOMAINS:
            raise ExportError(f"{case_id}: domain inválido")
        queries = case["queries"]
        if not isinstance(queries, list) or not 1 <= len(queries) <= MAX_QUERIES:
            raise ExportError(f"{case_id}: limite de consultas (1 a {MAX_QUERIES}) excedido")
        for index, item in enumerate(queries):
            where = f"{case_id}.queries[{index}]"
            item = _keys(item, {"query", "year"}, {"id"}, where)
            kind = item["query"]
            if not isinstance(kind, str) or kind not in KINDS:
                raise ExportError(f"{where}: consulta fora da allowlist")
            year = item["year"]
            if type(year) is not int or not 2015 <= year <= 2026:
                raise ExportError(f"{where}: year fora de 2015..2026")
            if kind == "financial":
                if "id" in item:
                    raise ExportError(f"{where}: financial não aceita id")
            elif type(item.get("id")) is not int or item["id"] <= 0:
                raise ExportError(f"{where}: id positivo obrigatório")
    return cases


def load_manifest(path: Path) -> list[dict]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream, object_pairs_hook=_unique_pairs,
                              parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExportError(f"Não foi possível ler manifesto JSON: {exc}") from exc
    return validate_manifest(value)


def _verified_snapshot(report: dict) -> dict:
    if (not isinstance(report, dict) or report.get("database") != "db_pesquisa_dw" or
            type(report.get("schema_version")) is not int or report["schema_version"] != 1 or
            not isinstance(report.get("source_fingerprint"), str) or
            re.fullmatch(r"[0-9a-f]{64}", report["source_fingerprint"]) is None or
            type(report.get("source_files")) is not int or report["source_files"] < 1 or
            not isinstance(report.get("quality_flags"), dict)):
        raise ExportError("verify da DW não retornou snapshot válido")
    return {"database": report["database"],
            "schema_version": report["schema_version"],
            "source_fingerprint": report["source_fingerprint"],
            "source_files": report["source_files"]}


def _item_result(request: dict, result: dict) -> dict:
    if result.get("query") != request["query"] or result.get("year") != request["year"]:
        raise ExportError("Consulta da DW retornou filtros diferentes do solicitado")
    expected = {"query", "year", "grain", "sources", "formula", "units",
                "coverage", "rows", "interpretation"}
    if set(result) != expected or not isinstance(result["rows"], list):
        raise ExportError("Consulta da DW retornou contrato incompleto")
    if not isinstance(result["coverage"], dict) or result["coverage"].get("rows") != len(result["rows"]):
        raise ExportError("Consulta da DW retornou cobertura inconsistente")
    if result["coverage"].get("state") not in ("observed", "no_observation"):
        raise ExportError("Consulta da DW retornou estado de cobertura desconhecido")
    if (result["coverage"]["state"] == "no_observation") != (len(result["rows"]) == 0):
        raise ExportError("Consulta da DW retornou estado e linhas incompatíveis")
    return {"filters": request, **result}


def build_packets(cases: list[dict], *, verify_fn=None, query_fn=None,
                  query_code_path: Path | None = None) -> dict[str, bytes]:
    """Prepara todo o lote em memória; nenhuma saída é publicada em erro."""
    validate_manifest({"schema_version": SCHEMA_VERSION, "cases": cases})
    if verify_fn is None or query_fn is None:
        from BancoModeloUse.dw import cli as dw
        verify_fn = verify_fn or dw.verify
        query_fn = query_fn or dw.query
    query_code_path = query_code_path or Path(fixed_queries.__file__)
    query_code_sha256 = hashlib.sha256(query_code_path.read_bytes()).hexdigest()
    report = verify_fn()
    snapshot = _verified_snapshot(report)
    global_flags = report["quality_flags"]
    if any(type(value) is not int or value < 0 for value in global_flags.values()):
        raise ExportError("Flags globais de qualidade inválidas")
    packets = {}
    for case in cases:
        items = []
        row_count = 0
        for request in case["queries"]:
            result = query_fn(request["query"], request["year"], request.get("id"))
            item = _item_result(request, result)
            row_count += len(item["rows"])
            if row_count > MAX_ROWS:
                raise ExportError(f"{case['case_id']}: limite de {MAX_ROWS} linhas excedido")
            items.append(item)
        body = {"schema_version": SCHEMA_VERSION, "schema_path": SCHEMA_PATH,
                "case_id": case["case_id"], "question": case["question"],
                "domain": case["domain"], "source_snapshot": snapshot,
                "query_contract_version": QUERY_CONTRACT_VERSION,
                "query_code_sha256": query_code_sha256,
                "quality_summary": {"scope": "global_dw_load", "flags": global_flags},
                "limits": {"queries": MAX_QUERIES, "rows": MAX_ROWS, "bytes": MAX_BYTES},
                "evidence_items": items}
        body_bytes = canonical(body)
        envelope = {"body": body, "sha256": hashlib.sha256(body_bytes).hexdigest()}
        payload = canonical(envelope)
        if len(payload) > MAX_BYTES:
            raise ExportError(f"{case['case_id']}: limite de {MAX_BYTES} bytes excedido")
        packets[case["case_id"]] = payload
    if hashlib.sha256(query_code_path.read_bytes()).hexdigest() != query_code_sha256:
        raise ExportError("Código da consulta mudou durante a exportação")
    return packets


def verify_packet_bytes(payload: bytes, *, expected_case_id: str | None = None) -> dict:
    """Confere bytes canônicos, checksum e invariantes que JSON Schema não compara."""
    if not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        raise ExportError("Pacote não é bytes ou excede o limite")
    try:
        envelope = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_pairs,
                              parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ExportError(f"Pacote JSON inválido: {exc}") from exc
    envelope = _keys(envelope, {"body", "sha256"}, set(), "pacote")
    body = _keys(envelope["body"],
                 {"schema_version", "schema_path", "case_id", "question", "domain",
                  "source_snapshot", "query_contract_version", "query_code_sha256",
                  "quality_summary", "limits", "evidence_items"}, set(), "corpo")
    try:
        canonical_packet = canonical(envelope)
        body_bytes = canonical(body)
    except UnicodeEncodeError as exc:
        raise ExportError("Pacote contém Unicode inválido") from exc
    if payload != canonical_packet:
        raise ExportError("Pacote não está em JSON canônico")
    if envelope["sha256"] != hashlib.sha256(body_bytes).hexdigest():
        raise ExportError("Checksum do corpo diverge")
    if (type(body["schema_version"]) is not int or body["schema_version"] != SCHEMA_VERSION or
            body["schema_path"] != SCHEMA_PATH or
            type(body["query_contract_version"]) is not int or
            body["query_contract_version"] != QUERY_CONTRACT_VERSION or
            body["limits"] != {"queries": MAX_QUERIES, "rows": MAX_ROWS, "bytes": MAX_BYTES}):
        raise ExportError("Versão ou limites do pacote incompatíveis")
    if expected_case_id is not None and body["case_id"] != expected_case_id:
        raise ExportError("case_id do arquivo difere do corpo")
    snapshot = _keys(body["source_snapshot"],
                     {"database", "schema_version", "source_fingerprint", "source_files"},
                     set(), "source_snapshot")
    _verified_snapshot(snapshot | {"quality_flags": {}})
    if not isinstance(body["query_code_sha256"], str) or re.fullmatch(
            r"[0-9a-f]{64}", body["query_code_sha256"]) is None:
        raise ExportError("query_code_sha256 inválido")
    quality = _keys(body["quality_summary"], {"scope", "flags"}, set(), "quality_summary")
    if quality["scope"] != "global_dw_load" or not isinstance(quality["flags"], dict):
        raise ExportError("Resumo global de qualidade inválido")
    if any(type(value) is not int or value < 0 for value in quality["flags"].values()):
        raise ExportError("Flags globais de qualidade inválidas")
    items = body["evidence_items"]
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_QUERIES:
        raise ExportError("Quantidade de itens do pacote inválida")
    requests = []
    total_rows = 0
    for index, item in enumerate(items):
        item = _keys(item, {"filters", "query", "year", "grain", "sources", "formula",
                            "units", "coverage", "rows", "interpretation"}, set(),
                     f"evidence_items[{index}]")
        filters = item["filters"]
        if not isinstance(filters, dict) or item["query"] != filters.get("query") or item["year"] != filters.get("year"):
            raise ExportError("Filtros do item diferem da consulta")
        rows = item["rows"]
        coverage = item["coverage"]
        if not isinstance(rows, list) or not isinstance(coverage, dict):
            raise ExportError("Linhas ou cobertura inválidas")
        if (coverage.get("rows") != len(rows) or
                coverage.get("state") != ("observed" if rows else "no_observation")):
            raise ExportError("Cobertura contradiz as linhas do item")
        total_rows += len(rows)
        if total_rows > MAX_ROWS:
            raise ExportError("Limite total de linhas excedido")
        requests.append(filters)
    validate_manifest({"schema_version": SCHEMA_VERSION, "cases": [
        {"case_id": body["case_id"], "question": body["question"],
         "domain": body["domain"], "queries": requests}]})
    errors = list(_packet_validator().iter_errors(envelope))
    if errors:
        raise ExportError(f"Pacote não atende ao schema: {errors[0].message}")
    return envelope


def publish_packets(packets: dict[str, bytes], output_dir: Path) -> list[dict]:
    """Publica arquivos novos atomicamente, sem substituir existentes."""
    output_dir.mkdir(parents=True, exist_ok=True)
    actions = []
    for case_id, payload in packets.items():
        verify_packet_bytes(payload, expected_case_id=case_id)
        destination = output_dir / f"{case_id}.json"
        if destination.is_symlink():
            raise ExportError(f"Pacote existente é link simbólico: {destination}")
        if destination.exists():
            if not destination.is_file() or destination.read_bytes() != payload:
                raise ExportError(f"Pacote existente diverge; preservado: {destination}")
            actions.append({"case_id": case_id, "path": str(destination), "status": "reused",
                            "sha256": json.loads(payload)["sha256"]})
        else:
            actions.append({"case_id": case_id, "path": str(destination), "status": "created",
                            "sha256": json.loads(payload)["sha256"]})
    created = []
    try:
        for action in actions:
            if action["status"] == "reused":
                continue
            destination = Path(action["path"])
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(mode="wb", dir=output_dir, prefix=".packet-",
                                                 suffix=".tmp", delete=False) as stream:
                    temp_path = Path(stream.name)
                    stream.write(packets[action["case_id"]])
                    stream.flush()
                    os.fsync(stream.fileno())
                # Hard link is an atomic create-if-absent on the same filesystem.
                os.link(temp_path, destination)
                created.append(destination)
            finally:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)
    except OSError as exc:
        for destination in created:
            destination.unlink(missing_ok=True)
        raise ExportError(f"Falha ao publicar lote; novos arquivos removidos: {exc}") from exc
    return actions


def export(manifest_path: Path, output_dir: Path = DEFAULT_OUTPUT) -> list[dict]:
    cases = load_manifest(manifest_path)
    packets = build_packets(cases)
    return publish_packets(packets, output_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Manifesto JSON v1 de casos candidatos")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        actions = export(args.manifest, args.output_dir)
    except (ExportError, OSError, TypeError, ValueError) as exc:
        parser.exit(1, f"export failed: {exc}\n")
    print(json.dumps(actions, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
