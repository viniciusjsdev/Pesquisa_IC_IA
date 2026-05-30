#!/usr/bin/env python3
"""
DOWNLOAD MISTRAL-7B-INSTRUCT-V0.3 (WSL OTIMIZADO)
==================================================
Script otimizado para download no WSL com melhor gerenciamento de memória
"""

import os
import sys
import torch
import shutil
import subprocess
from pathlib import Path
from huggingface_hub import snapshot_download
import gc

def verificar_gpu():
    """Verifica GPU e VRAM disponível"""
    print("=== VERIFICAÇÃO DE GPU ===")
    
    if not torch.cuda.is_available():
        print("❌ CUDA não disponível!")
        return False
    
    gpu_name = torch.cuda.get_device_name(0)
    vram_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
    
    print(f"GPU: {gpu_name}")
    print(f"VRAM: {vram_total:.2f} GB")
    
    if vram_total < 10:
        print("⚠️  VRAM limitada - usando quantização 4-bit")
        return "4bit"
    elif vram_total < 16:
        print("✅ VRAM adequada - usando quantização 8-bit")
        return "8bit"
    else:
        print("✅ VRAM excelente - sem quantização")
        return "none"

def limpar_cache_wsl():
    """Limpa cache do WSL de forma segura"""
    print("\n=== LIMPEZA DE CACHE WSL ===")
    
    cache_dir = Path(os.environ.get("HF_HOME", "/mnt/e/Qwen"))
    
    if cache_dir.exists():
        try:
            # Remove apenas arquivos .incomplete
            for file in cache_dir.rglob("*.incomplete"):
                try:
                    file.unlink()
                    print(f"Removido: {file}")
                except:
                    pass
            
            # Limpa cache do HuggingFace
            hf_cache = Path.home() / ".cache" / "huggingface"
            if hf_cache.exists():
                for file in hf_cache.rglob("*.incomplete"):
                    try:
                        file.unlink()
                    except:
                        pass
            
            print("✅ Cache limpo com sucesso")
        except Exception as e:
            print(f"⚠️  Erro ao limpar cache: {e}")
    else:
        print("✅ Cache já limpo")

def verificar_espaco_disco():
    """Verifica espaço em disco disponível"""
    print("\n=== VERIFICAÇÃO DE ESPAÇO ===")
    
    # Verifica espaço no disco E:
    try:
        stat = shutil.disk_usage('/mnt/e')
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        
        print(f"Espaço total: {total_gb:.1f} GB")
        print(f"Espaço livre: {free_gb:.1f} GB")
        
        if free_gb < 20:
            print("❌ Espaço insuficiente! Necessário pelo menos 20GB")
            return False
        
        print("✅ Espaço suficiente")
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar espaço: {e}")
        return False

def baixar_modelo_wsl():
    """Download otimizado para WSL"""
    print("\n=== DOWNLOAD WSL OTIMIZADO ===")
    
    # Configurações
    model_name = "Qwen/Qwen2.5-7B-Instruct"
    cache_dir = os.environ.get("HF_HOME", "/mnt/e/Qwen")
    
    print(f"Modelo: {model_name}")
    print(f"Cache: {cache_dir}")
    print("Executando no WSL - sem limitações NTFS!")
    
    try:
        # Configurações de download otimizadas
        download_config = {
            "cache_dir": cache_dir,
            "local_files_only": False,
            "resume_download": True,
            "force_download": False,
        }
        
        print("Iniciando download...")
        print("⏳ Isso pode levar 10-20 minutos...")
        
        # Download com progress bar
        model_path = snapshot_download(
            repo_id=model_name,
            **download_config
        )
        
        print(f"✅ Download concluído!")
        print(f"📁 Modelo salvo em: {model_path}")
        
        # Verifica arquivos baixados
        model_files = list(Path(model_path).glob("*"))
        print(f"📊 Arquivos baixados: {len(model_files)}")
        
        for file in model_files:
            if file.is_file():
                size_mb = file.stat().st_size / (1024**2)
                print(f"  - {file.name}: {size_mb:.1f} MB")
        
        return model_path
        
    except Exception as e:
        print(f"❌ Erro no download: {e}")
        return None

def configurar_ambiente_wsl():
    """Configura variáveis de ambiente para WSL"""
    print("\n=== CONFIGURAÇÃO WSL ===")
    
    # Variáveis de ambiente otimizadas
    env_vars = {
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
        "CUDA_VISIBLE_DEVICES": "0",
        "TOKENIZERS_PARALLELISM": "false",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "TRANSFORMERS_CACHE": os.environ.get("HF_HOME", "/mnt/e/Qwen"),
        "HF_HOME": os.environ.get("HF_HOME", "/mnt/e/Qwen")
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✅ {key}={value}")
    
    # Limpa cache CUDA
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("✅ Cache CUDA limpo")

def main():
    """Função principal"""
    print("DOWNLOAD DO MODELO MISTRAL-7B-INSTRUCT-V0.3 (WSL OTIMIZADO)")
    print("=" * 60)
    
    # 1. Verificar GPU
    gpu_status = verificar_gpu()
    if not gpu_status:
        print("❌ GPU não disponível!")
        return False
    
    # 2. Verificar espaço
    if not verificar_espaco_disco():
        return False
    
    # 3. Configurar ambiente
    configurar_ambiente_wsl()
    
    # 4. Limpar cache
    limpar_cache_wsl()
    
    # 5. Download
    model_path = baixar_modelo_wsl()
    
    if model_path:
        print("\n🎉 DOWNLOAD CONCLUÍDO COM SUCESSO!")
        print(f"📁 Caminho: {model_path}")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Execute: python 2_treinar_wsl.py")
        print("2. Monitore: tail -f training_log.txt")
        return True
    else:
        print("❌ Download falhou!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
