# Ajuste de feedback JSON — 06/11/2026

SPEC reaberta após auditoria detectar que o feedback de saída estrutural inválida não informava schema e caminho. O reparo fornece identificador, versão e SHA-256 do schema do papel/cenário, caminho derivado apenas de nomes declarados no schema (segmentos de array como `*`), keyword, número da tentativa e saldo atualizado. Não inclui mensagem de exceção nem usa campos arbitrários do modelo para construir o caminho. O papel recebe o feedback na chamada seguinte; bloqueios de política continuam terminais.

Teste `test_nested_schema_error_feedback_reaches_same_role_with_path_and_budget` confirma erro aninhado `/necessidade/medida` e feedback recebido pelo mesmo papel. `test_spec014` passou (13 testes); regressão backend passou (129 testes, 8 skips), avaliação passou (21), integração local A/B × 3 foi repetida com sucesso e revisão independente aprovou o ajuste. Parecer/completion anteriores foram preservados em `*-before-json-feedback-2026-11-06.json`. Nenhuma inferência externa ou edição de diagrama/dados protegidos.

Revisor independente `01a1b28c-fc61-71f3-8e0a-bcb77b684bcd`, runtime observado `gpt-6-astra/high`: aprovou o ajuste, sem achados bloqueantes, após 129 testes (8 skips) e seis verificações em memória. O parecer complementa a revisão anterior; não aprova ensaios remotos nem pontuação científica.
