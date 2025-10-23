#!/usr/bin/env python3
"""
TREINAMENTO MISTRAL-7B COM LORA (WSL OTIMIZADO)
===============================================
Script otimizado para treinamento no WSL com melhor gerenciamento de VRAM
"""

import os
import sys
import json
import torch
import gc
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import numpy as np
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    TrainingArguments, Trainer, DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from datasets import Dataset, load_dataset
from transformers.trainer_callback import TrainerCallback

def safe_format(value, format_str=".4f"):
    """Formata valor de forma segura, tratando strings"""
    if isinstance(value, (int, float)) and value != "N/A":
        return f"{value:{format_str}}"
    else:
        return str(value)

class WSLTrainingCallback(TrainerCallback):
    """Callback otimizado para WSL com logging detalhado"""
    
    def __init__(self, log_file="training_log_wsl.txt"):
        self.log_file = log_file
        self.start_time = datetime.now()
        self.log_hyperparameters()
    
    def log_hyperparameters(self):
        """Log das configurações iniciais"""
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write("=== CONFIGURAÇÕES DE TREINAMENTO WSL ===\n")
            f.write(f"Data: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}\n")
            f.write(f"VRAM Total: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB\n")
            f.write(f"PyTorch: {torch.__version__}\n")
            f.write(f"CUDA: {torch.version.cuda}\n")
            f.write("=" * 50 + "\n\n")
    
    def on_log(self, args, state, control, logs=None, **kwargs):
        """Log detalhado durante treinamento"""
        if logs is None:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # VRAM usage
        if torch.cuda.is_available():
            vram_allocated = torch.cuda.memory_allocated(0) / 1024**3
            vram_reserved = torch.cuda.memory_reserved(0) / 1024**3
            vram_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            vram_free = vram_total - vram_allocated
        else:
            vram_allocated = vram_reserved = vram_total = vram_free = 0
        
        # CPU e RAM
        cpu_percent = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent
        
        # Gradient norm (se disponível)
        grad_norm = logs.get("grad_norm", "N/A")
        
        # Learning rate
        lr = logs.get("learning_rate", "N/A")
        
        # Loss
        train_loss = logs.get("train_loss", "N/A")
        eval_loss = logs.get("eval_loss", "N/A")
        
        # Log formatado - CORRIGIDO para evitar erro de formatação
        log_line = (
            f"[{timestamp}] "
            f"Step: {state.global_step}, "
            f"Epoch: {safe_format(state.epoch, '.2f')}, "
            f"Train Loss: {safe_format(train_loss)}, "
            f"Eval Loss: {safe_format(eval_loss)}, "
            f"LR: {safe_format(lr, '.2e')}, "
            f"Grad Norm: {safe_format(grad_norm)}, "
            f"VRAM: {safe_format(vram_allocated, '.2f')}/{safe_format(vram_total, '.2f')}GB "
            f"({safe_format(vram_free, '.2f')}GB free), "
            f"CPU: {safe_format(cpu_percent, '.1f')}%, "
            f"RAM: {safe_format(ram_percent, '.1f')}%\n"
        )
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
        
        # Log no console a cada 10 steps
        if state.global_step % 10 == 0:
            print(f"Step {state.global_step}: Loss={safe_format(train_loss)}, VRAM={safe_format(vram_allocated, '.2f')}GB")

