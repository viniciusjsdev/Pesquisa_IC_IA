# SPEC-013 · formato de filtro de intervalo no Planejador

A primeira repetição I1 sob contrato v4 passou, mas
[I2-r1](m2-groq-i2-r1-2026-11-02.json) parou antes da consulta. O modelo
escolheu `registros_operacao` e propôs `hora_inicio` com operadores
`gte/lte`, depois `gte/lt`. A tool local exige exatamente `from` e `to`
com strings ISO e intervalo `[from,to)`. O mapa aprovado dizia apenas
`hora_inicio:range`; o formato JSON exigido **não era entregue ao Planejador**.
O backend rejeitou ambas as tentativas como `invalid_range_filter`. O run
privado tem SHA-256
`52420829e206b869a31c505e5eab00b86445c0a28756c801e98d804ae88d85c5`.

O contrato de entrada avançou para v4 e inclui `range_filter_format` quando
há filtro `:range`; a tarefa do Planejador avançou para v5 e o feedback de
erro explicita `from`/`to`. O código da tool e o catálogo semântico aprovado
não foram alterados. O modelo continua escolhendo fonte, campos, filtros e
valores; o backend valida sem converter operadores.

SHA-256 dos contratos após a correção: tarefa/saída
`eb5a5da847afac53ede808f73730fe878f64b2d5b4ce881102c21f3c53d7f070`,
entrada `ebe3ded69dda58c36c2a60f31330804506c3d7c3c2f5d59b7c008cb2aa8e1795`.
Os dois runs `i1-r1` e `i2-r1` com hashes anteriores são **ensaios de
engenharia**, não repetições comparáveis. Permanecem preservados, sem nota
final. A nova matriz usa rótulos `v5-<case_id>-r<repetição>`, sem reutilizar
jobs ou traces anteriores. Os testes direcionados passaram: 30 do motor e 8
do adaptador local.
