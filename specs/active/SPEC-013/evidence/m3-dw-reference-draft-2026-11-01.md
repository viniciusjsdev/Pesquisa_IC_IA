# M3 · referência DW privada para seis casos candidatos (01/11/2026)

`model_evaluation/spec013_reference_draft.py` reexecutou em leitura somente
três consultas `machine` e três `financial` contra a DW V2 local. O script
verificou que o fingerprint da carga coincide com o catálogo candidato, usou
o código de consultas compartilhado e gravou os valores em arquivo privado,
ignorado pelo Git:

`model_evaluation/.local/spec013-pilot-dw-reference-draft-2026-11-01.json`

SHA-256 dos bytes: `04769e61cf5095ff8372b52e91d9cecbdfa65b61a468a7d73b6628c88cd22afd`.
Tamanho: 5.875 bytes. Contagens por consulta: `machine(2021,2000002)` 1,
`machine(2026,1)` 0, `machine(2020,1000002)` 1, `financial(2021)` 13,
`financial(2019)` 0 e `financial(2020)` 0. O relatório versionado não expõe
valores de observações financeiras. Não houve chamada a provedor.

Na primeira tentativa, `financial` revelou um `KeyError: 'operation_rows'`
na montagem de metadados compartilhados, pois a expressão da fonte `machine`
era avaliada para toda consulta. O código foi corrigido para avaliar essa
expressão só em `kind == 'machine'`; os testes de regressão para linha
financeira presente e ausente passaram. O SHA-256 do código de consulta mudou
e faz parte do pacote privado. A tentativa falha não criou arquivo parcial.

Este pacote é apenas material de preparo. Faltam as três referências de
detalhe/linhagem, cálculos/tolerâncias por caso, validação dos limites e
revisão humana individual. Nenhum caso recebeu status `approved`.

Atualização: o [conteúdo dos nove casos foi aprovado](m3-human-case-content-approval-2026-11-01.md)
na versão do pacote revisado. Esta referência ainda precisa ser vinculada a
manifests executáveis antes de qualquer score.
