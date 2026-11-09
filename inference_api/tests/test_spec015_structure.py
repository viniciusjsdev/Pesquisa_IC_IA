import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from inference_api.agent_harness.graph.builder import build
from inference_api.agent_harness.graph.state import RunContext
from inference_api.agent_harness import scenarios, runtime_identity
from inference_api.observability.noop import Noop
from inference_api.model_service import ModelService
from spec014_fixture import profile, Transport, MAPS, fixture_query, QUESTION

class StructureTests(unittest.TestCase):
    def test_compiled_graph_has_distinct_agents_tools_and_explicit_edges(self):
        graph=build(RunContext(None,None,lambda:False,Noop())).get_graph()
        self.assertTrue({'analyst','selector','project_context','consolidated_specialist',
            'industrial_specialist','financial_specialist','execute_tool','reviewer','writer'} <= set(graph.nodes))
        self.assertTrue(any(e.source=='execute_tool' and e.target=='consolidated_specialist' for e in graph.edges))

    def test_recursive_identity_changes_when_deep_module_changes(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); package=root/'inference_api/src/inference_api'
            source=package/'agent_harness/agents/deep.py'; source.parent.mkdir(parents=True)
            source.write_text('first',encoding='utf-8')
            (root/'BancoModeloUse/dw').mkdir(parents=True)
            (root/'BancoModeloUse/dw/fixed_queries.py').write_text('fixture',encoding='utf-8')
            (root/'inference_api/requirements.txt').write_text('fixture',encoding='utf-8')
            with patch.object(runtime_identity,'ROOT',root),patch.object(runtime_identity,'PACKAGE',package):
                first=runtime_identity.identity()
                source.write_text('changed',encoding='utf-8')
                self.assertNotEqual(first,runtime_identity.identity())

    def test_repairs_do_not_hit_default_framework_recursion_limit(self):
        seen=set()
        def malformed(e,v):
            key=(e['role'],e['round'])
            if key not in seen: seen.add(key); return 'invalid-json'
            return v
        p=profile(); result=scenarios.run(QUESTION,'data_access',p['id'],
            ModelService(p,{},transport=Transport(malformed)),maps=MAPS,query=fixture_query)
        self.assertEqual(result['status'],'answered_unverified',result['final_state'])
        self.assertGreater(result['model_calls'],20)
        self.assertEqual(result['query_attempts'],3)

    def test_tools_route_from_approved_source_not_model_decision(self):
        from inference_api.agent_harness.tools.registry import resolve
        for sid,domain,tool in [('machine','dw','dw_query'),('contributors','dw','contributors'),
              ('trace','dw','trace'),('detail','industrial','industrial_query'),('detail','financeiro','financial_query')]:
            self.assertEqual(resolve({'id':sid,'domain':domain}).tool_id,tool)

    def test_unexpected_recursion_error_preserves_already_executed_calls(self):
        p=profile()
        with patch('inference_api.agent_harness.graph.execution.recursion_limit',return_value=1):
            result=scenarios.run(QUESTION,'data_access',p['id'],ModelService(p,{},transport=Transport()),
                                 maps=MAPS,query=fixture_query)
        self.assertEqual(result['final_state']['error'],'internal_graph_recursion_limit')
        self.assertEqual(result['model_calls'],1)
        self.assertEqual(result['trace'][0]['role'],'analista_pergunta')

if __name__=='__main__': unittest.main()
