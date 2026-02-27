#!/usr/bin/env python3
"""Gera subsets versionados (hybrid_v1, finqa_v1, failure_v1) e manifests a partir de data_ft/."""
from __future__ import annotations

import argparse
from pathlib import Path

from common.config_utils import load_jsonl, repo_root
from common.dataset_utils import filter_by_dataset, write_dataset_with_manifest

def main() -> int:
    parser = argparse.ArgumentParser(description='Preparar datasets versionados para múltiplos fine-tunings')
    parser.add_argument('--repo-root', default=str(repo_root()))
    parser.add_argument('--source-dir', default='data_ft')
    parser.add_argument('--target-root', default='data/processed')
    parser.add_argument('--manifests-root', default='data/manifests')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    root = Path(args.repo_root)
    source_dir = root / args.source_dir
    target_root = root / args.target_root
    manifests_root = root / args.manifests_root

    splits = {}
    for split in ['train', 'val', 'test']:
        p = source_dir / f'{split}.jsonl'
        if not p.exists():
            raise FileNotFoundError(f'Arquivo ausente: {p}')
        splits[split] = load_jsonl(p)

    hybrid_splits = {k: v for k, v in splits.items()}
    finqa_splits = {k: filter_by_dataset(v, 'FinQA') for k, v in splits.items()}
    failure_splits = {k: filter_by_dataset(v, 'FailureSensorIQ') for k, v in splits.items()}

    print('Contagens:')
    for name, ds in [('hybrid_v1', hybrid_splits), ('finqa_v1', finqa_splits), ('failure_v1', failure_splits)]:
        counts = {k: len(v) for k, v in ds.items()}
        print(f'  {name}: {counts}')

    if args.dry_run:
        return 0

    write_dataset_with_manifest(
        'hybrid_v1',
        hybrid_splits,
        target_root=target_root,
        manifests_root=manifests_root,
        source='data_ft (snapshot lógico do dataset híbrido atual)',
        notes='Dataset híbrido v1 derivado diretamente de data_ft legado.',
    )
    write_dataset_with_manifest(
        'finqa_v1',
        finqa_splits,
        target_root=target_root,
        manifests_root=manifests_root,
        source='data_ft filtrado por meta.dataset=FinQA',
        notes='Subconjunto FinQA preservando splits de data_ft.',
    )
    write_dataset_with_manifest(
        'failure_v1',
        failure_splits,
        target_root=target_root,
        manifests_root=manifests_root,
        source='data_ft filtrado por meta.dataset=FailureSensorIQ',
        notes='Subconjunto FailureSensorIQ preservando splits de data_ft.',
    )
    print('Datasets versionados e manifests gerados com sucesso.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
