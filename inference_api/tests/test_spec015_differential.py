import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
"""Compare the new graph against frozen baseline outputs and exact HTTP bodies."""
import json
from pathlib import Path
import unittest
from inference_api.agent_harness import scenarios
from spec015_cases import execute, normalize

class DifferentialTests(unittest.TestCase):
    def test_all_frozen_baseline_cases(self):
        baseline = json.loads((Path(__file__).resolve().parents[2]/
            'specs/active/SPEC-015/evidence/differential-baseline.json').read_text(encoding='utf-8'))
        self.assertEqual(len(baseline['cases']), 78)
        for key, expected in baseline['cases'].items():
            if key.startswith('fixed_evidence/'):
                continue  # Contract 3 intentionally changes A; frozen old expectations remain in the baseline.
            with self.subTest(case=key):
                actual = normalize(execute(scenarios, *key.split('/')))
                self.assertEqual(json.loads(json.dumps(actual)), expected)

if __name__ == '__main__': unittest.main()
