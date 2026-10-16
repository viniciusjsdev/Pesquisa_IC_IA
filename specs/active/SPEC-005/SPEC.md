---
id: SPEC-005
title: Validacao integrada e operacao da sessao curta
status: done
contract_version: 1
---

# SPEC-005: Validacao integrada e operacao da sessao curta

## Goal

Entregar verificações reproduzíveis e um runbook para a sessão científica
compartilhada inferior a 24 horas, separando preparo local, ativação paga,
validação remota e encerramento.

## Context

As SPECs 001–004 têm implementação e revisão independente aprovadas em seus
escopos locais. O checkout contém cadeia de agentes, preparação de serving,
identidade individual e bancada de comparação. A validação local anterior não
prova geração na RunPod nem acesso pelo ngrok.

## Scope

- Criar checklist executável de pré-voo: Git limpo/revisado, dados locais já
  carregados, conexão somente leitura, hashes dos adapters, base/revisão,
  configuração do vLLM, identidade e limites.
- Criar smoke test que recebe URL/credencial do vLLM por ambiente e verifica
  `/v1/models`, uma geração curta por alias e metadados de proveniência; nunca
  inicia ou cria Pod sozinho.
- Criar teste ponta a ponta para cada rota de dados e pelo menos dois modelos,
  com snapshots, revisões, checks, falhas controladas e isolamento entre dois
  usuários, sem enviar gold set.
- Criar procedimento de ngrok que expõe só a aplicação, testa autenticação
  remota e confirma que PostgreSQL/vLLM interno não ficam abertos por esse túnel.
- Criar runbook de início, monitoramento de custo/tempo, parada do Pod/túnel,
  exportação dos snapshots e readback final sem tocar dados científicos.

## Non-scope

- Iniciar Pod, abrir ngrok, comprar créditos, publicar URL, rodar treino,
  benchmark formal ou recriar dados de origem nesta SPEC sem autorização
  explícita da sessão.
- Declarar GPU suficiente por inventário estático ou `status: completed`.
- Mudar protocolo do artigo ou preencher o DW.

## Requirements

- REQ-001: Comandos locais e remotos são separados; nenhuma validação padrão
  causa cobrança ou exposição pública.
- REQ-002: Teste remoto exige endpoint HTTPS e credencial explícitos, registra
  tempo/alias/resultado e não imprime token ou conteúdo sensível.
- REQ-003: Readback distingue inventário, leitura de carga existente,
  geração remota, HTTP via ngrok e avaliação científica formal.
- REQ-004: Falha de qualquer gate bloqueia a afirmação de prontidão e aponta
  o componente exato, sem recriar Pod ou reenviar geração automaticamente.
- REQ-005: Encerramento confirma Pod e túnel desligados, preserva snapshots e
  identifica eventual armazenamento que ainda possa custar.

## Business or domain rules

- BR-001: Experimento interativo não é métrica do artigo.
- BR-002: Falha ou indisponibilidade de modelo não autoriza resposta simulada.
- BR-003: Fonte de dados preservada não recebe escrita do front/harness.

## Decisions already made

- Topologia notebook + PostgreSQL local + RunPod vLLM + ngrok e sessão curta
  estão em `docs/arquitetura_inferencia_compartilhada.md`.
- A execução paga e a exposição pública exigem acionamento explícito do usuário
  em turno futuro; esta thread entrega apenas preparo e validação local.

## Constraints

- Executar depois da reconciliação das SPECs 001–004.
- Documentar comandos exatos sem colocar segredos em histórico, código ou logs.
- Não misturar teste exploratório com harness científico ainda não implementado.

## Acceptance criteria

- AC-001: Pré-voo local falha de modo seguro quando falta banco, alias, hash,
  identidade ou configuração protegida.
- AC-002: Smoke test remoto é opt-in; teste padrão/mock prova que não inicia
  Pod e não chama URL externa.
- AC-003: Runbook define prova separada para banco, modelo, aplicação, túnel e
  desligamento, com estados `CONFIRMED`, `BLOCKED` ou `UNCERTAIN`.
- AC-004: Relatório de ensaio local registra o que foi realmente testado e
  marca geração remota/ngrok como não executados até haver sessão autorizada.
- AC-005: Procedimento de encerramento preserva histórico e não altera bases,
  adapters, manifests ou resultados científicos.

## Affected areas

- `inference_api/tests/`, `inference_api/README.md`, `runpod/serving/`,
  `docs/arquitetura_inferencia_compartilhada.md`, runbook da sessão em `docs/`.

## References

- `specs/active/SPEC-001/SPEC.md`: cadeia de agentes e evidências.
- `specs/active/SPEC-002/SPEC.md`: serving e proveniência.
- `specs/active/SPEC-003/SPEC.md`: identidade e limites.
- `specs/active/SPEC-004/SPEC.md`: interface e comparação.
- `docs/arquitetura_inferencia_compartilhada.md`: topologia e fronteiras.
- `inference_api/README.md`: comandos locais.
- `BancoModeloUse/README.md`: verificação de carga existente.

## Skills

- Nenhum skill adicional requerido; executar somente após as dependências e
  sem efeitos externos antes da autorização da sessão.

## Validation requirements

- VAL-001: `git diff --check` na raiz do projeto.
- VAL-002: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v`.
- VAL-003: Execução local/mock do pré-voo e smoke test, comprovando zero
  chamadas externas por padrão.
- VAL-004: Revisão manual de comandos do runbook e de cada estado reportado;
  validação remota fica pendente até a sessão autorizada.

## Review requirements

Revisão independente Sol/high de gates, comandos externos, limites de
afirmação, preservação de dados e encerramento de recursos cobrados.

## Execution and runtime

Executar conforme `SPEC.execution.json` somente após SPEC-001 a SPEC-004.
Esta thread não inicia RunPod nem ngrok; prepara e testa o procedimento local.
