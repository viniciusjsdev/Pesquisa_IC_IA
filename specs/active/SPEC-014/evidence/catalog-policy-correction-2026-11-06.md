# Correção de catálogo e política — 06/11/2026

SPEC reaberta antes do código. Catálogo aprovado usa versão inteira `1`; API, interface e comparação devem usar inteiro positivo estrito, rejeitando bool, texto e coerções ambíguas. Não editar catálogo, seus hashes ou aprovação.

Fonte explicitamente fora do índice aprovado deve ser negada antes de reparo estrutural tanto no Selecionador quanto no plano do Especialista; tipo ausente ou malformado sem fonte identificável continua erro de schema corrigível. Sem consulta adicional, alteração da política ou fallback.

Validar `prepare` usando `approved_catalog.load` e `compile_maps` reais, com perfil e autorização de teste injetados, sem banco ou rede. Investigar WinError 10053 dos testes HTTP de cookies. Revisão independente necessária antes de `done`.

## Implementação e verificação local

`service._validate_input` exige inteiro positivo estrito; o tipo TypeScript foi alinhado. O teste `test_prepare_with_approved_catalog_and_compiled_maps` usa os carregadores reais do catálogo aprovado e dos 12 mapas, com somente perfil/autorização injetados e conexão de banco proibida. O contrato de saída malformada é testado com fontes externas e outra fonte permitida mas não selecionada; nenhuma consulta adicional ocorre. Fonte permitida com erro estrutural permanece reparável. A auditoria da thread de origem confirmou os dois consertos em seis variantes, sem rede ou banco.

No teste HTTP de cookies, 30 repetições anteriores produziram 7 erros WinError 10053; após usar corpos vazios nos POSTs rejeitados antes da leitura e no logout, 30 repetições passaram. A explicação de reset por bytes não lidos é consistente com o comportamento dos handlers, mas não foi demonstrada como causa exclusiva. O teste continua exigindo 403 e 200, sem retry. O servidor de produção não foi alterado para mascarar o erro.

A segunda auditoria independente também executou experimento loopback: o servidor registrou 403 em 20 POSTs cross-origin e não chamou login/logout; o cliente recebeu 10/10 respostas com corpo vazio e 8/10 com 44 bytes, ocorrendo WinError 10053 nas demais duas. Isso sustenta a hipótese de disputa no fechamento com corpo não consumido; não prova comportamento de todos os clientes nem altera o servidor.

Validação posterior: backend 132 testes, 8 skips; avaliação 21; frontend 17, typecheck, lint e build; integração de navegador A/B × 3 com catálogo fixture numérico e PostgreSQL descartável passou (`local-integration.json`, banco parado). O preflight separado usa catálogo aprovado e mapas reais, mas substitui perfil e autorização; não executa consulta científica. 126 hashes protegidos, incluindo SPEC-013 e diagrama, conferem com o baseline. Nenhum provedor remoto foi chamado. Revisão independente final aprovada, sem bloqueios no escopo local.

Revisão independente: aprovada por `01a1b28c-fc61-71f3-8e0a-bcb77b684bcd` (runtime `gpt-6-astra/high`). Confirmou o gate real de autorização, o catálogo aprovado, política de fonte, reparo permitido, 132 testes/8 skips e integração local. A proteção CSRF continua fechada; abortos de transporte para POST recusado com corpo não foram corrigidos no servidor.
