# SPEC-013 · filtros entregues ao Planejador · 02/11/2026

O [diagnóstico I1 v3b](m2-groq-i1-diagnostico-v3b-2026-11-02.json) persistiu
job e trace: nove chamadas Groq, nenhuma consulta e `contract_error`.
O Especialista terminou, mas o Planejador propôs filtro `machine_id` como
texto. A fonte aprovada `machine` declara filtros `year:integer:2015..2026`
e `id:positive_integer`. O backend rejeitou as duas tentativas. A análise do
envelope mostrou que o Planejador recebia somente fonte, campos e grão;
**as especificações de filtro se perdiam entre Especialista e Planejador**.
O trace privado tem SHA-256
`e0e5dbed973766308105d19950edc5c4b48ea513de7026d0395e5c2795c55348`.

O contrato de entrada do Planejador avançou para versão 3 e agora exige
`map_snippet.filter_specs`, projetado somente da fonte selecionada. O contrato
de tarefa avançou para versão 4 e instrui o uso das chaves e tipos literais.
O feedback de consulta rejeitada repete os filtros permitidos. A validação da
tool continua no backend e rejeita filtro DW inválido com
`filters_outside_catalog`, sem executar SQL ou corrigir plano por conta própria.
O catálogo semântico aprovado e as fontes habilitadas não mudaram.

SHA-256 dos contratos atuais: saída/tarefa
`db49b24db95d7597cddd6c98a59e9d96ba3a0d79c3a6738827d7b1b4cd136b57`;
entrada
`7465d6ce0e1e01c85e523d4da8e82918198c8e342b681842b9f4b659de0dec02`.
Os diagnósticos anteriores ficam fora da matriz. Os testes direcionados do
motor (30) e do adaptador local (8) passaram. Ainda falta demonstrar uma
consulta real concluída pelo modelo.
