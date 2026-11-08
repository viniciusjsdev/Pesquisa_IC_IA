"""Route-independent code/data identities, without network or databases."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from inference_api.agent_harness import runtime_identity, local_queries, approved_catalog


class RuntimeIdentityTests(unittest.TestCase):
    def test_code_bundle_covers_effective_transports_compilers_and_context(self):
        files = runtime_identity.identity()['files']
        for name in ('engine.py', 'typed_detail.py', 'local_queries.py', 'real_pilot.py',
                     'openai_pilot.py', 'catalog_runtime.py', 'synthetic_demo.py',
                     'openai_provider.py', 'groq.py', 'request_budget.py', 'fixed_queries.py'):
            self.assertTrue(any(path.endswith('/' + name) for path in files), name)
        for group, module in (('api', 'server.py'), ('identity', 'auth.py'),
                              ('executions', 'service.py'), ('data_access', 'dw_tools.py'),
                              ('evidence', 'evidence_packets.py'), ('persistence', 'storage.py')):
            self.assertTrue(any(path.endswith(f'/{group}/{module}') for path in files), group)
        with TemporaryDirectory() as folder, patch.object(runtime_identity, 'ROOT', Path(folder)):
            source = Path(folder) / 'compiler.py'
            source.write_bytes(b'first')
            first = runtime_identity.identity([source])
            source.write_bytes(b'changed')
            self.assertNotEqual(first, runtime_identity.identity([source]))

    def test_source_loads_include_all_enabled_tables_without_model_route(self):
        catalog = approved_catalog.load()
        def collect(changed=False):
            connections = []
            for domain in ('industrial', 'financeiro'):
                definition = catalog['domains'][domain]
                connection = MagicMock()
                cursor = connection.cursor.return_value.__enter__.return_value
                cursor.fetchone.return_value = (definition['database'],)
                cursor.fetchall.return_value = [(name, 2, 'b' * 64 if changed else 'a' * 64)
                    for name, source in definition['sources'].items() if source.get('enabled')]
                connections.append(connection)
            with patch.object(local_queries, '_connect', side_effect=connections) as connect:
                result = local_queries.source_fingerprints(catalog)
            self.assertEqual(connect.call_count, 2)
            for connection in connections:
                connection.rollback.assert_called_once()
                connection.close.assert_called_once()
                self.assertIn('SET TRANSACTION READ ONLY', str(connection.cursor.return_value.__enter__.return_value.execute.call_args_list))
            return result
        first = collect()
        self.assertEqual(first['status'], 'recorded')
        self.assertNotEqual(first, collect(changed=True))
        for domain in ('industrial', 'financeiro'):
            self.assertEqual(len(first['domains'][domain]['files']),
                sum(bool(source.get('enabled')) for source in catalog['domains'][domain]['sources'].values()))
        with patch.object(local_queries, '_connect', side_effect=OSError('sensitive connection detail')):
            failed = local_queries.source_fingerprints(catalog)
        self.assertEqual(failed, {'status': 'unavailable', 'error_type': 'OSError'})
        self.assertNotIn('sensitive', json.dumps(failed))


if __name__ == '__main__': unittest.main()
