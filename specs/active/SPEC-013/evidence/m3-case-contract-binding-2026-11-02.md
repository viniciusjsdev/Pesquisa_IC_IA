# M3 · vínculo técnico dos nove casos piloto (02/11/2026)

O conteúdo I1–I3, F1–F3 e X1–X3 continua vinculado ao
[recibo humano de 01/11](m3-human-case-content-approval-2026-11-01.md).
`model_evaluation/materialize_spec013_pilot_cases.py` verificou os hashes do
pacote revisado e das duas referências, extraiu as perguntas e materializou
um contrato privado por caso com plano/filtro, hash do resultado de referência,
unidade, fórmula, tolerância exata e rotas aceitáveis. O arquivo privado atual
`model_evaluation/.local/spec013-pilot-case-contracts-2026-11-02-v3.json`
tem SHA-256
`279e91fdccc289d75dea3ab02495d708bf99b753cbd09dcf8a208246784c1532`.
As versões v1 e v2 do mesmo dia foram preservadas; a v2 acrescentou fórmulas
e a v3 acrescentou o estado esperado da evidência por fonte, inclusive
`no_observation`. Use apenas a v3 para a próxima revisão.

As consultas de referência foram reexecutadas no PostgreSQL local em
transações `READ ONLY`, sem chamar provedor. O replay DW produziu exatamente
o mesmo SHA-256 do arquivo revisado:
`04769e61cf5095ff8372b52e91d9cecbdfa65b61a468a7d73b6628c88cd22afd`
(6 consultas, respectivamente 1/0/1/13/0/0 linhas). O replay de detalhe e
linhagem também produziu o mesmo SHA-256:
`33c8005b327e1209c6bc49feefff702daf9af0e49b9f85f9a3abdfb5743f69bb`
(13 paradas geradas, 11 vendas, 38 IDs contribuidores e 13 IDs gerados
presentes na DW). Os arquivos de replay estão em `model_evaluation/.local/`.

O catálogo em disco continua `candidate_not_enabled`; nenhum dado real foi
enviado a agente ou provedor. Este vínculo técnico ainda não ativa score: o
motor real precisa executar as rotas sob o catálogo aprovado, e cálculo e
conclusão de cada run precisam de revisão humana. A revisão independente da
SPEC permanece pendente.
