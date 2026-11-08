"""Exact serialized payload ceilings; transport is always mocked."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError, URLError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from inference_api import groq, models, openai_provider
from inference_api.model_service.request_budget import encode_request, RequestBudgetExceeded
from inference_api.agent_harness import run, Limits
from inference_api.agent_harness import openai_pilot, real_pilot, synthetic_demo, openai_audit
from test_spec012 import Stream, response, answer


class RequestBudgetTests(unittest.TestCase):
    def test_provider_failures_keep_exact_payload_receipt_in_trace_without_retry(self):
        for provider in ('openai', 'groq'):
            for failure in ('http', 'timeout', 'connection', 'stream'):
                with self.subTest(provider=provider, failure=failure):
                    error = {'http': HTTPError('https://fixture.invalid', 429, 'limited', {}, None),
                             'timeout': TimeoutError(), 'connection': URLError('fixture')} .get(failure)
                    with patch.dict(os.environ, {'OPENAI_API_KEY': 'fixture-not-a-key', 'GROQ_API_KEY': 'fixture'}), \
                         patch.object(openai_pilot, 'require_external_approval'), \
                         patch.object(real_pilot, 'require_external_approval'), \
                         patch.object(models, 'urlopen') as send, \
                         patch.object(models, '_read_chat_stream', side_effect=models.ModelResponseError('invalid stream', {})):
                        send.side_effect = error
                        send.return_value = Stream(response([]), complete=False)
                        factory = (openai_pilot.make_model_call(openai_provider.MODEL, '') if provider == 'openai'
                                   else real_pilot.make_groq_model_call(groq.harness_configuration()['model'], ''))
                        result = run(synthetic_demo.QUESTION, synthetic_demo.MAPS, factory,
                                     lambda _: self.fail('no query on provider error'))
                        self.assertEqual(send.call_count, 1)
                        event = result['trace'][0]
                        self.assertEqual(event['status'], 'provider_error')
                        body = send.call_args.args[0].data
                        self.assertEqual(event['request_budget']['sha256'], hashlib.sha256(body).hexdigest())
                        self.assertEqual(event['request_budget']['bytes'], len(body))
                        if failure == 'http': self.assertEqual(event['http_status'], 429)

    def test_utf8_exact_boundary_and_hash(self):
        value = {'message': 'ação 漢字'}
        body, receipt = encode_request(value)
        self.assertEqual(receipt['bytes'], len(body))
        self.assertGreater(len(body), len(body.decode('utf-8')))
        self.assertEqual(receipt['sha256'], hashlib.sha256(body).hexdigest())
        self.assertEqual(encode_request(value, len(body))[0], body)
        with self.assertRaises(RequestBudgetExceeded):
            encode_request(value, len(body) - 1)

    def test_openai_measures_actual_body_and_blocks_before_network(self):
        messages = [{'role': 'system', 'content': 'ação' * 400}, {'role': 'user', 'content': '{}'}]
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fixture-not-a-key'}), \
             patch.object(models, 'urlopen', return_value=Stream(response([answer('ok')]))) as send:
            _, meta = openai_provider.Conversation().chat_turn(messages, 0, 50, tools=None)
            sent = send.call_args.args[0].data
            self.assertEqual(meta['request_budget']['bytes'], len(sent))
            send.reset_mock()
            with self.assertRaises(RequestBudgetExceeded):
                openai_provider.Conversation().chat_turn(messages, 0, 50, tools=None, max_request_bytes=len(sent)-1)
            send.assert_not_called()
            openai_provider.Conversation().chat_turn(messages, 0, 50, tools=None, max_request_bytes=len(sent))
            self.assertEqual(send.call_args.args[0].data, sent)

    def test_groq_measures_actual_body_and_blocks_before_network(self):
        messages = [{'role': 'system', 'content': 'ação' * 400}, {'role': 'user', 'content': '{}'}]
        result = {'model': 'fixture', 'choices': [{'finish_reason': 'stop', 'message': {'content': '{}'}}]}
        with patch.dict(os.environ, {'GROQ_API_KEY': 'fixture-not-a-key', 'GROQ_MODEL': 'fixture'}), \
             patch.object(models, 'urlopen') as send, \
             patch.object(models, '_read_chat_stream', return_value=(result, '')):
            send.return_value.__enter__.return_value.headers = {'Content-Type': 'text/event-stream'}
            _, meta = groq.chat_turn(messages, 0, 50, tools=None)
            body = send.call_args.args[0].data
            self.assertEqual(meta['request_budget']['bytes'], len(body))
            self.assertEqual(meta['request_budget']['sha256'], hashlib.sha256(body).hexdigest())
            send.reset_mock()
            with self.assertRaises(RequestBudgetExceeded):
                groq.chat_turn(messages, 0, 50, tools=None, max_request_bytes=len(body)-1)
            send.assert_not_called()

    def test_small_envelope_large_protocol_is_terminal_visible_and_never_sent(self):
        with patch.object(openai_pilot, 'require_external_approval'), \
             patch.dict(os.environ, {'OPENAI_API_KEY': 'fixture-not-a-key'}), \
             patch.object(models, 'urlopen') as send:
            result = run(synthetic_demo.QUESTION, synthetic_demo.MAPS,
                openai_pilot.make_model_call(openai_provider.MODEL, 'instrução ' * 1000),
                lambda _: self.fail('query must not execute'), limits=Limits(input_bytes=4096))
            send.assert_not_called()
        self.assertEqual(result['status'], 'contract_error')
        self.assertEqual(result['final_state']['error'], 'input_context_limit')
        self.assertEqual(len(result['trace']), 1)
        event = result['trace'][0]
        self.assertLess(event['input_envelope_bytes'], 4096)
        self.assertGreater(event['request_budget']['bytes'], 4096)
        self.assertFalse(event['request_dispatched'])
        self.assertEqual(event['status'], 'rejected')

    def test_all_harness_transports_receive_envelope_budget(self):
        envelope = {'role': 'analista_pergunta', 'request_byte_limit': 9876}
        contract = {'task': 'test', 'schema': {'type': 'object'}}
        with patch.object(real_pilot, 'require_external_approval'), \
             patch.object(groq, 'chat_turn', return_value=({'content': '{}'}, {})) as send:
            for factory in (real_pilot.make_groq_model_call, synthetic_demo.make_groq_model_call):
                factory('fixture', '')('analista_pergunta', envelope, contract)
                self.assertEqual(send.call_args.kwargs['max_request_bytes'], 9876)
        with patch.object(openai_provider, 'Conversation') as factory:
            factory.return_value.chat_turn.return_value = ({'content': '{}'}, {})
            openai_audit.model_call('analista_pergunta', envelope, contract)
            self.assertEqual(factory.return_value.chat_turn.call_args.kwargs['max_request_bytes'], 9876)


if __name__ == '__main__': unittest.main()
