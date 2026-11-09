"""Bounded read-only SDK reconciliation: invented identities, no sockets."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from contextlib import nullcontext
from copy import deepcopy
from datetime import datetime, timezone
import json
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch, Mock
from uuid import uuid4
import requests
from inference_api.observability import reconciliation as r, receipts, config
READ_CONFIG=config.for_read

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.rid,self.pid,self.tid,self.child=[str(uuid4()) for _ in range(4)]
        self.cfg=config.Config(True,'metadata',project='fixture',api_key='invented')
        self.did,self.desc=config.destination(self.cfg)
        self.record=dict(harness_run_id=str(uuid4()),run_id=self.rid,principal_id=self.pid,
            trace_id=self.tid,destination_id=self.did,descriptor=self.desc,sealed=True,
            expected_event_ids=[{'id':self.tid,'parent_run_id':None},{'id':self.child,'parent_run_id':self.tid}],
            state='submitted',remote_verified=False,submitted_events=2,failed_events=0,dropped_events=0,
            pending_events=0,url=None,trusted_origin=None,last_check_error=None,last_checked_at=None,
            observed_remote_events=None,revision=1)
        self.url=f'https://smith.langchain.com/o/invented/projects/p/invented/r/{self.tid}'
        self.root=NS(id=self.tid,trace_id=self.tid,parent_run_id=None,url=self.url)
        self.spans=[NS(id=e['id'],parent_run_id=e['parent_run_id'],trace_id=self.tid) for e in self.record['expected_event_ids']]
        self.owner=NS(id=self.pid)
        self.storage=NS(get_run=Mock(return_value={'snapshot':{'identity':{'principal_id':self.pid}}}))
        def checked(_,**kw):
            rec=self.record
            if not rec['remote_verified'] or kw.get('verified'):
                if kw.get('state'):rec['state']=kw['state']
                if kw.get('observed') is not None:rec['observed_remote_events']=kw['observed']
            rec['remote_verified'] |= kw.get('verified',False)
            for key,source in [('url','url'),('trusted_origin','origin')]:
                if kw.get(source):rec[key]=kw[source]
            rec.update(last_check_error=kw.get('error'),last_checked_at=datetime.now(timezone.utc),revision=rec['revision']+1)
        for target,value in [('get',lambda _:deepcopy(self.record)),('claim',lambda _:nullcontext()),
                             ('checked',checked),('current',lambda _,p:receipts.public(self.record,p))]:
            p=patch.object(receipts,target,side_effect=value);p.start();self.addCleanup(p.stop)
        p=patch.object(config,'for_read',return_value=self.cfg);self.destination=p.start();self.addCleanup(p.stop)
        self.reader=Mock(side_effect=lambda *_:(self.root,self.spans))
    def run_check(self):return r.reconcile(self.rid,self.owner,storage=self.storage,reader=self.reader)
    def test_complete_tree_public_dto_and_failed_later_read_preserves_verified_url(self):
        result=self.run_check();self.assertTrue(result['remote_verified']);self.assertEqual(result['url'],self.url)
        self.assertEqual(set(result),{'schema_version','state','remote_verified','can_reconcile','trace_id',
            'submitted_events','failed_events','dropped_events','pending_events','expected_events','observed_remote_events',
            'url','trusted_origin','last_checked_at','last_check_error','revision'})
        self.reader.side_effect=r.ReadFailure('remote_timeout')
        later=self.run_check();self.assertTrue(later['remote_verified']);self.assertEqual(later['url'],self.url)
        self.assertEqual(later['last_check_error'],'remote_timeout');self.assertGreater(later['revision'],result['revision'])
    def test_receipt_read_or_write_failure_returns_last_authorized_dto_not_null(self):
        self.run_check()
        for failure in ('read','write'):
            with self.subTest(failure=failure):
                with patch.object(receipts,'current',return_value=None) if failure=='read' else patch.object(receipts,'checked',side_effect=OSError('private')):
                    result=self.run_check()
                self.assertIsNotNone(result);self.assertEqual(result['url'],self.url)
                self.assertTrue(result['remote_verified'])
                self.assertEqual(result['last_check_error'],'receipt_storage_unavailable')
    def test_partial_same_count_wrong_ids_parents_trace_duplicate_and_limit(self):
        for mutation in ('missing','id','parent','trace','duplicate','limit'):
            with self.subTest(mutation=mutation):
                spans=deepcopy(self.spans)
                if mutation=='missing':spans.pop()
                elif mutation=='id':spans[1].id=str(uuid4())
                elif mutation=='parent':spans[1].parent_run_id=None
                elif mutation=='trace':spans[1].trace_id=str(uuid4())
                elif mutation=='duplicate':spans[1]=spans[0]
                else:spans=spans*65
                self.reader.side_effect=None;self.reader.return_value=(self.root,spans)
                result=self.run_check();self.assertFalse(result['remote_verified'])
                self.assertEqual(result['last_check_error'],'remote_span_limit' if mutation=='limit' else 'remote_tree_incomplete')
    def test_exact_128_complete_spans_can_be_verified(self):
        self.spans.extend(NS(id=str(uuid4()),parent_run_id=self.tid,trace_id=self.tid) for _ in range(126))
        self.record['expected_event_ids']=[{'id':s.id,'parent_run_id':s.parent_run_id} for s in self.spans]
        result=self.run_check();self.assertTrue(result['remote_verified']);self.assertEqual(result['observed_remote_events'],128)
    def test_root_not_indexed_destination_unavailable_invalid_url_no_remote_writes(self):
        self.reader.side_effect=r.ReadFailure('root_not_indexed')
        self.assertEqual(self.run_check()['state'],'pending')
        self.destination.return_value=None;self.reader.reset_mock()
        self.assertEqual(self.run_check()['last_check_error'],'destination_unavailable');self.reader.assert_not_called()
        self.destination.return_value=self.cfg;self.reader.side_effect=None;self.reader.return_value=(self.root,self.spans)
        for url in ('https://evil.test/',self.url.replace(self.tid,str(uuid4())),self.url.replace('https://','https://u:p@')):
            self.root.url=url
            self.assertEqual(self.run_check()['last_check_error'],'invalid_remote_url')
    def test_authorization_existence_uuid_and_lock_precede_remote_reads(self):
        with self.assertRaises(ValueError):r.reconcile('bad',self.owner,storage=self.storage,reader=self.reader)
        self.storage.get_run.return_value=None
        with self.assertRaises(r.NotFound):self.run_check()
        self.storage.get_run.return_value={'snapshot':{'identity':{'principal_id':'another'}}}
        with self.assertRaises(r.Forbidden):self.run_check()
        self.storage.get_run.return_value={'snapshot':{'identity':{'principal_id':self.pid}}}
        self.record['principal_id']='another'
        with self.assertRaises(r.Forbidden):self.run_check()
        self.record['principal_id']=self.pid
        with patch.object(receipts,'claim',side_effect=receipts.ReconciliationBusy('reconciliation_in_progress')):
            with self.assertRaises(receipts.ReconciliationBusy):self.run_check()
        self.reader.assert_not_called()
    def test_collection_off_can_read_only_original_trusted_destination(self):
        env={'INFERENCE_OBSERVABILITY':'off','INFERENCE_OBSERVABILITY_PROJECT':'fixture','LANGSMITH_API_KEY':'invented'}
        # Restore actual function; the instance mock is only used by run_check.
        with patch.dict('os.environ',env,clear=True):
            self.assertFalse(config.load().enabled)
            self.assertTrue(READ_CONFIG(self.did,self.desc).enabled)
            self.assertIsNone(READ_CONFIG(self.did,{**self.desc,'project':'changed'}))
        self.assertNotEqual(config.destination(config.Config(True,project='changed'))[0],self.did)

class SDKReadTests(unittest.TestCase):
    def test_slow_headers_and_oversize_body_cannot_exceed_read_budget(self):
        endpoint='https://api.smith.langchain.com';tid=str(uuid4())
        def slow(*_,**__):
            time.sleep(.2)
            response=requests.Response();response.status_code=200;response._content=b'{}';response._content_consumed=True
            return response
        session=r.ReadSession(endpoint,tid,transport=slow);session.deadline=time.monotonic()+.03
        start=time.monotonic()
        with self.assertRaisesRegex(r.ReadFailure,'remote_timeout'):session.request('GET',endpoint+'/runs/'+tid)
        self.assertLess(time.monotonic()-start,.15)
        def huge(*_,**__):
            response=requests.Response();response.status_code=200;response._content=b'x'*(1024*1024+1);response._content_consumed=True
            return response
        with self.assertRaisesRegex(r.ReadFailure,'remote_response_limit'):
            r.ReadSession(endpoint,tid,transport=huge).request('GET',endpoint+'/runs/'+tid)
    def test_actual_sdk_serialization_only_root_and_bounded_trace_query(self):
        tid=str(uuid4());sid=str(uuid4());calls=[]
        def transport(method,url,**kw):
            calls.append((method,url,kw))
            item={'id':tid,'trace_id':tid,'parent_run_id':None,'session_id':sid,'name':'invented',
                'run_type':'chain','start_time':datetime.now(timezone.utc).isoformat(),
                'inputs':{},'app_path':f'/o/invented/projects/p/{sid}/r/{tid}'}
            response=requests.Response();response.status_code=200;response.url=url
            response._content=json.dumps(item if method=='GET' else {'runs':[item]}).encode()
            response._content_consumed=True
            return response
        session=r.ReadSession('https://api.smith.langchain.com',tid,transport=transport)
        with patch.object(r,'ReadSession',return_value=session):
            root,spans=r.read_tree(config.Config(True,project='invented',api_key='invented'),tid)
        self.assertEqual(str(root.id),tid);self.assertEqual(len(spans),1)
        self.assertLessEqual(len(calls),3)
        self.assertEqual([(m,u.rsplit('/',1)[-1]) for m,u,_ in calls],[('GET',tid),('POST','query')])
        payload=calls[-1][2].get('data') or calls[-1][2].get('json')
        if isinstance(payload,(bytes,str)):payload=json.loads(payload)
        self.assertEqual(payload['trace'],tid)
        self.assertEqual(payload['limit'],100)
    def test_hosted_page_limit_100_and_cursor_keep_three_reads_128_spans(self):
        for total in (127,128,129):
            with self.subTest(total=total):
                tid=str(uuid4());sid=str(uuid4());calls=[]
                base={'trace_id':tid,'parent_run_id':tid,'session_id':sid,'name':'invented',
                      'run_type':'chain','start_time':datetime.now(timezone.utc).isoformat(),'inputs':{}}
                root={**base,'id':tid,'parent_run_id':None}
                def transport(method,url,**kw):
                    response=requests.Response();response.status_code=200;response.url=url
                    if method=='GET':value=root
                    else:
                        body=json.loads(kw['data']);calls.append(body)
                        if body['limit']>100:
                            response.status_code=400;value={'detail':'Limit exceeds maximum allowed value of100'}
                        elif 'cursor' not in body:
                            value={'runs':[root]+[{**base,'id':str(uuid4())} for _ in range(99)],'cursors':{'next':'page2'}}
                        else:
                            value={'runs':[{**base,'id':str(uuid4())} for _ in range(min(28,total-100))],
                                   'cursors':{'next':'page3'} if total>128 else {}}
                    response._content=json.dumps(value).encode();response._content_consumed=True;return response
                session=r.ReadSession('https://api.smith.langchain.com',tid,transport=transport)
                with patch.object(r,'ReadSession',return_value=session):
                    if total>128:
                        with self.assertRaisesRegex(r.ReadFailure,'remote_read_limit'):
                            r.read_tree(config.Config(True,project='invented',api_key='invented'),tid)
                    else:
                        _,spans=r.read_tree(config.Config(True,project='invented',api_key='invented'),tid)
                        self.assertEqual(len(spans),total)
                self.assertEqual([c['limit'] for c in calls],[100,28]);self.assertEqual(session.count,3)
    def test_physical_request_deadline_redirect_size_and_operation_limits(self):
        tid=str(uuid4());endpoint='https://api.smith.langchain.com'
        def response(*_,**__):
            value=requests.Response();value.status_code=200;value._content=b'{}';value._content_consumed=True;return value
        session=r.ReadSession(endpoint,tid,transport=response)
        for _ in range(3):session.request('GET',endpoint+'/runs/'+tid)
        with self.assertRaises(r.ReadFailure):session.request('GET',endpoint+'/runs/'+tid)
        for method,url in [('DELETE',endpoint+'/runs/'+tid),('GET','https://evil.test/runs/'+tid),('POST',endpoint+'/runs')]:
            with self.assertRaises(r.ReadFailure):r.ReadSession(endpoint,tid,transport=response).request(method,url)
        clock=Mock(side_effect=[0,11])
        with self.assertRaises(r.ReadFailure):r.ReadSession(endpoint,tid,transport=response,clock=clock).request('GET',endpoint+'/runs/'+tid)

if __name__=='__main__':unittest.main()
