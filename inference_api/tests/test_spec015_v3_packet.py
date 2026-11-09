import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from copy import deepcopy
import unittest
from unittest.mock import patch
from inference_api.agent_harness import scenarios
from inference_api.agent_harness.context.packet_index import build
from inference_api.model_service import ModelService
from inference_api.model_service.registry import digest
from spec014_fixture import profile,Transport,QUESTION
from spec015_v3_fixture import packet,answer

class PacketTests(unittest.TestCase):
    def run_packet(self,p=None,mutate=None,adapter='groq_chat',limits=None):
        p=p or packet();before=deepcopy(p)
        transport=Transport(lambda e,_:mutate(e,answer(e)) if mutate else answer(e))
        model=profile(adapter)
        with patch('psycopg2.connect',side_effect=AssertionError('research database')), \
             patch('inference_api.agent_harness.catalog_runtime.compile_maps',side_effect=AssertionError('catalog refresh')), \
             patch('inference_api.agent_harness.local_queries.source_fingerprints',side_effect=AssertionError('fingerprint')):
            r=scenarios.run(QUESTION,'fixed_evidence',model['id'],ModelService(model,{},transport=transport),
                packet=p,limits=limits or scenarios.ScenarioLimits(query_attempts=0))
        self.assertEqual(p,before)
        self.assertEqual(r['queries'],0)
        return r,transport

    def test_matrix_and_physical_origin_remain_separate(self):
        for adapter in ('openai_responses','groq_chat','chat_completions'):
            r,t=self.run_packet(adapter=adapter)
            self.assertEqual(r['status'],'answered_unverified',r['final_state'])
            specialists=[e['input'] for e in r['trace'] if e['role']=='especialista_consulta']
            self.assertEqual([e['input']['domain'] for e in specialists],['industrial','financeiro'])
            self.assertTrue(all(e['input']['source_origin']['database']=='db_pesquisa_dw' for e in specialists))
            self.assertEqual(r['scenario_contract_version'],2)
            self.assertEqual(r['packet_projection_version'],2)
            self.assertEqual(r['packet_sha256'],packet()['sha256'])
            self.assertEqual(r['examined_item_ids'],['packet:v3-invented:1','packet:v3-invented:2'])

    def test_budget_at_specialist_does_not_expose_unexamined_item_to_writer(self):
        for calls in (2,3,4):
            r,t=self.run_packet(limits=scenarios.ScenarioLimits(model_calls=calls,query_attempts=0))
            self.assertEqual(r['status'],'insufficient_evidence')
            writer=next(e for e in t.envelopes if e['role']=='redator_resposta')
            self.assertEqual(writer['input']['available_evidence_ids'],r['examined_item_ids'])
            self.assertEqual(r['model_calls'],calls)
            if calls==3:self.assertEqual(writer['input']['evidence_state'],[])

    def test_budget_during_repair_resets_context_before_reserved_writer(self):
        for role,calls in [('selecionador_fontes',3),('especialista_consulta',4),('revisor_evidencias',5)]:
            with self.subTest(role=role):
                r,t=self.run_packet(mutate=lambda e,v:'invalid-json' if e['role']==role else v,
                    limits=scenarios.ScenarioLimits(model_calls=calls,query_attempts=0))
                self.assertEqual(r['status'],'insufficient_evidence')
                self.assertEqual(r['model_calls'],calls)
                writer=t.envelopes[-1]
                self.assertEqual(writer['role'],'redator_resposta')
                self.assertIn('findings',writer['input']);self.assertNotIn('feedback',writer['input'])
                self.assertEqual(writer['input']['available_evidence_ids'],r['examined_item_ids'])

    def test_absent_domain_is_insufficiency_not_review_contract_error(self):
        r,_=self.run_packet(packet(('machine',)))
        self.assertEqual(r['status'],'insufficient_evidence')
        self.assertEqual(r['closure_reason'],'requested_domain_absent_from_packet')
        self.assertIsNotNone(r['response'])
        self.assertEqual(r['model_calls'],5)

    def test_only_absent_need_can_be_declared_unanswerable(self):
        def missing(e,v):
            if e['role']=='analista_pergunta':v.update(tratavel=False,dominios=['financeiro'],lacunas=['Ausente'])
            return v
        r,_=self.run_packet(packet(('machine',)),missing)
        self.assertEqual(r['status'],'insufficient_evidence');self.assertEqual(r['model_calls'],2)

    def test_mixed_items_use_one_consolidated_specialist_each(self):
        for kind in ('product','material'):
            def sufficient(e,v):
                if e['role']=='revisor_evidencias':v.update(decisao='suficiente',lacuna=None,proximo_dado_necessario=None,dominio_sugerido=None)
                return v
            r,_=self.run_packet(packet((kind,)),sufficient)
            calls=[e for e in r['trace'] if e['role']=='especialista_consulta']
            self.assertEqual(len(calls),1);self.assertEqual(calls[0]['input']['input']['domain'],'dw')
            self.assertEqual(calls[0]['input']['input']['semantic_domains'],['industrial','financeiro'])

    def test_periods_keep_distinct_ids_and_global_index_has_no_rows(self):
        p=packet(('machine','machine'))
        index=build(p)
        self.assertNotEqual(index[0]['item_id'],index[1]['item_id'])
        self.assertEqual([x['year'] for x in index],[2020,2021])
        self.assertTrue(all('rows' not in x and 'reported_operation_quantity' not in x for x in index))
        r,t=self.run_packet()
        analyst=t.envelopes[0]['input']
        self.assertNotIn('rows',analyst['source_index'][1])
        specialist=next(e for e in t.envelopes if e['role']=='especialista_consulta')
        self.assertEqual(len(specialist['input']['evidence']),1)
        self.assertEqual(specialist['input']['evidence_state'],[])

    def test_empty_item_is_available_but_not_zero(self):
        p=packet(empty=True);index=build(p)
        self.assertEqual(index[0]['coverage']['state'],'no_observation')
        self.assertTrue(index[0]['fields'])
        r,_=self.run_packet(p)
        self.assertEqual(r['status'],'insufficient_evidence')
        self.assertEqual(r['closure_reason'],'no_observation')
        self.assertEqual(len(r['examined_item_ids']),2)

    def test_no_source_contradiction_and_unknown_reference(self):
        for decision in ('sem_fonte','contraditoria','invented_reference'):
            def mutate(e,v):
                if decision=='sem_fonte' and e['role']=='selecionador_fontes':v.update(decisao='sem_fonte',fonte_id=None,map_refs=[])
                if decision=='contraditoria' and e['role']=='revisor_evidencias':v.update(decisao='contraditoria',lacuna='Contradição inventada')
                if decision=='invented_reference' and e['role']=='redator_resposta':v['evidencias_utilizadas']=['packet:unseen:9']
                return v
            r,_=self.run_packet(mutate=mutate)
            self.assertEqual(r['status'],'contract_error' if decision=='invented_reference' else 'insufficient_evidence')

    def test_budget_reserves_writer_without_changing_limits(self):
        r,_=self.run_packet(limits=scenarios.ScenarioLimits(query_attempts=0,model_calls=4))
        self.assertEqual(r['model_calls'],4);self.assertEqual(r['status'],'insufficient_evidence')
        self.assertEqual(r['closure_reason'],'model_call_budget_exhausted')
        self.assertEqual(r['trace'][-1]['role'],'redator_resposta')

    def test_cycle_and_new_gap_have_distinct_progress(self):
        def repeat(e,v):
            if e['role']=='selecionador_fontes':v.update(fonte_id='packet:v3-invented:1',map_refs=['packet:v3-invented:1'])
            if e['role']=='revisor_evidencias':v.update(decisao='precisa_aprofundar',lacuna='Mesmo recorte',proximo_dado_necessario='Novo recorte',dominio_sugerido='industrial')
            return v
        r,_=self.run_packet(mutate=repeat)
        self.assertEqual(r['closure_reason'],'no_progress')
        def changed(e,v):
            v=repeat(e,v)
            if e['role']=='revisor_evidencias':v['proximo_dado_necessario']=f"Recorte {e['round']}"
            return v
        r,_=self.run_packet(mutate=changed)
        self.assertEqual(r['closure_reason'],'investigation_round_budget_exhausted')

    def test_unknown_query_rejected_before_model_call_and_json_repair(self):
        p=packet(('unknown',));model=profile();transport=Transport()
        with self.assertRaisesRegex(ValueError,'invalid_packet_query'):
            scenarios.run(QUESTION,'fixed_evidence',model['id'],ModelService(model,{},transport=transport),
                          packet=p,limits=scenarios.ScenarioLimits(query_attempts=0))
        self.assertEqual(transport.requests,[])
        first=True
        def bad(e,v):
            nonlocal first
            if first:first=False;return 'bad-json'
            return v
        r,t=self.run_packet(mutate=bad)
        self.assertEqual(r['status'],'answered_unverified')
        self.assertEqual([e['role'] for e in t.envelopes[:2]],['analista_pergunta']*2)

if __name__=='__main__':unittest.main()
