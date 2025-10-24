# Sistema RAG - Retrieval Augmented Generation

Sistema completo de análise de dados empresariais com Inteligência Artificial, especializado em domínios financeiro e industrial.

## 🏗️ Arquitetura

### Componentes Principais

- **Pipeline RAG**: Orquestração principal do sistema
- **Agentes Especializados**: Processamento inteligente por domínio
- **Ferramentas**: Acesso a dados e cálculos especializados
- **API**: Endpoints RESTful para integração
- **Providers**: Integração com modelos de IA

### Estrutura de Pastas

```
rag/
├── __init__.py              # Exportações principais
├── config.py                # Configurações do sistema
├── pipeline.py              # Pipeline principal RAG
├── state.py                 # Gerenciamento de estado
├── enums.py                 # Enumerações do sistema
├── graph.py                 # Grafo de agentes
├── roteador.py              # Roteamento de consultas
├── state_service.py         # Serviço de estado
├── agents/                  # Agentes especializados
│   ├── __init__.py
│   ├── orquestrador.py      # Agente orquestrador
│   ├── agente_financeiro.py # Agente financeiro
│   ├── agente_industrial.py# Agente industrial
│   ├── agente_integracao.py # Agente de integração
│   ├── agente_finalizador.py# Agente finalizador
│   ├── preprocessador.py    # Pré-processamento
│   ├── validador_global.py  # Validação global
│   └── prompts/             # Prompts dos agentes
├── tools/                   # Ferramentas especializadas
│   ├── __init__.py
│   ├── base.py              # Classe base para tools
│   ├── financeiro_tools.py  # Tools financeiros
│   ├── industrial_tools.py  # Tools industriais
│   ├── integracao_tools.py  # Tools de integração
│   └── registry.py           # Registro de tools
├── providers/               # Providers de IA
│   ├── __init__.py
│   ├── base.py              # Classe base
│   ├── openai_provider.py   # OpenAI
│   ├── finetuned_provider.py# Modelo fine-tuned
│   └── loader.py             # Carregador de providers
├── schemas/                 # Schemas de dados
│   ├── data_schema.json     # Schema dos dados
│   └── rag_schema.json      # Schema do RAG
└── api/                     # API REST
    ├── __init__.py
    └── rag_router.py        # Router da API
```

## 🚀 Funcionalidades

### Domínios Suportados

1. **Financeiro**
   - Análise de vendas e receitas
   - Cálculo de custos e margens
   - Indicadores financeiros (ROI, lucratividade)
   - Lançamentos contábeis

2. **Industrial**
   - Monitoramento de produção
   - Análise de eficiência (OEE)
   - Controle de qualidade
   - Gestão de equipamentos

3. **Integração**
   - Correlações financeiro-industrial
   - Dashboards executivos
   - KPIs integrados
   - Análises consolidadas

### Tipos de Consulta

- **Consultas Diretas**: "Quais foram as vendas do último mês?"
- **Análises Comparativas**: "Compare a eficiência entre máquinas"
- **Correlações**: "Qual a relação entre custos e qualidade?"
- **Dashboards**: "Mostre o dashboard executivo"

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Configurações de LLM
RAG_LLM_PROVIDER=openai
RAG_LLM_MODEL=gpt-4
RAG_LLM_TEMPERATURE=0.1
RAG_LLM_MAX_TOKENS=4000

# Configurações de Embedding
RAG_EMBEDDING_PROVIDER=openai
RAG_EMBEDDING_MODEL=text-embedding-ada-002

# Configurações de Cache
RAG_CACHE_ENABLED=true
RAG_CACHE_TTL=3600

# Configurações de Rate Limiting
RAG_RATE_LIMIT_ENABLED=true
RAG_MAX_REQUESTS_PER_MINUTE=60

# Configurações de Logging
RAG_LOG_LEVEL=INFO
RAG_LOG_REQUESTS=true
RAG_LOG_RESPONSES=false

# Configurações de Telemetria
RAG_TELEMETRY_ENABLED=true
RAG_LANGFUSE_ENABLED=false
```

### Uso Básico

```python
from rag import RAGPipeline

# Inicializar pipeline
pipeline = RAGPipeline()

# Processar consulta
resultado = pipeline.processar_consulta("Quais foram as vendas do último mês?")

print(resultado)
```

## 📊 API Endpoints

### Consultas

- `POST /rag/consulta` - Processar consulta RAG
- `GET /rag/exemplos` - Exemplos de consultas
- `GET /rag/estatisticas` - Estatísticas do sistema
- `POST /rag/teste` - Testar pipeline

### Agentes

- `GET /rag/agentes` - Informações sobre agentes
- `GET /rag/ferramentas` - Ferramentas disponíveis

## 🔍 Exemplos de Uso

### Consultas Financeiras

```python
# Vendas por período
consulta = "Quais foram as vendas do último trimestre?"

# Análise de custos
consulta = "Como está a margem de contribuição do produto X?"

# Indicadores financeiros
consulta = "Qual o ROI do investimento Y?"
```

### Consultas Industriais

```python
# Produção
consulta = "Como está a produção da máquina 1?"

# Eficiência
consulta = "Qual a eficiência (OEE) dos equipamentos?"

# Qualidade
consulta = "Mostre a taxa de defeitos por período"
```

### Consultas Integradas

```python
# Correlações
consulta = "Qual a correlação entre custos e eficiência?"

# Dashboard
consulta = "Mostre o dashboard executivo"

# KPIs integrados
consulta = "Quais são os KPIs integrados?"
```

## 🛠️ Desenvolvimento

### Adicionando Novos Agentes

1. Criar arquivo em `agents/`
2. Implementar classe do agente
3. Registrar no `__init__.py`
4. Atualizar pipeline

### Adicionando Novas Ferramentas

1. Criar arquivo em `tools/`
2. Herdar de `BaseTool`
3. Implementar métodos necessários
4. Registrar no registry

### Adicionando Novos Providers

1. Criar arquivo em `providers/`
2. Herdar de `BaseProvider`
3. Implementar métodos de IA
4. Registrar no loader

## 📈 Monitoramento

### Métricas Disponíveis

- Número de consultas processadas
- Tempo de resposta médio
- Taxa de sucesso por domínio
- Uso de ferramentas
- Performance dos agentes

### Logs

- Consultas recebidas
- Respostas geradas
- Erros e exceções
- Performance detalhada

## 🔒 Segurança

- Rate limiting por usuário
- Validação de inputs
- Sanitização de consultas
- Logs de auditoria
- Controle de acesso

## 📚 Documentação Adicional

- [Schemas de Dados](schemas/)
- [Exemplos de Uso](examples/)
- [Guia de Desenvolvimento](docs/)
- [API Reference](api/)

---

**Versão**: 1.0.0  
**Autor**: V&N Datamind Team  
**Licença**: Proprietary
