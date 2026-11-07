"""Create an offline review bundle; never approve, score, query or call a model."""
import argparse
import json
from pathlib import Path

try:
    from .harness_score import _digest, evaluate
except ImportError:
    from harness_score import _digest, evaluate


def prepare(run: dict, case: dict) -> dict:
    checks = evaluate(run, case)
    if checks['status'] != 'awaiting_run_review':
        raise ValueError('run_and_case_not_ready_for_review')
    return {'schema_version': 1, 'run': run, 'case': case, 'checks': checks,
            'adjudication_template': {'status': 'pending', 'run_id': run['run_id'],
                'case_id': case['case_id'], 'run_sha256': _digest(run),
                'case_sha256': _digest(case), 'reviewer': '', 'reviewed_at': '',
                'rationale': '', 'calculation': None, 'conclusion': None}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path, help='Exact harness result JSON used by evaluate')
    parser.add_argument('case', type=Path, help='Approved private case JSON')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    bundle = prepare(json.loads(args.run.read_text(encoding='utf-8')),
                     json.loads(args.case.read_text(encoding='utf-8')))
    # Exclusive creation preserves prior review packages.
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(bundle, output, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({'status': 'pending', 'run_sha256': bundle['checks']['run_sha256']}))


if __name__ == '__main__':
    main()
