"""Run the DW suite with read-only checks of the already loaded local cluster."""

import os
from pathlib import Path
import unittest

os.environ['DW_LOCAL_INTEGRATION'] = '1'
suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