def carregar_dados_wsl():
    """Carrega dados originais completos para WSL - CARREGAMENTO MANUAL"""
    print("=== CARREGAMENTO DE DADOS ORIGINAIS COMPLETOS WSL ===")
    
    data_files = [
        "/mnt/e/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/Datasets/data_ft/train.jsonl",
        "/mnt/e/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/Datasets/data_ft/val.jsonl",
        "/mnt/e/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/Datasets/data_ft/test.jsonl"
    ]
    
    # Verifica se arquivos existem
    for file_path in data_files:
        if not Path(file_path).exists():
            print(f"ERRO: Arquivo não encontrado: {file_path}")
            return None
    
    try:
        # Carregamento manual para evitar problemas de schema
        def load_jsonl_manual(file_path):
            data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
            return data
        
        # Carrega dados manualmente
        print("Carregando dados manualmente...")
        train_data = load_jsonl_manual(data_files[0])
        val_data = load_jsonl_manual(data_files[1])
        test_data = load_jsonl_manual(data_files[2])
        
        # VALIDAÇÕES ROBUSTAS
        if not train_data:
            raise ValueError("ERRO: Dataset de treino está vazio")
        if not val_data:
            raise ValueError("ERRO: Dataset de validação está vazio")
        if not test_data:
            raise ValueError("ERRO: Dataset de teste está vazio")
        
        # Validar estrutura dos dados
        sample = train_data[0]
        required_fields = ['prompt', 'resposta']
        for field in required_fields:
            if field not in sample:
                raise ValueError(f"ERRO: Campo obrigatório '{field}' não encontrado nos dados")
        
        # Cria datasets usando Dataset.from_list()
        datasets = {
            "train": Dataset.from_list(train_data),
            "validation": Dataset.from_list(val_data),
            "test": Dataset.from_list(test_data)
        }
        
        print(f"SUCESSO: Dados ORIGINAIS carregados manualmente:")
        print(f"  - Train: {len(datasets['train'])} exemplos COMPLETOS")
        print(f"  - Validation: {len(datasets['validation'])} exemplos COMPLETOS")
        print(f"  - Test: {len(datasets['test'])} exemplos COMPLETOS")
        print("QUALIDADE: Dados originais preservados integralmente")
        print("SUCESSO: CARREGAMENTO MANUAL: Evitando erros de schema")
        
        return datasets
        
    except Exception as e:
        print(f"\nERRO AO CARREGAR DADOS:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        print(f"\nPOSSÍVEIS SOLUÇÕES:")
        print("   1. Verificar se arquivos existem nos caminhos corretos")
        print("   2. Verificar se arquivos não estão corrompidos")
        print("   3. Verificar se estrutura JSON está correta")
        print("   4. Verificar permissões de leitura dos arquivos")
        import traceback
        traceback.print_exc()
        return None

def configurar_modelo_wsl():
    """Configura modelo otimizado para WSL"""
    print("\n=== CONFIGURAÇÃO DO MODELO WSL ===")
    
    # Configurações de quantização 4-bit otimizadas
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )
    
    # Carrega tokenizer ORIGINAL do Mistral (100% performance)
    print("Carregando tokenizer...")
    print("Carregando tokenizer Mistral original (100% performance)...")
    tokenizer = AutoTokenizer.from_pretrained(
        "mistralai/Mistral-7B-Instruct-v0.3",
        use_fast=False,  # Usar tokenizer lento (mais estável)
        trust_remote_code=True
    )
    print("SUCESSO: Tokenizer Mistral original carregado (100% performance)")
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Carrega modelo com quantização SIMPLIFICADA
    print("Carregando modelo com quantização 4-bit e CPU offloading...")
    try:
        # Usar modelo do Hub (mais estável)
        model = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.3",
            quantization_config=quantization_config,
            device_map="auto",
            max_memory={0: "10GB", "cpu": "30GB"},  # CPU offloading otimizado para dados completos
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        print("SUCESSO: Modelo carregado do Hub")
    except Exception as e:
        print(f"ERRO: Erro ao carregar modelo: {e}")
        print("Tentando sem quantização...")
        try:
            # Fallback sem quantização
            model = AutoModelForCausalLM.from_pretrained(
                "mistralai/Mistral-7B-Instruct-v0.3",
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True
            )
            print("SUCESSO: Modelo carregado sem quantização")
        except Exception as e2:
            print(f"ERRO: Erro final: {e2}")
            raise e2
    
    # Configuração LoRA otimizada para WSL (baseada no arquivo original)
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,                    # Rank do adapter (8-32) - aumentado para melhor performance
        lora_alpha=32,           # Scaling factor (2x rank)
        lora_dropout=0.1,        # Dropout para regularização
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
            "gate_proj", "up_proj", "down_proj"       # MLP
        ],
        bias="none",
        inference_mode=False
    )
    
    # Aplica LoRA
    model = get_peft_model(model, lora_config)
    
    # CORREÇÃO CRÍTICA: Habilitar gradientes para treinamento
    print("Habilitando gradientes para treinamento...")
    model.train()  # Habilita modo de treinamento
    model.enable_input_require_grads()  # Habilita gradientes
    
    # Validar parâmetros treináveis
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    
    print(f"SUCESSO: Modelo configurado:")
    print(f"  - Parâmetros treináveis: {trainable_params:,} ({safe_format(100 * trainable_params / total_params, '.2f')}%)")
    print(f"  - Total de parâmetros: {total_params:,}")
    print(f"  - LoRA r={lora_config.r}, alpha={lora_config.lora_alpha}")
    print(f"  - Gradientes habilitados: {model.training}")
    
    return model, tokenizer

