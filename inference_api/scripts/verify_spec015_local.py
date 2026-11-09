"""SPEC-015 browser/API/jobs on a NEW disposable PostgreSQL cluster and fake HTTP.

No research cluster or external inference endpoint is accessed. All patches are
test-process dependencies; production has no fixture flag or auth bypass.
"""
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
from unittest.mock import patch
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'inference_api/src'), str(ROOT/'inference_api/tests'), str(ROOT)]
import psycopg2
from psycopg2.extras import Json
from inference_api import auth, storage, limits, server, service, evidence_packets
from inference_api.agent_harness import scenarios
from inference_api.model_service import registry
from inference_api.agent_harness.graph import execution
from inference_api.observability.config import Config
from inference_api.observability.service import Observer
from test_spec015_observability import MemorySink
from spec014_fixture import profile, Transport, MAPS, fixture_query, QUESTION
from model_evaluation.export import build_packets
from model_evaluation.tests.test_export import fixture_case, fixture_report, fixture_query as packet_query


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def main():
    work = ROOT/'inference_api/.local'/('spec015-integration-'+str(uuid4())[:8])
    work.mkdir(parents=True)
    pg = Path('C:/Program Files/PostgreSQL/15/bin')
    port = free_port()
    flags = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    def pg_run(*args):
        proc = subprocess.run([str(pg/args[0]), *args[1:]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True, **flags)
        if proc.returncode: raise RuntimeError('PostgreSQL command failed: ' + args[0])
    pg_run('initdb.exe', '-D', str(work/'pgdata'), '-U', 'fixture_owner', '-A', 'trust', '--encoding=UTF8', '--locale=C')
    pg_run('pg_ctl.exe', '-D', str(work/'pgdata'), '-l', str(work/'postgres.log'),
           '-o', f'-h 127.0.0.1 -p {port}', '-w', 'start')
    report = {'kind': 'local_synthetic_fixture', 'external_inference': False,
              'research_cluster_access': False, 'database': {'host':'127.0.0.1','port':port,
              'cluster': str(work/'pgdata'), 'fixture_version': 'spec014_fixture_v1'}, 'runs': []}
    servers = []
    try:
        db = dict(host='127.0.0.1',port=port,user='fixture_owner',dbname='postgres')
        with psycopg2.connect(**db) as conn, conn.cursor() as cur:
            cur.execute(storage.SCHEMA)
            for migration in ('001_identity_up.sql','002_criteria_up.sql','003_run_jobs_up.sql'):
                cur.execute((ROOT/'inference_api/migrations'/migration).read_text(encoding='utf-8'))
            cur.execute('CREATE TABLE fixture_sources (source_id text PRIMARY KEY, result jsonb NOT NULL)')
            for domain in MAPS.values():
                for sid, src in domain['sources'].items():
                    result=fixture_query(dict(fonte_id=sid,campos=src['fields'],filtros={},limite=20,grao=src['grain']))
                    result['origin']={'fixture':True,'database':'disposable_postgresql','source_id':sid}
                    cur.execute('INSERT INTO fixture_sources VALUES (%s,%s)',(sid,Json(result)))
        code = work/'fixture_query.py'; code.write_text('fixture only',encoding='utf-8')
        packets=build_packets([fixture_case()],verify_fn=fixture_report,query_fn=packet_query,query_code_path=code)
        packet_dir=work/'packets'; packet_dir.mkdir()
        for key,value in packets.items(): (packet_dir/(key+'.json')).write_bytes(value)
        query_calls=[]
        def query(plan,catalog):
            # Same typed fixture grammar as unit tests; actual rows read in a read-only SQL transaction.
            fixture_query(plan)
            query_calls.append(plan['fonte_id'])
            with psycopg2.connect(**db) as conn, conn.cursor() as cur:
                cur.execute('SET TRANSACTION READ ONLY')
                cur.execute('SELECT result FROM fixture_sources WHERE source_id=%s',(plan['fonte_id'],))
                return cur.fetchone()[0]
        class FakeHandler(BaseHTTPRequestHandler):
            def log_message(self,*_): pass
            def do_POST(self):
                raw=self.rfile.read(int(self.headers['Content-Length']))
                body=json.loads(raw)
                envelope=json.loads((body.get('input') or body['messages'])[-1]['content'])
                if 'erro fixture' in envelope['question']:
                    self.send_response(429); self.end_headers(); return
                stream=Transport()(Request('http://127.0.0.1/fake',data=raw),600)
                self.send_response(200); self.send_header('Content-Type','text/event-stream'); self.end_headers()
                for line in stream: self.wfile.write(line)
        fake=ThreadingHTTPServer(('127.0.0.1',0),FakeHandler); servers.append(fake)
        threading.Thread(target=fake.serve_forever,daemon=True).start()
        ps={}
        for adapter in ('openai_responses','groq_chat','chat_completions'):
            p=profile(adapter); p['endpoint']=f'http://127.0.0.1:{fake.server_port}/fake'; p['sha256']=registry.digest(p)
            p['reason']='Fixture sintética em HTTP local'; ps[p['id']]=p
        catalog={'version':1,'dw_source_fingerprint':'fixture','physical_inventory_sha256':'fixture'}
        fingerprints={'status':'recorded','domains':{d:{'database':'disposable_postgresql', 'sha256':registry.digest(MAPS[d]),
            'files':[{'table':next(iter(MAPS[d]['sources'])),'sha256':registry.digest(MAPS[d]),'period_index':0}]}
            for d in ['industrial','financeiro']}}
        sinks=[]
        def observer(run_id):
            sink=MemorySink(failure=len(sinks)==3)
            sinks.append(sink)
            return Observer(run_id, Config(True,'redacted',project='local-spec015'), sink)
        with ExitStack() as stack:
            stack.enter_context(patch.object(execution,'create',side_effect=observer))
            for module in (auth,storage,limits): stack.enter_context(patch.object(module,'app_db_params',return_value=db))
            stack.enter_context(patch.object(registry,'profiles',return_value=ps))
            # Test-owned authorization explicitly binds a synthetic destination and data.
            stack.enter_context(patch.object(registry,'authorize',side_effect=lambda p,s,d,l:registry.digest(['fixture',p['sha256'],s,d,l])))
            stack.enter_context(patch.object(evidence_packets,'packet_directory',return_value=packet_dir))
            stack.enter_context(patch.object(service.approved_catalog,'load',return_value=catalog))
            stack.enter_context(patch.object(service.catalog_runtime,'compile_maps',return_value=MAPS))
            stack.enter_context(patch.object(service.local_queries,'execute',side_effect=query))
            fingerprint_spy=stack.enter_context(patch.object(service.local_queries,'source_fingerprints',return_value=fingerprints))
            auth.set_password('Vinicius','fixture-local-password')
            legacy={'schema_version':3,'evidence_mode':'dw_snapshot','status':'answered_unverified',
                'question_request':{'question':'Histórico preservado'},'model':{'alias':'historical'},'model_output':{'raw_text':'Resposta histórica'}}
            old=storage.create_run('Vinicius',legacy); old_sha=registry.digest(old)
            api=ThreadingHTTPServer(('127.0.0.1',0),server.Handler); servers.append(api)
            threading.Thread(target=api.serve_forever,daemon=True).start()
            origin=f'http://127.0.0.1:{api.server_port}'
            env={**os.environ,'SPEC015_TEST_ORIGIN':origin,'SPEC015_TEST_OUTPUT':str(work),
                 'SPEC015_LEGACY_ID':old['id']}
            browser=subprocess.run([shutil.which('node'),str(ROOT/'inference_api/tests/browser_spec015.cjs')],
                env=env,capture_output=True,text=True,timeout=150,**flags)
            (work/'browser.log').write_text(browser.stdout+browser.stderr,encoding='utf-8')
            if browser.returncode: raise RuntimeError(browser.stdout+browser.stderr)
            report['browser']=json.loads((work/'browser-report.json').read_text())
            runs=[r for r in storage.list_runs() if r['id']!=old['id']]
            assert registry.digest(storage.get_run(old['id']))==old_sha
            for r in runs:
                assert r['snapshot']['data_class']=='synthetic_fixture'
                assert r['snapshot']['scientific_status']=='not_scored'
                report['runs'].append({'id':r['id'],'scenario':r['snapshot']['scenario'],
                    'adapter':r['snapshot']['model']['api_surface'],'status':r['snapshot']['status'],
                    'observability':r['snapshot'].get('observability'),
                    'queries':r['snapshot']['harness_result']['queries'], 'sha256':registry.digest(r)})
            report.update(query_sources=query_calls, fingerprint_calls=fingerprint_spy.call_count,
                          legacy_hash_unchanged=True)
            states={r['snapshot']['observability']['state'] for r in runs}
            assert 'submitted' in states and 'failed' in states
            assert any(s.events for s in sinks)
            report.update(telemetry_sink='local_memory_only',hosted_panel_validated=False)
            (work/'runs.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2),encoding='utf-8')
        report['status']='passed'
    finally:
        for http in servers: http.shutdown(); http.server_close()
        pg_run('pg_ctl.exe','-D',str(work/'pgdata'),'-m','fast','-w','stop')
        report['database']['stopped']=True
        output=ROOT/'specs/active/SPEC-015/evidence/local-integration.json'
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'work':str(work),'runs':len(report['runs'])}))


if __name__=='__main__': main()
