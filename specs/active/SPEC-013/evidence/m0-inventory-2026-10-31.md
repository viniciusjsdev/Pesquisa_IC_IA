# M0 — inventário físico local, somente leitura (31/10/2026)

**Tipo de evidência:** readback de carga já existente. Esta checagem não criou
bancos, tabelas, registros ou usuários, não executou ingestão, não testou
inferência e não constitui avaliação científica.

- Cluster isolado do projeto: `127.0.0.1:5544`, com `data_directory` conferido
  pelo conector `BancoModeloUse/scripts/bootstrap_local.py`. O `pg_ctl status`
  indicou o processo desse cluster em execução.
- Bancos presentes: `db_industrial`, `db_financeiro`, `db_pesquisa_dw` e os
  preexistentes `db_datamind_dw` (legado), `db_inference_app`, `postgres`.
- Comparação por `information_schema.columns` contra
  `contrato_tabelas_canonicas.json` do worktree
  `C:/Users/vinic/.codex/worktrees/datamind-dw-rebuild/Pesquisa_IC_IA`:
  **56 tabelas de origem** (38 industriais, 18 financeiras), sem divergência
  de nomes, ordem ou tipos de coluna. `public` contém ainda objetos auxiliares;
  a contagem de todas as tabelas `public` é 39/19, respectivamente.
- `db_pesquisa_dw.dw`: **35 tabelas**. Para as 20 novas, a comparação dos
  campos tipados gerados pelo `DW_TABLES` + contrato de origem, mais
  `source_file_id`, `period_index` e `original_id`, encontrou **240 colunas**
  físicas esperadas, sem divergência de nome, ordem ou tipo. As 20 PKs
  (`source_file_id`, `original_id`) e as FKs de `source_file_id` e
  `period_index` para as dimensões de proveniência também coincidiram com o
  código. As outras 15 tabelas são as da migração V1; não se reexecutou aqui
  uma comparação completa de todas as suas colunas.
- `dw.schema_migrations`: versão **2**, fingerprint
  `66f8808cf83902ff6c7fd277937bf8e0671482058f540f3ea9c1ec8c5a182800`,
  igual ao SHA-256 calculado sobre os arquivos atuais de manifesto e contrato
  canônicos. O contrato e o carregador ainda são arquivos não commitados no
  worktree separado, ambos em HEAD `13d7df5`.
- `dw.source_file`: **167 partições**, com soma de **1.565.666 linhas**,
  igual à soma do manifesto (166 CSVs; um arquivo gera duas partições).
- `db_industrial.public.paradas_maquinas_geradas`: **90 linhas**.
  `dw.fact_downtime` contém **1.200** linhas de `paradas_maquinas` e **90**
  de `paradas_maquinas_geradas`, identificadas via `dw.source_file`.
- Um `trace('fact_downtime', id)` de parada gerada recuperou as linhas `raw`
  e `public` da fonte correta. `contributors('machine', ano, maquina_id)`
  incluiu o mesmo ID no agregado. Porém, `fixed_queries.py` **deste checkout**
  retornou para a consulta `machine` apenas `paradas_maquinas` na lista
  `sources`, embora o agregado inclua a parada gerada. O worktree canônico tem
  uma correção local ainda não reconciliada. O mapa e as tools da SPEC-013 não
  podem herdar essa proveniência incompleta.
- `dw/cli.py` deste checkout fixa `VERSION = 1`; a chamada somente leitura
  `target_state` contra a DW V2 recusou a migração com `Unknown or incomplete
  DW migration`. `model_evaluation/export.py` chama `dw.verify()` e exige
  `schema_version == 1`, portanto a preparação de novos pacotes do cenário A
  não está compatível com esta carga V2. A SPEC-013 deve exigir uma verificação
  V2 consciente e testes de compatibilidade, preservando snapshots antigos.

As verificações usaram transações `SET TRANSACTION READ ONLY`, consultas a
`pg_database`, `information_schema`, `pg_constraint`, `dw.schema_migrations`,
`dw.source_file` e contagens delimitadas. Não houve comparação linha a linha
dos 1.565.666 registros nem teste de desempenho/concorrência. O fato de o
schema físico coincidir não aprova grãos, unidades, relações entre domínios,
fontes habilitadas ou gabaritos do harness. Antes de `ready`, reconciliar no
checkout de implementação o código/manifesto que hoje estão no worktree
separado, corrigir a lista de fontes da tool `machine` e fechar DEC-001–005 da
SPEC-013.
