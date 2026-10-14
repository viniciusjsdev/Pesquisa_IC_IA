---
id: SPEC-004
title: Bancada web de prompts verificacoes e comparacao
status: ready
contract_version: 1
---

# SPEC-004: Bancada web de prompts verificacoes e comparacao

## Goal

Completar a interface compartilhada de exploração para editar prompts e
critérios de verificação, escolher modelos por execução e comparar respostas
com suas evidências e limitações lado a lado.

## Context

`inference_api/web/index.html` já permite rascunho/revisão de prompt, seleção
de alias disponível, pergunta e histórico básico. Não há revisão de critérios,
comparação estruturada nem identidade individual. SPEC-001 define evidências e
checks; SPEC-003 define autoria autenticada.

## Scope

- Ajustar a interface ao contrato versionado de SPEC-001 e à identidade de
  SPEC-003, sem campo `author` livre.
- Permitir revisão imutável de critérios **estruturados** de verificação:
  presença de evidência, período, unidades, IDs citados e ressalvas exigidas.
  Não aceitar JavaScript, SQL ou expressão executável do usuário.
- Guardar a versão e o texto/configuração exatos dos critérios em cada run;
  conflito de edição usa revisão esperada, como os prompts.
- Exibir resposta, consulta, evidência, origem, período, unidades, checks e
  erros separadamente; marcar `answered_unverified` de forma inequívoca.
- Comparar dois ou mais runs existentes lado a lado, com aviso quando pergunta,
  período, evidência, prompt, parâmetros ou versão do modelo forem diferentes.
- Preservar seleção de modelo individual por requisição; atualização da lista
  de disponibilidade consulta o backend, não uma lista hardcoded no navegador.

## Non-scope

- Criar harness formal, métricas do artigo, gold set, SQL editável ou painel
  administrativo do vLLM/RunPod.
- Prometer comparação causal ou científica quando snapshots diferirem.
- Mudar os dados de origem, adapters ou manifests.

## Requirements

- REQ-001: A UI mostra dados reais do snapshot imutável e não recalcula nem
  sobrescreve uma execução antiga ao editar prompt ou critério.
- REQ-002: Critérios editáveis são dados estruturados com revisão, validação de
  schema e tamanho; são executados apenas por verificadores autorizados do
  backend, nunca por `eval` ou código enviado pelo usuário.
- REQ-003: Salvar revisão conflitante devolve estado atual legível sem perder
  o rascunho local do pesquisador.
- REQ-004: Comparação destaca diferenças materiais e não agrega pontuação
  científica. Cada coluna mantém seu próprio alias e proveniência.
- REQ-005: Token/segredo não aparece em URL, HTML persistido, snapshot ou
  log do navegador; identidade vem da API autenticada.
- REQ-006: Interface funciona em navegador de notebook e celular, com labels,
  status de carregamento e erros legíveis sem depender de console técnico.

## Business or domain rules

- BR-001: Resposta de LLM não é validação científica.
- BR-002: Um check parcial não prova correção numérica, causalidade ou
  comparabilidade entre modelos.
- BR-003: Revisão de prompt/critério e escolha de modelo pertencem ao run;
  outro usuário não altera o snapshot já registrado.

## Decisions already made

- Manter uma interface simples servida pela mesma aplicação local, conforme
  `docs/arquitetura_inferencia_compartilhada.md`.
- Comparação nesta SPEC é visual/exploratória; benchmark formal permanece em
  `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`.

## Constraints

- Começar somente depois de SPEC-001 e SPEC-003 implementadas/reconciliadas;
  consumir seus contratos finais em vez de criar paralelos.
- Não introduzir dependência front pesada sem necessidade demonstrada.
- Atualizar documentação quando a UI e a API mudarem.

## Acceptance criteria

- AC-001: Pesquisador salva duas revisões de prompt e de critérios; runs
  antigos continuam exibindo os textos/versões originais.
- AC-002: UI executa dois aliases disponíveis sem seleção global e compara
  respostas com evidência, período, prompt, checks e erros visíveis.
- AC-003: Runs com insumos diferentes exibem aviso de não comparabilidade;
  nenhum número de acurácia é apresentado.
- AC-004: Entrada contendo código/SQL nos critérios é rejeitada como contrato
  inválido ou tratada só como texto, nunca executada.
- AC-005: Fluxos de conflito, modelo indisponível e falha de consulta/modelo
  são legíveis em tela pequena e não perdem rascunho.

## Affected areas

- `inference_api/web/`, rotas e persistência de critérios em
  `inference_api/src/inference_api/`, testes e README.

## References

- `inference_api/web/index.html`: interface inicial.
- `inference_api/README.md`: contrato inicial.
- `docs/arquitetura_inferencia_compartilhada.md`: experiência compartilhada.
- `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`: separação exploratório/formal.
- `specs/active/SPEC-001/SPEC.md`: contrato de evidências e checks.
- `specs/active/SPEC-003/SPEC.md`: identidade e autorização.

## Skills

- Nenhum skill de front adicional é obrigatório para esta evolução localizada;
  usar o contrato de UI e API da SPEC.

## Validation requirements

- VAL-001: `git diff --check` na raiz do projeto.
- VAL-002: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v`.
- VAL-003: Teste de navegador local para duas revisões, dois runs, comparação,
  conflito e falha de modelo; registrar capturas/evidência sem segredo.
- VAL-004: Inspeção do front para ausência de `eval`, SQL livre e segredo em URL.

## Review requirements

Revisão independente Terra/medium do contrato UI/API, histórico e mensagens de
comparabilidade. Segurança de identidade permanece sob revisão da SPEC-003.

## Execution and runtime

Executar conforme `SPEC.execution.json` quando SPEC-001 e SPEC-003 estiverem
concluídas; o checkout compartilhado não recebe escritores simultâneos.
