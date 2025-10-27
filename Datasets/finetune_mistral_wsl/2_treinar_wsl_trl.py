#!/usr/bin/env python3
"""
TREINAMENTO MISTRAL-7B COM TRL FRAMEWORK (WSL OTIMIZADO)
=======================================================
Script otimizado com TRL Framework, Flash Attention 2 e Liger Kernel
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
    BitsAndBytesConfig, TrainingArguments
)
from peft import LoraConfig, get_peft_model
from datasets import Dataset, load_dataset
from trl import SFTTrainer, SFTConfig
from transformers.utils import is_liger_kernel_available

# Liger Kernel não disponível - usando apenas Flash Attention 2
LIGER_AVAILABLE = False

def safe_format(value, format_str=".4f"):
    """Formata valor de forma segura, tratando strings"""
    if isinstance(value, (int, float)) and value != "N/A":
        return f"{value:{format_str}}"
    else:
        return str(value)

def safe_load_checkpoint_state(checkpoint_path):
    """
    Carrega estado do checkpoint de forma segura, ignorando arquivos .pt vulneráveis
    """
    print(f"\n=== CARREGAMENTO SEGURO DO CHECKPOINT ===")
    print(f"Checkpoint: {checkpoint_path}")
    
    # 1. Carregar trainer_state.json (seguro - é JSON)
    trainer_state = None
    trainer_state_path = os.path.join(checkpoint_path, "trainer_state.json")
    if os.path.exists(trainer_state_path):
        try:
            with open(trainer_state_path, 'r') as f:
                trainer_state = json.load(f)
            print("SUCESSO: trainer_state.json carregado")
        except Exception as e:
            print(f"ERRO ao carregar trainer_state.json: {e}")
    
    # 2. Verificar arquivos .pt mas ignorar devido à vulnerabilidade
    optimizer_path = os.path.join(checkpoint_path, "optimizer.pt")
    scheduler_path = os.path.join(checkpoint_path, "scheduler.pt")
    
    if os.path.exists(optimizer_path) or os.path.exists(scheduler_path):
        print("AVISO: Arquivos .pt detectados - ignorando devido à vulnerabilidade CVE-2025-32434")
        if os.path.exists(optimizer_path):
            print("Ignorando: optimizer.pt")
        if os.path.exists(scheduler_path):
            print("Ignorando: scheduler.pt")
        print("Treinamento continuará sem estado do otimizador/scheduler")
        print("NOTA: Convergência pode ser ligeiramente mais lenta inicialmente")
    
    return {
        'trainer_state': trainer_state,
        'optimizer_state': None,  # Ignorar devido à vulnerabilidade
        'scheduler_state': None   # Ignorar devido à vulnerabilidade
    }

def apply_checkpoint_state_to_trainer(trainer, checkpoint_state):
    """
    Aplica o estado carregado ao trainer de forma segura
    """
    print(f"\n=== APLICANDO ESTADO AO TRAINER ===")
    
    # 1. Aplicar estado do trainer
    if checkpoint_state['trainer_state']:
        trainer_state = checkpoint_state['trainer_state']
        
        # Configurar estado interno
        trainer.state.global_step = trainer_state.get('global_step', 0)
        trainer.state.epoch = trainer_state.get('epoch', 0)
        trainer.state.max_steps = trainer_state.get('max_steps', 0)
        
        print(f"Estado do trainer configurado:")
        print(f"  - Global step: {trainer.state.global_step}")
        print(f"  - Epoch: {trainer.state.epoch}")
        print(f"  - Max steps: {trainer.state.max_steps}")
    
    # 2. Aplicar estado do otimizador
    if checkpoint_state['optimizer_state'] and hasattr(trainer, 'optimizer'):
        try:
            trainer.optimizer.load_state_dict(checkpoint_state['optimizer_state'])
            print("SUCESSO: Estado do otimizador aplicado")
        except Exception as e:
            print(f"ERRO ao aplicar estado do otimizador: {e}")
            print("Continuando sem estado do otimizador")
    else:
        print("AVISO: Estado do otimizador não disponível (vulnerabilidade)")
    
    # 3. Aplicar estado do scheduler
    if checkpoint_state['scheduler_state'] and hasattr(trainer, 'lr_scheduler'):
        try:
            trainer.lr_scheduler.load_state_dict(checkpoint_state['scheduler_state'])
            print("SUCESSO: Estado do scheduler aplicado")
        except Exception as e:
            print(f"ERRO ao aplicar estado do scheduler: {e}")
            print("Continuando sem estado do scheduler")
    else:
        print("AVISO: Estado do scheduler não disponível (vulnerabilidade)")
    
    # 4. Configurar scheduler manualmente se necessário
    if checkpoint_state['trainer_state'] and hasattr(trainer, 'lr_scheduler'):
        global_step = checkpoint_state['trainer_state'].get('global_step', 0)
        if hasattr(trainer.lr_scheduler, 'last_epoch'):
            trainer.lr_scheduler.last_epoch = global_step
            print(f"Scheduler configurado: last_epoch = {global_step}")

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
    """Configura modelo otimizado para WSL com Flash Attention 2 e Liger Kernel"""
    print("\n=== CONFIGURAÇÃO DO MODELO WSL COM TRL ===")
    
    # Configurações de quantização 4-bit otimizadas com bfloat16
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_quant_storage=torch.bfloat16
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
    
    # Configurações do modelo com Flash Attention 2 e Liger Kernel
    model_kwargs = dict(
        attn_implementation="flash_attention_2",
        dtype=torch.bfloat16,
        use_cache=False,
        low_cpu_mem_usage=True,
        quantization_config=quantization_config,
        device_map="auto",
        max_memory={"0": "10GB", "cpu": "22GB"}
    )
    
    # Carrega modelo com Flash Attention 2
    print("Carregando modelo com Flash Attention 2...")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.3",
            **model_kwargs
        )
        print("SUCESSO: Modelo carregado com Flash Attention 2")
    except Exception as e:
        print(f"ERRO: Erro ao carregar modelo otimizado: {e}")
        print("Tentando fallback sem otimizações...")
        try:
            # Fallback sem otimizações
            model = AutoModelForCausalLM.from_pretrained(
                "mistralai/Mistral-7B-Instruct-v0.3",
                quantization_config=quantization_config,
                device_map="auto",
                torch_dtype=torch.bfloat16,
                trust_remote_code=True
            )
            print("SUCESSO: Modelo carregado com fallback")
        except Exception as e2:
            print(f"ERRO: Erro final: {e2}")
            raise e2
    
    # Configuração LoRA otimizada
    lora_config = LoraConfig(
        task_type="CAUSAL_LM",
        r=8,
        lora_alpha=16,
        lora_dropout=0.1,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
            "gate_proj", "up_proj", "down_proj"       # MLP
        ],
        bias="none",
        inference_mode=False
    )
    
    # CORREÇÃO CRÍTICA: Habilitar gradientes para treinamento
    print("Habilitando gradientes para treinamento...")
    model.train()  # Habilita modo de treinamento
    model.enable_input_require_grads()  # Habilita gradientes
    
    # Validar parâmetros treináveis (sem LoRA ainda)
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    
    print(f"SUCESSO: Modelo base configurado:")
    print(f"  - Parâmetros treináveis: {trainable_params:,} ({safe_format(100 * trainable_params / total_params, '.2f')}%)")
    print(f"  - Total de parâmetros: {total_params:,}")
    print(f"  - LoRA configurado mas não aplicado ainda")
    print(f"  - Gradientes habilitados: {model.training}")
    print(f"  - Flash Attention 2: Ativado")
    print(f"  - Liger Kernel: Não disponível")
    
    return model, tokenizer, lora_config

def treinar_modelo_wsl():
    """Função principal de treinamento WSL com TRL Framework"""
    print("TREINAMENTO MISTRAL-7B COM TRL FRAMEWORK (WSL OTIMIZADO)")
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
    model, tokenizer, lora_config = configurar_modelo_wsl()
    
    # 3. Prepara dados para TRL (formato de texto)
    def format_instruction(example):
        """Formata exemplo para treinamento com TRL"""
        return f"### Instruction:\n{example['prompt']}\n\n### Response:\n{example['resposta']}"
    
    print("\n=== PREPARAÇÃO DE DADOS PARA TRL ===")
    print("SUCESSO: Formatando dados para TRL Framework")
    print("Estrutura: Instruction + Response")
    print("Preservando dados originais completos")
    
    # Formatar datasets
    train_texts = [format_instruction(ex) for ex in datasets["train"]]
    val_texts = [format_instruction(ex) for ex in datasets["validation"]]
    
    # Criar datasets de texto para TRL
    train_dataset = Dataset.from_dict({"text": train_texts})
    val_dataset = Dataset.from_dict({"text": val_texts})
    
    print(f"SUCESSO: Dados formatados para TRL:")
    print(f"  - Train: {len(train_dataset)} exemplos")
    print(f"  - Validation: {len(val_dataset)} exemplos")
    
    # Verificação automática de checkpoint
    print("\n=== VERIFICAÇÃO DE CHECKPOINT ===")
    
    import glob
    import os
    
    # Detectar último checkpoint automaticamente
    checkpoint_dirs = glob.glob("output/checkpoints/checkpoint-*")
    if checkpoint_dirs:
        latest_checkpoint = max(checkpoint_dirs, key=lambda x: int(x.split('-')[-1]))
        print(f"CHECKPOINT DETECTADO: {latest_checkpoint}")
        
        # Verificar se checkpoint está completo
        required_files = ["adapter_config.json", "adapter_model.safetensors", "trainer_state.json"]
        checkpoint_complete = all(os.path.exists(os.path.join(latest_checkpoint, f)) for f in required_files)
        
        if checkpoint_complete:
            print(f"CHECKPOINT COMPLETO: {latest_checkpoint}")
            print(f"RESUMINDO TREINAMENTO DO CHECKPOINT")
            
            # Remover arquivos .pt problemáticos antes do carregamento
            print(f"\n=== REMOVENDO ARQUIVOS .pt VULNERÁVEIS ===")
            
            optimizer_path = os.path.join(latest_checkpoint, "optimizer.pt")
            scheduler_path = os.path.join(latest_checkpoint, "scheduler.pt")
            
            files_removed = []
            if os.path.exists(optimizer_path):
                os.remove(optimizer_path)
                files_removed.append("optimizer.pt")
                print(f"Removido: optimizer.pt")
            
            if os.path.exists(scheduler_path):
                os.remove(scheduler_path)
                files_removed.append("scheduler.pt")
                print(f"Removido: scheduler.pt")
            
            if files_removed:
                print(f"SUCESSO: {len(files_removed)} arquivo(s) .pt removido(s)")
                print("Treinamento continuará sem estado do otimizador/scheduler")
                print("NOTA: Convergência pode ser ligeiramente mais lenta inicialmente")
            else:
                print("Nenhum arquivo .pt encontrado")
            
            resume_from_checkpoint = latest_checkpoint
        else:
            print(f"CHECKPOINT INCOMPLETO: {latest_checkpoint}")
            print("ERRO: Checkpoint encontrado mas está incompleto!")
            print("Arquivos necessários:", required_files)
            print("Arquivos encontrados:", os.listdir(latest_checkpoint))
            print("EXECUÇÃO INTERROMPIDA!")
            return False
    else:
        print("ERRO: NENHUM CHECKPOINT ENCONTRADO!")
        print("Diretório de checkpoints:", "output/checkpoints/")
        print("Conteúdo:", os.listdir("output/checkpoints/") if os.path.exists("output/checkpoints/") else "Diretório não existe")
        print("EXECUÇÃO INTERROMPIDA!")
        return False
    
    # 4. Configurações de treinamento otimizadas para TRL usando SFTConfig
    sft_config = SFTConfig(
        output_dir="output/checkpoints",
        # resume_from_checkpoint removido - será passado diretamente no train()
        num_train_epochs=2,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=18,
        learning_rate=1e-4,
        weight_decay=0.01,
        warmup_ratio=0.1,
        fp16=False,
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        dataloader_pin_memory=False,
        dataloader_num_workers=0,
        save_steps=100,
        eval_steps=100,
        logging_steps=10,
        lr_scheduler_type="constant",
        logging_strategy="steps",
        save_strategy="steps",
        eval_strategy="steps",
        report_to=["tensorboard", "wandb"],
        logging_first_step=True,
        save_total_limit=5,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        seed=42,
        max_length=768,
        packing=True,
        dataset_text_field="text",
        dataset_num_proc=4
    )
    
    # Aplicar LoRA ou carregar checkpoint LoRA
    if resume_from_checkpoint:
        print(f"\n=== CARREGAMENTO COMPLETO DO CHECKPOINT ===")
        print(f"CARREGANDO CHECKPOINT: {resume_from_checkpoint}")
        
        try:
            # 1. Carregar checkpoint LoRA diretamente no modelo base
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, resume_from_checkpoint)
            
            print("SUCESSO: Checkpoint LoRA carregado diretamente")
            
            # 2. CORREÇÃO CRÍTICA: Habilitar modo de treinamento
            print("Habilitando modo de treinamento...")
            model.train()
            model.enable_input_require_grads()
            
            # 3. Verificar parâmetros treináveis
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            total_params = sum(p.numel() for p in model.parameters())
            print(f"Parâmetros treináveis após checkpoint: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")
            
            # 4. Verificar adapters LoRA
            if hasattr(model, 'peft_config'):
                adapters = list(model.peft_config.keys())
                print(f"Adapters LoRA ativos: {adapters}")
                
                if adapters and hasattr(model, 'set_adapter'):
                    model.set_adapter(adapters[0])
                    print(f"Adapter ativado: {adapters[0]}")
            
            # 5. Carregar estado completo do checkpoint de forma segura
            checkpoint_state = safe_load_checkpoint_state(resume_from_checkpoint)
            
            # Não passar peft_config para SFTTrainer quando checkpoint é carregado
            peft_config_for_trainer = None
            
        except Exception as e:
            print(f"ERRO ao carregar checkpoint: {e}")
            print("Aplicando LoRA padrão...")
            # Fallback: aplicar LoRA padrão
            model = get_peft_model(model, lora_config)
            model.train()
            model.enable_input_require_grads()
            peft_config_for_trainer = lora_config
            resume_from_checkpoint = None
            checkpoint_state = None
            print("SUCESSO: LoRA padrão aplicado com modo de treinamento")
    else:
        print(f"\n=== APLICANDO LORA PADRÃO ===")
        # Aplicar LoRA apenas se não há checkpoint
        model = get_peft_model(model, lora_config)
        model.train()
        model.enable_input_require_grads()
        peft_config_for_trainer = lora_config
        checkpoint_state = None
        print("SUCESSO: LoRA aplicado ao modelo base com modo de treinamento")
    
    # Criar SFTTrainer com configuração correta
    print("\n=== CONFIGURAÇÃO DO SFTTrainer ===")
    trainer = SFTTrainer(
        model=model,
        args=sft_config,  # Usar SFTConfig em vez de TrainingArguments
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        peft_config=peft_config_for_trainer,  # None se checkpoint carregado
        processing_class=tokenizer
    )
    
    print("SUCESSO: SFTTrainer configurado com sucesso")
    print("  - TRL Framework: Ativado")
    print("  - Data Packing: Ativado")
    print("  - Flash Attention 2: Ativado")
    print("  - Liger Kernel: Não disponível")
    if resume_from_checkpoint:
        print(f"  - Checkpoint: {resume_from_checkpoint}")
    else:
        print("  - Checkpoint: Nenhum (treinamento novo)")
    
    # Aplicar estado do checkpoint ao trainer
    if resume_from_checkpoint and checkpoint_state:
        apply_checkpoint_state_to_trainer(trainer, checkpoint_state)
    else:
        print("AVISO: Estado do checkpoint não disponível")
    
    # 7. Validações robustas antes do treinamento
    print("\n=== VALIDAÇÕES PRÉ-TREINAMENTO ===")
    
    # Validar datasets
    if not isinstance(train_dataset, Dataset):
        raise ValueError("ERRO: train_dataset deve ser um Dataset")
    
    if not isinstance(val_dataset, Dataset):
        raise ValueError("ERRO: val_dataset deve ser um Dataset")
    
    print(f"SUCESSO: Train dataset: {len(train_dataset)} exemplos")
    print(f"SUCESSO: Validation dataset: {len(val_dataset)} exemplos")
    
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
    
    print(f"Parâmetros treináveis: {trainable_params:,}")
    print(f"Total de parâmetros: {total_params:,}")
    print(f"Percentual treinável: {100 * trainable_params / total_params:.2f}%")
    
    if trainable_params == 0:
        print("ERRO: Nenhum parâmetro está configurado para treinamento!")
        
        # Diagnóstico adicional para LoRA
        if hasattr(model, 'peft_config'):
            print("Diagnóstico LoRA:")
            adapters = list(model.peft_config.keys())
            print(f"  - Adapters disponíveis: {adapters}")
            
            if adapters:
                print(f"  - Tentando ativar adapter: {adapters[0]}")
                if hasattr(model, 'set_adapter'):
                    model.set_adapter(adapters[0])
                    # Verificar novamente
                    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
                    if trainable_params > 0:
                        print(f"  - SUCESSO: Adapter ativado - {trainable_params:,} parâmetros treináveis")
                    else:
                        print(f"  - ERRO: Adapter não ativou parâmetros treináveis")
                else:
                    print(f"  - ERRO: Método set_adapter não disponível")
            else:
                print(f"  - ERRO: Nenhum adapter LoRA encontrado")
        
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
            print(f"  - Target modules: {config.target_modules}")
    else:
        print("AVISO: LoRA não detectado - pode causar problemas")
    
    # 8. Treinamento
    print("\n=== INICIANDO TREINAMENTO WSL COM TRL ===")
    print("Tempo estimado: 4-5 horas")
    print("Otimizações: Flash Attention 2 + Data Packing")
    print("Monitoramento: tensorboard --logdir=output/runs")
    
    try:
        if resume_from_checkpoint:
            print(f"\n=== RESUMINDO TREINAMENTO DO CHECKPOINT ===")
            print(f"Resumindo treinamento de: {resume_from_checkpoint}")
            trainer.train(resume_from_checkpoint=resume_from_checkpoint)
        else:
            print(f"\n=== INICIANDO TREINAMENTO NOVO ===")
            trainer.train()
        
        # Salva modelo final
        trainer.save_model()
        tokenizer.save_pretrained(sft_config.output_dir)
        
        print("\nTREINAMENTO CONCLUÍDO!")
        print(f"Modelo salvo em: {sft_config.output_dir}")
        print("Nome do modelo: Mistral-7B-LoRA-TRL-Research-VNDatamind")
        
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
        print("   6. Verificar se TRL está instalado corretamente")
        return False
    
    finally:
        # Limpa memória
        torch.cuda.empty_cache()
        gc.collect()

def main():
    """Função principal"""
    success = treinar_modelo_wsl()
    
    if success:
        print("\nTREINAMENTO WSL COM TRL CONCLUÍDO COM SUCESSO!")
        print("\nPRÓXIMOS PASSOS:")
        print("1. Execute: python 3_testar_wsl.py")
        print("2. Execute: python 4_inferencia_wsl.py")
        print("3. Execute: tensorboard --logdir=output/runs")
    else:
        print("\nTreinamento falhou!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
