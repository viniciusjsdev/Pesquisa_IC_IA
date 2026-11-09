"""Regressions first: failures reproduced on the contract-2 baseline."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from dataclasses import asdict
from unittest.mock import patch
import unittest
import threading
import time
from inference_api.agent_harness import scenarios
from inference_api.observability.config import Config
from inference_api.observability.service import Observer
from inference_api.model_service import ModelService
from inference_api.model_service.registry import digest
from inference_api.identity.auth import Principal
from inference_api.executions import service
from spec014_fixture import profile,Transport,MAPS,fixture_query,QUESTION
from spec015_v3_fixture import packet,answer
from test_spec015_observability import MemorySink
from inference_api.observability import receipts

class Regressions(unittest.TestCase):
    def test_A_understands_industrial_and_financial_packet_without_query(self):
        p=profile()
        with patch('psycopg2.connect',side_effect=AssertionError('database forbidden')):
            result=scenarios.run(QUESTION,'fixed_evidence',p['id'],
                ModelService(p,{},transport=Transport(lambda e,_:answer(e))),packet=packet(),
                limits=scenarios.ScenarioLimits(query_attempts=0))
        self.assertEqual(result['status'],'answered_unverified',result['final_state'])
        self.assertEqual(result['model_calls'],8)
        self.assertEqual(result['queries'],0)

    def test_root_has_technical_error_for_timeout(self):
        p=profile();sink=MemorySink();obs=Observer('v3-timeout',Config(True,'redacted'),sink)
        result=scenarios.run(QUESTION,'data_access',p['id'],ModelService(p,{},transport=Transport(fail=TimeoutError())),
                             maps=MAPS,query=fixture_query,observer=obs)
        self.assertEqual(result['final_state']['error'],'provider_timeout')
        root=next(e for e in sink.events if e['metadata']['local_event_id']=='root')
        self.assertEqual(root['error'],'provider_timeout')

    def test_service_closes_root_after_persistence_not_inside_graph(self):
        p=profile();sink=MemorySink();obs=Observer('v3-managed',Config(True,'redacted'),sink)
        payload={'scenario':'data_access','question':QUESTION,'generation':{}}
        context={'profile':p,'request_sha256':digest(payload),'source':{},'catalog':{},'maps':MAPS,
                 'packet':None,'limits':asdict(scenarios.ScenarioLimits()),'authorization_sha256':'fixture'}
        def persist(author,snapshot):
            self.assertNotIn('root',obs.ended)
            return {'id':'00000000-0000-4000-8000-000000000003','snapshot':snapshot,'author':author}
        with patch('inference_api.agent_harness.graph.execution.create',return_value=obs), \
             patch.object(service,'create_observer',return_value=obs,create=True), \
             patch.object(service,'ModelService',return_value=ModelService(p,{},transport=Transport())), \
             patch.object(service.local_queries,'source_fingerprints',return_value={}), \
             patch.object(service.local_queries,'execute',side_effect=lambda plan,catalog:fixture_query(plan)), \
             patch.object(service.storage,'create_run',side_effect=persist), \
             patch.object(service.real_pilot,'preserve_failed_persistence'), \
             patch('psycopg2.connect',side_effect=AssertionError('unit test forbids DB')):
            result=service.execute_run(payload,Principal('00000000-0000-4000-8000-000000000001','Vinicius'),prepared=context)
        self.assertEqual(result['snapshot']['status'],'answered_unverified')
        self.assertIn('root',obs.ended)

    def test_persistence_failure_preserves_original_exception_and_closes_root_once(self):
        p=profile();sink=MemorySink();obs=Observer('v3-persist-failure',Config(True,'redacted'),sink)
        payload={'scenario':'fixed_evidence','question':QUESTION,'generation':{}}
        context={'profile':p,'request_sha256':digest(payload),'source':{},'catalog':None,'maps':None,
                 'packet':packet(),'limits':asdict(scenarios.ScenarioLimits(query_attempts=0)),'authorization_sha256':'fixture'}
        original=OSError('invented disk failure')
        with patch.object(service,'create_observer',return_value=obs), \
             patch.object(service,'ModelService',return_value=ModelService(p,{},transport=Transport(lambda e,_:answer(e)))), \
             patch.object(service.storage,'create_run',side_effect=original), \
             patch.object(service.real_pilot,'preserve_failed_persistence') as preserve, \
             patch('psycopg2.connect',side_effect=AssertionError('DB forbidden')):
            with self.assertRaises(OSError) as caught:
                service.execute_run(payload,Principal('fixture','Vinicius'),prepared=context)
        self.assertIs(caught.exception,original)
        self.assertIs(preserve.call_args.args[1],original)
        roots=[e for e in sink.events if e['parent_run_id'] is None]
        self.assertEqual(len(roots),1);self.assertEqual(roots[0]['error'],'persistence_error')
        obs.finish({'status':'answered_unverified'})
        self.assertEqual(len([e for e in sink.events if e['parent_run_id'] is None]),1)

    def test_success_insufficiency_and_technical_statuses_root_error_mapping(self):
        for status,code in [('answered_unverified',None),('insufficient_evidence',None),
                            ('contract_error','query_blocked'),('cancelled','cancelled'),
                            ('contract_error','provider_timeout'),('execution_error','execution_error')]:
            with self.subTest(status=status,code=code):
                sink=MemorySink();obs=Observer('v3-'+str(code),Config(True,'redacted'),sink)
                obs.finish({'status':status,'final_state':{'error':code} if code else None})
                self.assertEqual(sink.events[0]['error'],code)

    def test_slow_receipt_does_not_block_flush_and_final_late_delivery_is_durable(self):
        entered=threading.Event();release=threading.Event();saved=[]
        def progress(*args):
            entered.set();release.wait(3);saved.append(args)
        sink=MemorySink();obs=Observer('v3-late',Config(True,'metadata'),sink)
        obs.receipt_attached=True
        with patch.object(receipts,'progress',side_effect=progress):
            start=time.monotonic()
            obs.finish({'status':'insufficient_evidence'},timeout=.1)
            self.assertLess(time.monotonic()-start,.5)
            self.assertTrue(entered.wait(1));release.set()
            with obs.condition:
                obs.condition.wait_for(lambda:not obs._receipt_running,timeout=2)
        self.assertTrue(saved)
        self.assertTrue(saved[-1][2]);self.assertEqual(saved[-1][3]['pending_events'],0)

    def test_tracing_on_A_runs_remain_isolated_without_research_queries(self):
        p=profile();results=[]
        with patch('psycopg2.connect',side_effect=AssertionError('DB forbidden')), \
             patch.object(service.local_queries,'source_fingerprints',side_effect=AssertionError('fingerprint forbidden')):
            for number in range(2):
                sink=MemorySink();obs=Observer('v3-isolated-'+str(number),Config(True,'metadata'),sink)
                result=scenarios.run(QUESTION,'fixed_evidence',p['id'],
                    ModelService(p,{},transport=Transport(lambda e,_:answer(e))),packet=packet(),
                    limits=scenarios.ScenarioLimits(query_attempts=0),observer=obs)
                self.assertEqual(result['status'],'answered_unverified');self.assertEqual(result['queries'],0)
                results.append({e['id'] for e in sink.events})
        self.assertFalse(results[0]&results[1])

if __name__=='__main__':unittest.main()
