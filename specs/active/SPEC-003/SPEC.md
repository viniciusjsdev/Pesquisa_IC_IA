---
id: SPEC-003
title: Identidade individual e limites de uso da API compartilhada
status: done
contract_version: 2
---

# SPEC-003: Identidade individual e limites de uso da API compartilhada

## Goal

Substituir o token único e o autor declarado no navegador por login individual
verificado pelo backend para Nicoli e Vinicius. Ambos podem permanecer logados,
mas apenas uma inferência pode estar em execução em cada instante.

## Context

Antes desta mudança, a API local em `inference_api/` aceitava
`INFERENCE_API_TOKEN` e gravava o campo `author` enviado pelo navegador.
Isso foi suficiente para validação local, mas não provava quem executou cada
pergunta. O ngrok ainda não está ativo.

## Scope

- Criar exclusivamente os logins Nicoli e Vinicius por CLI com senha digitada
  em prompt oculto, hash com sal persistido em `db_inference_app` e sessões
  revogáveis cujo bearer aleatório é guardado apenas como digest com sal.
- Resolver identidade e autorização no backend em toda rota de leitura/escrita;
  autor de prompt, run e feedback vem do principal autenticado, ignorando ou
  recusando o campo `author` do corpo.
- Definir acesso de leitura ao histórico compartilhado, gravação de revisões e
  feedback, e revogação durante a sessão. Registrar identificador estável no
  snapshot sem gravar token ou digest.
- Permitir dois logins simultâneos, mas reservar atomicamente uma única vaga
  global para inferência; a segunda chamada recebe erro claro antes de consultar
  fontes ou chamar a LLM. Limites diários ficam desativados por decisão do
  usuário, com configuração opcional para uma sessão futura.
- Mostrar sempre o teto manual da sessão de US$ 10 e, quando uma credencial de
  leitura estiver configurada, consultar o saldo real da conta RunPod. Indicar
  indisponibilidade e horário da leitura; não confundir teto informativo com
  limite aplicado pelo provedor nem fabricar saldo.
- Documentar o alvo HTTP futuro do ngrok sem autenticação adicional na borda,
  conforme decisão do usuário, mas não abrir túnel. Conferir que só a porta
  8765 da aplicação é alvo, jamais a porta 5544 do PostgreSQL.

## Non-scope

- Abrir túnel, distribuir senhas, iniciar Pod ou alterar
  credenciais do cluster PostgreSQL existente.
- Implantar SSO corporativo, cobrança, cadastro público ou papéis complexos.
- Afirmar segurança de produção da API HTTP de desenvolvimento.

## Requirements

- REQ-001: Somente Nicoli e Vinicius podem ser cadastrados; senhas e sessões
  são revogáveis, autenticadas por comparação segura, sem segredo recuperável
  do banco.
- REQ-002: `author` de prompt, execução e feedback é decidido no servidor;
  falsificação via JSON ou cabeçalho arbitrário não muda o autor gravado.
- REQ-003: Toda rota de API exige identidade válida; token revogado/ausente
  falha sem acessar histórico ou banco de origem. Página estática pode abrir
  sem dados, mas jamais contém segredo.
- REQ-004: A vaga global de inferência é atômica sob concorrência e impede a
  segunda chamada à LLM; a falha por ocupação não dispara cobrança remota.
- REQ-005: Scripts e documentos mantêm segredos em ambiente/arquivo ignorado
  pelo Git. O futuro túnel ngrok encaminha somente o HTTP da aplicação; a
  própria aplicação valida a sessão revogável por usuário.

## Business or domain rules

- BR-001: Autoria científica registrada não é um campo editável pelo navegador.
- BR-002: Revogar acesso não apaga snapshots já registrados.
- BR-003: O banco de origem é lido em transações de leitura; a aplicação não
  oferece SQL livre a usuários autenticados.

## Decisions already made

- O primeiro ambiente é local, curto e compartilhado conforme
  `docs/arquitetura_inferencia_compartilhada.md`.
- Em 15/10/2026 o usuário definiu dois logins locais, sem limite diário e com
  uma inferência global por vez. As senhas escolhidas não entram neste contrato;
  serão digitadas apenas no terminal local com eco desativado.
- O usuário definiu teto informativo de US$ 10 e pediu exibição separada do
  saldo real da RunPod. Consulta de saldo exige chave de leitura configurada.
- Em 15/10/2026, o usuário dispensou autenticação adicional na borda do ngrok
  e confirmou a manutenção do bearer opaco revogável, sem troca por JWT.
  As senhas deverão ser trocadas em terminal local antes da primeira exposição,
  pois as escolhas originais passaram pelo chat.

## Constraints

- Não migrar ou reescrever snapshots históricos da primeira API; se necessário,
  marcar autoria antiga como declarada e nova como verificada.
- Alterações de esquema de `db_inference_app` exigem migração explícita e
  reversível, com backup lógico antes da aplicação em um banco não vazio.
- Manter a porta da aplicação no loopback e não ligar ngrok nesta SPEC.

## Acceptance criteria

- AC-001: Dois logins distintos registram runs e prompts com autores
  corretos mesmo enviando outro `author` no corpo.
- AC-002: Token inválido ou revogado recebe 401/403; nenhum acesso a histórico,
  consulta de origem ou chamada de modelo ocorre.
- AC-003: Duas pessoas podem estar logadas; uma segunda inferência simultânea
  é rejeitada antes da consulta de origem e do cliente vLLM.
- AC-004: Nenhum token aparece em banco, snapshot, arquivo versionado ou log de
  erro; auditoria e testes verificam isso.
- AC-005: Alvo futuro do ngrok documentado como HTTP da aplicação na porta
  8765, mas túnel desligado; PostgreSQL segue em `127.0.0.1:5544`.
- AC-006: Interface mostra US$ 10 como teto manual e o saldo RunPod com fonte,
  horário e estado de leitura, sem afirmar saldo quando a API não responde.

## Affected areas

- `inference_api/src/inference_api/auth.py`, `limits.py`, `budget.py`,
  `server.py`, `storage.py`, `service.py`, `web/index.html`,
  migração do banco da aplicação, testes e README.

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
