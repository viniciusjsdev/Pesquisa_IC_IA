from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .config_utils import ensure_dir, file_hashes, load_jsonl, save_json, save_jsonl

def _word_len(text: str) -> int:
    return len(str(text or '').split())

def filter_by_dataset(rows: Iterable[Dict[str, Any]], dataset_name: str) -> List[Dict[str, Any]]:
    return [r for r in rows if ((r.get('meta') or {}).get('dataset') or '').strip() == dataset_name]

def _summarize_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    domain_counter = Counter()
    prompt_lengths = []
    response_lengths = []
    finqa_ops = Counter()
    for row in rows:
        meta = row.get('meta') or {}
        domain_counter[meta.get('dataset', '<none>')] += 1
        prompt_lengths.append(_word_len(row.get('prompt', '')))
        response_lengths.append(_word_len(row.get('resposta', '')))
        prog = meta.get('program')
        if prog:
            finqa_ops[str(prog).split('(')[0]] += 1
    def stats(vals: List[int]) -> Dict[str, Any]:
        if not vals:
            return {'min': 0, 'max': 0, 'mean': 0.0, 'p95': 0}
        vals = sorted(vals)
        return {
            'min': vals[0],
            'max': vals[-1],
            'mean': round(sum(vals) / len(vals), 2),
            'p95': vals[int(0.95 * (len(vals) - 1))],
        }
    return {
        'n_rows': len(rows),
        'by_domain': dict(domain_counter),
        'prompt_tokens_approx': stats(prompt_lengths),
        'response_tokens_approx': stats(response_lengths),
        'finqa_program_ops_top10': dict(finqa_ops.most_common(10)),
    }

def build_manifest(dataset_id: str, split_paths: Dict[str, Path], source: str, notes: str = '') -> Dict[str, Any]:
    split_counts = {}
    by_domain_counts = {}
    token_stats = {}
    hashes = {}
    for split, path in split_paths.items():
        rows = load_jsonl(path)
        summary = _summarize_rows(rows)
        split_counts[split] = summary['n_rows']
        by_domain_counts[split] = summary['by_domain']
        token_stats[split] = {
            'prompt_tokens_approx': summary['prompt_tokens_approx'],
            'response_tokens_approx': summary['response_tokens_approx'],
            'finqa_program_ops_top10': summary['finqa_program_ops_top10'],
        }
        hashes[split] = file_hashes(path)
    return {
        'dataset_id': dataset_id,
        'source': source,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by_script': 'finetune_mistral_wsl/prepare_experiment_datasets.py',
        'upstream_inputs': ['data_ft/train.jsonl', 'data_ft/val.jsonl', 'data_ft/test.jsonl'],
        'split_counts': split_counts,
        'by_domain_counts': by_domain_counts,
        'max_length_policy': {
            'max_length': 1024,
            'rationale': 'Mantido conforme EDA em analise_datasets.ipynb para limitar truncamento e preservar FinQA no cenário híbrido.'
        },
        'token_stats_summary': token_stats,
        'hashes': hashes,
        'notes': notes,
    }

def write_dataset_with_manifest(dataset_id: str, splits: Dict[str, List[Dict[str, Any]]], target_root: Path, manifests_root: Path, source: str, notes: str = '') -> Dict[str, Any]:
    ds_dir = ensure_dir(target_root / dataset_id)
    split_paths = {}
    for split, rows in splits.items():
        path = ds_dir / f'{split}.jsonl'
        save_jsonl(path, rows)
        split_paths[split] = path
    manifest = build_manifest(dataset_id, split_paths, source=source, notes=notes)
    save_json(manifests_root / f'{dataset_id}.json', manifest)
    return manifest
