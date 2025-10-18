# Sistema Integrado Financeiro-Industrial com RAG

Sistema integrado que conecta dados financeiros e industriais através de uma Data Warehouse, com sistema RAG (Retrieval-Augmented Generation) para consultas inteligentes.

## 🏗️ Arquitetura

### Componentes Principais

1. **Bancos de Dados Separados**
   - `db_financeiro` (Porta 5432) - Dados financeiros/contábeis
   - `db_industrial` (Porta 5433) - Dados operacionais/MES
   - `db_datamind_dw` (Porta 5434) - Data Warehouse consolidada

2. **Sistema ETL**
   - Extração diária de dados dos sistemas fonte
   - Transformação e limpeza dos dados
   - Carregamento na DW com granularidade diária

3. **Sistema RAG**
   - Agente Orquestrador - interpreta consultas
   - Agente Financeiro - especializado em dados financeiros
   - Agente Industrial - especializado em dados operacionais
   - Agente Finalizador - consolida respostas

4. **API REST**
   - Endpoints para consultas RAG
   - Endpoints para gerenciamento ETL
   - Documentação automática

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- PostgreSQL 12+
- 3 instâncias PostgreSQL (portas 5432, 5433, 5434)

### Configuração

1. **Clone o repositório**
   ```bash
   git clone <repository-url>
   cd BancoModeloUse
   ```

2. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure o ambiente**
   ```bash
   cp env.example .env
   # Edite o arquivo .env com suas configurações
   ```

4. **Configure os bancos de dados**
   ```bash
   # Crie os bancos de dados PostgreSQL
   createdb db_financeiro
   createdb db_industrial
   createdb db_datamind_dw
   ```

5. **Configure o sistema**
   ```bash
   python scripts/setup_sistema.py configurar
   ```

6. **Execute ETL inicial**
   ```bash
   python scripts/run_etl.py etl-inicial
   ```

7. **Teste o sistema RAG**
   ```bash
   python scripts/run_rag.py testar
   ```

8. **Inicie a API**
   ```bash
   uvicorn infrastructure.api.main:app --reload
   ```

## 📊 Estrutura de Dados

### Banco Financeiro
- `custos_padrao` - Custos padrão por tipo
- `custos_producao` - Custos de produção (CPP, CPA, CPV)
- `vendas` - Registros de vendas
- `lancamentos_financeiros` - Lançamentos contábeis

### Banco Industrial
- `produtos` - Cadastro de produtos
- `maquinas` - Cadastro de máquinas
- `ordens_producao` - Ordens de produção
- `registros_operacao` - Registros de operação
- `controle_qualidade` - Controles de qualidade

### Data Warehouse
- `dim_produto` - Dimensão produto
- `dim_tempo` - Dimensão tempo (granularidade diária)
- `dim_maquina` - Dimensão máquina
- `fato_vendas` - Fato vendas
- `fato_producao` - Fato produção
- `fato_custos` - Fato custos
- `kpi_integrado` - KPIs integrados

## 🤖 Sistema RAG

### Agentes Disponíveis

1. **Orquestrador**
   - Interpreta consultas em linguagem natural
   - Classifica domínio (financeiro, industrial, integração)
   - Direciona para agente especializado

2. **Agente Financeiro**
   - Especializado em vendas, custos, lançamentos
   - Calcula indicadores financeiros
   - Gera insights sobre performance financeira

3. **Agente Industrial**
   - Especializado em produção, equipamentos, qualidade
   - Calcula KPIs industriais (OEE, eficiência)
   - Gera insights sobre performance operacional

4. **Agente Finalizador**
   - Consolida respostas de múltiplos agentes
   - Identifica correlações entre domínios
   - Produz recomendações estratégicas

### Exemplos de Consultas

**Financeiro:**
- "Quais foram as vendas do último mês?"
- "Como está a margem de contribuição do produto X?"
- "Mostre os custos de produção por período"

**Industrial:**
- "Como está a produção da máquina 1?"
- "Qual a eficiência (OEE) dos equipamentos?"
- "Mostre a taxa de defeitos por período"

**Integração:**
- "Qual a correlação entre custos e eficiência?"
- "Mostre o dashboard executivo"
- "Como está a qualidade vs lucratividade?"

## 🔄 Sistema ETL

### Frequências de Execução

- **Diário**: 02:00 - Dados industriais
- **Semanal**: Segunda 03:00 - Dados financeiros
- **Mensal**: Dia 1 04:00 - KPIs integrados

