"""New A/B contract: exact fake transport, policy boundaries and migration gates."""
from copy import deepcopy
from dataclasses import replace, asdict
import hashlib
import json
import unittest
from unittest.mock import patch, Mock
from urllib.error import HTTPError
from inference_api.agent_harness import scenarios
from inference_api.model_service import ModelService, ModelError
from inference_api.model_service.registry import digest
from inference_api import service
from spec014_fixture import profile, packet, Transport, Stream, QUESTION, MAPS, fixture_query


class ScenariosTests(unittest.TestCase):
    def run_case(self, scenario='fixed_evidence', adapter='groq_chat', transport=None, **kwargs):
        p = profile(adapter)
        self.transport = transport or Transport()
        self.query = kwargs.pop('query', Mock(side_effect=fixture_query))
        fixed = scenario == 'fixed_evidence'
        return scenarios.run(QUESTION, scenario, p['id'], ModelService(p, {}, transport=self.transport),
            packet=kwargs.pop('packet', packet()) if fixed else None,
            maps=None if fixed else MAPS, query=None if fixed else self.query,
            limits=kwargs.pop('limits', scenarios.ScenarioLimits(query_attempts=0 if fixed else 3)), **kwargs)

    def test_matrix_2_scenarios_3_adapters_exact_body_and_identity(self):
        for scenario in ('fixed_evidence', 'data_access'):
            for adapter in ('openai_responses', 'groq_chat', 'chat_completions'):
                with self.subTest(scenario=scenario, adapter=adapter):
                    result = self.run_case(scenario, adapter)
                    self.assertEqual(result['status'], 'answered_unverified', result['final_state'])
                    self.assertEqual(result['queries'], 0 if scenario == 'fixed_evidence' else 3)
                    self.assertEqual({e['role'] for e in result['trace'] if e['role'] not in {'data_query','map_projection'}},
                                     set(scenarios.contracts(scenario)))
                    calls = [e for e in result['trace'] if e.get('model')]
                    for event, req in zip(calls, self.transport.requests):
                        self.assertEqual(event['model']['request_budget']['sha256'], hashlib.sha256(req.data).hexdigest())
                        self.assertEqual(event['model']['request_budget']['bytes'], len(req.data))
                        self.assertEqual(event['input']['question'], QUESTION)
                    self.assertEqual(result['scientific_status'], 'not_scored')
                    if scenario == 'data_access':
                        self.assertEqual({e['source_id'] for e in result['evidence']}, {'dw_paradas','ind_parada','fin_resultado'})
                        self.assertEqual(len(self.transport.envelopes[-1]['input']['evidence_state']), 3)

    def test_fixed_never_opens_research_even_fingerprint(self):
        with patch('inference_api.agent_harness.local_queries.source_fingerprints', side_effect=AssertionError), \
             patch('inference_api.agent_harness.local_queries.execute', side_effect=AssertionError), \
             patch('psycopg2.connect', side_effect=AssertionError):
            result = self.run_case()
        self.assertEqual(result['status'], 'answered_unverified')

    def test_forbidden_action_source_and_changed_packet(self):
        for attack in ('action', 'source'):
            def mutate(e, v):
                if attack == 'action' and e['role'] == 'especialista_consulta': v['action'] = 'query_source'
                if attack == 'source' and e['role'] == 'selecionador_fontes': v['fonte_id'] = 'external'
                return v
            result = self.run_case(transport=Transport(mutate))
            self.assertEqual(result['status'], 'contract_error')
            self.assertEqual(result['queries'], 0)
            self.assertEqual(len([e for e in result['trace'] if e['status']=='rejected']), 1)
        changed = packet(); changed['body']['question'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'packet_hash_mismatch'): self.run_case(packet=changed)

    def test_forbidden_source_precedes_schema_repair_in_selector_and_specialist(self):
        for scenario, role, field in [('fixed_evidence','selecionador_fontes','fonte_id'),
                                       ('data_access','selecionador_fontes','map_refs'),
                                       ('data_access','especialista_consulta','plano'),
                                       ('data_access','especialista_consulta','other_approved')]:
            with self.subTest(scenario=scenario, role=role, field=field):
                def attack(e, value):
                    if e['role'] == role:
                        del value['justificativa']
                        if field in {'plano','other_approved'}:
                            value['plano']['fonte_id'] = 'ind_parada' if field == 'other_approved' else 'external'
                        elif field == 'map_refs': value['map_refs'] = ['external']
                        else: value['fonte_id'] = 'external'
                    return value
                result = self.run_case(scenario, transport=Transport(attack))
                self.assertEqual(result['final_state']['error'], 'source_forbidden')
                self.assertEqual(sum(e['role'] == role for e in self.transport.envelopes), 1)
                self.assertEqual(result['query_attempts'], 0)
                self.query.assert_not_called()

    def test_allowed_source_with_malformed_output_remains_repairable(self):
        first = True
        def malformed(e, value):
            nonlocal first
            if e['role'] == 'selecionador_fontes' and first:
                del value['justificativa']
                first = False
            return value
        result = self.run_case(transport=Transport(malformed))
        self.assertEqual(result['status'], 'answered_unverified')
        self.assertEqual(sum(e['role'] == 'selecionador_fontes' for e in self.transport.envelopes), 2)

    def test_prepare_with_approved_catalog_and_compiled_maps(self):
        from inference_api.agent_harness import approved_catalog, catalog_runtime
        catalog = approved_catalog.load()
        self.assertIs(type(catalog['version']), int)
        body = {'execution_contract_version':1, 'scenario':'data_access',
                'model_profile_id':'fixture', 'question':QUESTION, 'evidence_packet':None,
                'catalog_version':catalog['version'], 'generation':{}}
        with patch('inference_api.model_service.registry.resolve', return_value=profile()), \
             patch('inference_api.model_service.registry.authorize', return_value='fixture-approval') as auth, \
             patch('inference_api.executions.service.approved_catalog.load', wraps=approved_catalog.load) as load, \
             patch('inference_api.executions.service.catalog_runtime.compile_maps', wraps=catalog_runtime.compile_maps) as compile_maps, \
             patch('psycopg2.connect', side_effect=AssertionError('unexpected database access')):
            prepared=service.prepare(body)
            self.assertEqual(sum(len(m['sources']) for m in prepared['maps'].values()),12)
            self.assertEqual(prepared['source']['version'],catalog['version'])
            load.assert_called_once(); compile_maps.assert_called_once(); auth.assert_called_once()
            for invalid in [True, False, '1', 1.0, 0, None]:
                with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError,'data_access_catalog_required'):
                    service._validate_input({**body,'catalog_version':invalid})
            with self.assertRaisesRegex(ValueError,'catalog_version_mismatch'):
                service.prepare({**body,'catalog_version':catalog['version']+1})

    def test_incomplete_packet_and_no_progress(self):
        p = packet(); p['body']['evidence_items'][0].update(rows=[], coverage={'rows':0,'state':'no_observation'}); p['sha256']=digest(p['body'])
        self.assertEqual(self.run_case(packet=p)['status'], 'insufficient_evidence')
        def again(e, v):
            if e['role']=='revisor_evidencias': v.update(decisao='precisa_aprofundar', lacuna='gap', proximo_dado_necessario='data', dominio_sugerido='industrial')
            return v
        r = self.run_case(transport=Transport(again))
        self.assertEqual(r['final_state']['reason'], 'no_progress')
        self.assertEqual(r['queries'], 0)

    def test_plan_refusal_counts_and_returns_to_same_specialist(self):
        query = Mock(side_effect=[ValueError('filters_outside_catalog'), fixture_query({'fonte_id':'dw_paradas','campos':MAPS['dw']['sources']['dw_paradas']['fields'],'filtros':{},'limite':20,'grao':'linha/ano'}), ValueError('source_not_enabled')])
        r = self.run_case('data_access', query=query)
        self.assertEqual(r['query_attempts'], 3)
        special = [e for e in self.transport.envelopes if e['role']=='especialista_consulta']
        feedback = special[1]['input']['feedback']
        self.assertEqual(feedback['rejected_plan']['fonte_id'], special[1]['input']['source_contract']['id'])
        self.assertEqual(feedback['remaining_budget']['remaining_queries'], 2)
        self.assertEqual(r['final_state']['error'], 'query_blocked:source_not_enabled')

    def test_json_repair_same_role_and_reference_validation(self):
        seen = []
        def bad(e,v):
            seen.append(e['role'])
            return 'not-json' if len(seen)==1 else v
        result = self.run_case(transport=Transport(bad))
        self.assertEqual(result['status'], 'answered_unverified')
        self.assertEqual(seen[:2], ['analista_pergunta']*2)
        def invented(e,v):
            if e['role']=='redator_resposta': v['evidencias_utilizadas']=['invented']
            return v
        self.assertEqual(self.run_case(transport=Transport(invented))['status'], 'contract_error')

    def test_nested_schema_error_feedback_reaches_same_role_with_path_and_budget(self):
        first = True
        def malformed(e, value):
            nonlocal first
            if e['role'] == 'analista_pergunta' and first:
                first = False
                value['necessidade']['medida'] = 42
            return value
        transport = Transport(malformed)
        result = self.run_case(transport=transport)
        self.assertEqual(result['status'], 'answered_unverified')
        initial, repair = transport.envelopes[:2]
        self.assertEqual(initial['role'], repair['role'])
        feedback = repair['input']['feedback']
        self.assertEqual(feedback['schema_id'], 'analista_pergunta.fixed_evidence.v2')
        self.assertEqual(feedback['schema_version'], 2)
        self.assertEqual(feedback['schema_sha256'], digest(scenarios.contracts('fixed_evidence')['analista_pergunta']['schema']))
        self.assertEqual(feedback['path'], '/necessidade/medida')
        self.assertEqual(feedback['keyword'], 'type')
        self.assertEqual(feedback['attempt'], 1)
        self.assertEqual(feedback['remaining_budget']['remaining_model_calls'], 47)
        self.assertEqual(feedback['event_id'], result['trace'][0]['event_id'])

    def test_errors_terminal_receipts_missing_usage_and_cancellation(self):
        for error in (TimeoutError(), HTTPError('http://127.0.0.1',429,'limited',{},None)):
            t = Transport(fail=error); r = self.run_case(transport=t)
            self.assertEqual(len(t.requests), 1)
            self.assertTrue(r['trace'][0]['model']['request_dispatched'])
        t=Transport(finish='length'); self.assertEqual(self.run_case(transport=t)['final_state']['error'], 'output_truncated'); self.assertEqual(len(t.requests),1)
        r=self.run_case(transport=Transport(usage=False)); self.assertIsNone(r['trace'][0]['model']['usage']['input'])
        r=self.run_case(limits=scenarios.ScenarioLimits(query_attempts=0,input_bytes=10)); self.assertEqual(r['final_state']['error'],'input_context_limit'); self.assertFalse(self.transport.requests)
        p=profile(); t=Transport(); m=ModelService(p,{},transport=t,cancelled=lambda:True)
        with self.assertRaises(ModelError) as exc: m('role',{'call_id':'one'}, {})
        self.assertFalse(exc.exception.metadata['request_dispatched']); self.assertFalse(t.requests)

    def test_preflight_rejects_parameters_before_http_and_legacy_creation(self):
        t=Transport()
        with self.assertRaisesRegex(ValueError, 'unsupported_parameter'): ModelService(profile(),{'seed':1},transport=t)
        self.assertFalse(t.requests)
        for mode in ['dw_snapshot','dw_tools','agent_harness_pilot','synthetic_tools','agent_harness']:
            with self.assertRaisesRegex(ValueError,'legacy_execution_mode_retired'): service._validate_input({'evidence_mode':mode})
        payload={'execution_contract_version':1,'scenario':'fixed_evidence','model_profile_id':'fixture','question':QUESTION}
        with patch('inference_api.model_service.registry.resolve',return_value=profile()):
            with self.assertRaisesRegex(ValueError,'packet_required'): service._validate_input(payload)
            payload.update(evidence_packet={'id':'fixture','sha256':'a'*64}, limits={'query_attempts':1})
            with self.assertRaisesRegex(ValueError,'limit_may_only_reduce'): service._validate_input(payload)

    def test_provider_refusal_and_interrupted_stream_are_terminal_with_receipt(self):
        for adapter in ('openai_responses', 'groq_chat', 'chat_completions'):
            for kind in ('refusal', 'disconnect'):
                with self.subTest(adapter=adapter, kind=kind):
                    sent = []
                    def fake(request, timeout):
                        sent.append(request.data)
                        if adapter == 'openai_responses':
                            result = {'id': 'fixture-id', 'model': 'fixture-model', 'status': 'completed',
                                'usage': {'input_tokens': 11, 'output_tokens': 4},
                                'output': [{'type': 'message', 'content': [{'type': 'refusal', 'refusal': 'no'}]}]}
                            lines = [b'data: ' + json.dumps({'type': 'response.completed', 'response': result}).encode()+b'\n'] if kind == 'refusal' else []
                        else:
                            chunk = {'model':'fixture-model','choices':[{'index':0,'delta':{'refusal':'no'},'finish_reason':'stop'}],
                                     'usage': {'prompt_tokens':11,'completion_tokens':4}}
                            lines = [b'data: '+json.dumps(chunk).encode()+b'\n',b'data: [DONE]\n'] if kind == 'refusal' else []
                        return Stream(lines)
                    p = profile(adapter)
                    result = scenarios.run(QUESTION, 'fixed_evidence', p['id'], ModelService(p, {}, transport=fake),
                        packet=packet(), limits=scenarios.ScenarioLimits(query_attempts=0))
                    event = result['trace'][0]
                    self.assertEqual(len(sent), 1)
                    self.assertEqual(event['error'], 'provider_refusal' if kind == 'refusal' else 'stream_incomplete')
                    self.assertEqual(event['model']['request_budget']['sha256'], hashlib.sha256(sent[0]).hexdigest())
                    if kind == 'refusal':
                        self.assertEqual(event['model']['usage']['input'], 11)
                        self.assertEqual(event['model']['usage']['output'], 4)
                        self.assertTrue(event['model']['finish_reason'])
                        self.assertEqual(event['model']['request_id'], 'fixture-request')

    def test_openai_wrong_model_preserves_actual_identity_and_usage(self):
        result = {'id':'response-known','model':'different-model','status':'completed',
            'usage':{'input_tokens':11,'output_tokens':4},
            'output':[{'type':'message','content':[{'type':'output_text','text':'{}'}]}]}
        lines = [b'data: '+json.dumps({'type':'response.completed','response':result}).encode()+b'\n']
        p = profile('openai_responses'); transport = Mock(return_value=Stream(lines))
        run = scenarios.run(QUESTION, 'fixed_evidence', p['id'], ModelService(p, {}, transport=transport),
                            packet=packet(), limits=scenarios.ScenarioLimits(query_attempts=0))
        receipt = run['trace'][0]['model']
        self.assertEqual(run['trace'][0]['error'], 'provider_model_mismatch')
        self.assertEqual(receipt['model_id'], 'fixture-model')
        self.assertEqual(receipt['served_model'], 'different-model')
        self.assertEqual(receipt['usage']['input'], 11)
        self.assertEqual(receipt['response_id'], 'response-known')
        self.assertEqual(receipt['request_id'], 'fixture-request')
        self.assertEqual(transport.call_count, 1)

    def test_chat_partial_stream_keeps_known_fields_without_retry(self):
        for adapter in ('groq_chat', 'chat_completions'):
            for mismatch in (False, True):
                with self.subTest(adapter=adapter, mismatch=mismatch):
                    chunk={'id':'known-id','model':'different-model' if mismatch else 'fixture-model',
                           'usage':{'prompt_tokens':11,'completion_tokens':4},
                           'choices':[{'index':0,'delta':{'content':'{}'},'finish_reason':'stop'}]}
                    lines=[b'data: '+json.dumps(chunk).encode()+b'\n']
                    p=profile(adapter); transport=Mock(return_value=Stream(lines))
                    result=scenarios.run(QUESTION,'fixed_evidence',p['id'],ModelService(p,{},transport=transport),
                        packet=packet(),limits=scenarios.ScenarioLimits(query_attempts=0))
                    event=result['trace'][0]; receipt=event['model']
                    self.assertEqual(event['error'],'provider_model_mismatch' if mismatch else 'stream_incomplete')
                    self.assertEqual(receipt['served_model'],chunk['model'])
                    self.assertEqual(receipt['response_id'],'known-id')
                    self.assertEqual(receipt['usage']['input'],11)
                    self.assertEqual(receipt['finish_reason'],'stop')
                    self.assertFalse(receipt['usage_complete'])
                    self.assertEqual(transport.call_count,1)

    def test_fingerprint_failure_after_run_preserves_trace_in_snapshot(self):
        from inference_api.identity.auth import Principal
        p=profile(); payload={'scenario':'data_access','question':QUESTION,'generation':{}}
        context={'profile':p,'request_sha256':digest(payload),'source':{},'catalog':{},
                 'maps':MAPS,'packet':None,'limits':asdict(scenarios.ScenarioLimits()),
                 'authorization_sha256':'fixture'}
        simulated={'run_id':'fixture-run','status':'answered_unverified','contract_sha256':'contract',
                   'trace':[{'event_id':'call_01','model':{'request_dispatched':True}}],
                   'response':{'resposta':'fixture'},'final_state':None}
        with patch('inference_api.executions.service.local_queries.source_fingerprints',side_effect=[{'status':'recorded'}, OSError('failed')]), \
             patch('inference_api.executions.service.scenarios.run',return_value=simulated), \
             patch('inference_api.executions.service.storage.create_run',side_effect=lambda _author,snapshot:{'id':'00000000-0000-4000-8000-000000000003','snapshot':snapshot}):
            snapshot=service.execute_run(payload,Principal('fixture','Vinicius'),prepared=context)['snapshot']
        self.assertEqual(snapshot['status'],'contract_error')
        self.assertEqual(snapshot['harness_result']['trace'][0]['event_id'],'call_01')
        self.assertEqual(snapshot['evidence_source']['detail_loads']['after']['status'],'unavailable')
        self.assertEqual(snapshot['error']['message'],'source_fingerprint_after_failed')


if __name__ == '__main__': unittest.main()
