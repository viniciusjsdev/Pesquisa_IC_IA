# SPEC-013 · primeiro I1 completo com dados reais · 02/11/2026

O [recibo público](m2-groq-i1-diagnostico-v4-2026-11-02.json) registra o
diagnóstico `i1-diagnostico-v4`: job
`cb02c2bb-97de-4a4b-819b-1cbbb576bbf2`, run
`9a5aa90c-eace-47eb-9744-2352f8e8481f`, Qwen da Groq, 10 chamadas,
uma consulta `machine` na DW e resposta `answered_unverified`. O GET HTTP
leu o snapshot v6 persistido. O trace privado tem SHA-256
`70fafd686e09f7e171dc9331ed24146b26f30c3b08b62585fdefb25f2d064828`.

Os hashes dos contratos executados foram: tarefa/saída
`db49b24db95d7597cddd6c98a59e9d96ba3a0d79c3a6738827d7b1b4cd136b57`
e entrada
`7465d6ce0e1e01c85e523d4da8e82918198c8e342b681842b9f4b659de0dec02`.
O modelo usou `result_01` para citar a única linha observada. O avaliador
isolado retornou `awaiting_run_review`, com checks automáticos de rota e
referência de evidência iguais a 1. Isso não atribui nota de cálculo ou
conclusão; a pessoa revisora ainda precisa ler o run e o gabarito privado.

O diagnóstico não conta como repetição da matriz. Ele demonstra a rota
HTTP → job → Groq → plano tipado → DW → revisão → resposta → PostgreSQL, com
autenticação bearer de teste mapeada a pesquisador existente. Não demonstra
autenticação de produção nem comparação científica entre modelos.
