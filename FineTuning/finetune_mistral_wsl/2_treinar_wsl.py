#!/usr/bin/env python3
"""
Treinamento Mistral-7B com LoRA/QLoRA (WSL) - versão parametrizada para multi-fine-tuning.
- Config via YAML
- Paths sem hardcode
- Artefatos em runs/<experimento>/<run>/
- dry-run para validação estrutural
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import os
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from common.config_utils import (
    build_run_dirs,
    collect_system_info,
    count_jsonl,
    default_run_name,
    ensure_dir,
    get_git_commit,
    load_config,
    load_jsonl,
    load_paths_config,
    nested_get,
    repo_root,
    resolve_path,
    save_json,
    deep_merge,  # type: ignore[attr-defined]
)

REQUIRED_KEYS = [
    'experiment.id',
    'experiment.description',
    'data.dataset_manifest',
    'data.train_path',
    'data.val_path',
    'data.test_path',
    'model.base_model',
    'model.cache_dir',
    'tokenization.max_length',
    'qlora.load_in_4bit',
    'lora.r',
    'lora.alpha',
    'lora.dropout',
    'lora.target_modules',
    'training.num_train_epochs',
    'training.per_device_train_batch_size',
    'training.per_device_eval_batch_size',
    'training.gradient_accumulation_steps',
    'training.learning_rate',
    'training.weight_decay',
    'training.warmup_ratio',
    'training.evaluation_strategy',
    'training.save_strategy',
    'training.load_best_model_at_end',
    'training.metric_for_best_model',
    'training.greater_is_better',
    'training.seed',
    'training.fp16',
    'training.gradient_checkpointing',
    'output.root_runs_dir',
]

MODEL_SHORTCUTS = {
    'hibrido': {
        'train_config': 'configs/train/ft_hibrido_v1.yaml',
        'experiment_id': 'ft_hibrido_v1',
    },
    'finqa': {
        'train_config': 'configs/train/ft_finqa_v1.yaml',
        'experiment_id': 'ft_finqa_v1',
    },
    'failure': {
        'train_config': 'configs/train/ft_failure_v1.yaml',
        'experiment_id': 'ft_failure_v1',
    },
}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Treinamento LoRA/QLoRA parametrizado (multi-fine-tuning)')
    parser.add_argument('--modelo', dest='model_preset', choices=['hibrido', 'finqa', 'failure'], default=None,
                        help='Atalho para selecionar config can?nica e experiment_id')
    parser.add_argument('--train-config', default=None)
    parser.add_argument('--paths-config', default='configs/paths.local.yaml')
    parser.add_argument('--experiment-id', choices=['ft_hibrido_v1', 'ft_finqa_v1', 'ft_failure_v1'], default=None)
    parser.add_argument('--run-name', default=None)
    parser.add_argument('--resume-from-checkpoint', default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit-train-samples', type=int, default=None)
    parser.add_argument('--limit-val-samples', type=int, default=None)
    return parser.parse_args()

def apply_model_preset(args: argparse.Namespace) -> argparse.Namespace:
    preset_key = getattr(args, 'model_preset', None)
    if not preset_key:
        return args
    preset = MODEL_SHORTCUTS[preset_key]
    if not args.train_config:
        args.train_config = preset['train_config']
    if not args.experiment_id:
        args.experiment_id = preset['experiment_id']
    return args

def load_train_config_with_base(path: Path) -> Dict[str, Any]:
    cfg = load_config(path)
    base_path = path.parent / 'base.yaml'
    if base_path.exists() and path.resolve() != base_path.resolve():
        try:
            base_cfg = load_config(base_path)
            cfg = deep_merge(base_cfg, cfg)
        except Exception:
            pass
    return cfg

def validate_required_keys(cfg: Dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_KEYS if nested_get(cfg, k) is None]
    if missing:
        raise ValueError('Campos obrigatórios ausentes na config: ' + ', '.join(missing))

def resolve_runtime_config(args: argparse.Namespace) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Path], Dict[str, Any]]:
    args = apply_model_preset(args)
    root = repo_root()
    train_config_arg = args.train_config or MODEL_SHORTCUTS['hibrido']['train_config']
    train_cfg_path = resolve_path(train_config_arg, root)
    cfg = load_train_config_with_base(train_cfg_path)
    validate_required_keys(cfg)

    if args.experiment_id:
        cfg['experiment']['id'] = args.experiment_id

    paths_cfg = load_paths_config(args.paths_config)
    variables = {
        'repo_root': str(root),
        'hf_cache_dir': nested_get(paths_cfg, 'hf.cache_dir', '/mnt/e/Mistral'),
    }

    data_cfg = cfg['data']
    resolved_paths = {
        'train': resolve_path(data_cfg['train_path'], root, variables=variables),
        'val': resolve_path(data_cfg['val_path'], root, variables=variables),
        'test': resolve_path(data_cfg['test_path'], root, variables=variables),
        'dataset_manifest': resolve_path(data_cfg['dataset_manifest'], root, variables=variables),
    }
    cfg['model']['cache_dir'] = str(resolve_path(cfg['model']['cache_dir'], root, variables=variables)) if '{' in str(cfg['model']['cache_dir']) else cfg['model']['cache_dir']
    experiment_id = cfg['experiment']['id']
    seed = int(cfg['training']['seed'])
    run_name = args.run_name or default_run_name(seed)
    runs_root = resolve_path(cfg['output']['root_runs_dir'], root, variables=variables)
    run_dir_candidate = runs_root / experiment_id / run_name
    if run_dir_candidate.exists() and any(run_dir_candidate.iterdir()) and not args.resume_from_checkpoint:
        raise FileExistsError(
            f'Run já existe e não está vazio: {run_dir_candidate}. '
            'Use --run-name diferente ou --resume-from-checkpoint para retomar.'
        )
    run_dirs = build_run_dirs(runs_root, experiment_id, run_name)
    metadata = {
        'repo_root': str(root),
        'train_config_path': str(train_cfg_path),
        'paths_config_path': str(resolve_path(args.paths_config, root)),
        'experiment_id': experiment_id,
        'run_name': run_name,
        'seed': seed,
    }
    return cfg, paths_cfg, resolved_paths, {**run_dirs, **metadata}

def estimate_steps(train_count: int, cfg: Dict[str, Any]) -> Dict[str, Any]:
    bs = int(cfg['training']['per_device_train_batch_size'])
    grad_acc = int(cfg['training']['gradient_accumulation_steps'])
    epochs = int(cfg['training']['num_train_epochs'])
    steps_per_epoch = math.ceil(train_count / max(1, bs * grad_acc))
    return {
        'train_samples': train_count,
        'steps_per_epoch': steps_per_epoch,
        'estimated_total_steps': steps_per_epoch * epochs,
        'epochs': epochs,
    }

def build_run_manifest(status: str, cfg: Dict[str, Any], runtime: Dict[str, Any], resolved_paths: Dict[str, Path], estimates: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'experiment_id': runtime['experiment_id'],
        'run_name': runtime['run_name'],
        'dataset_manifest': str(resolved_paths['dataset_manifest']),
        'train_config_path': runtime['train_config_path'],
        'resolved_config_snapshot': cfg,
        'git_commit': get_git_commit(repo_root()),
        'start_time': datetime.utcnow().isoformat() + 'Z',
        'end_time': None,
        'hardware': {},
        'software_versions': {},
        'seed': runtime['seed'],
        'status': status,
        'best_checkpoint': None,
        'best_metric': None,
        'estimates': estimates,
        'resolved_paths': {k: str(v) for k, v in resolved_paths.items()},
    }

def save_run_manifest(runtime: Dict[str, Any], manifest: Dict[str, Any]) -> None:
    save_json(Path(runtime['meta_dir']) / 'run_manifest.json', manifest)

def _max_memory_from_cfg(cfg: Dict[str, Any]) -> Dict[Any, str] | None:
    mem = nested_get(cfg, 'model.max_memory')
    if not mem:
        return None
    out: Dict[Any, str] = {}
    for k, v in mem.items():
        key = 0 if str(k).lower() in {'gpu0', '0'} else str(k)
        out[key] = str(v)
    return out

def _dtype_from_name(name: str):
    import torch
    n = str(name).lower()
    if n in {'bf16', 'bfloat16'}:
        return torch.bfloat16
    return torch.float16

def tokenize_rows(tokenizer, rows: List[Dict[str, Any]], max_length: int):
    from datasets import Dataset
    ds = Dataset.from_list(rows)
    def fn(batch):
        texts = []
        for p, r in zip(batch['prompt'], batch['resposta']):
            texts.append(f"{p} {r}")
        return tokenizer(texts, truncation=True, max_length=max_length, padding=False)
    return ds.map(fn, batched=True, remove_columns=ds.column_names)

class FileLogCallback:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        ensure_dir(log_path.parent)
    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs:
            return
        row = {'step': state.global_step, 'epoch': state.epoch, **logs}
        with self.log_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

def train(cfg: Dict[str, Any], runtime: Dict[str, Any], resolved_paths: Dict[str, Path], args: argparse.Namespace) -> bool:
    import torch
    from datasets import Dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
        TrainerCallback,
    )
    from peft import LoraConfig, TaskType, get_peft_model

    rows_train = load_jsonl(resolved_paths['train'])
    rows_val = load_jsonl(resolved_paths['val'])
    if args.limit_train_samples:
        rows_train = rows_train[: args.limit_train_samples]
    if args.limit_val_samples:
        rows_val = rows_val[: args.limit_val_samples]
    if not rows_train or not rows_val:
        raise ValueError('Datasets de treino/validação vazios após filtros/limites.')

    ql = cfg['qlora']
    qcfg = BitsAndBytesConfig(
        load_in_4bit=bool(ql['load_in_4bit']),
        bnb_4bit_quant_type=ql['bnb_4bit_quant_type'],
        bnb_4bit_use_double_quant=bool(ql['bnb_4bit_use_double_quant']),
        bnb_4bit_compute_dtype=_dtype_from_name(ql['bnb_4bit_compute_dtype']),
    )
    base_model = cfg['model']['base_model']
    cache_dir = cfg['model'].get('cache_dir')
    tokenizer = AutoTokenizer.from_pretrained(base_model, cache_dir=cache_dir, trust_remote_code=True, use_fast=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        cache_dir=cache_dir,
        quantization_config=qcfg,
        device_map='auto',
        max_memory=_max_memory_from_cfg(cfg),
        torch_dtype=_dtype_from_name(ql['bnb_4bit_compute_dtype']),
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )

    lcfg = cfg['lora']
    peft_cfg = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=int(lcfg['r']),
        lora_alpha=int(lcfg['alpha']),
        lora_dropout=float(lcfg['dropout']),
        target_modules=list(lcfg['target_modules']),
        bias=lcfg.get('bias', 'none'),
        inference_mode=False,
    )
    model = get_peft_model(model, peft_cfg)
    model.train()
    model.enable_input_require_grads()

    max_length = int(cfg['tokenization']['max_length'])
    tokenized_train = tokenize_rows(tokenizer, rows_train, max_length=max_length)
    tokenized_val = tokenize_rows(tokenizer, rows_val, max_length=max_length)

    t = cfg['training']
    eval_strategy = t.get('evaluation_strategy', 'epoch')
    save_strategy = t.get('save_strategy', 'epoch')
    training_args = TrainingArguments(
        output_dir=str(runtime['checkpoints_dir']),
        num_train_epochs=int(t['num_train_epochs']),
        per_device_train_batch_size=int(t['per_device_train_batch_size']),
        per_device_eval_batch_size=int(t['per_device_eval_batch_size']),
        gradient_accumulation_steps=int(t['gradient_accumulation_steps']),
        learning_rate=float(t['learning_rate']),
        weight_decay=float(t['weight_decay']),
        warmup_ratio=float(t.get('warmup_ratio', 0.05)),
        logging_steps=int(t.get('logging_steps', 10)),
        evaluation_strategy=eval_strategy,
        save_strategy=save_strategy,
        eval_steps=(None if eval_strategy == 'epoch' else int(t['eval_steps'])),
        save_steps=(None if save_strategy == 'epoch' else int(t['save_steps'])),
        load_best_model_at_end=bool(t['load_best_model_at_end']),
        metric_for_best_model=t['metric_for_best_model'],
        greater_is_better=bool(t['greater_is_better']),
        fp16=bool(t.get('fp16', True)),
        gradient_checkpointing=bool(t.get('gradient_checkpointing', True)),
        dataloader_pin_memory=bool(t.get('dataloader_pin_memory', False)),
        dataloader_num_workers=int(t.get('dataloader_num_workers', 0)),
        remove_unused_columns=bool(t.get('remove_unused_columns', False)),
        report_to=[],
        seed=int(t['seed']),
        save_total_limit=3,
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    cb = FileLogCallback(Path(runtime['logs_dir']) / 'training_log.jsonl')
    # Adapter simples para TrainerCallback sem importar classe dedicada
    class _Callback(TrainerCallback):  # type: ignore[misc]
        def on_log(self, args, state, control, logs=None, **kwargs):  # noqa: D401
            cb.on_log(args, state, control, logs=logs, **kwargs)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        data_collator=data_collator,
        callbacks=[_Callback()],
    )

    trainer.train(resume_from_checkpoint=args.resume_from_checkpoint)

    # salvar adapter/tokenizer em adapter/
    trainer.model.save_pretrained(str(runtime['adapter_dir']))
    tokenizer.save_pretrained(str(runtime['adapter_dir']))

    # snapshot config resolvida
    save_json(Path(runtime['meta_dir']) / 'resolved_train_config.json', cfg)

    # atualizar manifest
    manifest_path = Path(runtime['meta_dir']) / 'run_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['status'] = 'completed'
    manifest['end_time'] = datetime.utcnow().isoformat() + 'Z'
    manifest['hardware'] = collect_system_info()
    manifest['software_versions'] = {k: v for k, v in collect_system_info().items() if k in {'torch', 'transformers', 'datasets', 'peft', 'trl', 'bitsandbytes'}}
    state = trainer.state
    manifest['best_metric'] = getattr(state, 'best_metric', None)
    manifest['best_checkpoint'] = getattr(state, 'best_model_checkpoint', None)
    manifest['runtime'] = {
        'global_step': getattr(state, 'global_step', None),
        'epoch': getattr(state, 'epoch', None),
        'max_length': max_length,
        'train_samples_used': len(rows_train),
        'val_samples_used': len(rows_val),
        'steps_por_epoca': math.ceil(len(rows_train) / max(1, int(t['per_device_train_batch_size']) * int(t['gradient_accumulation_steps']))),
        'tokens_aproximados_processados': int(len(rows_train) * int(t['num_train_epochs']) * max_length),
    }
    save_json(manifest_path, manifest)
    return True

def main() -> int:
    args = parse_args()
    cfg, paths_cfg, resolved_paths, runtime = resolve_runtime_config(args)

    train_count = count_jsonl(resolved_paths['train'])
    val_count = count_jsonl(resolved_paths['val'])
    estimates = estimate_steps(train_count, cfg)

    manifest = build_run_manifest('dry_run' if args.dry_run else 'initialized', cfg, runtime, resolved_paths, estimates)
    save_run_manifest(runtime, manifest)

    print('=' * 72)
    print('TREINAMENTO PARAMETRIZADO (MULTI-FINE-TUNING v1)')
    print('=' * 72)
    print(f"Repo: {runtime['repo_root']}")
    print(f"Experiment: {runtime['experiment_id']}")
    print(f"Run: {runtime['run_name']}")
    print(f"Train config: {runtime['train_config_path']}")
    print(f"Train path: {resolved_paths['train']} ({train_count} linhas)")
    print(f"Val path: {resolved_paths['val']} ({val_count} linhas)")
    print(f"Test path: {resolved_paths['test']}")
    print(f"Dataset manifest: {resolved_paths['dataset_manifest']}")
    print(f"Runs dir: {runtime['run_dir']}")
    print(f"Est. steps/epoch: {estimates['steps_per_epoch']} | Est. total steps: {estimates['estimated_total_steps']}")
    print('[INFO] output legado em finetune_mistral_wsl/output permanece preservado; novos runs são salvos em runs/.')

    if args.dry_run:
        manifest['status'] = 'dry_run_ok'
        manifest['end_time'] = datetime.utcnow().isoformat() + 'Z'
        manifest['hardware'] = collect_system_info()
        save_run_manifest(runtime, manifest)
        print('[OK] Dry-run concluído.')
        return 0

    try:
        ok = train(cfg, runtime, resolved_paths, args)
        return 0 if ok else 1
    except Exception as e:
        print(f'[ERRO] Falha no treinamento: {e}')
        traceback.print_exc()
        manifest_path = Path(runtime['meta_dir']) / 'run_manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest['status'] = 'failed'
        manifest['end_time'] = datetime.utcnow().isoformat() + 'Z'
        manifest['error'] = {'type': type(e).__name__, 'message': str(e)}
        save_json(manifest_path, manifest)
        return 1
    finally:
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        gc.collect()

if __name__ == '__main__':
    raise SystemExit(main())
