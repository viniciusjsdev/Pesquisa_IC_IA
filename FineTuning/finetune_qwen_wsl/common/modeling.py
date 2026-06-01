from pathlib import Path
from typing import Any, Dict, Optional

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

def _dtype_from_string(name: str | None):
    if not name:
        return torch.float16
    n = str(name).lower()
    if n in {'float16', 'fp16'}:
        return torch.float16
    if n in {'bfloat16', 'bf16'}:
        return torch.bfloat16
    return torch.float16

def load_tokenizer(base_model: str, cache_dir: str | None = None):
    tok = AutoTokenizer.from_pretrained(base_model, cache_dir=cache_dir, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = 'left'
    return tok

def load_model(base_model: str, cache_dir: str | None = None, qlora_cfg: Optional[Dict[str, Any]] = None, adapter_path: str | None = None, max_memory: Optional[Dict[Any, str]] = None):
    qcfg = None
    if qlora_cfg and qlora_cfg.get('load_in_4bit', True):
        qcfg = BitsAndBytesConfig(
            load_in_4bit=bool(qlora_cfg.get('load_in_4bit', True)),
            bnb_4bit_quant_type=qlora_cfg.get('bnb_4bit_quant_type', 'nf4'),
            bnb_4bit_use_double_quant=bool(qlora_cfg.get('bnb_4bit_use_double_quant', True)),
            bnb_4bit_compute_dtype=_dtype_from_string(qlora_cfg.get('bnb_4bit_compute_dtype', 'float16')),
        )
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        cache_dir=cache_dir,
        quantization_config=qcfg,
        device_map='auto',
        max_memory=max_memory,
        torch_dtype=_dtype_from_string((qlora_cfg or {}).get('bnb_4bit_compute_dtype', 'float16')),
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    if adapter_path:
        ap = Path(adapter_path)
        if not ap.exists():
            raise FileNotFoundError(f'Adapter não encontrado: {ap}')
        model = PeftModel.from_pretrained(model, str(ap), torch_dtype=torch.float16)
    model.eval()
    return model

def generate_answer(model, tokenizer, prompt: str, max_new_tokens: int = 128, temperature: float = 0.0, top_p: float = 0.9, top_k: int = 50, do_sample: bool = False, repetition_penalty: float = 1.0, max_input_length: int = 1024) -> str:
    inputs = tokenizer(prompt, return_tensors='pt', truncation=True, max_length=max_input_length)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    input_len = inputs['input_ids'].shape[1]
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            do_sample=do_sample,
            repetition_penalty=repetition_penalty,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True).strip()

def generate_answers_batch(model, tokenizer, prompts: list[str], max_new_tokens: int = 128, temperature: float = 0.0, top_p: float = 0.9, top_k: int = 50, do_sample: bool = False, repetition_penalty: float = 1.0, max_input_length: int = 1024) -> list[str]:
    if not prompts:
        return []
    inputs = tokenizer(
        prompts,
        return_tensors='pt',
        truncation=True,
        max_length=max_input_length,
        padding=True,
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    prompt_width = inputs['input_ids'].shape[1]
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            do_sample=do_sample,
            repetition_penalty=repetition_penalty,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    return [
        tokenizer.decode(output[prompt_width:], skip_special_tokens=True).strip()
        for output in outputs
    ]