### Scripts Disponíveis

```bash
# Executar ETL manual
python scripts/run_etl.py manual

# Executar ETL diário
python scripts/run_etl.py diario

# Executar ETL semanal
python scripts/run_etl.py semanal

# Executar ETL mensal
python scripts/run_etl.py mensal

# Configurar agendamentos
python scripts/run_etl.py configurar

# Ver status
python scripts/run_etl.py status
```

## 🧪 Testes

### Testar RAG
```bash
python scripts/run_rag.py testar
python scripts/run_rag.py agentes
python scripts/run_rag.py ferramentas
python scripts/run_rag.py interativo
```

### Testar ETL
```bash
python scripts/run_etl.py manual
python scripts/run_etl.py status
```

### Verificar Sistema
```bash
python scripts/setup_sistema.py verificar
python scripts/setup_sistema.py status
```

## 📡 API Endpoints

### RAG
- `POST /rag/consulta` - Processar consulta RAG
- `GET /rag/exemplos` - Exemplos de consultas
- `GET /rag/agentes` - Informações dos agentes
- `GET /rag/ferramentas` - Ferramentas disponíveis

### ETL
- `POST /etl/executar` - Executar ETL
- `POST /etl/executar-diario` - ETL diário
- `POST /etl/executar-semanal` - ETL semanal
- `POST /etl/executar-mensal` - ETL mensal
- `GET /etl/status` - Status do ETL
- `POST /etl/agendar-diario` - Agendar ETL diário

## 📁 Estrutura do Projeto

```
BancoModeloUse/
├── core/
│   ├── models/          # Modelos SQLAlchemy
│   │   ├── financeiro/  # Modelos financeiros
│   │   ├── industrial/  # Modelos industriais
│   │   └── dw/          # Modelos DW
│   ├── repositories/    # Repositórios de dados
│   ├── services/        # Serviços de negócio
│   │   └── etl/         # Serviços ETL
│   └── rag/             # Sistema RAG
│       ├── agents/      # Agentes especializados
│       ├── tools/       # Ferramentas de consulta
│       └── pipeline.py  # Pipeline principal
├── infrastructure/
│   ├── api/             # API REST
│   ├── config/          # Configurações
│   └── database/        # Conexões e sessões
├── scripts/             # Scripts de gerenciamento
├── docs/                # Documentação
│   └── schemas/         # Schemas JSON
└── requirements.txt     # Dependências
```

## 🔧 Configuração Avançada

### Modelo Local
Para usar um modelo local finetunado:

1. Configure o caminho no `.env`:
   ```
   RAG_MODEL_PATH=/caminho/para/seu/modelo
   ```

2. O sistema carregará automaticamente o modelo local

### Múltiplos Bancos
O sistema suporta múltiplos bancos PostgreSQL:
- Financeiro: `localhost:5432`
- Industrial: `localhost:5433`
- DW: `localhost:5434`

### Agendamento ETL
Configure horários personalizados no `.env`:
```
ETL_DAILY_HOUR=02:00
ETL_WEEKLY_DAY=1
ETL_WEEKLY_HOUR=03:00
```

## 🐛 Troubleshooting

### Problemas Comuns

1. **Erro de conexão com banco**
   - Verifique se os bancos existem
   - Confirme as credenciais no `.env`
   - Teste conectividade: `telnet localhost 5432`

2. **ETL não executa**
   - Verifique logs: `tail -f logs/sistema.log`
   - Execute manualmente: `python scripts/run_etl.py manual`

3. **RAG não responde**
   - Teste agentes: `python scripts/run_rag.py agentes`
   - Verifique conexão com DW

4. **API não inicia**
   - Verifique dependências: `pip install -r requirements.txt`
   - Confirme configurações no `.env`

### Logs
- Logs do sistema: `logs/sistema.log`
- Logs da API: console
- Logs ETL: console + arquivo

## 📈 Monitoramento

### Métricas Disponíveis
- Consultas RAG por agente
- Taxa de sucesso das consultas
- Tempo médio de resposta
- Execuções ETL
- Status dos bancos de dados

### Health Checks
- `GET /database-status` - Status dos bancos
- `GET /etl/status` - Status do ETL
- `GET /rag/estatisticas` - Estatísticas RAG

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 📞 Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação da API em `/docs`
- Execute `python scripts/setup_sistema.py status` para diagnóstico