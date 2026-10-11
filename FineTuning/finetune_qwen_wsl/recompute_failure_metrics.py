#!/usr/bin/env python3
"""Recompute FailureSensorIQ metrics from saved predictions without inference."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from common.metrics import evaluate_failure


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--label', required=True)
    return parser.parse_args()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open('r', encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    predictions_path = args.predictions.resolve()
    output_path = args.output.resolve()
    records = [
        record for record in load_jsonl(predictions_path)
        if record.get('dataset') == 'FailureSensorIQ'
    ]
    if not records:
        raise ValueError(f'No FailureSensorIQ records found in {predictions_path}')

    rows = [
        {
            'prompt': record.get('prompt', ''),
            'resposta': record.get('gold', ''),
            'meta': record.get('meta') or {},
        }
        for record in records
    ]
    preds = [str(record.get('prediction', '')) for record in records]
    payload = {
        'model_label': args.label,
        'dataset': 'FailureSensorIQ',
        'n_samples': len(records),
        'metrics': evaluate_failure(rows, preds),
        'source_predictions': str(predictions_path),
        'source_predictions_sha256': sha256(predictions_path),
        'recomputed_at': datetime.now(timezone.utc).isoformat(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(f'Refusing to overwrite existing output: {output_path}')
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
