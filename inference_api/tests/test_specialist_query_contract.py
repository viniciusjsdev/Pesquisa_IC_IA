"""Contract 3 regression: model routing, intact schema and actionable recovery."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'inference_api/src'))
sys.path.insert(0, str(ROOT / 'inference_api/scripts'))
from inference_api.agent_harness import run, Limits
from inference_api.agent_harness.catalog_runtime import compile_maps, filter_contract
from inference_api.agent_harness.engine import CONTRACT, INPUT_CONTRACT
from inference_api.agent_harness.synthetic_demo import QUESTION, MAPS, fixture_query
from inference_api import dw_tools
from jsonschema import Draft202012Validator
from test_agent_harness import ScriptedModel, scripted_outputs
from verify_spec013_local_chain import scripted_model, PLANS, QUESTION as PILOT_QUESTION


class SpecialistQueryContractTests(unittest.TestCase):
    def assert_dependency_graph(self, result):
        seen = set()
        for event in result['trace']:
            refs = (event['input'].get('source_event_ids', []) if 'model' in event
                    else event.get('source_event_ids', []))
            self.assertEqual(len(refs), len(set(refs)))
            self.assertTrue(set(refs) <= seen, (event['event_id'], refs))
            seen.add(event['event_id'])
        self.assertEqual(result['dependency_policy'], 'direct_input_events_v1')

    def test_dependencies_cover_received_evidence_and_decisions_without_last_events_window(self):
        model = ScriptedModel(scripted_outputs())
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result['status'], 'answered_unverified')
        self.assert_dependency_graph(result)
        refs = {e['event_id']: e['input'].get('source_event_ids', e.get('source_event_ids'))
                for e in result['trace']}
        self.assertEqual(refs['call_01'], [])
        self.assertEqual(refs['call_02'], ['call_01'])
        self.assertEqual(refs['map_01'], ['call_02'])
        self.assertEqual(refs['call_03'], ['call_01', 'call_02', 'map_01'])
        self.assertEqual(refs['tool_01'], ['call_03'])
        self.assertEqual(refs['call_04'], ['call_01', 'tool_01'])
        self.assertEqual(refs['call_05'], ['call_01', 'tool_01', 'call_04'])
        self.assertEqual(refs['call_06'], ['call_01', 'tool_01', 'call_04', 'call_05', 'map_02'])
        self.assertEqual(refs['call_07'], ['call_01', 'tool_01', 'tool_02'])
        self.assertEqual(refs['call_08'], ['tool_01', 'tool_02', 'call_07'])

    def test_writer_correction_links_rejected_attempt_and_all_evidence(self):
        outputs = scripted_outputs()
        bad = copy.deepcopy(outputs[-1]); bad[1]['evidencias_utilizadas'] = ['invented']
        model = ScriptedModel([*outputs[:-1], bad, outputs[-1]])
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result['status'], 'answered_unverified')
        self.assert_dependency_graph(result)
        self.assertEqual(model.calls[-1][1]['source_event_ids'],
                         ['tool_01', 'tool_02', 'call_07', 'call_08'])

    def test_no_source_writer_references_selector_not_unrelated_events(self):
        outputs = scripted_outputs()
        outputs[1][1].update(decisao='sem_fonte', fonte_id=None, map_refs=[])
        outputs[-1][1]['evidencias_utilizadas'] = []
        model = ScriptedModel([outputs[0], outputs[1], outputs[-1]])
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result['status'], 'insufficient_evidence')
        self.assert_dependency_graph(result)
        self.assertEqual(model.calls[-1][1]['source_event_ids'], ['call_02'])

    def test_synthetic_interval_uses_delivered_filter_contract(self):
        outputs=scripted_outputs()
        outputs[5][1]['plano']['filtros']={'data':{'from':'2020-01-01','to':'2021-01-01'}}
        model=ScriptedModel(outputs)
        result=run(QUESTION,MAPS,model,fixture_query)
        self.assertEqual(result['status'],'answered_unverified')
        inputs=model.calls[5][1]['input']; schema=inputs['source_contract']['filter_contracts']
        self.assertTrue(Draft202012Validator(schema).is_valid(outputs[5][1]['plano']['filtros']))
        self.assertEqual(inputs['source_contract']['field_types']['data'],'date')
        with self.assertRaisesRegex(ValueError,'unsupported_synthetic_filter'):
            fixture_query({**outputs[5][1]['plano'],'filtros':{'data':{'gte':'2020-01-01'}}})

    def test_selected_source_contract_is_intact_and_other_source_detail_is_absent(self):
        maps = copy.deepcopy(MAPS)
        source = maps['dw']['sources']['dw_paradas']
        source.update({'field_types': {'ano': 'integer'},
            'filter_contracts': {'type': 'object', 'properties': {'ano': {'type': 'integer'}}},
            'relations': [], 'units': {'minutos_parada': 'min'}})
        maps['dw']['sources']['other'] = {'fields': ['private_measure'], 'grain': 'other/year'}
        model = ScriptedModel(scripted_outputs())
        result = run(QUESTION, maps, model, fixture_query)
        self.assertEqual(result['status'], 'answered_unverified')
        self.assertEqual(result['model_calls'], 8)
        roles = [role for role, _ in model.calls]
        self.assertEqual(roles, ['analista_pergunta', 'selecionador_fontes', 'especialista_consulta',
                                'revisor_evidencias', 'selecionador_fontes', 'especialista_consulta',
                                'revisor_evidencias', 'redator_resposta'])
        self.assertEqual(set(CONTRACT['roles']), set(INPUT_CONTRACT['roles']))
        self.assertEqual(len(CONTRACT['roles']), 5)
        selector = model.calls[1][1]['input']
        self.assertNotIn('private_measure', json.dumps(selector))
        self.assertEqual(selector['available_source_ids'], ['dw_paradas', 'other'])
        inputs = model.calls[2][1]['input']
        self.assertEqual(inputs['source_contract'], {**source, 'source_id': 'dw_paradas', 'domain': 'dw'})
        self.assertEqual(inputs['question'], QUESTION)
        self.assertNotIn('private_measure', json.dumps(inputs))
        next_input = model.calls[5][1]['input']
        self.assertEqual(next_input['evidence_state'][0]['result_id'], 'result_01')
        self.assertEqual(next_input['gap']['dominio'], 'financeiro')

    def test_rejected_query_returns_exact_plan_and_current_budget_to_same_specialist(self):
        outputs = scripted_outputs()
        bad = copy.deepcopy(outputs[2]); bad[1]['plano']['filtros'] = {'bad': 1}
        model = ScriptedModel([*outputs[:2], bad, *outputs[2:]])
        result = run(QUESTION, MAPS, model, fixture_query, limits=Limits(queries=3))
        self.assertEqual(result['status'], 'answered_unverified')
        repaired = model.calls[3][1]['input']
        feedback = repaired['correction_feedback']
        self.assertEqual(model.calls[3][0], 'especialista_consulta')
        self.assertEqual(feedback['rejected_plan'], bad[1]['plano'])
        self.assertEqual(feedback['rejected_event_id'], 'tool_01')
        self.assertEqual(feedback['budget']['remaining_queries'], 2)
        self.assertEqual(repaired['limits']['remaining_queries'], 2)
        self.assertEqual(repaired['source_contract'], model.calls[2][1]['input']['source_contract'])
        self.assertEqual(result['query_attempts'], 3)
        self.assertIn('tool_01', model.calls[3][1]['source_event_ids'])
        self.assert_dependency_graph(result)

    def test_invalid_output_returns_raw_output_to_same_role_without_query(self):
        outputs = scripted_outputs()
        invalid = copy.deepcopy(outputs[2]); invalid[1]['plano']['campos'] = ['invented']
        model = ScriptedModel([*outputs[:2], invalid, *outputs[2:]])
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result['status'], 'answered_unverified')
        feedback = model.calls[3][1]['input']['correction_feedback']
        self.assertEqual(json.loads(feedback['rejected_output']), invalid[1])
        self.assertEqual(feedback['rejected_event_id'], 'call_03')
        self.assertEqual(feedback['budget']['remaining_queries'], 2)
        self.assertEqual(result['query_attempts'], 2)
        self.assertIn('call_03', model.calls[3][1]['source_event_ids'])
        self.assert_dependency_graph(result)

    def test_unknown_source_is_rejected_before_projection_or_query(self):
        outputs = scripted_outputs(); bad = copy.deepcopy(outputs[1])
        bad[1].update(fonte_id='secret', map_refs=['secret'])
        model = ScriptedModel([outputs[0], bad, bad]); queries=[]
        result=run(QUESTION, MAPS, model, lambda plan: queries.append(plan))
        self.assertEqual(result['status'], 'contract_error')
        self.assertFalse(queries)
        self.assertFalse(any(e['role']=='map_projection' for e in result['trace']))

    def test_additional_domain_is_static_index_not_another_discovery_agent(self):
        outputs=scripted_outputs()
        request=('selecionador_fontes', {'decisao':'pedir_dominio','fonte_id':None,
            'dominio_adicional':'financeiro','map_refs':[], 'justificativa':'Preciso do financeiro'})
        model=ScriptedModel([outputs[0],request,*outputs[1:]])
        result=run(QUESTION,MAPS,model,fixture_query)
        self.assertEqual(result['status'],'answered_unverified')
        self.assertEqual(model.calls[1][0],model.calls[2][0])
        self.assertEqual(model.calls[2][1]['input']['available_source_ids'],['dw_paradas','fin_resultado'])
        self.assertEqual(model.calls[2][1]['source_event_ids'], ['call_01', 'call_02'])

    def test_three_domains_with_real_catalog_and_mock_reads(self):
        path=ROOT/'specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json'
        before=path.read_bytes(); catalog=json.loads(before)
        catalog['status']='approved_for_local_query'
        for domain in catalog['domains'].values():
            for source in domain['sources'].values(): source['enabled']=True
        maps=compile_maps(catalog); calls=[]
        def model(role,envelope,contract):
            calls.append((role,envelope));return scripted_model(role,envelope,contract)
        def query(plan):
            self.assertEqual(plan,PLANS[plan['fonte_id']])
            return {'rows':[dict.fromkeys(plan['campos'],1)],
                    'coverage':{'state':'observed','rows':1},'units':{}}
        result=run(PILOT_QUESTION,maps,model,query,limits=Limits(calls=48,queries=3,input_bytes=32768),protocol='local_readonly_pilot')
        self.assertEqual(result['status'],'answered_unverified',result['final_state'])
        self.assertEqual((result['model_calls'],result['queries']),(11,3))
        self.assert_dependency_graph(result)
        self.assertEqual(calls[-1][1]['source_event_ids'], ['tool_01', 'tool_02', 'tool_03', 'call_10'])
        inputs=[e['input'] for role,e in calls if role=='especialista_consulta']
        self.assertEqual([i['domain'] for i in inputs],['dw','industrial','financeiro'])
        for item in inputs:
            source=item['source_contract']; original=catalog['domains'][item['domain']]['sources'][source['source_id']]
            self.assertEqual(source['fields'],original['fields'])
            self.assertEqual(source.get('field_types'),original.get('field_types'))
            self.assertTrue(Draft202012Validator(source['filter_contracts']).is_valid(PLANS[source['source_id']]['filtros']))
        self.assertEqual(path.read_bytes(),before)

    def test_filter_contracts_match_fixed_executor_and_require_numeric_ids(self):
        for item in dw_tools.catalog():
            fn=item['function'];self.assertEqual(filter_contract(fn['name'],{}),fn['parameters'])
        schema=filter_contract('paradas',{'kind':'typed_table_detail',
            'field_types':{'maquina_id':'integer','inicio':'timestamp without time zone'},
            'filter_candidates':['maquina_id','inicio:range']})
        validator=Draft202012Validator(schema)
        self.assertFalse(validator.is_valid({'maquina_id':'2000002'}))
        self.assertTrue(validator.is_valid({'maquina_id':2000002,'inicio':{'from':'2021-01-01','to':'2022-01-01'}}))
        self.assertFalse(validator.is_valid({'inicio':{'gte':'2021-01-01','lt':'2022-01-01'}}))


if __name__=='__main__':unittest.main()
