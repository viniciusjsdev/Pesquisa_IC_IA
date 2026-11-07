"""A review receipt must stop matching after its reviewed bytes change."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from model_evaluation import verify_human_review_receipt as gate  # noqa: E402


class ReviewGateTests(unittest.TestCase):
    def test_exact_packet_and_reference_then_tamper(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            reviewed = base / "reviewed.md"
            reference = base / "reference.json"
            receipt_path = base / "receipt.json"
            reviewed.write_text("## I1 · example\n", encoding="utf-8")
            reference.write_text('{"value":1}\n', encoding="utf-8")
            artifact = lambda path: {"path": path.name,
                                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            receipt = {"schema_version": 1, "reviewer": "researcher",
                       "preparer": "preparer",
                       "review_source": {"reply_verbatim": "Approved I1"},
                       "reviewed_artifact": artifact(reviewed),
                       "reference_artifacts": [artifact(reference)],
                       "case_decisions": [{"case_id": "I1", "decision": "approved_content"}],
                       "scoring_eligibility": "pending_executable_case_contract_and_run_review"}
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with patch.object(gate, "ROOT", base):
                self.assertEqual(gate.verify(receipt_path)["reviewed_case_ids"], ["I1"])
                reviewed.write_text("## I1 · changed\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "artifact_hash_mismatch"):
                    gate.verify(receipt_path)


if __name__ == "__main__":
    unittest.main()