def treinar_modelo_wsl():
    """Função principal de treinamento WSL"""
    print("TREINAMENTO MISTRAL-7B COM LORA (WSL OTIMIZADO)")
    print("=" * 60)
    
    # Limpa cache CUDA
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()
    
    # 1. Carrega dados
    datasets = carregar_dados_wsl()
    if datasets is None:
        return False
    
    # 2. Configura modelo
    model, tokenizer = configurar_modelo_wsl()
    
    # 3. Prepara dados - CORRIGIDO para estrutura correta
    def tokenize_function(examples):
        # Combinar prompt + resposta para formar texto completo
        texts = []
        for i in range(len(examples["prompt"])):
            # Combina prompt + resposta com separador
            full_text = examples["prompt"][i] + " " + examples["resposta"][i]
            texts.append(full_text)
        
        return tokenizer(
            texts,  # Usar textos combinados
            truncation=True,
            padding=True,
            max_length=1024,  # Aumentado para dados completos
            return_tensors="pt"
        )
    
    print("\n=== TOKENIZAÇÃO ===")
    print("SUCESSO: CORREÇÃO APLICADA: Combinando prompt + resposta")
    print("Estrutura: prompt + ' ' + resposta")
    print("Preservando dados originais completos")
    
    # Tokenizar cada dataset individualmente (CORREÇÃO DO ERRO)
    print("Tokenizando dataset de treino...")
    tokenized_train = datasets["train"].map(
        tokenize_function,
        batched=True,
        remove_columns=datasets["train"].column_names
    )
    
    print("Tokenizando dataset de validação...")
    tokenized_validation = datasets["validation"].map(
        tokenize_function,
        batched=True,
        remove_columns=datasets["validation"].column_names
    )
    
    # Criar dicionário tokenizado
    tokenized_datasets = {
        "train": tokenized_train,
        "validation": tokenized_validation
    }
    
    print("SUCESSO: Tokenização concluída:")
    print(f"  - Train: {len(tokenized_train)} exemplos")
    print(f"  - Validation: {len(tokenized_validation)} exemplos")
    
    # 4. Configurações de treinamento otimizadas para WSL
    training_args = TrainingArguments(
        output_dir="/mnt/e/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/Datasets/finetune_mistral_wsl/output",
        num_train_epochs=3,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=32,  # Otimizado para dados completos
        warmup_steps=100,
        learning_rate=2e-4,
        weight_decay=0.01,
        logging_steps=5,
        eval_strategy="steps",
        eval_steps=50,
        save_steps=100,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=True,
        gradient_checkpointing=True,
        dataloader_pin_memory=False,
        dataloader_num_workers=0,
        remove_unused_columns=False,
        report_to=None,  # Desabilita wandb/tensorboard
        seed=42
    )
    
    # 5. Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    
    # 6. Callback de logging
    logging_callback = WSLTrainingCallback()
    
    # 7. Validações robustas antes do treinamento
    print("\n=== VALIDAÇÕES PRÉ-TREINAMENTO ===")
    
    # Validar datasets tokenizados
    if not isinstance(tokenized_datasets, dict):
        raise ValueError("ERRO: tokenized_datasets deve ser um dicionário")
    
    if "train" not in tokenized_datasets:
        raise ValueError("ERRO: Dataset de treino não encontrado")
    
    if "validation" not in tokenized_datasets:
        raise ValueError("ERRO: Dataset de validação não encontrado")
    
    print(f"SUCESSO: Train dataset: {len(tokenized_datasets['train'])} exemplos")
    print(f"SUCESSO: Validation dataset: {len(tokenized_datasets['validation'])} exemplos")
    
    # Validar tokenizer
    if tokenizer is None:
        raise ValueError("ERRO: Tokenizer não foi carregado")
    
    print(f"SUCESSO: Tokenizer: {type(tokenizer).__name__}")
    
    # Validar modelo
    if model is None:
        raise ValueError("ERRO: Modelo não foi carregado")
    
    print(f"SUCESSO: Modelo: {type(model).__name__}")
    
    # VALIDAÇÕES ADICIONAIS DO MODELO
    print("\n=== VALIDAÇÕES DO MODELO ===")
    
    # Verificar se modelo está em modo de treinamento
    if not model.training:
        print("AVISO: Modelo não está em modo de treinamento - corrigindo...")
        model.train()
    
    # Verificar parâmetros treináveis
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    
    if trainable_params == 0:
        raise ValueError("ERRO: Nenhum parâmetro está configurado para treinamento!")
    
    print(f"SUCESSO: Parâmetros treináveis: {trainable_params:,} ({safe_format(100 * trainable_params / total_params, '.2f')}%)")
    print(f"SUCESSO: Modo de treinamento: {model.training}")
    
    # Verificar se LoRA está configurado
    if hasattr(model, 'peft_config'):
        print("SUCESSO: LoRA configurado corretamente")
        for adapter_name, config in model.peft_config.items():
            print(f"  - Adapter: {adapter_name}")
            print(f"  - Rank: {config.r}")
            print(f"  - Alpha: {config.lora_alpha}")
    else:
        print("AVISO: LoRA não detectado - pode causar problemas")
    
    # 8. Trainer
    print("\n=== CONFIGURAÇÃO DO TRAINER ===")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        data_collator=data_collator,
        callbacks=[logging_callback]
    )
    
    print("SUCESSO: Trainer configurado com sucesso")
    
    # 8. Treinamento
    print("\n=== INICIANDO TREINAMENTO WSL ===")
    print("Tempo estimado: 2-4 horas")
    print("Monitoramento: tail -f training_log_wsl.txt")
    
    try:
        trainer.train()
        
        # Salva modelo final
        trainer.save_model()
        tokenizer.save_pretrained(training_args.output_dir)
        
        print("\nTREINAMENTO CONCLUÍDO!")
        print(f"Modelo salvo em: {training_args.output_dir}")
        
        return True
        
    except Exception as e:
        print(f"\nERRO DURANTE TREINAMENTO:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        print(f"\nPOSSÍVEIS SOLUÇÕES:")
        print("   1. Verificar se todos os datasets foram carregados")
        print("   2. Verificar se tokenizer está funcionando")
        print("   3. Verificar se modelo foi carregado corretamente")
        print("   4. Verificar espaço em disco disponível")
        print("   5. Verificar se CUDA está funcionando")
        return False
    
    finally:
        # Limpa memória
        torch.cuda.empty_cache()
        gc.collect()

def main():
    """Função principal"""
    success = treinar_modelo_wsl()
    
    if success:
        print("\nTREINAMENTO WSL CONCLUÍDO COM SUCESSO!")
        print("\nPRÓXIMOS PASSOS:")
        print("1. Execute: python 3_testar_wsl.py")
        print("2. Execute: python 4_inferencia_wsl.py")
    else:
        print("\nTreinamento falhou!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
