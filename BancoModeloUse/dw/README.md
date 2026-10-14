# DW local de pesquisa (SPEC-006)

**Estado em 13/10/2026:** esquema e carga local v1 implementados em `db_pesquisa_dw`, no cluster isolado `127.0.0.1:5544`. A carga nova foi criada após verificação somente leitura dos dois bancos de origem; o relatório local ignorado pelo Git fica em `../reports/dw_validation.json`. O fingerprint inicial dos 75 arquivos é `64493abfdfd0b87535778eafd9d5938fad6039a99d9307f85e4cfc6eec0e89f2`. Esta evidência é local, não prova integração ao backend, harness ou validade científica.

`db_datamind_dw` é legado e permanece intocado. O novo banco não substitui `db_industrial` e `db_financeiro` nem altera suas cargas. Os CSVs preservados são a fonte bruta; as tabelas `public` dos dois bancos são a fonte tipada. A validação do importador compara ambas com os CSVs antes de criar o DW.

Para a comparação futura dos modelos, a [arquitetura de avaliação](../docs/arquitetura_avaliacao_modelos.md) separa evidências fixas de pesquisa com tools. A [SPEC-007](../../specs/active/SPEC-007/SPEC.md) documenta um exportador local de pacotes fixos a partir das consultas da DW; ele ainda não foi implementado. O harness, a escolha de tools pela LLM e a integração da DW à API também permanecem pendentes. A revisão independente da SPEC-006 ainda precisa ser reconciliada antes de usar estes dados como casos científicos oficiais.

## Perguntas e grãos

| Fato | Uma linha por | Vínculos comprovados | Uso permitido |
| --- | --- | --- | --- |
| `fact_operation` | `registros_operacao.registro_id` | ordem, produto e máquina industriais | Contagem e soma da quantidade **reportada por operação**. Uma peça pode passar por etapas repetidas. |
| `fact_downtime` | `paradas_maquinas.parada_id` | máquina industrial | Minutos de parada atribuídos ao dia do início; sem FK para operação. |
| `fact_sale` | `vendas.venda_id` | produto industrial do mesmo índice de importação | Soma de `quantidade_vendida * preco_unitario_venda`, somente vendas observadas. |
| `fact_financial_observation` | `resultados_financeiros.id` | data efetiva | Valores reportados por linha; sem atribuição a produto, ordem ou máquina e sem soma anual publicada. |
| `fact_quality_inspection` | `controle_qualidade.controle_id` | lote de produção, ordem, produto | Unidades inspecionadas reportadas; podem repetir lote ou superar quantidade do lote. |
| `fact_material_consumption` | `consumo_materiais.consumo_id` | operação, material e lote de material | Quantidade consumida observada. |
| `fact_material_price_observation` | `materiais_custo_historico.custo_material_id` | material e lote de material | Preço histórico observado; não é custo realizado do consumo. |

`dim_day` usa a data registrada na linha. `dim_source_period` é a partição de importação `0..2`, sem afirmar cobertura da faixa no nome da pasta. `dim_product`, `dim_machine`, `dim_material` e `dim_material_lot` preservam o ID deslocado do importador; registros de mesmo nome em períodos diferentes continuam distintos. Os fatos guardam `source_file_id`, `period_index` e `original_id`. `source_file` guarda caminho relativo, tabela, schema bruto, SHA-256 e contagem. `trace` mostra a chave para voltar a `db_*.raw_pN.<tabela>` e `db_*.public.<tabela>`.

Associações por ano, produto ou máquina são exploratórias. Venda por produto e operação por produto compartilham uma chave de cadastro, mas venda não tem chave de ordem ou máquina. Resultado financeiro tem somente data. Coincidência temporal não prova causa. O DW não corrige lacunas ou anomalias e não é um gold set.

## Comandos

Na raiz do repositório, após iniciar o cluster já existente:

```powershell
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py start
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py build
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py verify
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py query product --year 2020 --id 1000001
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py query machine --year 2020 --id 1000001
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py query financial --year 2020
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py query quality --year 2020
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py query material --year 2020 --id 1000001
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py trace fact_sale 1000001
```

`build` faz o inventário dos 75 CSVs e uma verificação completa e somente leitura de `raw_pN`/`public`. Depois cria **somente** `db_pesquisa_dw`, executa `migrations/001_init.sql` e a carga numa transação. Se falhar, o banco novo pode ficar vazio, mas as tabelas não são parcialmente publicadas. Repetir `build` com o mesmo fingerprint confere a carga e retorna `already_current`, sem recriar objetos. Se qualquer fonte mudou, o comando recusa substituir a carga existente. Uma versão nova exige migração e plano de reconciliação explícitos. `verify`, `query` e `trace` fazem apenas leitura nos bancos; `verify` atualiza o arquivo de relatório local.

As consultas recebem somente nomes da lista fixa, ano de 2015 a 2026 e ID opcional. Retornam fórmula, unidade, grão, tabelas fonte, cobertura e limite de interpretação. `financial` retorna cada observação datada e meses representados; ano sem linha retorna `no_observation`. Não existe SQL arbitrário. O código confere host, porta e `data_directory` do cluster; não aceita o serviço PostgreSQL de `localhost:5432`. Credenciais ficam no `.env.local` ignorado.

## Reconciliação e limites observados

A carga v1 reconciliou 75 arquivos/540.600 linhas fonte, 539.140 linhas tipadas industriais e 1.460 financeiras. Fatos: 429.565 operações, 1.200 paradas, 120 vendas, 72 observações financeiras, 4.021 inspeções, 1.800 consumos e 180 observações de preço. Dimensões: 15 produtos, 13 máquinas, 30 materiais e 650 lotes de material. As somas `quantidade_produzida_real` (61.592.575), `quantidade_vendida` (107.089) e valor das vendas observadas (5.414.227,91) coincidiram entre fonte tipada e DW. O relatório registra os valores sem caracterizá-los como produção final, receita contábil ou custo realizado.

Os flags iniciais incluem 224.336 linhas de operação ligadas a ordens com datas invertidas, 9 operações fora da faixa escrita no nome da pasta, 2.258 inspeções cuja soma aprovada+rejeitada supera a quantidade do lote e 2 inspeções fora da faixa escrita na pasta. Todas as 72 observações financeiras vieram de colunas `Float` no ORM, portanto a representação tipada já tem esse limite. O relatório contém exemplos de IDs por flag e amostras de linhagem raw/public. No CSV, 339/650 **ordens** têm início posterior ao fim; o número de operações afetadas não é o número de ordens distintas.

`resultados_financeiros` tem 72 linhas com datas em 2015, 2017–2018 e 2021–2023. Não há observações dessa tabela em 2016, 2019–2020 e 2024–2025. Mesmo nos anos presentes, as datas não formam meses únicos completos: por exemplo, as 12 linhas de 2015 ocupam 10 meses distintos. A consulta expõe essa cobertura e não calcula um total anual. Dados simulados podem ser inconsistentes; uma validação científica do benchmark exige protocolo e gabarito separados.
