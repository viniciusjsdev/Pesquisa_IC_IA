> **Nota de localização em 07/11/2026:** a V2 foi integrada ao checkout principal. Os caminhos de worktree abaixo registram a execução histórica. Para uso atual, consulte [fontes vigentes](../../docs/fontes_ativas_e_arquivo.md).

# Carga canônica DataMind — 31/10/2026

Estado verificado no checkout `13d7df5` com alterações locais ainda não
commitadas. O código e os 166 CSVs usados estão no worktree
`C:/Users/vinic/.codex/worktrees/datamind-dw-rebuild/Pesquisa_IC_IA`.
O cluster PostgreSQL isolado é o do checkout principal em
`D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/BancoModeloUse/.local/postgres`,
escutando em `127.0.0.1:5544`. O conector conferiu o `data_directory` antes
da escrita. Os dumps anteriores ao DROP permanecem em
`C:/Users/vinic/.codex/archives/datamind_db_before_canonical_20261029`.

## Execução

1. `python BancoModeloUse/scripts/canonical_ingest.py plan` passou offline:
   166 CSVs, 167 partições de carga, 56 tabelas de origem, 20 tabelas novas
   da DW e 1.565.666 linhas de origem. Conferiu também o DER salvo, o contrato,
   a migração V1 e os 180 pares coluna/tipo das tabelas novas.
2. Antes da carga, a consulta ao catálogo retornou zero bancos com os três
   nomes de destino. O comando `load --database-home
   D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/BancoModeloUse` criou e
   carregou `db_industrial`, `db_financeiro` e `db_pesquisa_dw` sem erro.
3. `verify_canonical_load.py --database-home` fez leitura independente do
   PostgreSQL depois do commit. O relatório JSON está em
   [carga_canonica_readback_2026-10-31.json](carga_canonica_readback_2026-10-31.json),
   SHA-256 `e1b4456cdac1dbbfcf1cbcc2129a7e1e3190fa00760f193f2573c1e796a1bbd8`.

## Resultado lido do banco

| Banco | Tabelas tipadas | Partições CSV | Linhas de origem | FKs físicas |
| --- | ---: | ---: | ---: | ---: |
| `db_industrial` | 38 | 113 | 1.561.794 | 12 |
| `db_financeiro` | 18 | 54 | 3.872 | 1 |

Na DW, 15 tabelas V1 e 20 tabelas novas coincidiram em nome, ordem das
colunas, tipo e chave primária com o DER/contrato. As 20 novas têm duas FKs
físicas de proveniência cada. `dw.source_file` registrou 167 partições com
caminho, SHA-256 e contagem iguais ao manifesto, somando 1.565.666 linhas
de origem. Todos os 167 schemas/tabelas brutos e os 56 tipados foram lidos
e suas contagens coincidiram com o manifesto.

`dw.fact_downtime` contém **1.290 linhas**: 1.200 de `paradas_maquinas` e 90
de `paradas_maquinas_geradas`. As sete tabelas de fatos V1 e as 20 novas
passaram na reconciliação de contagem por fonte. A migração gravada é a versão
2 com fingerprint
`66f8808cf83902ff6c7fd277937bf8e0671482058f540f3ea9c1ec8c5a182800`.

Esta evidência confirma criação, esquema físico, inventário de arquivos,
contagens e proveniência das paradas. Não é uma comparação célula a célula de
todos os valores nem uma validação científica dos dados simulados. Estrutura
de consultas e acesso dos modelos ficam fora desta etapa. O cluster foi
deixado em execução após a leitura para permitir inspeção local.
