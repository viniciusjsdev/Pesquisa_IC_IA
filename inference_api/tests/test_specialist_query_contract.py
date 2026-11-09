import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
"""Filter contracts remain identical after the graph migration."""
import unittest
from inference_api.agent_harness.catalog_runtime import filter_contract
from inference_api import dw_tools
from jsonschema import Draft202012Validator


class SpecialistQueryContractTests(unittest.TestCase):
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

if __name__=="__main__": unittest.main()
