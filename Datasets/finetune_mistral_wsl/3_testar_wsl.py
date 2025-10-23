#!/usr/bin/env python3
"""
TESTE DO MODELO MISTRAL-7B TREINADO (WSL)
=========================================
Script para testar o modelo base e o modelo LoRA treinado
"""

import os
import sys
import torch
import gc
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

class TestadorModeloWSL:
    """Classe para testar modelos no WSL"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.base_model_path = "/mnt/e/Mistral/models--mistralai--Mistral-7B-Instruct-v0.3/snapshots"
        self.adapter_path = "/mnt/e/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/Datasets/finetune_mistral_wsl/output"
        
    def carregar_modelo(self, is_lora_model: bool = False):
        """Carrega modelo base ou LoRA"""
        print("=== CARREGAMENTO DO MODELO WSL ===")
        
        try:
            # Configuração de quantização 4-bit
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            
            # Carrega tokenizer
            print("Carregando tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_path,
                cache_dir="/mnt/e/Mistral"
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Carrega modelo base
            print("Carregando modelo base...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                cache_dir="/mnt/e/Mistral",
                quantization_config=quantization_config,
                device_map="auto",
                max_memory={0: "8GB", "cpu": "20GB"},
                torch_dtype=torch.float16,
                trust_remote_code=True
            )
            
            # Carrega LoRA se solicitado
            if is_lora_model:
                if Path(self.adapter_path).exists():
                    print(f"Carregando adapter LoRA de: {self.adapter_path}")
                    self.model = PeftModel.from_pretrained(self.model, self.adapter_path)
                else:
                    print("❌ Adapter LoRA não encontrado!")
                    return False
            
            print("✅ Modelo carregado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar modelo: {e}")
            return False
    
    def gerar_resposta(self, prompt: str, max_length: int = 512) -> str:
        """Gera resposta do modelo"""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response.replace(prompt, "").strip()
            
        except Exception as e:
            return f"Erro na geração: {e}"
    
    def testar_pergunta_financeira(self, model_name: str):
        """Testa pergunta financeira"""
        print(f"\n=== TESTE FINANCEIRO ({model_name}) ===")
        
        prompt = """### Instruction:
Analise a situação financeira da empresa Gerdau com base nos dados fornecidos.

### Context:
Receita Líquida: R$ 45.2 bilhões
EBITDA: R$ 8.7 bilhões
Dívida Líquida: R$ 12.3 bilhões
Patrimônio Líquido: R$ 28.9 bilhões

### Response:"""
        
        print("Pergunta:", prompt[:100] + "...")
        
        resposta = self.gerar_resposta(prompt)
        print(f"Resposta: {resposta}")
        
        return resposta
    
    def testar_pergunta_industrial(self, model_name: str):
        """Testa pergunta industrial"""
        print(f"\n=== TESTE INDUSTRIAL ({model_name}) ===")
        
        prompt = """### Instruction:
Explique como otimizar a eficiência energética em uma planta siderúrgica.

### Context:
A planta possui 3 fornos elétricos, 2 compressores de ar e sistema de refrigeração.
Consumo atual: 2.5 GWh/mês
Meta: Reduzir 15% do consumo

### Response:"""
        
        print("Pergunta:", prompt[:100] + "...")
        
        resposta = self.gerar_resposta(prompt)
        print(f"Resposta: {resposta}")
        
        return resposta
    
    def testar_pergunta_integrada(self, model_name: str):
        """Testa pergunta integrada financeiro-industrial"""
        print(f"\n=== TESTE INTEGRADO ({model_name}) ===")
        
        prompt = """### Instruction:
Analise o impacto financeiro de uma parada não programada de 8 horas em um alto-forno.

### Context:
Alto-forno: Produção 2.500 t/dia
Custo operacional: R$ 1.200/t
Receita: R$ 1.800/t
Custo de parada: R$ 50.000/hora

### Response:"""
        
        print("Pergunta:", prompt[:100] + "...")
        
        resposta = self.gerar_resposta(prompt)
        print(f"Resposta: {resposta}")
        
        return resposta
    
    def testar_modelo_base(self):
        """Testa modelo base"""
        print("\n" + "="*60)
        print("TESTANDO MODELO BASE")
        print("="*60)
        
        if not self.carregar_modelo(is_lora_model=False):
            return False
        
        # Testes
        self.testar_pergunta_financeira("MODELO BASE")
        self.testar_pergunta_industrial("MODELO BASE")
        self.testar_pergunta_integrada("MODELO BASE")
        
        # Limpa memória
        del self.model
        torch.cuda.empty_cache()
        gc.collect()
        
        return True
    
    def testar_modelo_lora(self):
        """Testa modelo LoRA"""
        print("\n" + "="*60)
        print("TESTANDO MODELO LORA")
        print("="*60)
        
        if not self.carregar_modelo(is_lora_model=True):
            return False
        
        # Testes
        self.testar_pergunta_financeira("MODELO LORA")
        self.testar_pergunta_industrial("MODELO LORA")
        self.testar_pergunta_integrada("MODELO LORA")
        
        return True
    
    def comparar_modelos(self):
        """Compara respostas dos dois modelos"""
        print("\n" + "="*60)
        print("COMPARAÇÃO DE MODELOS")
        print("="*60)
        
        # Testa modelo base
        print("\n🔄 Carregando modelo base...")
        if not self.carregar_modelo(is_lora_model=False):
            return False
        
        print("\n📊 Testando modelo base...")
        resposta_base = self.testar_pergunta_financeira("BASE")
        
        # Limpa memória
        del self.model
        torch.cuda.empty_cache()
        gc.collect()
        
        # Testa modelo LoRA
        print("\n🔄 Carregando modelo LoRA...")
        if not self.carregar_modelo(is_lora_model=True):
            return False
        
        print("\n📊 Testando modelo LoRA...")
        resposta_lora = self.testar_pergunta_financeira("LORA")
        
        # Comparação
        print("\n" + "="*40)
        print("COMPARAÇÃO DE RESPOSTAS")
        print("="*40)
        print(f"BASE:  {resposta_base[:200]}...")
        print(f"LORA:  {resposta_lora[:200]}...")
        
        return True

def main():
    """Função principal"""
    print("TESTE DO MODELO MISTRAL-7B (WSL)")
    print("=" * 50)
    
    testador = TestadorModeloWSL()
    
    print("\nEscolha o tipo de teste:")
    print("1. Testar modelo base")
    print("2. Testar modelo LoRA")
    print("3. Comparar ambos")
    print("4. Teste completo")
    
    try:
        opcao = input("\nOpção (1-4): ").strip()
        
        if opcao == "1":
            testador.testar_modelo_base()
        elif opcao == "2":
            testador.testar_modelo_lora()
        elif opcao == "3":
            testador.comparar_modelos()
        elif opcao == "4":
            testador.testar_modelo_base()
            testador.testar_modelo_lora()
            testador.comparar_modelos()
        else:
            print("❌ Opção inválida!")
            return False
        
        print("\n✅ Testes concluídos!")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️  Teste interrompido pelo usuário")
        return False
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
