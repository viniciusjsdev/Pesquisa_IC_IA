"""Explicit hosted synthetic-panel check. Never calls a real model or research DB.

Requires --send-synthetic and backend LangSmith settings. Not a routine test gate.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'inference_api/src'),str(ROOT/'inference_api/tests')]
from dotenv import load_dotenv
from inference_api.agent_harness import scenarios
from inference_api.model_service import ModelService
from inference_api.observability.config import load
from inference_api.observability.service import create as create_observer
from spec014_fixture import profile,packet,Transport,QUESTION,MAPS,fixture_query

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--send-synthetic',action='store_true',required=True)
    args=parser.parse_args()
    target=ROOT/'specs/active/SPEC-015/evidence/hosted-synthetic-check.json'
    if target.exists(): raise SystemExit('Receipt already exists; inspect prior runs before another send.')
    load_dotenv(ROOT/'inference_api/.local/observability.env',override=False)
    # The required CLI opt-in enables this synthetic process only. Backend stays off.
    os.environ['INFERENCE_OBSERVABILITY']='langsmith'
    os.environ['INFERENCE_OBSERVABILITY_CONTENT']='redacted'
    config=load()
    if not config.enabled: raise SystemExit('Configure backend LangSmith settings locally; no data sent.')
    results=[]
    observers=[]
    def observe(run_id):
        observer=create_observer(run_id)
        observers.append(observer)
        return observer
    with patch('psycopg2.connect',side_effect=AssertionError('Hosted synthetic check cannot read databases')), \
         patch('inference_api.agent_harness.graph.execution.create',side_effect=observe):
        for scenario in ('fixed_evidence','data_access'):
            fixed=scenario=='fixed_evidence';p=profile()
            result=scenarios.run(QUESTION,scenario,p['id'],ModelService(p,{},transport=Transport()),
                packet=packet() if fixed else None,maps=None if fixed else MAPS,
                query=None if fixed else fixture_query,
                limits=scenarios.ScenarioLimits(query_attempts=0 if fixed else 3))
            results.append({'run_id':result['run_id'],'scenario':scenario,'status':result['status'],
                'model_calls':result['model_calls'],'queries':result['queries'],'observability':result['observability']})
    # Keep this diagnostic process alive for bounded asynchronous delivery. This is
    # not a retry or a second run flush: every event is still submitted only once,
    # and the ordinary run's maximum 2-second flush is unchanged.
    deadline=time.monotonic()+20
    for observer in observers:
        if hasattr(observer,'condition'):
            with observer.condition:
                while observer.pending and time.monotonic()<deadline:
                    observer.condition.wait(max(0,deadline-time.monotonic()))
    for result,observer in zip(results,observers):
        result['observability']=observer.snapshot()
    evidence={'date':'2026-11-08','synthetic_only':True,'external_inference':False,
        'research_database_access':False,'content_mode':config.content,'runs':results,
        'visual_panel_verified':False}
    target.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence,ensure_ascii=False,indent=2))
    return 0 if all(r['observability']['state']=='submitted' for r in results) else 1

if __name__=='__main__':raise SystemExit(main())
