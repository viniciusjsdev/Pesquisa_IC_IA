"""Migration allowlist and provenance checks for the existing V2 warehouse."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from inference_api import dw_tools


class V2GateTests(unittest.TestCase):
    def test_reviewed_v2_and_historical_v1(self):
        self.assertEqual(dw_tools._supported_migration([(2, dw_tools.KNOWN_V2_FINGERPRINT)]),
                         (2, dw_tools.KNOWN_V2_FINGERPRINT))
        self.assertEqual(dw_tools._supported_migration([(1, "a" * 64)]), (1, "a" * 64))

    def test_unknown_version_or_fingerprint_is_blocked(self):
        for rows in ([(2, "a" * 64)], [(3, dw_tools.KNOWN_V2_FINGERPRINT)],
                     [(2, "invalid")], [], [(1, "a" * 64), (2, dw_tools.KNOWN_V2_FINGERPRINT)]):
            with self.subTest(rows=rows), self.assertRaises(dw_tools.DWFingerprintError):
                dw_tools._supported_migration(rows)


if __name__ == "__main__":
    unittest.main()
