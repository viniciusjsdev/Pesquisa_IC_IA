"""Provider-specific authorization, isolated role calls and snapshot identity."""
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from inference_api import service, openai_provider, models
from inference_api.agent_harness import openai_pilot, real_pilot
from inference_api.auth import Principal


class OpenAIPilotTests(unittest.TestCase):
    def payload(self):
        return dict(provider='openai', model_alias='openai_harness_pilot',
                    evidence_mode='agent_harness_pilot', question='Pergunta de teste',
                    system_prompt=real_pilot.PROTOCOL_PROMPT)

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    def test_approval_exact_document_and_destination(self):
        with patch.dict(os.environ, {'INFERENCE_SPEC013_OPENAI_REAL_DATA': '1'}):
            openai_pilot.require_external_approval()
            with TemporaryDirectory() as folder:
                bad = Path(folder) / 'receipt.json'
                receipt = json.loads(openai_pilot.RECEIPT_PATH.read_text(encoding='utf-8'))
                receipt['destination'] = 'https://example.invalid'
                bad.write_text(json.dumps(receipt), encoding='utf-8')
                with patch.object(openai_pilot, 'RECEIPT_PATH', bad):
                    with self.assertRaisesRegex(ValueError, 'does not match'):
                        openai_pilot.require_external_approval()

    def test_role_context_is_fresh_and_provider_error_not_retried(self):
        with patch.object(openai_pilot, 'require_external_approval'), \
             patch.object(openai_provider, 'Conversation') as factory:
            factory.return_value.chat_turn.return_value = ({'content': '{}'},
                {'provider': 'openai', 'model_id': openai_provider.MODEL, 'usage': {}})
            call = openai_pilot.make_model_call(openai_provider.MODEL, real_pilot.PROTOCOL_PROMPT)
            for _ in range(2):
                call('analista_pergunta', {'role': 'analista_pergunta'},
                     {'task': 'test', 'schema': {'type': 'object'}})
            self.assertEqual(factory.call_count, 2)
            self.assertIsNone(factory.return_value.chat_turn.call_args.args[2])
            self.assertTrue(factory.return_value.chat_turn.call_args.kwargs['omit_output_token_limit'])
            factory.return_value.chat_turn.side_effect = openai_provider.OpenAIError('provider_rate_limited', 'limited')
            with self.assertRaises(openai_provider.OpenAIError):
                call('analista_pergunta', {'role': 'analista_pergunta'},
                     {'task': 'test', 'schema': {'type': 'object'}})
            self.assertEqual(factory.return_value.chat_turn.call_count, 3)

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass


if __name__ == '__main__':
    unittest.main()
