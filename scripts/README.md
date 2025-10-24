# Scripts de Carga e ETL

Este diretório contém scripts para:
- Carga de CSVs industriais no banco `industrial`
- Carga de CSVs financeiros no banco `financeiro`
- ETL para preparação/carga do Data Warehouse (DW)

## Pré-requisitos
- Python 3.10+
- Dependências do projeto instaladas:

```bash
pip install -r BancoModeloUse/requirements.txt
```

- Bancos PostgreSQL acessíveis conforme `BancoModeloUse/infrastructure/config/database_config.py` ou variáveis de ambiente.

## Variáveis de ambiente (opcional)
Você pode sobrescrever as configs padrão dos bancos via env vars:
- Industrial: `INDUSTRIAL_DB_HOST`, `INDUSTRIAL_DB_PORT`, `INDUSTRIAL_DB_NAME`, `INDUSTRIAL_DB_USER`, `INDUSTRIAL_DB_PASSWORD`
- Financeiro: `FINANCEIRO_DB_HOST`, `FINANCEIRO_DB_PORT`, `FINANCEIRO_DB_NAME`, `FINANCEIRO_DB_USER`, `FINANCEIRO_DB_PASSWORD`
- DW: `DW_DB_HOST`, `DW_DB_PORT`, `DW_DB_NAME`, `DW_DB_USER`, `DW_DB_PASSWORD`

## Como executar

- Carga Industrial:
```bash
python scripts/load_industrial.py --base "BancoModeloUse/dados_simulados" --periodo "2015_2017"
```

- Carga Financeira:
```bash
python scripts/load_financeiro.py --base "BancoModeloUse/dados_simulados" --periodo "2021_2025"
```

- ETL para DW (gera e/ou carrega dimensões e fatos):
```bash
python scripts/etl_dw.py --acao build
```

Parâmetros úteis:
- `--chunksize`: tamanho de lote para inserção (default: 5000)
- `--if-exists`: comportamento em conflito (append, upsert) – nós implementamos upsert simples por PK.

## Observações
- Os scripts usam os modelos ORM já presentes em `BancoModeloUse/core/models/*` e as conexões em `BancoModeloUse/infrastructure/database/connections/*`.
- Os mapeamentos de colunas para DataFrames são baseados nos cabeçalhos dos CSVs.
- Logs básicos são impressos no stdout; trate warnings/erros conforme necessário.
