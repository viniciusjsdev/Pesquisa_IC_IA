import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'finetune_qwen_wsl'))

from common.metrics import choice_labels, evaluate_failure  # noqa: E402


class FailureMultilabelMetricsTests(unittest.TestCase):
    def test_extracts_multiple_explicit_labels_and_ignores_generated_options(self):
        prediction = (
            'B) rotor windings fault e E) loss of output power phase '
            '### Response Options: A) eccentric rotor B) rotor windings fault C) misalignment'
        )
        self.assertEqual(choice_labels(prediction), {'b', 'e'})

    def test_matches_option_text_when_model_omits_letter(self):
        prompt = (
            'Questão: teste. Opções: A) air flow B) temperature C) pressure '
            'D) vibration E) power ### Response:'
        )
        self.assertEqual(choice_labels('The relevant sensor is air flow.', prompt), {'a'})

    def test_extracts_truncated_markdown_label(self):
        self.assertEqual(choice_labels('The least relevant option is: **C'), {'c'})

    def test_reports_exact_set_accuracy_and_multilabel_f1(self):
        rows = [
            {'prompt': '', 'resposta': 'A) alpha e B) beta'},
            {'prompt': '', 'resposta': 'D) delta'},
        ]
        metrics = evaluate_failure(rows, ['A) alpha', 'D) delta'])
        self.assertEqual(metrics['accuracy'], 0.5)
        self.assertEqual(metrics['subset_accuracy'], 0.5)
        self.assertEqual(metrics['precision_micro'], 1.0)
        self.assertEqual(metrics['recall_micro'], 0.6667)
        self.assertEqual(metrics['f1_micro'], 0.8)
        self.assertEqual(metrics['metric_definition'], 'multilabel_exact_set_accuracy_and_labelwise_f1')


if __name__ == '__main__':
    unittest.main()
