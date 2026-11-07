# SPEC-009 — conferência das tools da DW em 22/10/2026

Checkout base `13d7df5c748f79387d34f39cd30b6cf82c96c869`. Conferência
local em `127.0.0.1:5544`, usando `inference_api.dw_tools` contra
`db_pesquisa_dw`. Não houve carga, migração, escrita no DW, novo run
persistido, chamada à Groq ou execução na RunPod.

## Leitura da DW atual

`dw_tools.availability()` retornou `available=True`, migração v1 e prefixo
do fingerprint `64493abfdfd0`. As cinco chamadas de `dw_tools.execute()`
usaram `expected_fingerprint` e transações `READ ONLY`:

| Tool | Argumentos | Resultado observado |
| --- | --- | --- |
| `product` | `year=2020, id=1000001` | 1 linha; cobertura `observed` |
| `machine` | `year=2020, id=1000001` | 1 linha; cobertura `observed` |
| `financial` | `year=2021` | 13 linhas; cobertura `observed` |
| `quality` | `year=2020, id=1000001` | 1 linha; cobertura `observed` |
| `material` | `year=2020, id=1000001` | 1 linha; cobertura `observed` |

Os valores e linhas da DW não foram copiados para este recibo.

## Caminho do serviço

`service.execute_run()` recebeu uma escolha simulada do modelo para
`product(year=2020,id=1000001)`. A função `dw_tools.execute()` permaneceu
real, consultou a DW e devolveu uma linha. O segundo turno recebeu uma
mensagem de tool; o snapshot em memória terminou `answered_unverified`, com
`tool_trace[0].status=returned`. Somente `models.chat_turn` e
`storage.create_run` foram substituídos por mocks. Isso verifica a integração
local entre orquestração e DW, mas não é nova inferência por uma LLM.

## Leitura de runs anteriores

O banco da aplicação conserva dois runs `dw_tools` da base `qwen-base` com
`product` em estado `returned`: `f2cf4be7-abf0-4bcf-9ab6-a1a30a9ffe93`
e `4a9cc490-0afe-4117-957f-2e98d733df16`, ambos de 17/10/2026 e
`answered_unverified`. As evidências das sessões
[de integração](../../../../runpod/serving/evidence/2026-10-17-integracao-bancada.md)
e [dos sete aliases](../../../../runpod/serving/evidence/2026-10-17-bancada-sete-aliases.md)
registram que a LLM da RunPod escolheu essa tool e a consulta fixa respondeu.
Os snapshots v3 não trazem campo `provider`; essa proveniência vem das
evidências da sessão, não de um campo novo no banco.

O teste real Groq da SPEC-010 chamou somente `synthetic_metric` e uma fixture
inventada. O contrato atual recusa `dw_tools` para Groq. Logo, esta conferência
não demonstra Groq consultando a DW nem avalia a qualidade científica das
respostas.
