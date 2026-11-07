"""SPEC-013 Groq pilot wiring, closed until exact real-data approval exists."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time
from uuid import UUID

from .engine import INPUT_SCHEMAS, Limits
from . import approved_catalog, catalog_runtime, local_queries
from .. import groq


ROOT = Path(__file__).resolve().parents[4]
REVIEW_PATH = ROOT / "specs/active/SPEC-013/evidence/m2-groq-real-data-transmission-review-2026-11-02.md"
RECEIPT_PATH = ROOT / "specs/active/SPEC-013/evidence/m2-groq-real-data-approval.json"
APPROVED_REVIEW_SHA256 = "271e6b1b9b647b33df991fa5b5763ae4de162ef70fcbdcf1563024f2516a0451"
APPROVAL_QUESTION_ID = "call_dde320b417a0400d9bf90d1843e27c35/1"
PROTOCOL_PROMPT = (
    "Execute apenas o papel JSON desta chamada. Use somente o trecho do mapa e "
    "as evidências entregues. Declare grão, cobertura e limites; ausência de "
    "observação não equivale a zero e associação não prova causalidade."
)
PILOT_LIMITS = Limits(calls=48, queries=3, input_bytes=32_768,
                      output_bytes=8_192, result_bytes=32_768)
PILOT_MIN_CALL_SPACING_SECONDS = 35


def require_external_approval() -> None:
    """A local semantic approval never opens the external Groq data gate."""
    if os.environ.get("INFERENCE_SPEC013_GROQ_REAL_DATA") != "1":
        raise ValueError("SPEC-013 real-data Groq gate is disabled")
    try:
        receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        review_sha = hashlib.sha256(REVIEW_PATH.read_bytes()).hexdigest()
    except (OSError, ValueError) as exc:
        raise ValueError("SPEC-013 real-data approval receipt is unavailable") from exc
    if (receipt.get("spec_id") != "SPEC-013" or
            receipt.get("decision") != "approved" or
            receipt.get("destination") != groq.ENDPOINT or
            receipt.get("reviewed_document_sha256") != APPROVED_REVIEW_SHA256 or
            review_sha != APPROVED_REVIEW_SHA256 or
            receipt.get("reviewed_document") != str(REVIEW_PATH.relative_to(ROOT)).replace("\\", "/") or
            receipt.get("approved_data_class") != "dw_industrial_financial_detail" or
            not isinstance(receipt.get("review_source"), dict) or
            receipt["review_source"].get("question_item_id") != APPROVAL_QUESTION_ID or
            receipt["review_source"].get("reply_verbatim") != "Autorizo esse envio à Groq"):
        raise ValueError("SPEC-013 real-data approval receipt does not match review")


def context():
    catalog = approved_catalog.load()
    return catalog, catalog_runtime.compile_maps(catalog)


def preserve_failed_persistence(snapshot: dict, error: Exception) -> Path:
    """Keep a private trace when PostgreSQL fails after provider calls.

    This is an emergency record, not a successful run or permission to retry.
    The caller must reconcile it with the app DB before any manual rerun.
    """
    run_id = snapshot["harness_result"]["run_id"]
    UUID(run_id)
    directory = ROOT / "inference_api/.local/spec013_failed_persistence"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{run_id}.json"
    record = {"status": "persistence_uncertain", "error_type": type(error).__name__,
              "snapshot": snapshot}
    rendered = json.dumps(record, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
    with target.open("xb") as stream:
        stream.write(rendered)
        stream.flush()
        os.fsync(stream.fileno())
    return target


def role_messages(envelope: dict, contract: dict, protocol_prompt: str) -> list[dict]:
    role = envelope["role"]
    system = ("Você executa um papel de uma consulta de pesquisa. Responda "
              "somente com um objeto JSON válido, sem markdown ou campos extras. "
              "Use null quando aplicável. Se houver correction_feedback, corrija "
              "o mesmo papel. " + protocol_prompt + "\nTarefa: " + contract["task"] +
              "\nSchema da entrada: " + json.dumps(INPUT_SCHEMAS[role].schema,
                                                   ensure_ascii=False) +
              "\nSchema obrigatório da saída: " + json.dumps(contract["schema"],
                                                                ensure_ascii=False))
    return [{"role": "system", "content": system},
            {"role": "user", "content": json.dumps(envelope, ensure_ascii=False)}]


def make_groq_model_call(model_id: str, protocol_prompt: str):
    require_external_approval()
    if not isinstance(model_id, str) or not model_id or any(
            forbidden in model_id.casefold() for forbidden in ("gpt", "openai")):
        raise ValueError("SPEC-013 pilot requires a non-GPT Groq model")
    last_started: float | None = None

    def call(role: str, envelope: dict, contract: dict) -> tuple[str, dict]:
        nonlocal last_started
        if last_started is not None:
            remaining = PILOT_MIN_CALL_SPACING_SECONDS - (time.monotonic() - last_started)
            if remaining > 0:
                time.sleep(remaining)
        last_started = time.monotonic()
        message, metadata = groq.chat_turn(
            role_messages(envelope, contract, protocol_prompt),
            0, 900, tools=None, harness_model=model_id,
            max_request_bytes=envelope.get("request_byte_limit", PILOT_LIMITS.input_bytes))
        return message.get("content") or "", {
            "provider": "groq", "model_id": metadata.get("served_model"),
            "usage": metadata.get("usage"), "finish_reason": metadata.get("finish_reason"),
            "request_budget": metadata.get("request_budget")}
    return call
