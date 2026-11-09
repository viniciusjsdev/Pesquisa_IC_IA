import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
"""Synthetic telemetry: SDK serialization, privacy, failure isolation and opt-in."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
import unittest
from unittest.mock import patch
from uuid import UUID
import requests
from urllib3.util.retry import Retry
from langsmith import Client
from inference_api.agent_harness import scenarios
from inference_api.observability.config import Config, load
from inference_api.observability.contracts import sdk_id, usage_metadata
from inference_api.observability.langsmith_sink import LangSmithSink
from inference_api.observability.service import Observer, Dispatcher
from inference_api.observability.sanitize import project
from spec014_fixture import profile, packet, Transport, MAPS, fixture_query, QUESTION
from inference_api.model_service import ModelService
from spec015_cases import normalize

RUN = '00000000-0000-4000-8000-000000000015'

class MemorySink:
    def __init__(self, failure=False): self.events, self.failure = [], failure
    def send(self, event):
        if self.failure: raise TimeoutError('synthetic telemetry failure')
        self.events.append(deepcopy(event))
    def url(self, trace_id): return None

class LocalSession(requests.Session):
    """Actual SDK serializes each request; this transport never opens a socket."""
    def __init__(self, fail=False): super().__init__(); self.sent=[]; self.fail=fail
    def request(self, method, url, **kwargs):
        self.sent.append((method, url, kwargs))
        if self.fail: raise requests.Timeout('synthetic timeout')
        response = requests.Response(); response.status_code = 200
        response.url=url; response.headers['Content-Type']='application/json'
        value = {}
        if method.upper() == 'GET' and '/runs/' in url:
            rid=url.rsplit('/',1)[-1]
            value={'id':rid,'name':'Bancada','run_type':'chain','start_time':datetime.now(timezone.utc).isoformat(),
                   'inputs':{},'outputs':{},'app_path':f'/o/fixture-org/projects/p/fixture-project/r/{rid}'}
        response._content=json.dumps(value).encode()
        return response

class ObservabilityTests(unittest.TestCase):
    def run_case(self, scenario='fixed_evidence', adapter='groq_chat', *, sink=None, observer=None, transport=None):
        sink = sink or MemorySink()
        observer = observer or Observer(RUN, Config(True, 'redacted', project='fixture', api_key='fixture-key'), sink)
        p=profile(adapter); transport=transport or Transport(); fixed=scenario=='fixed_evidence'
        with patch.object(scenarios,'uuid4',return_value=UUID(RUN)):
            result=scenarios.run(QUESTION,scenario,p['id'],ModelService(p,{},transport=transport),
                packet=packet() if fixed else None,maps=None if fixed else MAPS,
                query=None if fixed else fixture_query,
                limits=scenarios.ScenarioLimits(query_attempts=0 if fixed else 3),observer=observer)
        return result,sink,transport

    def test_matrix_hierarchy_identity_tokens_and_no_duplicates(self):
        for scenario in ('fixed_evidence','data_access'):
            for adapter in ('groq_chat','openai_responses','chat_completions'):
                with self.subTest(scenario=scenario,adapter=adapter):
                    result,sink,_=self.run_case(scenario,adapter)
                    self.assertEqual(result['observability']['state'],'submitted')
                    self.assertEqual(len(sink.events),1+2*result['model_calls']+result['query_attempts'])
                    ids={e['id'] for e in sink.events}; self.assertEqual(len(ids),len(sink.events))
                    root=next(e for e in sink.events if e['metadata']['local_event_id']=='root')
                    self.assertEqual(root['metadata']['profile_sha256'],profile(adapter)['sha256'])
                    from inference_api.model_service.registry import digest
                    self.assertEqual(root['metadata']['generation_sha256'],digest({}))
                    for event in sink.events:
                        UUID(event['id']); self.assertEqual(event['trace_id'],sdk_id(RUN,'root'))
                        if event['parent_run_id']: self.assertIn(event['parent_run_id'],ids)
                        if event['run_type']=='llm':
                            self.assertEqual(event['metadata']['usage_metadata'],{'input_tokens':10,'output_tokens':20})
                            self.assertTrue(event['inputs']['messages'])
                            self.assertEqual(event['metadata']['ls_model_name'],'fixture-model')

    def test_sdk_serialization_and_private_url_without_socket(self):
        session=LocalSession()
        client=Client(api_url='https://api.smith.langchain.com',api_key='fixture-key',session=session,
            auto_batch_tracing=False,info={'version':'fixture'},omit_traced_runtime_info=True,
            retry_config=Retry(total=0),timeout_ms=2000)
        sink=LangSmithSink(Config(True,'redacted',project='fixture',api_key='fixture-key'),client)
        result,_,_=self.run_case('data_access',sink=sink)
        self.assertEqual(result['observability']['state'],'submitted')
        self.assertIn('/o/fixture-org/projects/p/fixture-project/r/',result['observability']['url'])
        posts=[json.loads(kwargs['data']) for method,_,kwargs in session.sent if method=='POST']
        self.assertEqual(len(posts),1+2*result['model_calls']+result['query_attempts'])
        llm=next(p for p in posts if p['run_type']=='llm')
        self.assertEqual(llm['extra']['metadata']['ls_model_name'],'fixture-model')
        self.assertTrue(llm['inputs']['messages'])
        self.assertTrue(llm['end_time'])

    def test_production_constructor_with_real_sdk_and_local_transport(self):
        session=LocalSession()
        with patch.dict('os.environ',{'LANGSMITH_RUNS_ENDPOINTS':json.dumps({'https://untrusted.invalid':'foreign-fixture-key'})}), \
             patch('langsmith.Client',side_effect=lambda **kwargs: Client(session=session,**kwargs)):
            sink=LangSmithSink(Config(True,'redacted',project='fixture',api_key='fixture-key'))
        result,_,_=self.run_case(sink=sink)
        self.assertEqual(result['observability']['state'],'submitted')
        self.assertEqual(len([m for m,_,_ in session.sent if m=='POST']),11)
        self.assertTrue(all(url.startswith('https://api.smith.langchain.com/') for _,url,_ in session.sent))

    def test_snapshot_does_not_end_or_submit_again(self):
        sink=MemorySink();observer=Observer(RUN,Config(True,'redacted'),sink)
        span=observer.start('one','fixture','chain');observer.end(span)
        report=observer.finish({'status':'completed'})
        count=len(sink.events)
        for _ in range(3):self.assertEqual(observer.snapshot(),report)
        self.assertEqual(count,len(sink.events))

    def test_off_ignores_global_flags_and_creds_no_network(self):
        with patch.dict('os.environ',{'LANGSMITH_TRACING':'true','LANGCHAIN_TRACING_V2':'true',
                'LANGSMITH_API_KEY':'fixture-key','INFERENCE_OBSERVABILITY':'off'}), \
             patch('requests.Session.request',side_effect=AssertionError('unexpected telemetry')) as send:
            p=profile(); result=scenarios.run(QUESTION,'fixed_evidence',p['id'],
                ModelService(p,{},transport=Transport()),packet=packet(),limits=scenarios.ScenarioLimits(query_attempts=0))
            self.assertEqual(result['observability']['state'],'disabled'); send.assert_not_called()
        self.assertFalse(load({'LANGSMITH_API_KEY':'fixture-key'}).enabled)
        self.assertFalse(load({'INFERENCE_OBSERVABILITY':'langsmith'}).enabled)

    def test_sdk_timeout_no_retry_and_response_preserved(self):
        session=LocalSession(fail=True)
        client=Client(api_url='https://api.smith.langchain.com',api_key='fixture-key',session=session,
            auto_batch_tracing=False,info={'version':'fixture'},omit_traced_runtime_info=True,
            retry_config=Retry(total=0),timeout_ms=2000)
        result,_,transport=self.run_case(sink=LangSmithSink(Config(True,'redacted',project='fixture',api_key='fixture-key'),client))
        self.assertEqual(result['status'],'answered_unverified')
        self.assertEqual(result['observability']['state'],'failed')
        self.assertEqual(len(transport.requests),result['model_calls'])
        self.assertEqual(len(session.sent),1+2*result['model_calls'])

    def test_redaction_before_queue_never_mutates_local_inputs(self):
        data={'messages':[{'role':'user','content':json.dumps({'password':'nested-secret','gold':'answer-secret','ok':42})}],
              'nested':{'api_key':'secret','client':object()},'error':'Bearer abcdef postgresql://user:pass@host/db'}
        before=deepcopy(data)
        event={'id':'fixture','inputs':data,'outputs':{},'metadata':{'ls_model_name':'fixture','arbitrary':'secret'}}
        cleaned=project(event,'redacted')
        serialized=json.dumps(cleaned)
        for secret in ('nested-secret','answer-secret','abcdef','user:pass','"api_key": "secret"'):
            self.assertNotIn(secret,serialized)
        self.assertEqual(data['messages'],before['messages'])
        self.assertNotIn('arbitrary',cleaned['metadata'])
        metadata=project(event,'metadata'); self.assertEqual(metadata['inputs'],{})
        oversized=project({**event,'outputs':{'large':'x'*70000}},'redacted')
        self.assertTrue(oversized['metadata']['content_omitted']); self.assertLessEqual(len(json.dumps(oversized).encode()),65536)

    def test_reasoning_is_subtype_and_unknown_is_unknown(self):
        self.assertEqual(usage_metadata({'input':None,'output':None,'reasoning':None,'total':None}),{})
        self.assertEqual(usage_metadata({'input':10,'output':20,'reasoning':5}),
                         {'input_tokens':10,'output_tokens':20,'output_token_details':{'reasoning':5}})
        _,sink,_=self.run_case(transport=Transport(usage=False))
        self.assertTrue(all(e['metadata']['usage_metadata']=={} for e in sink.events if e['run_type']=='llm'))

    def test_opaque_tokens_metadata_hash_and_invalid_config_are_isolated(self):
        from inference_api.observability.service import create
        from hashlib import sha256
        for field in ('token','access_token','refresh_token','id_token'):
            self.assertNotIn('opaque-secret',json.dumps(project({'inputs':{field:'opaque-secret'}},'redacted')))
        malformed=project({'outputs':{'raw':'{"password":"opaque-secret"'}},'redacted')
        self.assertNotIn('opaque-secret',json.dumps(malformed))
        embedded=project({'outputs':{'raw':'payload {"access_token":"opaque-secret"'}},'redacted')
        self.assertNotIn('opaque-secret',json.dumps(embedded))
        sink=MemorySink(); observer=Observer(RUN,Config(True,'metadata'),sink)
        span=observer.start('hash','fixture','chain',inputs={'business':42})
        expected=observer.events[span]['metadata']['inputs_sha256']
        observer.end(span); observer.finish({'status':'fixture'})
        event=next(e for e in sink.events if e['name']=='fixture')
        self.assertEqual(event['metadata']['inputs_sha256'],expected)
        self.assertNotEqual(expected,sha256(b'{}').hexdigest())
        with patch.dict('os.environ',{'INFERENCE_OBSERVABILITY':'langsmith','LANGSMITH_API_KEY':'fixture',
                'INFERENCE_OBSERVABILITY_PROJECT':'fixture','INFERENCE_OBSERVABILITY_ENDPOINT':'https://[invalid'}):
            self.assertEqual(create(RUN).finish({})['state'],'disabled')
        class BadUrl(MemorySink):
            def url(self,*_): raise ValueError('fixture')
        result,_,_=self.run_case(sink=BadUrl())
        self.assertEqual(result['status'],'answered_unverified')

    def test_repairs_errors_and_no_cross_run_context(self):
        first=True
        def malformed(e,v):
            nonlocal first
            if first: first=False; return 'not-json'
            return v
        result,sink,_=self.run_case(transport=Transport(malformed))
        agent_spans=[e for e in sink.events if e['name']=='analista_pergunta']
        self.assertEqual([e['status'] for e in agent_spans],['rejected','validated'])
        with ThreadPoolExecutor(max_workers=2) as executor:
            def one(rid):
                sink=MemorySink(); observer=Observer(rid,Config(True,'redacted'),sink)
                p=profile(); r=scenarios.run(QUESTION,'fixed_evidence',p['id'],ModelService(p,{},transport=Transport()),
                    packet=packet(),limits=scenarios.ScenarioLimits(query_attempts=0),observer=observer)
                return sink.events
            groups=list(executor.map(one,['run-one','run-two']))
        self.assertTrue({e['id'] for e in groups[0]}.isdisjoint({e['id'] for e in groups[1]}))
        for group,rid in zip(groups,['run-one','run-two']):
            self.assertEqual({e['metadata']['local_run_id'] for e in group},{rid})

    def test_queue_full_flush_bounded_and_duplicate_end(self):
        class Reject:
            def submit(self,*_): return False
        observer=Observer(RUN,Config(True),MemorySink(),dispatch=Reject())
        span=observer.start('one','fixture','chain'); observer.end(span); observer.end(span)
        report=observer.finish({'status':'fixture'},timeout=0)
        self.assertEqual(report['dropped_events'],2); self.assertEqual(report['state'],'failed')
        gate=threading.Event()
        class Blocked(MemorySink):
            def send(self,event): gate.wait(3)
        try:
            observer=Observer(RUN,Config(True),Blocked(),dispatch=Dispatcher(capacity=1))
            span=observer.start('one','fixture','chain'); observer.end(span)
            start=time.monotonic(); report=observer.finish({'status':'fixture'},timeout=0.02)
            self.assertLess(time.monotonic()-start,0.25)
            self.assertIn(report['state'],{'pending','partial','failed'})
        finally: gate.set()

    def test_off_on_parity_and_A_no_database_even_fingerprints(self):
        from spec015_cases import execute
        for scenario in ('fixed_evidence','data_access'):
            result,_,_=self.run_case(scenario)
            baseline=execute(scenarios,scenario,'groq_chat','success')['result']
            self.assertEqual(json.loads(json.dumps(normalize(result))),json.loads(json.dumps(normalize(baseline))))
        with patch('psycopg2.connect',side_effect=AssertionError('database')), \
             patch('inference_api.agent_harness.local_queries.source_fingerprints',side_effect=AssertionError('fingerprint')):
            result,_,_=self.run_case()
            self.assertEqual(result['queries'],0)

if __name__=='__main__': unittest.main()
