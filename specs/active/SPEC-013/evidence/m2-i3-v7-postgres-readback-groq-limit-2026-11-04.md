# Diagnóstico I3 v7 em 04/11: duas consultas concluídas, limite no Redator

O ensaio único `i3-diagnostico-v7-20261104b` foi executado após
`pg_isready` confirmar `127.0.0.1:5544 - accepting connections` e o smoke
local com catálogo aprovado completar 17 chamadas programadas e três consultas
(DW, industrial e financeiro), sem provedor. A transmissão delimitada à
Groq/Qwen já estava aprovada; este ensaio não integra a matriz científica.

O job `a8e2f3e1-b188-4bcc-ad8e-4c4b38757cd8` terminou `completed` no sentido
de que seu resultado foi persistido, com run
`a01c40a5-2e11-4b11-9866-c9a491055026`. A execução do harness terminou
`provider_rate_limited`: 17 chamadas de modelo, duas consultas reais
concluídas, primeiro em `paradas_maquinas_geradas` e depois em `machine`.
O Revisor validado da rodada 1 decidiu `precisa_aprofundar`, sugerindo DW;
o da rodada 2 decidiu `suficiente`. A chamada final do Redator recebeu HTTP
429 da Groq (`Retry-After: 3`). Não houve resposta final, repetição automática
nem nota científica. O PostgreSQL permaneceu acessível durante o ensaio e
respondeu a `pg_isready` após seu término. Isto não demonstra a causa da queda
anterior nem estabilidade sustentada em todas as condições.

O [recibo público](m2-groq-i3-diagnostico-v7-20261104b-2026-11-02.json)
registra caso, modelo, hashes, job, run, fontes, estados das chamadas e ausência
de score. O sufixo `2026-11-02` é o padrão de nome do verificador; o rótulo
único e este registro identificam a execução de 04/11. O snapshot privado
está em
`model_evaluation/.local/spec013-groq-i3-diagnostico-v7-20261104b-2026-11-02.json`,
SHA-256 `081c866499eac5513ced92a00b3efaedfd84cef3f5fce5bd4e77bfe7988ac773`.
Ele contém pergunta, entradas, saídas e dados, e não deve ser publicado nem
enviado aos agentes como gabarito.

O gate de uma cadeia v7 **com resposta final** ainda está aberto. A matriz
comparável de 27 runs, a adjudicação humana por run e a revisão técnica
independente continuam pendentes.
