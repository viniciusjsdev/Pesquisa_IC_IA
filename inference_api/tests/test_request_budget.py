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
from test_spec012 import Stream, response, answer




class RequestBudgetTests(unittest.TestCase):
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

if __name__=="__main__": unittest.main()
