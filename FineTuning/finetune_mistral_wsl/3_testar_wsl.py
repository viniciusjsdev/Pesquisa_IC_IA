#!/usr/bin/env python3
"""Teste manual/qualitativo (demo) para modelo base e LoRA, com CLI parametrizada."""
from __future__ import annotations

import argparse
import gc
from pathlib import Path
from typing import Optional

from common.config_utils import load_paths_config, nested_get

class TestadorModeloWSL:
    def __init__(self, base_model: str, cache_dir: str | None, adapter_path: str | None):
        self.base_model = base_model
        self.cache_dir = cache_dir
        self.adapter_path = adapter_path
        self.model = None
        self.tokenizer = None

    def carregar_modelo(self, usar_lora: bool = False):
        from common.modeling import load_model, load_tokenizer
        print('\n' + '=' * 70)
        print(f"CARREGAMENTO ({'BASE+LORA' if usar_lora else 'BASE'})")
        print('=' * 70)
        adapter = self.adapter_path if usar_lora else None
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
            adapter_path=adapter,
            max_memory={0: '8GB', 'cpu': '20GB'},
        )
        print('[OK] Modelo carregado.')
        return True

    def liberar(self):
        self.model = None
        self.tokenizer = None
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        gc.collect()

    def _gerar(self, prompt: str, max_new_tokens: int = 256, temperature: float = 0.2):
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

    def construir_prompt(self, instruction: str, context: str) -> str:
        return f"### Instruction:\n{instruction}\n\n### Context:\n{context}\n\n### Response:"

    def teste_financeiro(self):
        instruction = "Analise a situação financeira da empresa e destaque saúde financeira, riscos e pontos fortes."
        context = (
            "Receita Líquida: R$ 45.2 bilhões\n"
            "EBITDA: R$ 8.7 bilhões\n"
            "Dívida Líquida: R$ 12.3 bilhões\n"
            "Patrimônio Líquido: R$ 28.9 bilhões"
        )
        return self._gerar(self.construir_prompt(instruction, context), max_new_tokens=350, temperature=0.1)

    def teste_industrial(self):
        instruction = "Explique como otimizar a eficiência energética em uma planta siderúrgica com recomendações priorizadas."
        context = (
            "A planta possui 3 fornos elétricos, 2 compressores de ar e sistema de refrigeração.\n"
            "Consumo atual: 2.5 GWh/mês\nMeta: Reduzir 15% do consumo"
        )
        return self._gerar(self.construir_prompt(instruction, context), max_new_tokens=350, temperature=0.1)

    def teste_integrado(self):
        instruction = "Analise o impacto financeiro de uma parada não programada de 8 horas em um alto-forno e sugira mitigação."
        context = (
            "Alto-forno: Produção 2.500 t/dia\n"
            "Custo operacional: R$ 1.200/t\n"
            "Receita: R$ 1.800/t\n"
            "Custo de parada: R$ 50.000/hora"
        )
        return self._gerar(self.construir_prompt(instruction, context), max_new_tokens=350, temperature=0.1)

    def executar_suite(self, usar_lora: bool, rotulo: str):
        self.carregar_modelo(usar_lora=usar_lora)
        print(f"\n=== TESTE FINANCEIRO ({rotulo}) ===")
        print(self.teste_financeiro())
        print(f"\n=== TESTE INDUSTRIAL ({rotulo}) ===")
        print(self.teste_industrial())
        print(f"\n=== TESTE INTEGRADO ({rotulo}) ===")
        print(self.teste_integrado())
        self.liberar()

def parse_args():
    p = argparse.ArgumentParser(description='Demo qualitativo base vs LoRA (script parametrizado)')
    p.add_argument('--adapter-path', default=None)
    p.add_argument('--cache-dir', default=None)
    p.add_argument('--base-model', default='mistralai/Mistral-7B-Instruct-v0.3')
    p.add_argument('--paths-config', default='configs/paths.local.yaml')
    p.add_argument('--mode', choices=['base', 'lora', 'compare', 'full'], default=None)
    return p.parse_args()

def menu_interativo() -> str:
    print("\n[MENU] Escolha o tipo de teste:")
    print("  1. Testar modelo base")
    print("  2. Testar modelo LoRA")
    print("  3. Comparar (suite base + suite LoRA)")
    print("  4. Teste completo (igual ao comparar)")
    opcao = input("\n[INPUT] Opcao (1-4): ").strip()
    return {'1': 'base', '2': 'lora', '3': 'compare', '4': 'full'}.get(opcao, 'compare')

def main() -> int:
    args = parse_args()
    paths_cfg = load_paths_config(args.paths_config)
    adapter_path = args.adapter_path or nested_get(paths_cfg, 'legacy.adapter_dir', None)
    cache_dir = args.cache_dir or nested_get(paths_cfg, 'hf.cache_dir', None)
    mode = args.mode or menu_interativo()

    tester = TestadorModeloWSL(args.base_model, cache_dir, adapter_path)
    print(f"[INFO] base_model={args.base_model}")
    print(f"[INFO] cache_dir={cache_dir}")
    print(f"[INFO] adapter_path={adapter_path}")
    print(f"[INFO] mode={mode}")

    if mode == 'base':
        tester.executar_suite(usar_lora=False, rotulo='BASE')
    elif mode == 'lora':
        if not adapter_path:
            raise SystemExit('Adapter path ausente. Use --adapter-path ou configure configs/paths.local.yaml')
        tester.executar_suite(usar_lora=True, rotulo='LORA')
    elif mode in {'compare', 'full'}:
        tester.executar_suite(usar_lora=False, rotulo='BASE')
        if not adapter_path:
            raise SystemExit('Adapter path ausente. Use --adapter-path ou configure configs/paths.local.yaml')
        tester.executar_suite(usar_lora=True, rotulo='LORA')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
