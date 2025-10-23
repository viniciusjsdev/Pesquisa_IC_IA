#!/usr/bin/env python3
"""
INFERÊNCIA MISTRAL-7B TREINADO (WSL)
====================================
Script Plug-and-Play para inferência do modelo LoRA treinado
"""

import os
import sys
import torch
import gc
import argparse
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

class InferenciaWSL:
    """Classe para inferência no WSL"""
    
    def __init__(self, model_path: str = None, adapter_path: str = None):
        self.model = None
        self.tokenizer = None
        
        # Caminhos padrão
        self.base_model_path = model_path or "/mnt/e/Mistral/models--mistralai--Mistral-7B-Instruct-v0.3/snapshots"
        self.adapter_path = adapter_path or "/mnt/e/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/Datasets/finetune_mistral_wsl/output"
        
    def carregar_modelo(self):
        """Carrega modelo e LoRA adapter"""
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
            
            # Carrega LoRA adapter
            if Path(self.adapter_path).exists():
                print(f"Carregando adapter LoRA de: {self.adapter_path}")
                self.model = PeftModel.from_pretrained(self.model, self.adapter_path)
            else:
                print("⚠️  Adapter LoRA não encontrado, usando modelo base")
            
            print("✅ Modelo carregado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar modelo: {e}")
            return False
    
    def gerar_resposta(self, prompt: str, max_length: int = 512, temperature: float = 0.7) -> str:
        """Gera resposta do modelo"""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    top_k=50,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response.replace(prompt, "").strip()
            
        except Exception as e:
            return f"Erro na geração: {e}"
    
    def analise_financeira(self, pergunta: str, contexto: str = "") -> str:
        """Análise financeira especializada"""
        prompt = f"""### Instruction:
{pergunta}

### Context:
{contexto}

### Response:"""
        
        return self.gerar_resposta(prompt)
    
    def analise_industrial(self, pergunta: str, contexto: str = "") -> str:
        """Análise industrial especializada"""
        prompt = f"""### Instruction:
{pergunta}

### Context:
{contexto}

### Response:"""
        
        return self.gerar_resposta(prompt)
    
    def analise_integrada(self, pergunta: str, contexto: str = "") -> str:
        """Análise integrada financeiro-industrial"""
        prompt = f"""### Instruction:
{pergunta}

### Context:
{contexto}

### Response:"""
        
        return self.gerar_resposta(prompt)
    
    def modo_interativo(self):
        """Modo interativo para perguntas"""
        print("\n" + "="*60)
        print("MODO INTERATIVO - MISTRAL-7B WSL")
        print("="*60)
        print("Digite suas perguntas (digite 'sair' para sair)")
        print("Comandos especiais:")
        print("  /financeiro - Análise financeira")
        print("  /industrial - Análise industrial")
        print("  /integrado - Análise integrada")
        print("="*60)
        
        while True:
            try:
                entrada = input("\n🤖 Você: ").strip()
                
                if entrada.lower() in ['sair', 'exit', 'quit']:
                    print("👋 Até logo!")
                    break
                
                if entrada.startswith('/financeiro'):
                    pergunta = entrada[12:].strip()
                    resposta = self.analise_financeira(pergunta)
                elif entrada.startswith('/industrial'):
                    pergunta = entrada[11:].strip()
                    resposta = self.analise_industrial(pergunta)
                elif entrada.startswith('/integrado'):
                    pergunta = entrada[11:].strip()
                    resposta = self.analise_integrada(pergunta)
                else:
                    # Resposta geral
                    resposta = self.gerar_resposta(entrada)
                
                print(f"\n🤖 Mistral: {resposta}")
                
            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    def exemplos_predefinidos(self):
        """Executa exemplos predefinidos"""
        print("\n" + "="*60)
        print("EXEMPLOS PREDEFINIDOS")
        print("="*60)
        
        # Exemplo 1: Financeiro
        print("\n📊 EXEMPLO 1: ANÁLISE FINANCEIRA")
        pergunta1 = "Analise a rentabilidade da empresa Gerdau"
        contexto1 = "Receita: R$ 45.2B, EBITDA: R$ 8.7B, Dívida: R$ 12.3B"
        resposta1 = self.analise_financeira(pergunta1, contexto1)
        print(f"Pergunta: {pergunta1}")
        print(f"Contexto: {contexto1}")
        print(f"Resposta: {resposta1}")
        
        # Exemplo 2: Industrial
        print("\n🏭 EXEMPLO 2: ANÁLISE INDUSTRIAL")
        pergunta2 = "Como otimizar a eficiência energética?"
        contexto2 = "3 fornos elétricos, consumo 2.5 GWh/mês, meta: -15%"
        resposta2 = self.analise_industrial(pergunta2, contexto2)
        print(f"Pergunta: {pergunta2}")
        print(f"Contexto: {contexto2}")
        print(f"Resposta: {resposta2}")
        
        # Exemplo 3: Integrado
        print("\n🔗 EXEMPLO 3: ANÁLISE INTEGRADA")
        pergunta3 = "Qual o impacto financeiro de uma parada de 8h?"
        contexto3 = "Alto-forno: 2.500 t/dia, custo R$ 1.200/t, receita R$ 1.800/t"
        resposta3 = self.analise_integrada(pergunta3, contexto3)
        print(f"Pergunta: {pergunta3}")
        print(f"Contexto: {contexto3}")
        print(f"Resposta: {resposta3}")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Inferência Mistral-7B WSL")
    parser.add_argument("--model-path", help="Caminho do modelo base")
    parser.add_argument("--adapter-path", help="Caminho do adapter LoRA")
    parser.add_argument("--interactive", action="store_true", help="Modo interativo")
    parser.add_argument("--exemplos", action="store_true", help="Executar exemplos")
    parser.add_argument("--pergunta", help="Pergunta específica")
    parser.add_argument("--contexto", help="Contexto para a pergunta")
    
    args = parser.parse_args()
    
    print("INFERÊNCIA MISTRAL-7B TREINADO (WSL)")
    print("=" * 50)
    
    # Inicializa inferência
    inferencia = InferenciaWSL(
        model_path=args.model_path,
        adapter_path=args.adapter_path
    )
    
    # Carrega modelo
    if not inferencia.carregar_modelo():
        return False
    
    try:
        if args.interactive:
            inferencia.modo_interativo()
        elif args.exemplos:
            inferencia.exemplos_predefinidos()
        elif args.pergunta:
            if args.contexto:
                resposta = inferencia.analise_integrada(args.pergunta, args.contexto)
            else:
                resposta = inferencia.gerar_resposta(args.pergunta)
            print(f"\n🤖 Resposta: {resposta}")
        else:
            # Menu interativo
            print("\nEscolha uma opção:")
            print("1. Modo interativo")
            print("2. Exemplos predefinidos")
            print("3. Pergunta específica")
            
            opcao = input("\nOpção (1-3): ").strip()
            
            if opcao == "1":
                inferencia.modo_interativo()
            elif opcao == "2":
                inferencia.exemplos_predefinidos()
            elif opcao == "3":
                pergunta = input("Digite sua pergunta: ")
                contexto = input("Digite o contexto (opcional): ")
                if contexto:
                    resposta = inferencia.analise_integrada(pergunta, contexto)
                else:
                    resposta = inferencia.gerar_resposta(pergunta)
                print(f"\n🤖 Resposta: {resposta}")
            else:
                print("❌ Opção inválida!")
                return False
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrompido pelo usuário")
        return False
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return False
    
    finally:
        # Limpa memória
        if inferencia.model:
            del inferencia.model
        torch.cuda.empty_cache()
        gc.collect()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
