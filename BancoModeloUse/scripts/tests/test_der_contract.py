"""Keep the saved DataMind DER and the canonical loader in sync offline."""

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


DATA_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DATA_ROOT))
from scripts import canonical_ingest as ingest  # noqa: E402


class DerContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(ingest.CONTRACT.read_text(encoding='utf-8'))

    def test_saved_der_matches_v1_migration_and_new_loader(self):
        ingest.validate_warehouse_model(self.contract, self.contract['tables'])
        self.assertEqual(len(self.contract['warehouse_v1_schema']), 15)
        self.assertEqual(len(self.contract['warehouse_new_schema']), 20)
        self.assertEqual(sum(len(table['fields']) for table in
                             self.contract['warehouse_new_schema'].values()), 180)

    def test_changed_loader_source_blocks_load_preflight(self):
        with patch.dict(ingest.DW_TABLES, {'dim_turn': ('maquinas',)}):
            with self.assertRaisesRegex(RuntimeError, 'New DW schema differs'):
                ingest.validate_warehouse_model(self.contract, self.contract['tables'])

    def test_changed_contract_blocks_load_preflight(self):
        changed = copy.deepcopy(self.contract)
        changed['warehouse_new_schema']['dim_turn']['fields'][0]['type'] = 'text'
        with self.assertRaisesRegex(RuntimeError, 'Saved DER XML differs'):
            ingest.validate_warehouse_model(changed, changed['tables'])


if __name__ == '__main__':
    unittest.main()
