#!/usr/bin/env python3
"""Inferência interativa parametrizada para base/LoRA (WSL)."""
from __future__ import annotations

import argparse
import gc
from pathlib import Path

from common.config_utils import load_paths_config, nested_get

class InferenciaWSL:
    def __init__(self, model_path: str, adapter_path: str | None, cache_dir: str | None, usar_adapter: bool = True):
        self.base_model = model_path
        self.adapter_path = adapter_path if usar_adapter else None
        self.cache_dir = cache_dir
        self.model = None
        self.tokenizer = None

    def carregar(self):
        from common.modeling import load_model, load_tokenizer
        self.tokenizer = load_tokenizer(self.base_model, cache_dir=self.cache_dir)
        self.model = load_model(
            self.base_model,
            cache_dir=self.cache_dir,
            qlora_cfg={
                'load_in_4bit': True,
                'bnb_4bit_quant_type': 'nf4',
                'bnb_4bit_use_double_quant': True,
                'bnb_4bit_compute_dtype': 'float16',
            },
            adapter_path=self.adapter_path,
            max_memory={0: '8GB', 'cpu': '20GB'},
        )
        print('[OK] Modelo carregado para inferência.')

    def descarregar(self):
        self.model = None
        self.tokenizer = None
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        gc.collect()

    def gerar(self, prompt: str, max_new_tokens: int = 256, temperature: float = 0.2) -> str:
        from common.modeling import generate_answer
        return generate_answer(
            self.model,
            self.tokenizer,
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            top_p=0.9,
            top_k=50,
            repetition_penalty=1.05,
            max_input_length=1024,
        )

    def prompt_instruct(self, pergunta: str, contexto: str = '') -> str:
        return f"### Instruction:\n{pergunta}\n\n### Context:\n{contexto or 'Sem contexto adicional.'}\n\n### Response:"

    def modo_interativo(self, max_new_tokens: int, temperature: float):
        print('\n' + '=' * 70)
        print('MODO INTERATIVO - MISTRAL (BASE/LoRA)')
        print('=' * 70)
        print("Comandos: /financeiro, /industrial, /integrado, /sair")
        while True:
            entrada = input('\n[VOCE] ').strip()
            if entrada.lower() in {'/sair', 'sair', 'exit', 'quit'}:
                break
            if not entrada:
                continue
            if entrada.startswith('/financeiro '):
                pergunta = entrada[len('/financeiro '):].strip()
                contexto = 'Responda como analista financeiro e destaque riscos e indicadores.'
            elif entrada.startswith('/industrial '):
                pergunta = entrada[len('/industrial '):].strip()
                contexto = 'Responda como especialista industrial com ações priorizadas.'
            elif entrada.startswith('/integrado '):
                pergunta = entrada[len('/integrado '):].strip()
                contexto = 'Integre aspectos financeiros e operacionais.'
            else:
                pergunta = entrada
                contexto = ''
            prompt = self.prompt_instruct(pergunta, contexto)
            resp = self.gerar(prompt, max_new_tokens=max_new_tokens, temperature=temperature)
            print('\n[MODELO]')
            print(resp)

def parse_args():
    p = argparse.ArgumentParser(description='Inferência interativa parametrizada (base/LoRA)')
    p.add_argument('--model-path', default='Qwen/Qwen2.5-7B-Instruct')
    p.add_argument('--adapter-path', default=None)
    p.add_argument('--cache-dir', default=None)
    p.add_argument('--paths-config', default='configs/paths.local.yaml')
    p.add_argument('--no-adapter', action='store_true')
    p.add_argument('--prompt', default=None, help='Prompt bruto único (sem modo interativo)')
    p.add_argument('--pergunta', default=None, help='Pergunta para template Instruct')
    p.add_argument('--contexto', default='', help='Contexto para template Instruct')
    p.add_argument('--max-new-tokens', type=int, default=256)
    p.add_argument('--temperature', type=float, default=0.2)
    return p.parse_args()

def main() -> int:
    args = parse_args()
    paths_cfg = load_paths_config(args.paths_config)
    cache_dir = args.cache_dir or nested_get(paths_cfg, 'hf.cache_dir', None)
    adapter_path = args.adapter_path or nested_get(paths_cfg, 'legacy.adapter_dir', None)
    infer = InferenciaWSL(args.model_path, adapter_path, cache_dir, usar_adapter=not args.no_adapter)
    print(f"[INFO] base_model={args.model_path}")
    print(f"[INFO] cache_dir={cache_dir}")
    print(f"[INFO] adapter_path={(None if args.no_adapter else adapter_path)}")
    infer.carregar()
    try:
        if args.prompt:
            print(infer.gerar(args.prompt, max_new_tokens=args.max_new_tokens, temperature=args.temperature))
        elif args.pergunta:
            prompt = infer.prompt_instruct(args.pergunta, args.contexto)
            print(infer.gerar(prompt, max_new_tokens=args.max_new_tokens, temperature=args.temperature))
        else:
            infer.modo_interativo(max_new_tokens=args.max_new_tokens, temperature=args.temperature)
    finally:
        infer.descarregar()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
