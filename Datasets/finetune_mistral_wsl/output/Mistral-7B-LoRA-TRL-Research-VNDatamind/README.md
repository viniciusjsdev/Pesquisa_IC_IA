---
base_model: mistralai/Mistral-7B-Instruct-v0.3
library_name: peft
model_name: Mistral-7B-LoRA-TRL-Research-VNDatamind
tags:
- base_model:adapter:mistralai/Mistral-7B-Instruct-v0.3
- lora
- sft
- transformers
- trl
- financial-analysis
- industrial-analysis
- portuguese
licence: license
pipeline_tag: text-generation
language: pt
---

# Mistral-7B-LoRA-TRL-Research-VNDatamind

## 📋 Descrição do Modelo

Este é um modelo **Mistral-7B-Instruct-v0.3** fine-tuned com **LoRA (Low-Rank Adaptation)** usando o **TRL Framework** para análise financeira e industrial integrada. O modelo foi treinado especificamente para responder perguntas sobre:

- **Análise Financeira**: Rentabilidade, avaliação de risco, projeções financeiras
- **Análise Industrial**: Otimização de processos, eficiência energética, gestão de produção
- **Análise Integrada**: Impacto financeiro de paradas, ROI de melhorias operacionais

## 🎯 Características Técnicas

### **Configuração LoRA:**
- **Rank (r)**: 8
- **Alpha**: 16
- **Dropout**: 0.1
- **Target Modules**: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj

### **Otimizações Aplicadas:**
- ✅ **Flash Attention 2** para eficiência de memória
- ✅ **Quantização 4-bit** (BitsAndBytesConfig)
- ✅ **Data Packing** para melhor utilização de tokens
- ✅ **Gradient Checkpointing** para reduzir uso de VRAM
- ✅ **bfloat16** para precisão otimizada

### **Métricas de Treinamento:**
- **Steps Totais**: 638
- **Épocas**: 2.0
- **Loss Final**: 0.6509
- **Accuracy Final**: 81.55%
- **Learning Rate**: 1e-4

## 🚀 Como Usar o Modelo

### **Pré-requisitos:**
```bash
pip install torch>=2.0.0 transformers>=4.35.0 peft>=0.6.0 bitsandbytes>=0.41.0 datasets>=2.14.0 accelerate>=0.24.0
```

### **1. Carregamento Básico:**
```python
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
import torch

# Carregar modelo base
base_model = "mistralai/Mistral-7B-Instruct-v0.3"
model_path = "./Mistral-7B-LoRA-TRL-Research-VNDatamind"

# Carregar tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_path)

# Carregar modelo base
model = AutoModelForCausalLM.from_pretrained(
    base_model,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )
)

# Carregar adaptador LoRA
model = PeftModel.from_pretrained(model, model_path)
```

### **2. Inferência Simples:**
```python
def gerar_resposta(pergunta, contexto=""):
    # Formatar prompt
    if contexto:
        prompt = f"### Instrução:\n{pergunta}\n\n### Contexto:\n{contexto}\n\n### Resposta:\n"
    else:
        prompt = f"### Instrução:\n{pergunta}\n\n### Resposta:\n"
    
    # Tokenizar
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
    
    # Gerar resposta
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decodificar resposta
    resposta = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return resposta.strip()

# Exemplo de uso
pergunta = "Como calcular o ROI de uma melhoria operacional?"
resposta = gerar_resposta(pergunta)
print(resposta)
```

### **3. Pipeline com Transformers:**
```python
from transformers import pipeline

# Criar pipeline
generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

# Usar pipeline
pergunta = "Qual é o impacto financeiro de uma parada não programada?"
resposta = generator(
    f"### Instrução:\n{pergunta}\n\n### Resposta:\n",
    max_new_tokens=256,
    temperature=0.7,
    do_sample=True
)

print(resposta[0]['generated_text'])
```

## 📊 Exemplos de Uso

