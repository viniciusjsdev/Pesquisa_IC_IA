"""Synthetic controls for the isolated SPEC-013 post-run evaluator."""

import sys
import copy
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from model_evaluation.harness_score import ScoreContractError, _digest, evaluate  # noqa: E402


RUN = {
    "run_id": "fixture-run", "status": "answered_unverified",
    "question": "Pergunta fictícia?", "map_sha256": {"dw": "fixture-map"},
    "evidence": [{"result_id": "result_01", "source_id": "machine",
                  "coverage": {"state": "observed", "rows": 1},
                  "rows": [{"minutes": 45}]},
                 {"result_id": "result_02", "source_id": "paradas_maquinas",
                  "coverage": {"state": "observed", "rows": 1},
                  "rows": [{"minutes": 45}]}],
    "response": {"resposta": "45 minutos, sem inferência causal.",
                 "evidencias_utilizadas": ["result_01", "result_02"],
                 "calculos": [], "ressalvas": []},
}
CASE = {"status": "approved", "case_id": "fixture-case",
        "prepared_by": "fixture-preparer",
        "question_sha256": _digest(RUN["question"]),
        "map_sha256": RUN["map_sha256"],
        "accepted_routes": [["machine", "paradas_maquinas"],
                            ["paradas_maquinas", "machine"]],
        "required_evidence_sources": ["machine", "paradas_maquinas"],
        "review": {"reviewer": "fixture-reviewer", "reviewed_at": "2026-11-01",
                   "evidence_receipt": "synthetic-only"}}
ADJUDICATION = {"status": "reviewed", "run_id": RUN["run_id"],
                "run_sha256": _digest(RUN),
                "case_id": CASE["case_id"], "case_sha256": _digest(CASE),
                "reviewer": "fixture-reviewer", "reviewed_at": "2026-11-01",
                "rationale": "Synthetic calculation and caveat checked.",
                "calculation": 1, "conclusion": 1}


class HarnessScoreTests(unittest.TestCase):
    def test_adjudication_is_bound_to_complete_run_and_canonical_content(self):
        for key, value in [('response', {**RUN['response'], 'resposta': 'Outra resposta'}),
                           ('trace', [{'event_id': 'changed'}]), ('limits', {'queries': 99}),
                           ('candidate', ['other', 'model']),
                           ('evidence', [{**RUN['evidence'][0], 'rows': [{'minutes': 999}]}, RUN['evidence'][1]])]:
            with self.subTest(key=key), self.assertRaisesRegex(ScoreContractError, 'invalid_run_adjudication'):
                evaluate({**RUN, key: value}, CASE, ADJUDICATION)
        legacy = {k: v for k, v in ADJUDICATION.items() if k != 'run_sha256'}
        with self.assertRaisesRegex(ScoreContractError, 'invalid_run_adjudication'):
            evaluate(RUN, CASE, legacy)
        reordered = dict(reversed(list(copy.deepcopy(RUN).items())))
        self.assertEqual(evaluate(reordered, CASE, ADJUDICATION)['status'], 'scored')

    def test_prepared_review_has_exact_objects_and_no_approval(self):
        from model_evaluation.prepare_run_review import prepare
        package = prepare(RUN, CASE)
        template = package['adjudication_template']
        self.assertEqual(template['run_sha256'], _digest(RUN))
        self.assertEqual(template['case_sha256'], _digest(CASE))
        self.assertEqual(package['run'], RUN)
        self.assertEqual(template['status'], 'pending')
        self.assertIsNone(evaluate(RUN, CASE, template)['scores'])

    def test_requires_case_and_run_review_before_any_score(self):
        self.assertEqual(evaluate(RUN, None)["status"], "not_scored")
        self.assertEqual(evaluate(RUN, {**CASE, "status": "draft"})["status"],
                         "not_scored")
        pending = evaluate(RUN, CASE)
        self.assertEqual(pending["status"], "awaiting_run_review")
        self.assertIsNone(pending["scores"])
        self.assertEqual(pending["automatic_checks"],
                         {"route": 1, "evidence_reference": 1})

    def test_reviewed_card_keeps_dimensions_separate(self):
        card = evaluate(RUN, CASE, ADJUDICATION)
        self.assertEqual(card["status"], "scored")
        self.assertEqual(card["scores"],
                         {"route": 1, "evidence_reference": 1,
                          "calculation": 1, "conclusion": 1})
        self.assertNotIn("average", card)

    def test_route_alternative_and_unobserved_reference(self):
        swapped = {**RUN, "evidence": list(reversed(RUN["evidence"]))}
        self.assertEqual(evaluate(swapped, CASE)["automatic_checks"]["route"], 1)
        missing = {**RUN, "evidence": [{**RUN["evidence"][0],
                     "coverage": {"state": "no_observation", "rows": 0},
                     "rows": []}, RUN["evidence"][1]]}
        self.assertEqual(evaluate(missing, CASE)["automatic_checks"]["evidence_reference"], 0)
        wrong = {**RUN, "evidence": RUN["evidence"][:1],
                 "response": {**RUN["response"],
                              "evidencias_utilizadas": ["invented"]}}
        checks = evaluate(wrong, CASE)["automatic_checks"]
        self.assertEqual(checks, {"route": 0, "evidence_reference": 0})
        uncited = {**RUN, "response": {**RUN["response"],
                   "evidencias_utilizadas": ["result_01"]}}
        self.assertEqual(evaluate(uncited, CASE)["automatic_checks"]["evidence_reference"], 0)

    def test_approved_no_observation_is_citable_without_treating_it_as_zero(self):
        empty = {**RUN, "evidence": [{"result_id": "result_01", "source_id": "financial",
                                      "coverage": {"state": "no_observation", "rows": 0},
                                      "rows": []}],
                 "response": {**RUN["response"],
                              "evidencias_utilizadas": ["result_01"]}}
        case = {**CASE, "accepted_routes": [["financial"]],
                "required_evidence_sources": ["financial"],
                "expected_evidence_states": {"financial": "no_observation"}}
        self.assertEqual(evaluate(empty, case)["automatic_checks"],
                         {"route": 1, "evidence_reference": 1})
        self.assertEqual(evaluate(empty, {**case,
            "expected_evidence_states": {"financial": "observed"}})["automatic_checks"],
                         {"route": 1, "evidence_reference": 0})

    def test_incomplete_mismatch_and_stale_adjudication(self):
        self.assertEqual(evaluate({**RUN, "status": "contract_error"}, CASE)["status"],
                         "not_scored")
        with self.assertRaisesRegex(ScoreContractError, "question_fingerprint_mismatch"):
            evaluate({**RUN, "question": "Outra pergunta"}, CASE)
        with self.assertRaisesRegex(ScoreContractError, "invalid_run_adjudication"):
            evaluate(RUN, CASE, {**ADJUDICATION, "case_sha256": "stale"})
        with self.assertRaisesRegex(ScoreContractError, "case_reviewer_must_be_independent"):
            evaluate(RUN, {**CASE, "prepared_by": "fixture-reviewer"})


if __name__ == "__main__":
    unittest.main()
