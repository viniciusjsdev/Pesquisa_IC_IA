"""Explicitly approved OpenAI engineering pilot; same role/query contracts."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace

from . import real_pilot
from .. import openai_provider

ROOT = real_pilot.ROOT
REVIEW_PATH = ROOT / 'specs/active/SPEC-013/evidence/engineering-scope-2026-11-05.md'
RECEIPT_PATH = ROOT / 'specs/active/SPEC-013/evidence/m2-openai-engineering-approval-2026-11-05.json'
APPROVED_SHA256 = '29d063dacd75e9de06b4f7aa2b2ca92af3ace836906d5dc94e1a426d98246b9c'
MAX_OUTPUT_TOKENS = None
OUTPUT_POLICY = 'engineering_output_observation_20261105'
PILOT_LIMITS = replace(real_pilot.PILOT_LIMITS, output_bytes=None)


def require_external_approval() -> None:
    if os.environ.get('INFERENCE_SPEC013_OPENAI_REAL_DATA') != '1':
        raise ValueError('SPEC-013 real-data OpenAI gate is disabled')
    try:
        receipt = json.loads(RECEIPT_PATH.read_text(encoding='utf-8'))
        digest = hashlib.sha256(REVIEW_PATH.read_bytes()).hexdigest()
    except (OSError, ValueError) as exc:
        raise ValueError('SPEC-013 OpenAI approval receipt is unavailable') from exc
    expected = {'spec_id': 'SPEC-013', 'decision': 'approved', 'provider': 'openai',
                'destination': openai_provider.ENDPOINT, 'purpose': 'engineering_validation',
                'approved_data_class': 'dw_industrial_financial_detail',
                'reviewed_document': REVIEW_PATH.relative_to(ROOT).as_posix(),
                'reviewed_document_sha256': APPROVED_SHA256,
                'scientific_scoring_authorized': False}
    if digest != APPROVED_SHA256 or any(receipt.get(k) != v for k, v in expected.items()):
        raise ValueError('SPEC-013 OpenAI approval receipt does not match scope')


def make_model_call(model_id: str, protocol_prompt: str):
    require_external_approval()
    if model_id != openai_provider.MODEL:
        raise ValueError('SPEC-013 OpenAI model does not match approved configuration')

    def call(role: str, envelope: dict, contract: dict) -> tuple[str, dict]:
        # No cross-role hidden history and no automatic retry on provider errors.
        conversation = openai_provider.Conversation()
        message, metadata = conversation.chat_turn(
            real_pilot.role_messages(envelope, contract, protocol_prompt),
            0, MAX_OUTPUT_TOKENS, tools=None, omit_output_token_limit=True,
            max_request_bytes=envelope.get('request_byte_limit', PILOT_LIMITS.input_bytes))
        return message.get('content') or '', {
            key: metadata[key] for key in ('provider', 'model_id', 'api_surface',
                'usage', 'finish_reason', 'request_id', 'response_id', 'store', 'request_budget')
            if key in metadata}
    return call
