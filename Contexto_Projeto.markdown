# 🧠 Projeto: Fine-Tuning Integrado FinQA + FailureSensorIQ

## 🎯 Objetivo Geral
Desenvolver um **modelo de Inteligência Artificial corporativa** capaz de **analisar simultaneamente dados financeiros e industriais**, identificando **inconsistências, desvios e correlações causais** entre indicadores de custo, produção e eficiência.

O modelo será **Fine-Tunado** em formato *Instruct* e integrado a uma arquitetura **RAG (Retrieval-Augmented Generation)** conectada ao **Data Warehouse (DW)** da empresa.

---

## 🧠 Contexto e Motivação
Empresas industriais possuem grandes volumes de dados distribuídos entre áreas **financeiras** e **operacionais**.  
Essas bases frequentemente não “conversam” — por exemplo:

- Custos aumentam sem crescimento proporcional da produção;  
- Consumo energético sobe sem alteração na capacidade produtiva;  
- Falhas operacionais geram impacto financeiro indireto não identificado.  

O projeto busca treinar um modelo que **entenda e explique essas relações**, conectando os indicadores de **produção, energia e custo** em uma análise automatizada e contextualizada.

---

## ⚙️ Arquitetura de Solução

### 🔹 **1. Data Layer (DW)**
Camada de dados consolidada com schemas financeiros e industriais.

- Arquivo `data_schema.json` descreve:  
  - Tabelas e colunas disponíveis;  
  - Tipos de dados e exemplos;  
  - Relações entre domínios (financeiro ↔ industrial).  

---

### 🔹 **2. Tools (Ferramentas SQL)**
Criadas com **SQLAlchemy** para consultas seguras e controladas ao DW.

Exemplos de Tools:
- `query_financeira()`: retorna custos, lucros e margens;  
- `query_operacional()`: traz indicadores de produção e sensores;  
- `join_financeiro_industrial()`: combina dados financeiros e industriais;  
- `compare_kpis()`: calcula variações percentuais e discrepâncias entre domínios.

---

### 🔹 **3. Agentes RAG**

- **Orquestrador:** interpreta a intenção do usuário e define quais agentes devem ser acionados;  
- **Financeiro:** executa consultas e análises no schema financeiro;  
- **Industrial:** analisa dados produtivos, sensores e eficiência;  
- **Finalizador:** consolida as respostas e produz o texto final em linguagem executiva.  

🧩 **Fluxo Geral:**

> Usuário → Orquestrador → Agente Específico → Tool SQL → Retorno JSON → Finalizador → Resposta Final

---

### 🔹 **4. Modelo Fine-Tunado**
O núcleo cognitivo do sistema.

Treinado com os datasets **FinQA** e **FailureSensorIQ**, o modelo aprende:

| Dataset | Competência Aprendida |
|----------|------------------------|
| **FinQA** | Raciocínio numérico e financeiro contextualizado |
| **FailureSensorIQ** | Raciocínio causal e diagnóstico industrial |

Essa combinação permite que o modelo interprete perguntas empresariais complexas, correlacionando **indicadores financeiros e produtivos**.

---

## 📊 Fluxo de Operação

1. **Usuário** faz uma pergunta contextual:
   > “Estamos com aumento de 12% nos custos de produção. O que pode estar acontecendo?”

2. **Orquestrador** identifica o tipo de análise (financeira, industrial ou integrada).

3. **Agentes** executam consultas SQL via Tools e retornam dados estruturados.

4. **RAG** insere as informações do DW no contexto do modelo Fine-Tunado.

5. **Modelo Fine-Tunado** interpreta os dados e gera uma explicação causal e quantitativa.

📘 **Exemplo de saída esperada:**
> “O custo cresceu 12% devido ao aumento de 15% no consumo energético e queda de 8% na eficiência da linha 2.  
> Esse desbalanceamento sugere perda de eficiência operacional.”

---

## 🧮 Treinamento e Metodologia

- **Formato Instruct (`prompt → resposta`)**  
  O modelo é treinado para responder perguntas com explicações analíticas e estruturadas.  

- **Fine-Tuning** define o estilo e o raciocínio das respostas:  
  - Explicações quantitativas (aprendidas do *FinQA*);  
  - Relações causais (aprendidas do *FailureSensorIQ*).  

- **RAG** fornece os dados reais da empresa para contextualizar cada resposta.  

- **Tools** calculam variações, médias e correlações — o modelo **interpreta**, não calcula.

---

## 🔍 Exemplo de Raciocínio do Modelo

### Prompt
> “A produção caiu 5% e o custo total aumentou 12%. O que isso indica?”

### Resposta Esperada
> “A relação entre aumento de custo e queda na produção sugere perda de eficiência operacional, possivelmente causada por falhas em equipamentos ou aumento no consumo energético.”

---

## 📈 Resultado Esperado

Um modelo Fine-Tunado que atua como um **Analista de IA Corporativo**, capaz de:

- Correlacionar dados financeiros e industriais;  
- Detectar inconsistências e anomalias operacionais;  
- Explicar causas de variação e impacto econômico;  
- Gerar relatórios analíticos em linguagem natural e corporativa.

📊 **Exemplo de resposta final:**
> “Os custos aumentaram 12% enquanto a produção caiu 9%.  
> Isso indica perda de eficiência.  
> A análise dos sensores aponta sobreaquecimento em dois motores, o que pode ter reduzido a produtividade e aumentado o consumo de energia.”

---

## 🧭 Resumo Geral

| Componente | Função |
|-------------|--------|
| **FinQA** | Ensina o modelo a raciocinar financeiramente |
| **FailureSensorIQ** | Ensina o modelo a raciocinar sobre falhas e sensores |
| **Fine-Tuning Instruct** | Define o formato e a linguagem das respostas |
| **RAG + Tools SQL** | Fornece os dados reais da empresa |
| **Agentes Especializados** | Orquestram consultas e análises |
| **Modelo Final** | Interpreta discrepâncias e explica causas corporativas |

---

## 🧩 Conclusão
O sistema resultante será capaz de:
- **Integrar dados financeiros e industriais** via RAG;  
- **Raciocinar sobre discrepâncias e perdas operacionais**;  
- **Gerar respostas explicativas e orientadas à decisão**.  

Este Fine-Tuning conjunto cria a base de um **assistente de IA corporativo híbrido**, unindo raciocínio financeiro e técnico-industrial para apoiar a tomada de decisão baseada em dados.
