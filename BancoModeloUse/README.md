# V&N Datamind - Sistema Financeiro

Sistema de gestão financeira integrado com dados industriais, desenvolvido com FastAPI e PostgreSQL.

## Configuração do Ambiente

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Banco de Dados PostgreSQL

Crie um banco de dados PostgreSQL com o nome `db_datamind`:

```sql
CREATE DATABASE db_datamind;
```

### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes configurações:

```env
# Configuração do Banco de Dados PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=db_datamind
DB_USER=postgres
DB_PASSWORD=host

# Ou use a URL completa (opcional)
# DATABASE_URL=postgresql://postgres:host@localhost:5432/db_datamind
```

### 4. Configuração para Novas Máquinas

**Setup Automático (Recomendado para primeira execução):**
```bash
# Configura tudo automaticamente: dependências, banco e aplicação
python scripts/setup_machine.py
```

**Configuração Manual:**
1. **Modificar configurações da máquina:**
   ```bash
   # Edite o arquivo infrastructure/config/machine_config.py
   # Modifique apenas as configurações do banco conforme sua máquina
   ```

2. **Executar build:**
   ```bash
   python scripts/build.py
   ```

### 5. Executar a Aplicação

**Opção 1 - Build Automático com Swagger (Recomendado):**
```bash
# Executa migração automática, inicia a aplicação e abre o Swagger
python scripts/build.py
```
*O Swagger será aberto automaticamente no navegador!*

**Opção 2 - Abrir Swagger Manualmente:**
```bash
# Se o servidor já estiver rodando, abre apenas o Swagger
python scripts/open_swagger.py
```

**Opção 3 - Manual:**
```bash
# Executar o servidor de desenvolvimento
uvicorn infrastructure.api.main:app --reload --host 0.0.0.0 --port 8000
```

A aplicação estará disponível em: http://localhost:8000

### 5. Gerenciamento do Banco de Dados

O sistema agora é **100% automático**:

- **Verifica** se o banco existe na inicialização
- **Cria** o banco automaticamente se não existir
- **Verifica** se as tabelas existem
- **Cria/Atualiza** tabelas automaticamente
- **Sempre mantém** o banco sincronizado com o código

**Endpoints disponíveis:**
- `GET /database-status` - Verifica status do banco
- `POST /create-tables` - Cria tabelas manualmente
- `POST /update-tables` - Atualiza tabelas manualmente

### 6. Resolução de Problemas

**Erro de Porta em Uso:**
```bash
# Verificar processos na porta 8000
netstat -ano | findstr :8000

# Parar processo específico (substitua PID pelo número encontrado)
taskkill /F /PID <PID>

# O build.py agora encontra automaticamente uma porta disponível
```

**Verificar Status do Banco:**
```bash
# Acessar endpoint de status
curl http://localhost:8000/database-status
```

### 7. Documentação da API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Estrutura do Projeto

```
BancoModeloUse/
├── core/                          # Lógica de negócio principal
│   ├── __init__.py
│   ├── models/                    # Modelos do domínio
│   │   ├── __init__.py
│   │   ├── industria.py           # Modelos industriais
│   │   └── financeiro.py          # Modelos financeiros
│   ├── schemas/                   # Schemas Pydantic
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── repositories/              # Camada de dados
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── financeiro_repo.py
│   │   └── industria_repo.py
│   └── services/                  # Serviços de negócio
│       ├── __init__.py
│       └── kpi_service.py
│
├── infrastructure/                # Infraestrutura técnica
│   ├── __init__.py
│   ├── config/                   # Configurações
│   │   ├── __init__.py
│   │   ├── database_config.py    # Configurações do banco
│   │   ├── app_config.py         # Configurações da aplicação
│   │   └── machine_config.py     # Configurações por máquina
│   ├── database/                 # Gerenciamento de banco
│   │   ├── __init__.py
│   │   ├── connection.py         # Configuração de conexão
│   │   ├── session.py            # Sessões do banco
│   │   └── manager.py            # Gerenciador do banco
│   └── api/                      # Routers e configuração API
│       ├── __init__.py
│       ├── main.py               # Aplicação principal
│       └── routers/
│           ├── __init__.py
│           ├── financeiro.py     # Router financeiro
│           └── industria.py      # Router industrial
│
├── scripts/                      # Scripts de automação
│   ├── __init__.py
│   ├── build.py                  # Script de build automático
│   ├── migrate.py                # Script de migração
│   ├── open_swagger.py           # Script para abrir Swagger
│   └── setup_machine.py          # Setup para novas máquinas
│
├── .gitignore                    # Arquivo para ignorar arquivos temporários
├── README.md
└── requirements.txt              # Dependências
```

## Funcionalidades

- **Gestão de Custos**: Controle de custos padrão, indiretos e históricos
- **Contabilidade**: Lançamentos financeiros e contas contábeis
- **Vendas**: Controle de vendas e orçamentos
- **KPIs**: Indicadores gerenciais
- **Integração Industrial**: Dados de produção e materiais

## Banco de Dados

O sistema cria automaticamente todas as tabelas necessárias na primeira execução. As tabelas incluem:

- Tabelas industriais (produtos, materiais, máquinas, ordens de produção)
- Tabelas financeiras (custos, contas contábeis, lançamentos, vendas)
- Tabelas de controle de qualidade e defeitos

## Desenvolvimento

Para desenvolvimento, o sistema usa SQLAlchemy com criação automática de tabelas. Em produção, recomenda-se o uso de Alembic para migrações.