### **Análise Financeira:**
```python
exemplos_financeiros = [
    "Como calcular a margem de contribuição de um produto?",
    "Qual é a diferença entre EBITDA e lucro líquido?",
    "Como avaliar o risco de crédito de uma empresa?",
    "Quais são os principais indicadores de rentabilidade?"
]
```

### **Análise Industrial:**
```python
exemplos_industriais = [
    "Como otimizar a eficiência energética de uma planta industrial?",
    "Quais são os principais KPIs de produção?",
    "Como implementar manutenção preditiva?",
    "Qual é o impacto do OEE na rentabilidade?"
]
```

### **Análise Integrada:**
```python
exemplos_integrados = [
    "Como calcular o ROI de uma melhoria operacional?",
    "Qual é o impacto financeiro de uma parada não programada?",
    "Como integrar métricas operacionais e financeiras?",
    "Quais são os custos ocultos de ineficiência operacional?"
]
```

## 📈 Performance

### **Requisitos de Hardware:**
- **GPU**: 8GB+ VRAM (recomendado: RTX 3080/4080 ou superior)
- **RAM**: 16GB+ (recomendado: 32GB)
- **Storage**: 5GB para modelo + dados

### **Métricas de Performance:**
- **Tempo de Inferência**: 1-3 segundos por resposta
- **Uso de VRAM**: ~6-8GB durante inferência
- **Temperatura GPU**: 60-65°C (normal)
- **Qualidade**: 81.55% accuracy no dataset de validação

## 🏗️ Arquitetura do Modelo

### **Estrutura de Arquivos:**
```
Mistral-7B-LoRA-TRL-Research-VNDatamind/
├── adapter_model.safetensors      # Pesos LoRA (83.9 MB)
├── adapter_config.json           # Configuração LoRA
├── tokenizer.json                # Vocabulário completo
├── tokenizer.model              # Modelo do tokenizer
├── tokenizer_config.json        # Configuração do tokenizer
├── special_tokens_map.json      # Tokens especiais
├── chat_template.jinja          # Template de conversação
├── README.md                    # Este arquivo
├── training_args.bin            # Argumentos de treinamento
├── checkpoint-200/              # Melhor checkpoint (accuracy: 62.86%)
├── checkpoint-400/              # Checkpoint intermediário
├── checkpoint-600/              # Checkpoint intermediário
├── checkpoint-638/              # Checkpoint final
└── runs/                        # Logs TensorBoard
```

## 🎓 Treinamento

### **Dataset:**
- **Formato**: JSONL com template de instrução
- **Campos**: `prompt`, `resposta`
- **Tamanho**: Dataset customizado para análise financeiro-industrial

### **Framework:**
- **TRL**: 0.24.0 (Supervised Fine-Tuning)
- **PEFT**: 0.17.1 (LoRA implementation)
- **Transformers**: 4.57.1
- **PyTorch**: 2.5.1+cu121

### **Configurações de Treinamento:**
- **Batch Size**: 1 (per device)
- **Gradient Accumulation**: 18 steps
- **Learning Rate**: 1e-4
- **Max Sequence Length**: 768
- **Warmup Ratio**: 0.1
- **Weight Decay**: 0.01

## 📚 Citações

Se você usar este modelo em sua pesquisa, cite:

```bibtex
@misc{vndatamind2025mistral,
    title        = {{Mistral-7B-LoRA-TRL-Research-VNDatamind: Fine-tuned Model for Financial and Industrial Analysis}},
    author       = {VNDatamind Research},
    year         = {2025},
    journal      = {GitHub repository},
    publisher    = {GitHub},
    howpublished = {\url{https://github.com/VNDatamind/mistral-financial-industrial-analysis}}
}
```

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:
1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

## 📄 Licença

Este modelo está sob licença MIT. Veja o arquivo LICENSE para detalhes.

## 🆘 Suporte

Para dúvidas ou problemas:
- **Issues**: Abra uma issue no GitHub
- **Email**: vndatamind@research.com
- **Documentação**: Consulte os exemplos de código acima

---

**Desenvolvido por VNDatamind Research | 2025**