# M2 · conta local de leitura do piloto (01/11/2026)

Após a aprovação da política piloto, `inference_api/scripts/provision_spec013_reader.py`
criou no cluster isolado `127.0.0.1:5544` a role `spec013_reader`, sem
privilégios elevados, herança ou escrita. A senha foi gerada localmente e
guardada somente em `inference_api/.local/spec013_reader_credentials.json`,
ignorado pelo Git. Nenhuma senha foi impressa ou incorporada a este recibo.

O [readback v3](m2-reader-role-readback-2026-11-01-v3.json) confirmou:

| Banco | Tabelas com SELECT | SELECT fora da lista | Privilégios de escrita |
| --- | ---: | ---: | ---: |
| `db_pesquisa_dw` | 12 | 0 | 0 |
| `db_industrial` | 4 | 0 | 0 |
| `db_financeiro` | 3 | 0 | 0 |

A role tem `default_transaction_read_only=on`; o script abriu conexão com
ela em cada banco, executou `SELECT ... LIMIT 0` em todas as tabelas
permitidas e conferiu ausência de `CREATE` no schema. O primeiro readback,
antes de acrescentar a verificação explícita de escrita/SELECT externo, foi
preservado. O script acrescentou duas regras específicas dessa role no topo
do `pg_hba.conf` do cluster isolado, recarregou a configuração e comprovou:
conexão aos três bancos permitidos funciona e a conexão a `postgres` é
rejeitada. O script também exige `listen_addresses=127.0.0.1`, de modo que
essa role só pode usar o listener IPv4 local configurado para o piloto.
A role não foi ligada à Bancada e o catálogo continua
`enabled:false`. Nenhum dado foi transmitido a provedor.

Um smoke adicional abriu `db_pesquisa_dw` com a role e executou as cinco
consultas fixas de `fixed_queries.query()` em 2021, com ID `1` para as
consultas que exigem dimensão. Todas completaram sem erro de permissão;
`financial` devolveu 13 linhas e as demais zero para esse ID/ano. Isso
verifica execução autorizada, não cobertura de todos os filtros ou casos.
