---
id: SPEC-003
title: Identidade individual e limites de uso da API compartilhada
status: ready
contract_version: 1
---

# SPEC-003: Identidade individual e limites de uso da API compartilhada

## Goal

Substituir o token único e o autor declarado no navegador por identidade
individual verificada pelo backend, preparando acesso compartilhado de curta
duração sem expor PostgreSQL ou segredos da RunPod.

## Context

A API local em `inference_api/` aceita `INFERENCE_API_TOKEN` e grava o campo
`author` enviado pelo navegador. Isso foi suficiente para validação local, mas
não prova quem executou cada pergunta. O ngrok ainda não está ativo.

## Scope

- Criar gestão local explícita de pesquisadores e credenciais individuais para
  a sessão: emissão/revogação por CLI, token mostrado uma única vez, somente
  digest com sal persistido em `db_inference_app`, sem contas automáticas.
- Resolver identidade e autorização no backend em toda rota de leitura/escrita;
  autor de prompt, run e feedback vem do principal autenticado, ignorando ou
  recusando o campo `author` do corpo.
- Definir acesso de leitura ao histórico compartilhado, gravação de revisões e
  feedback, e revogação durante a sessão. Registrar identificador estável no
  snapshot sem gravar token ou digest.
- Adicionar limites configuráveis por usuário e globais para novas inferências,
  tamanho de entrada e concorrência; devolver erro claro quando excedidos.
- Preparar política/configuração ngrok com autenticação na borda, mas não abrir
  túnel. Testar que só o HTTP da aplicação é alvo, jamais porta 5544.

## Non-scope

- Abrir túnel, criar contas reais, distribuir tokens, iniciar Pod ou alterar
  credenciais do cluster PostgreSQL existente.
- Implantar SSO corporativo, cobrança, cadastro público ou papéis complexos.
- Afirmar segurança de produção da API HTTP de desenvolvimento.

## Requirements

- REQ-001: Cada pesquisador possui identidade única e token revogável;
  autenticação usa comparação segura e o segredo não é recuperável do banco.
- REQ-002: `author` de prompt, execução e feedback é decidido no servidor;
  falsificação via JSON ou cabeçalho arbitrário não muda o autor gravado.
- REQ-003: Toda rota de API exige identidade válida; token revogado/ausente
  falha sem acessar histórico ou banco de origem. Página estática pode abrir
  sem dados, mas jamais contém segredo.
- REQ-004: Limites são atômicos sob concorrência e impedem excesso de chamadas
  à LLM; a falha por limite não dispara cobrança remota.
- REQ-005: Scripts e documentos mantêm segredos em ambiente/arquivo ignorado
  pelo Git. O túnel ngrok protege a entrada, enquanto a aplicação valida sua
  própria credencial por usuário.

## Business or domain rules

- BR-001: Autoria científica registrada não é um campo editável pelo navegador.
- BR-002: Revogar acesso não apaga snapshots já registrados.
- BR-003: O banco de origem é lido em transações de leitura; a aplicação não
  oferece SQL livre a usuários autenticados.

## Decisions already made

- O primeiro ambiente é local, curto e compartilhado conforme
  `docs/arquitetura_inferencia_compartilhada.md`.
- A credencial individual temporária é a opção inicial de menor infraestrutura;
  um provedor externo de identidade pode substituí-la em outra SPEC.
- Credenciais reais só serão emitidas no momento de operação da sessão.

## Constraints

- Não migrar ou reescrever snapshots históricos da primeira API; se necessário,
  marcar autoria antiga como declarada e nova como verificada.
- Alterações de esquema de `db_inference_app` exigem migração explícita e
  reversível, com backup lógico antes da aplicação em um banco não vazio.
- Manter a porta da aplicação no loopback e não ligar ngrok nesta SPEC.

## Acceptance criteria

- AC-001: Duas identidades distintas registram runs e prompts com autores
  corretos mesmo enviando outro `author` no corpo.
- AC-002: Token inválido ou revogado recebe 401/403; nenhum acesso a histórico,
  consulta de origem ou chamada de modelo ocorre.
- AC-003: Limite de uso e concorrência impede chamada adicional antes do cliente
  vLLM; teste concorrente reproduz o bloqueio.
- AC-004: Nenhum token aparece em banco, snapshot, arquivo versionado ou log de
  erro; auditoria e testes verificam isso.
- AC-005: Configuração ngrok documentada mas túnel desligado; PostgreSQL segue
  em `127.0.0.1:5544`.

## Affected areas

- `inference_api/src/inference_api/config.py`, `server.py`, `storage.py`,
  `service.py`, `web/index.html`, migração do banco da aplicação, testes e README.

## References

- `inference_api/README.md`: contrato e estado atuais.
- `inference_api/src/inference_api/server.py`: autenticação HTTP atual.
- `inference_api/src/inference_api/storage.py`: esquema e autoria atual.
- `docs/arquitetura_inferencia_compartilhada.md`: topologia e exposição limitada.
- `BancoModeloUse/README.md`: cluster isolado e preservação das fontes.

## Skills

- Nenhum skill de identidade especializado é requerido; aplicar revisão
  independente por ser superfície de autenticação/autorização.

## Validation requirements

- VAL-001: `git diff --check` na raiz do projeto.
- VAL-002: Testes automatizados de identidade, revogação, falsificação de autor
  e limites sob concorrência em banco de teste isolado.
- VAL-003: Varredura de arquivos novos, snapshots e logs de teste para tokens.
- VAL-004: Teste HTTP local de 401/403 e autoria verificada; nenhum ngrok ativo.

## Review requirements

Revisão independente Sol/high de autenticação, autorização, limites,
concorrência, migração e proteção de segredos antes de permitir túnel.

## Execution and runtime

Executar conforme `SPEC.execution.json`, em thread própria e após conferir o
estado do checkout. A abertura do ngrok pertence à SPEC-005 e depende de
autorização explícita para a sessão.
