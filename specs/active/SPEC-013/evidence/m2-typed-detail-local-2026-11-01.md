# M2 parcial · detalhe tipado local em leitura somente (01/11/2026)

`inference_api/src/inference_api/agent_harness/typed_detail.py` implementa
uma consulta por fonte tipada do recorte piloto. O plano JSON não contém SQL:
somente fonte, campos, filtros de ID/intervalo, limite e grão. O serviço exige
catálogo com status `approved_for_local_query` e fonte `enabled: true`, confere
campos e filtros contra o mapa, compõe identificadores com `psycopg2.sql.Identifier`,
vincula valores como parâmetros, inicia transação `READ ONLY`, aplica timeout,
confere nome do banco conectado e tipos físicos das colunas autorizadas,
ordena por PK e recusa mais linhas/bytes que o limite. Não faz joins.

Cada linha devolvida inclui banco, schema, tabela, PK, período e arquivo/hash de
`canonical_source_file`. Uma origem ausente encerra a consulta. `no_observation`
é separado de zero e nenhum resultado é cortado silenciosamente.

**Teste local real, sem modelo:** o script
`inference_api/scripts/verify_typed_detail_local.py` usou uma cópia **somente
em memória** do candidato com uma fonte habilitada por vez. A cópia foi usada
apenas para testar a função de leitura; o arquivo de catálogo e a Bancada
continuam desabilitados. O [readback](m2-typed-detail-local-readback-2026-11-01.json)
mostra uma linha e proveniência em cada uma das cinco tabelas tipadas, sem
registrar valores das linhas. A primeira conexão usou a credencial local
existente com transação `READ ONLY`.

Após acrescentar a guarda física, o ensaio local foi repetido com sucesso nas
cinco tabelas, sem alterar o arquivo de catálogo. O recibo anterior registra a
mesma seleção de cinco fontes; a repetição em stdout não criou novo arquivo.
Após a [criação da role dedicada](m2-reader-role-2026-11-01.md), o ensaio foi
repetido com `--reader-credentials` e passou nas cinco tabelas. O
[novo readback](m2-typed-detail-reader-readback-2026-11-01.json) identifica
`spec013_reader` sem registrar senha ou valores de linha. O catálogo no disco
continuou desabilitado.

`test_spec013_typed_detail.py` passou em cinco testes simulados: consulta
parametrizada com proveniência, bloqueio antes de abrir banco, limite explícito
de linhas/bytes, filtros temporais e recusa de banco/tipo divergente. Não houve chamada a Groq/OpenAI/RunPod,
escrita em banco nem envio de dados. O motor da Bancada permanece sintético;
consultas DW/linhagem, contrato de retorno versionado, acesso dedicado e
integração do harness real ainda não estão concluídos.
