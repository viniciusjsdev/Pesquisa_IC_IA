#!/usr/bin/env python3
"""Avaliação em lote para Base/LoRA com métricas FinQA e FailureSensorIQ."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

from common.config_utils import (
    build_run_dirs,
    default_run_name,
    ensure_dir,
    load_config,
    load_jsonl,
    load_paths_config,
    nested_get,
    repo_root,
    resolve_path,
    save_json,
    save_jsonl,
)
from common.metrics import evaluate_failure, evaluate_finqa, normalize_text, numeric_match, parse_numeric

def parse_args():
    p = argparse.ArgumentParser(description='Avaliação em lote (Base / LoRA / comparação)')
    p.add_argument('--eval-config', default='configs/eval/base.yaml')
    p.add_argument('--paths-config', default='configs/paths.local.yaml')
    p.add_argument('--experiment-id', default='ft_hibrido_v1')
    p.add_argument('--run-dir', help='Diretório de run (para localizar adapter e salvar outputs)')
    p.add_argument('--adapter-path', help='Caminho explícito do adapter LoRA')
    p.add_argument('--base-model', default='Qwen/Qwen2.5-7B-Instruct',
                   help='Modelo base HF (usado quando o run não registra resolved_train_config.json)')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--base-only', action='store_true')
    mode.add_argument('--adapter-only', action='store_true')
    mode.add_argument('--compare', action='store_true')
    p.add_argument('--domains', choices=['finqa', 'failure', 'both'], default=None)
    p.add_argument('--max-samples', type=int, default=None)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--dry-run', action='store_true')
    return p.parse_args()

def load_examples(test_data_path: Path, domain_filter: str | None, max_samples: int | None) -> List[Dict[str, Any]]:
    rows = load_jsonl(test_data_path)
    if domain_filter and domain_filter != 'both':
        target = 'FinQA' if domain_filter == 'finqa' else 'FailureSensorIQ'
        rows = [r for r in rows if ((r.get('meta') or {}).get('dataset') == target)]
    if max_samples:
        rows = rows[:max_samples]
    return rows

def run_model_predictions(rows, base_model, cache_dir, eval_cfg, adapter_path=None):
    from common.modeling import generate_answers_batch, load_model, load_tokenizer

    gen_cfg = nested_get(eval_cfg, 'evaluation.generation', {}) or {}
    model = load_model(
        base_model,
        cache_dir=cache_dir,
        qlora_cfg={
            'load_in_4bit': True,
            'bnb_4bit_quant_type': 'nf4',
            'bnb_4bit_use_double_quant': True,
            'bnb_4bit_compute_dtype': 'float16',
        },
        adapter_path=adapter_path,
    )
    tokenizer = load_tokenizer(base_model, cache_dir=cache_dir)
    preds = []
    batch_size = int(gen_cfg.get('batch_size', 8))
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        preds.extend(
            p.strip()
            for p in generate_answers_batch(
                model,
                tokenizer,
                [str(row.get('prompt', '')) for row in batch],
                max_new_tokens=int(gen_cfg.get('max_new_tokens', 128)),
                temperature=float(gen_cfg.get('temperature', 0.0)),
                top_p=float(gen_cfg.get('top_p', 0.9)),
                top_k=int(gen_cfg.get('top_k', 50)),
                do_sample=bool(gen_cfg.get('do_sample', False)),
                repetition_penalty=float(gen_cfg.get('repetition_penalty', 1.0)),
                max_input_length=int(gen_cfg.get('max_input_length', 1024)),
            )
        )
        print(f"[INFO] generated {min(start + batch_size, len(rows))}/{len(rows)}", flush=True)
    return preds

def build_prediction_records(rows, preds, abs_tol: float, rel_tol: float):
    records = []
    for i, (row, pred) in enumerate(zip(rows, preds)):
        gold = row.get('resposta', '')
        records.append(
            {
                'sample_id': ((row.get('meta') or {}).get('id') or f'sample_{i}'),
                'dataset': ((row.get('meta') or {}).get('dataset') or ''),
                'split': 'test',
                'prompt': row.get('prompt', ''),
                'gold': gold,
                'prediction': pred,
                'meta': row.get('meta', {}),
                'parsed_numeric_gold': parse_numeric(str(gold)),
                'parsed_numeric_pred': parse_numeric(str(pred)),
                'is_exact_match': normalize_text(str(gold)) == normalize_text(str(pred)),
                'is_numeric_match': numeric_match(gold, pred, abs_tol=abs_tol, rel_tol=rel_tol),
                'error_type': None,
            }
        )
    for rec in records:
        if not rec['is_exact_match'] and rec['parsed_numeric_gold'] is not None and rec['parsed_numeric_pred'] is None:
            rec['error_type'] = 'numeric_parse_fail'
        elif not rec['is_exact_match'] and rec['is_numeric_match']:
            rec['error_type'] = 'format_mismatch_numeric_ok'
        elif not rec['is_exact_match']:
            rec['error_type'] = 'mismatch'
    return records

def evaluate_and_save(rows, preds, eval_cfg, metrics_dir: Path, predictions_dir: Path, label: str, write_legacy_files: bool = False):
    abs_tol = float(nested_get(eval_cfg, 'evaluation.numeric_tolerance.absolute', 1e-3))
    rel_tol = float(nested_get(eval_cfg, 'evaluation.numeric_tolerance.relative', 1e-3))
    records = build_prediction_records(rows, preds, abs_tol=abs_tol, rel_tol=rel_tol)
    suffix = label.lower()

    rows_finqa = [r for r in rows if ((r.get('meta') or {}).get('dataset') == 'FinQA')]
    preds_finqa = [p for r, p in zip(rows, preds) if ((r.get('meta') or {}).get('dataset') == 'FinQA')]
    rows_failure = [r for r in rows if ((r.get('meta') or {}).get('dataset') == 'FailureSensorIQ')]
    preds_failure = [p for r, p in zip(rows, preds) if ((r.get('meta') or {}).get('dataset') == 'FailureSensorIQ')]

    gen_cfg = nested_get(eval_cfg, 'evaluation.generation', {}) or {}
    timestamp = __import__('datetime').datetime.utcnow().isoformat() + 'Z'
    summary = {
        'model_label': label,
        'dataset': 'hybrid_test_filtered',
        'n_samples': len(rows),
        'metrics': {},
        'generation_config': gen_cfg,
        'timestamp': timestamp,
    }
    if rows_finqa:
        finqa_metrics = evaluate_finqa(rows_finqa, preds_finqa, abs_tol=abs_tol, rel_tol=rel_tol)
        finqa_payload = {
            'model_label': label,
            'dataset': 'FinQA',
            'n_samples': len(rows_finqa),
            'metrics': finqa_metrics,
            'generation_config': gen_cfg,
            'timestamp': timestamp,
        }
        save_json(metrics_dir / f'finqa_{suffix}.json', finqa_payload)
        if write_legacy_files:
            save_json(metrics_dir / 'finqa.json', finqa_payload)
        summary['metrics']['FinQA'] = finqa_metrics
    if rows_failure:
        failure_metrics = evaluate_failure(rows_failure, preds_failure)
        failure_payload = {
            'model_label': label,
            'dataset': 'FailureSensorIQ',
            'n_samples': len(rows_failure),
            'metrics': failure_metrics,
            'generation_config': gen_cfg,
            'timestamp': timestamp,
        }
        save_json(metrics_dir / f'failure_{suffix}.json', failure_payload)
        if write_legacy_files:
            save_json(metrics_dir / 'failure.json', failure_payload)
        summary['metrics']['FailureSensorIQ'] = failure_metrics

    cross_domain_payload = {
        'model_label': label,
        'dataset': 'cross_domain_summary',
        'n_samples': len(rows),
        'metrics': summary['metrics'],
        'generation_config': gen_cfg,
        'timestamp': timestamp,
    }
    save_json(metrics_dir / f'cross_domain_{suffix}.json', cross_domain_payload)
    if write_legacy_files:
        save_json(metrics_dir / 'cross_domain.json', cross_domain_payload)

    save_json(metrics_dir / f'summary_{suffix}.json', summary)
    if write_legacy_files:
        save_json(metrics_dir / 'summary.json', summary)
    save_jsonl(predictions_dir / f'{label.lower()}_predictions.jsonl', records)

def main() -> int:
    args = parse_args()
    eval_cfg = load_config(resolve_path(args.eval_config, repo_root()))
    paths_cfg = load_paths_config(args.paths_config)
    mode_compare = args.compare or (not args.base_only and not args.adapter_only)
    domain_filter = args.domains or nested_get(eval_cfg, 'evaluation.domains', 'both')
    test_data_path = resolve_path(nested_get(eval_cfg, 'paths.test_data_path'), repo_root(), variables={'repo_root': str(repo_root())})
    rows = load_examples(test_data_path, domain_filter, args.max_samples)

    if args.run_dir:
        run_dir = Path(args.run_dir)
        metrics_dir = ensure_dir(run_dir / 'metrics')
        predictions_dir = ensure_dir(run_dir / 'predictions')
    else:
        tmp = build_run_dirs(repo_root() / 'results' / 'experiments' / 'manual_evaluations', args.experiment_id, default_run_name(args.seed))
        run_dir = tmp['run_dir']
        metrics_dir = tmp['metrics_dir']
        predictions_dir = tmp['predictions_dir']

    # Resolve o modelo base: prioriza o registrado no run treinado (garante que o
    # adapter seja carregado sobre a mesma base usada no treino); senão, usa --base-model.
    base_model = args.base_model
    if args.run_dir:
        resolved_cfg_path = Path(args.run_dir) / 'meta' / 'resolved_train_config.json'
        if resolved_cfg_path.exists():
            import json
            try:
                trained_cfg = json.loads(resolved_cfg_path.read_text(encoding='utf-8'))
                trained_base = nested_get(trained_cfg, 'model.base_model', None)
                if trained_base:
                    base_model = trained_base
            except Exception as e:
                print(f'[WARN] não foi possível ler resolved_train_config.json: {e}')
    print(f'[INFO] base_model={base_model}')
    cache_dir = nested_get(paths_cfg, 'hf.cache_dir', None)
    adapter_path = args.adapter_path
    if not adapter_path and args.run_dir:
        candidate = Path(args.run_dir) / 'adapter'
        if candidate.exists():
            adapter_path = str(candidate)

    print(f'[INFO] test_data_path={test_data_path}')
    print(f'[INFO] domain_filter={domain_filter} | n={len(rows)}')
    print(f'[INFO] run_dir={run_dir}')
    print(f'[INFO] adapter_path={adapter_path}')

    if args.dry_run:
        return 0

    single_model_mode = bool(args.base_only) ^ bool(args.adapter_only)

    if args.base_only or mode_compare:
        preds = run_model_predictions(rows, base_model, cache_dir, eval_cfg, adapter_path=None)
        evaluate_and_save(
            rows,
            preds,
            eval_cfg,
            metrics_dir,
            predictions_dir,
            'BASE',
            write_legacy_files=(single_model_mode and bool(args.base_only)),
        )

    if args.adapter_only or mode_compare:
        if not adapter_path:
            raise SystemExit('Adapter path é obrigatório para avaliação do modelo fine-tunado (--adapter-path ou --run-dir).')
        preds = run_model_predictions(rows, base_model, cache_dir, eval_cfg, adapter_path=adapter_path)
        evaluate_and_save(
            rows,
            preds,
            eval_cfg,
            metrics_dir,
            predictions_dir,
            'ADAPTER',
            write_legacy_files=(single_model_mode and bool(args.adapter_only)),
        )

    print('[OK] Avaliação concluída.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
