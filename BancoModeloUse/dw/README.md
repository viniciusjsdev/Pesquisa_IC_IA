# DW de pesquisa — carga V2 ativa

Em 07/11/2026, os arquivos, manifesto, contrato, DER e ingestão da V2 foram
consolidados no checkout principal. [Fontes vigentes e arquivo](../../docs/fontes_ativas_e_arquivo.md).
O banco usado é `db_pesquisa_dw` no cluster isolado `127.0.0.1:5544`.
São 35 tabelas, 167 partições de origem e 1.290 paradas (1.200 originais e
90 geradas). [Readback da integração](../../docs/evidence/organizacao-2026-11-07/canonical-readback.json).

O contrato físico atual está em [contrato_tabelas_canonicas.json](../dados_complementares_datamind/contrato_tabelas_canonicas.json)
e no [DER](../docs/datamind_erd_canonical.drawio.xml). A migração SQL V1 continua
sendo componente usado pelo carregador V2; não é uma segunda carga ativa.
As sete projeções abaixo são a parte herdada da V1; as 20 tabelas adicionais
e os tipos de todas as fontes estão no contrato. As consultas compartilhadas
foram mantidas na versão do principal, incluindo as correções de novembro.

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

`dim_day` usa a data registrada na linha. `dim_source_period` é a partição de importação `0..2`, sem afirmar cobertura da faixa no nome da pasta. `dim_product`, `dim_machine`, `dim_material` e `dim_material_lot` preservam o ID deslocado do importador; registros de mesmo nome em períodos diferentes continuam distintos. Os fatos guardam `source_file_id`, `period_index` e `original_id`. `source_file` guarda caminho relativo, tabela, schema bruto, SHA-256 e contagem. `contributors` enumera, com paginação, os IDs dos fatos por trás de uma linha agregada; `trace` retorna a linha DW e a chave para `db_*.raw_pN.<tabela>` e `db_*.public.<tabela>`.

Associações por ano, produto ou máquina são exploratórias. Venda por produto e operação por produto compartilham uma chave de cadastro, mas venda não tem chave de ordem ou máquina. Resultado financeiro tem somente data. Coincidência temporal não prova causa. O DW não corrige lacunas ou anomalias e não é um gold set.

## Comandos atuais

Na raiz do projeto, com o cluster existente em execução:

```powershell
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/canonical_ingest.py plan
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py verify
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py query product --year 2020 --id 1000001
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py query machine --year 2020 --id 1000001
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py query financial --year 2020
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py contributors product --year 2020 --id 1000001 --limit 100
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py trace fact_sale 1000039
```

`verify` encaminha para `scripts/verify_canonical_load.py` e verifica os três
bancos contra a V2, sem escrita. Confere schema, chaves, contagens e proveniência;
não é comparação célula a célula. `query`, `contributors` e `trace` permanecem
somente leitura. Os filtros continuam limitados às consultas fixas, ano de
2015 a 2026 e ID opcional; não há SQL arbitrário. As conexões conferem host,
porta e diretório do cluster. Credenciais ficam no `.env.local` ignorado.

`build` é o carregador histórico V1 e recusa executar com o manifesto V2.
Uma nova carga exige o plano canônico e decisão explícita; não rodar `load`
para iniciar a aplicação. [Operação dos dados](../README.md).
O exportador de pacotes tem opção explícita V2 (`--dw-v2`); o caminho V1 e os
testes de carga V1 são históricos e não devem validar o banco atual.

## Reconciliação histórica V1 e seus limites

As contagens e verificações desta seção foram observadas na V1 em outubro.
Não representam o inventário completo da V2 atual.



A carga v1 reconciliou 75 arquivos/540.600 linhas fonte, 539.140 linhas tipadas industriais e 1.460 financeiras. Fatos: 429.565 operações, 1.200 paradas, 120 vendas, 72 observações financeiras, 4.021 inspeções, 1.800 consumos e 180 observações de preço. Dimensões: 15 produtos, 13 máquinas, 30 materiais e 650 lotes de material. Em 16/10/2026, `verify()` comparou **cada coluna carregada** dos sete fatos e quatro dimensões de origem com a mesma projeção da carga, além do manifesto, três partições, 4.019 dias e somas de controle. Divergência de valor, data, vínculo ou quantidade de linhas falha sem substituir a carga. As somas `quantidade_produzida_real` (61.592.575), `quantidade_vendida` (107.089) e valor das vendas observadas (5.414.227,91) coincidiram entre fonte tipada e DW. O relatório registra os valores sem caracterizá-los como produção final, receita contábil ou custo realizado.

Os flags iniciais incluem 224.336 linhas de operação ligadas a ordens com datas invertidas, 9 operações fora da faixa escrita no nome da pasta, 2.258 inspeções cuja soma aprovada+rejeitada supera a quantidade do lote e 2 inspeções fora da faixa escrita na pasta. Todas as 72 observações financeiras vieram de colunas `Float` no ORM, portanto a representação tipada já tem esse limite. O relatório contém exemplos de IDs por flag e amostras de linhagem raw/public. No CSV, 339/650 **ordens** têm início posterior ao fim; o número de operações afetadas não é o número de ordens distintas.

`resultados_financeiros` tem 72 linhas com datas em 2015, 2017–2018 e 2021–2023. Não há observações dessa tabela em 2016, 2019–2020 e 2024–2025. Mesmo nos anos presentes, as datas não formam meses únicos completos: por exemplo, as 12 linhas de 2015 ocupam 10 meses distintos. A consulta expõe essa cobertura e não calcula um total anual. Dados simulados podem ser inconsistentes; uma validação científica do benchmark exige protocolo e gabarito separados.

A SPEC-009 centralizou as cinco consultas SQL em `fixed_queries.py` para a CLI,
o exportador e as tools da Bancada. Cada chamada da API usa conexão explícita
limitada a `db_pesquisa_dw` e transação somente leitura. A mudança de código
altera o hash de consulta de novos pacotes; pacotes antigos preservam o hash
registrado na sua exportação.

Em 22/10/2026, a Bancada passou a oferecer também `groq` + `dw_tools` após
autorização explícita do pesquisador. A consulta permanece fixa e somente
leitura nesta DW; o resultado limitado é enviado ao provedor externo para o
turno seguinte. Veja o [recibo do ensaio real](../../specs/active/SPEC-010/evidence/groq-dw-real-2026-10-22.md).

## Correção de metadados das consultas fixas (01/11/2026)

Ao preparar referências locais da SPEC-013, uma chamada `financial` expôs que
`fixed_queries.query()` construía a lista de fontes de `machine` mesmo para
outros tipos de consulta. Isso gerava `KeyError: 'operation_rows'` quando o
resultado financeiro tinha linhas. A lista dinâmica de fontes de máquina
agora é construída somente em `kind == 'machine'`; a consulta SQL e os campos
dos demais tipos não foram alterados. Há testes de regressão para observação
financeira presente e ausente. A mudança altera o SHA-256 do arquivo de
consultas; novos pacotes devem registrar o hash novo, sem reescrever pacotes
históricos.
