# Implementação Arquitetura DW + RAG Base

## 1. Configuração de Múltiplos Bancos de Dados

### 1.1 Atualizar configurações de banco

**Arquivo**: `infrastructure/config/database_config.py`

- Adicionar configurações para 3 databases separados:
- `db_financeiro` (porta 5432)
- `db_industrial` (porta 5433) 
- `db_datamind_dw` (porta 5434)
- Manter configuração existente como fallback

### 1.2 Criar gerenciadores de conexão separados

**Criar**: `infrastructure/database/connections/`

- `financeiro_connection.py` - Conexão exclusiva para banco financeiro
- `industrial_connection.py` - Conexão exclusiva para banco industrial
- `dw_connection.py` - Conexão exclusiva para Data Warehouse
- `__init__.py` - Exportar todas as conexões

### 1.3 Criar sessions separadas

**Criar**: `infrastructure/database/sessions/`

- `financeiro_session.py` - Session maker para banco financeiro
- `industrial_session.py` - Session maker para banco industrial
- `dw_session.py` - Session maker para DW
- `__init__.py` - Exportar dependency injection functions

## 2. Reorganização de Modelos por Banco

### 2.1 Separar modelos financeiros

**Reestruturar**: `core/models/financeiro/`

- Mover modelos de `financeiro.py` para subpastas organizadas:
- `custos.py` - CustoPadrao, CustoIndiretoRateio, etc
- `contabil.py` - ContaContabil, LancamentoFinanceiro
- `vendas.py` - Venda, Orcamento
- `kpis.py` - KPIGerencial
- Atualizar `__init__.py` com Base correto (FinanceiroBase)

### 2.2 Separar modelos industriais

**Reestruturar**: `core/models/industrial/`

- Mover modelos de `industria.py` para subpastas:
- `producao.py` - OrdemProducao, RegistroOperacao, etc
- `equipamentos.py` - Maquina, equipamentos
- `qualidade.py` - ControleQualidade, Defeito
- `cadastros.py` - Produto, Material, Fornecedor
- Atualizar `__init__.py` com Base correto (IndustrialBase)

### 2.3 Criar modelos da DW

**Criar**: `core/models/dw/`

- `dimensoes.py` - DimProduto, DimTempo, DimMaquina, DimCliente
- `fatos.py` - FatoVendas, FatoProducao, FatoCustos, FatoQualidade
- `agregados.py` - KPIFinanceiro, KPIIndustrial, KPIIntegrado
- `__init__.py` - Exportar com DWBase

## 3. Repositórios Especializados

### 3.1 Repositórios financeiros

**Criar**: `core/repositories/financeiro/`

- `custos_repository.py` - Operações de custos
- `vendas_repository.py` - Operações de vendas
- `contabil_repository.py` - Operações contábeis
- `__init__.py`

### 3.2 Repositórios industriais

**Criar**: `core/repositories/industrial/`

- `producao_repository.py` - Operações de produção
- `equipamentos_repository.py` - Operações de equipamentos
- `qualidade_repository.py` - Operações de qualidade
- `__init__.py`

### 3.3 Repositórios DW

**Criar**: `core/repositories/dw/`

- `dimensoes_repository.py` - Operações em dimensões
- `fatos_repository.py` - Operações em fatos
- `kpis_repository.py` - Consultas analíticas e KPIs
- `__init__.py`

## 4. Serviços ETL

### 4.1 Criar serviços de extração

**Criar**: `core/services/etl/extractors/`

- `financeiro_extractor.py` - Extrai dados do banco financeiro
- `industrial_extractor.py` - Extrai dados do banco industrial
- `__init__.py`

### 4.2 Criar serviços de transformação

**Criar**: `core/services/etl/transformers/`

- `dimensoes_transformer.py` - Transforma dados para dimensões
- `fatos_transformer.py` - Transforma dados para fatos
- `lookup_service.py` - Busca surrogate keys
- `__init__.py`

### 4.3 Criar serviços de carga

**Criar**: `core/services/etl/loaders/`

- `dimensoes_loader.py` - Carrega dimensões na DW
- `fatos_loader.py` - Carrega fatos na DW
- `__init__.py`

### 4.4 Criar orquestrador ETL

**Criar**: `core/services/etl/`

- `etl_pipeline.py` - Pipeline ETL completo (Extract → Transform → Load)
- `etl_scheduler.py` - Agendador usando APScheduler (execução diária)
- `etl_config.py` - Configurações de ETL (frequência diária, batch size reduzido)
- `__init__.py`

**Configurações específicas ETL**:

- Extração: Batch diário para dados industriais (captura granular)
- Transform: Manter granularidade original (dia/evento), sem agregação
- Load: Carregar registros detalhados na DW

## 5. Estrutura Base RAG

### 5.1 Criar ferramentas (Tools)

**Criar**: `rag/tools/`

- `dw_query_tools.py` - Ferramentas de consulta à DW
- `financeiro_tools.py` - Tools específicos financeiros
- `industrial_tools.py` - Tools específicos industriais
- `integracao_tools.py` - Tools de análise integrada
- `tool_registry.py` - Registro de todas as tools disponíveis
- `__init__.py`

### 5.2 Criar agentes especializados

**Criar**: `rag/agents/`

- `base_agent.py` - Classe base para agentes
- `orquestrador.py` - Agente orquestrador (roteia perguntas)
- `agente_financeiro.py` - Agente especialista financeiro
- `agente_industrial.py` - Agente especialista industrial
- `agente_integracao.py` - Agente para análises integradas
- `agente_finalizador.py` - Consolida respostas
- `prompts/` - Pasta com system prompts de cada agente
- `__init__.py`

### 5.3 Criar pipeline RAG

**Criar**: `rag/`

- `pipeline.py` - Pipeline principal RAG
- `rag_config.py` - Configurações RAG (modelo, temperaturas, etc)
- `llm_client.py` - Cliente para modelo local (estrutura base)
- `__init__.py`

### 5.4 Criar estrutura para modelo local

**Criar**: `rag/models/`

- `local_model.py` - Interface para carregar modelo fine-tunado
- `model_config.py` - Configurações do modelo (path, parâmetros)
- `README.md` - Instruções para carregar modelo
- `__init__.py`

## 6. Documentação da DW

### 6.1 Criar schema JSON

**Criar**: `data/schemas/`

- `data_schema.json` - Schema completo da DW documentado
- `financeiro_schema.json` - Schema do banco financeiro
- `industrial_schema.json` - Schema do banco industrial
- `README.md` - Documentação dos schemas

### 6.2 Criar exemplos de consultas

**Criar**: `data/examples/`

- `queries_financeiras.sql` - Exemplos de consultas financeiras
- `queries_industriais.sql` - Exemplos de consultas industriais
- `queries_integradas.sql` - Exemplos de consultas integradas DW
- `README.md` - Documentação dos exemplos

## 7. Atualização da API

### 7.1 Criar routers RAG

**Criar**: `infrastructure/api/routers/`

- `rag_router.py` - Endpoints para consultas RAG
- `etl_router.py` - Endpoints para gerenciar ETL
- `dw_router.py` - Endpoints para consultar DW diretamente

### 7.2 Atualizar main.py

**Arquivo**: `infrastructure/api/main.py`

- Adicionar novos routers
- Configurar startup do agendador ETL
- Adicionar health checks para os 3 bancos

## 8. Scripts de Gerenciamento (SIMPLIFICADO)

### 8.1 Scripts Essenciais

**Criar**: `scripts/`

- `run_etl.py` - Executa ETL manualmente

### 8.2 Atualizar Scripts Existentes

**Atualizar**:

- `scripts/build.py` - Incluir setup dos 3 databases
- `scripts/migrate.py` - Migrar para os 3 databases

**Scripts Removidos (Desnecessários)**:
- ❌ `setup_databases.py` - DatabaseManager já faz isso automaticamente
- ❌ `test_connections.py` - Endpoint /database-status já existe
- ❌ `seed_sample_data.py` - Não essencial para funcionalidade core

## 9. Configuração e Dependências

### 9.1 Atualizar requirements.txt

**Adicionar**:

- `apscheduler` - Para agendamento ETL
- `pandas` - Para transformações ETL
- `python-dateutil` - Para manipulação de datas

### 9.2 Criar arquivo .env.example

**Criar**: `.env.example`

- Template com todas as variáveis de ambiente necessárias
- Configurações para os 3 databases
- Configurações RAG e modelo local

## 10. Testes e Validação

### 10.1 Criar estrutura de testes

**Criar**: `tests/`

- `test_connections.py` - Testa conexões dos 3 bancos
- `test_etl_pipeline.py` - Testa processo ETL
- `test_rag_tools.py` - Testa ferramentas RAG
- `test_dw_queries.py` - Testa consultas DW

## Notas de Implementação

- Manter compatibilidade com código existente durante migração
- Implementar logs detalhados em todos os processos ETL
- Adicionar tratamento de erros robusto
- Seguir padrão atual de arquitetura (Clean Architecture)
- Documentar todos os novos componentes
