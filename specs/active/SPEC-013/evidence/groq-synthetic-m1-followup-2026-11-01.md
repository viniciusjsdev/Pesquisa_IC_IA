# Ensaios de correção do protocolo com Qwen na Groq — 01/11/2026

Cinco execuções diretas do `synthetic_demo.py` usaram
`qwen/qwen3.8-27b` via Groq, com pergunta, mapas e resultados inventados.
Nenhuma acessou PostgreSQL, GPT ou RunPod. O cliente usa
`GROQ_HARNESS_MODEL`, separado do `GROQ_MODEL` geral. O script não repete uma
falha de provedor. Os traces JSON completos estão preservados:

| Trace | Chamadas | Consultas | Desfecho observado |
| --- | ---: | ---: | --- |
| [Primeira tentativa](groq-synthetic-m1-retry-2026-11-01.json) | 4 | 0 | O Selecionador indicou simultaneamente `consultar` e `dominio_adicional`; `invalid_consult_decision`. |
| [Após feedback semântico](groq-synthetic-m1-correction-2026-11-01.json) | 7 | 0 | O Selecionador foi corrigido; o Planejador recebeu trecho sem colunas e esgotou a correção com `campos=[]`. |
| [Após exigência de campos](groq-synthetic-m1-fields-2026-11-01.json) | 3 | 0 | O Especialista recebeu feedback e citou colunas, mas omitiu o ID da fonte; rejeição explícita. |
| [Após referência completa](groq-synthetic-m1-source-refs-2026-11-01.json) | 7 | 0 | Os dois Especialistas corrigiram ID e colunas; o Selecionador confundiu domínio `dw` com fonte `dw_paradas` e esgotou sua correção. |
| [Após IDs de fonte explícitos](groq-synthetic-m1-source-choice-2026-11-01.json) | 4 | 0 | A Groq devolveu `429` antes da decisão do Selecionador. Não houve reenvio. |

O orquestrador agora devolve violações semânticas ao mesmo papel uma vez,
com código e dica visíveis no trace. O contrato dos especialistas exige ID da
fonte e colunas; o Selecionador recebe `available_source_ids` explícitos.
Os testes simulados cobrem esses caminhos. O ensaio real após a última correção
foi interrompido pela cota, portanto **não confirma uma cadeia completa**.
