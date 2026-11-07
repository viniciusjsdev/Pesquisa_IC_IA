"""Historical command names must not rebuild or validate a partial V1 dataset."""
import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import bootstrap_local
from dw import cli


class CanonicalEntrypointTests(unittest.TestCase):
    def test_bootstrap_verify_routes_to_canonical_without_v1_inventory(self):
        with patch.object(sys, 'argv', ['bootstrap_local.py', '--verify']), \
                patch('scripts.verify_canonical_load.verify', return_value={'database_writes': False}) as verify, \
                patch.object(bootstrap_local, 'inventory') as inventory, \
                contextlib.redirect_stdout(io.StringIO()):
            bootstrap_local.main()
        verify.assert_called_once_with(bootstrap_local.ROOT)
        inventory.assert_not_called()

    def test_bootstrap_load_refuses_before_database_access(self):
        with patch.object(sys, 'argv', ['bootstrap_local.py']), \
                patch.object(bootstrap_local, 'create_databases') as create:
            with self.assertRaisesRegex(RuntimeError, 'canonical_ingest.py plan'):
                bootstrap_local.main()
        create.assert_not_called()

    def test_dw_verify_routes_to_canonical(self):
        with patch.object(sys, 'argv', ['cli.py', 'verify']), \
                patch('scripts.verify_canonical_load.verify', return_value={'database_writes': False}) as verify, \
                patch.object(cli, 'verify') as legacy, \
                contextlib.redirect_stdout(io.StringIO()):
            cli.main()
        verify.assert_called_once_with(cli.ROOT)
        legacy.assert_not_called()

    def test_dw_build_refuses_before_inventory(self):
        with patch.object(bootstrap_local, 'inventory') as inventory:
            with self.assertRaisesRegex(RuntimeError, 'refusing to create an incomplete DW'):
                cli.build()
        inventory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
