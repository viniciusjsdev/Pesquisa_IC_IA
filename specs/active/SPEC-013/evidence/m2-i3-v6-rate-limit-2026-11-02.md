# Diagnóstico I3 v6: Revisor validado, limite no Redator

O run diagnóstico `i3-diagnostico-v6` usou apenas Groq/Qwen e o catálogo
aprovado. Job `2721e727-fe0d-4536-9107-2fac9e38979a` e run
`9d55a0c4-dbfd-4654-bcdb-bf1e6ab8330b` persistiram o trace. Houve 11
chamadas de modelo e uma leitura de `paradas_maquinas_geradas` com 13 linhas.
O Revisor validou `result_01` após receber o resultado atual uma vez. O
Redator recebeu HTTP `429` com `Retry-After: 9`; o estado é
`provider_rate_limited`, sem resposta final nem nota científica. Não houve
repetição automática. O snapshot privado tem SHA-256
`f18227e6963a6e0421e5137b593eec8bcb8aed2dbdd1a1b425489975b7abab7b`.

Este diagnóstico demonstra que a correção de contexto permitiu atravessar o
Revisor, mas não prova a causa do erro de provedor no I3 v5. Para novos runs,
o intervalo mínimo entre inícios de chamadas passa de 20 para 35 segundos.
É uma mudança de controle de taxa; pergunta, casos, papéis, contratos JSON,
modelo, dados e orçamento de consultas ficam fixos. Nenhum run anterior será
reutilizado ou repetido. Um novo diagnóstico deverá verificar se o fluxo
completa antes de iniciar a matriz v6.

O novo diagnóstico `i3-diagnostico-v6-spacing35` completou pelo mesmo caminho
HTTP/job/PostgreSQL/Groq: job `49d93f4f-1176-4e8d-b2d2-61e2adf5e0fe`, run
`01f292c9-33f0-4e51-9719-98c1ff395c1b`, 11 chamadas, uma leitura
industrial e estado `answered_unverified`. O snapshot privado tem SHA-256
`e8a8203f27c245dce77cea0dc5be5497869f0def8fccfdfd89b5d9acdf3d67c5`.
Este é um ensaio diagnóstico, não uma repetição da matriz; resposta, cálculo
e conclusão ainda não receberam revisão humana.
