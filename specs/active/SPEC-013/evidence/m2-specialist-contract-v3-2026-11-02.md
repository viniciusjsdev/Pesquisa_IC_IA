# SPEC-013 · correção do contrato do Especialista · 02/11/2026

O [diagnóstico I1 com espaçamento](m2-groq-i1-diagnostico-paced01-2026-11-02.json)
chegou à segunda chamada do Especialista duas vezes, sem `429`, mas o Qwen
devolveu em `map_refs` `machine.year`. O trecho aprovado da fonte `machine`
lista `machine_id`, `operation_rows`, `reported_operation_quantity`,
`downtime_rows` e `downtime_minutes`; `year` é filtro da consulta, não campo
selecionável. O backend rejeitou as duas saídas com
`specialist_ref_outside_domain_map`, sem consultar o banco. O trace privado
tem SHA-256 `c3d8e4fe37219bbcddf3d78dcfa56b14a0a0a5036f7f12f92a8c4bd74f98e8ce`.

O contrato de saída do Especialista avançou para `version=3`. A tarefa agora
explicita que `map_refs` contém o ID literal da fonte e apenas `fonte.campo`
para colunas listadas em `domain_detail.sources[fonte].fields`. Filtros e grão
não entram como referências se não estiverem nessa lista. Quando houver erro,
o feedback da mesma chamada lista os IDs permitidos para o trecho recebido.
O backend mantém a validação e o máximo de uma correção; não aceita nem
reescreve uma referência inválida por conta própria.

Esse ajuste muda o hash do contrato e o `case_fingerprint`. Comparações de
modelos devem usar somente runs produzidos sob o mesmo contrato v3. Os
diagnósticos anteriores, com contrato v2, ficam fora da matriz. Os 29 testes
do motor passaram após a alteração. Ainda não há resposta I1 completa.
