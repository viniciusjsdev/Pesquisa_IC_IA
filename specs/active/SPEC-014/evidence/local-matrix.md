# Matriz e evidência de aceite local — 06/11/2026

| AC | Evidência e limite |
|---|---|
| 001 | `test_spec014` recusa modos legados; `local-integration.json` confirma duas opções, reabertura e export histórico. |
| 002 | `test_matrix_2_scenarios_3_adapters_exact_body_and_identity`: 2×3 com SSE fake, hash do corpo e mesmo modelo; parâmetros inválidos sem envio. Não confirma disponibilidade real. |
| 003 | pacote alterado, fonte e ação proibidas, ausência de evidência e spies de pesquisa são testados em `test_spec014`. |
| 004 | três fontes e correção do mesmo especialista com orçamento; integração faz leituras SQL em PostgreSQL descartável fixture por adaptador fixture de consulta. Não é execução contra a carga científica. |
| 005 | testes de feedback aninhado com schema/path/tentativa/saldo, JSON inválido, teto, recusa, 429, timeout, interrupção, cancelamento, consumo ausente, modelo divergente e recibos; sem retry oculto. |
| 006 | export antigo/novo na integração, testes de comparação v7 e protocolo humano `not_scored`; proveniência e drift são comparados. |
| 007 | `local-integration.json`: navegador → autenticação → job → resposta → histórico/exportação para 2×3 e erro, servidor SSE fake, banco isolado parado. |
| 008 | backend 132 testes, 8 skips; model_evaluation 21; frontend 17; typecheck, lint e build passaram. Skips são pré-existentes e não substituem matriz local. Revisão independente local aprovada; ver `review.json`. |

O inventário das 27 expectativas legadas retiradas consta em `retired-test-contracts.json`; não afirmar que quantidade de testes prova equivalência funcional. Nenhuma execução paga, externa ou científica foi realizada. O parecer independente não substitui adjudicação humana de respostas.

Correção após auditoria: preflight com catálogo e mapas aprovados reais, fonte proibida antes de reparo e parecer independente em `catalog-policy-correction-2026-11-06.md`.
