---
id: SPEC-014
title: Dois cenários multiagente e serviço de modelos independente de provedor
status: done
contract_version: 1
---

# SPEC-014: Dois cenários multiagente e serviço de modelos

Implementação acionada manualmente em 06/11/2026 no chat `01a1b284-81a4-7493-9e7d-d379a3e091da`. Baseline e runtime efetivo constam em `evidence/lifecycle.json`; reaberta e corrigida em 06/11/2026 para reconciliar catálogo e bloqueio de fonte; nova revisão independente aprovada.

## Goal

Oferecer na Bancada exatamente dois cenários novos, ambos pelo harness de agentes: **A — sem consulta, com pacote fixo** e **B — com consulta aos dados**. Separar o provedor de inferência do cenário e dos papéis dos agentes por um serviço comum no backend. Implementada e aprovada em engenharia local com fixtures em 06/11/2026; não constitui validação científica.

## Context

Em 06/11/2026, a SPEC-013 contrato 3 está `done` de engenharia, com revisão independente e execução OpenAI pela Bancada. O fluxo tem cinco papéis: Analista, Selecionador, Especialista do domínio, Revisor e Redator. O Especialista monta a consulta; não existe Planejador separado.

No baseline anterior à SPEC-014, o checkout distinguia `dw_snapshot`, `dw_tools` e `agent_harness_pilot`; `service.py`, `models.py` e a UI contêm decisões por provedor/alias. O harness possui uma fronteira reutilizável `model_call(role, envelope, contract)`, mas a integração atual não equivale a suporte uniforme dos dois cenários em todos os provedores. A RunPod hospeda o endpoint vLLM; não deve definir a política de investigação.

Inicialmente, o usuário autorizou a etapa de **desenho e documentação**, antes do código; o acionamento posterior autorizou a implementação. O [diagrama](https://app.diagrams.net/#G1RbtLePrWCTs8GjCAmAegFv7XBcAtzN8E#%7B%22pageId%22%3A%22rC3Onoxkcgc0oOyFh0Ck%22%7D) foi atualizado na mesma página. A cópia editável e o readback estão em `evidence/`. A página de modelagem dos três bancos não foi editada.

## Scope

- Serviço interno de normalização de inferência e registro declarativo de perfis/capacidades.
- Adaptadores para os protocolos já usados por OpenAI, Groq e endpoint compatível de inferência, incluindo vLLM hospedado na RunPod.
- Mesmo motor e família de papéis nos cenários A/B, com contratos discriminados pela capacidade de consulta.
- Preparação, trajetória, histórico, exportação e comparação coerentes com os novos cenários.
- Retirada dos caminhos antigos de criação de runs, mantendo leitura de evidência histórica e compatibilidade de exportação.
- Testes offline, integração local e auditoria independente; execução remota somente dentro de autorização válida.

## Non-scope

Não criar microserviço separado, MCP, novo orquestrador LLM, novo Planejador, RAG, infraestrutura RunPod, túnel, treinamento ou novas fontes de dados. Não alterar dados congelados, catálogo aprovado, gabaritos ou resultados anteriores. Não executar bateria científica nem exigir adjudicação de respostas para concluir engenharia. Não transformar autorização de um piloto em autorização irrestrita de transmissão a outros destinos.

## Requirements

- **REQ-001:** novas execuções aceitam somente `scenario=fixed_evidence` (A) ou `scenario=data_access` (B), `model_profile_id` e contrato versionado. “Piloto” deixa de ser um terceiro cenário.
- **REQ-002:** todas as chamadas de papéis passam pelo serviço comum; nenhum papel conhece URL, chave, RunPod ou formato HTTP do provedor. Mesmo perfil congelado durante o run.
- **REQ-003:** A recebe pacote imutável identificado por hash, disponível antes de iniciar o run. Não executa leitura dos bancos de pesquisa, nem descoberta, fingerprint ou fallback oculto de consulta durante a execução. Banco da aplicação para autenticação/jobs/histórico continua permitido.
- **REQ-004:** B preserva fontes aprovadas DW, industrial e financeiro, seleção contextual, projeção de mapa por fonte, plano do Especialista, validação determinística e aprofundamento limitado.
- **REQ-005:** serviço normaliza mensagens, schemas, parâmetros, resultado, término, uso, erros, recibos e identidade; preserva valores brutos relevantes e diferenças entre provedores.
- **REQ-006:** registro de capacidades dirige UI e preflight no servidor. Configuração não suportada falha antes de enviar dados; disponibilidade não é inferida apenas da existência de uma chave.
- **REQ-007:** contratos JSON de entrada/saída por papel e cenário, estados e feedback conforme [contrato funcional](architecture-contract.md). Sem síntese semântica invisível no código de montagem de contexto.
- **REQ-008:** preservar orçamento do corpo HTTP completo, tentativas recusadas contadas, ausência de retries/fallbacks ocultos, provenance, identidade do runtime e vínculo da revisão ao run exato.
- **REQ-009:** preservar histórico/exportações anteriores sem reclassificá-los como execuções da nova arquitetura. Identificar o contrato e o cenário originais.
- **REQ-010:** deixar somente os dois cenários na preparação, com perfil independente, configurações efetivas visíveis e trajetória por papel, rodada, leitura, erro e resposta.
- **REQ-011:** manter isolamento dos gabaritos e estados `not_scored`/`answered_unverified`. Não confundir execução válida com resposta correta cientificamente.

## Business or domain rules

- **BR-001:** o modelo escolhe relevância, fonte e suficiência. O backend autoriza, projeta contexto, valida contratos, contabiliza limites e executa ações permitidas; não escolhe semanticamente a resposta.
- **BR-002:** A não é “sem agentes” nem “sem informação”. É sem aquisição de dados durante o run, usando somente o pacote recebido. Pacote inexistente, alterado ou incompatível bloqueia o início.
- **BR-003:** no A, fonte escolhida deve pertencer ao pacote; no B, ao catálogo aprovado. Nenhuma saída da LLM altera a política do run.
- **BR-004:** não se presume que A e B têm contexto idêntico. O tratamento inclui a política de aquisição de evidências; comparação exige registrar pacote inicial, fontes disponíveis, limites, prompts e versões. Diferenças de evidência não podem ser atribuídas exclusivamente à qualidade do modelo.
- **BR-005:** para comparar modelos dentro de um cenário, fixar protocolo, ferramentas e dados. Diferenças inevitáveis de parâmetros/capacidades ficam explícitas; ausência de metadados impede afirmar equivalência.
- **BR-006:** uma fonte por consulta, acesso somente leitura, filtros tipados, sem SQL livre nem joins entre bancos. O revisor pode confrontar resultados com proveniência e declarar ausência de vínculo causal.
- **BR-007:** limite de saída `null` significa omitir teto solicitado, apenas quando o perfil suporta essa política; nunca significa saída infinita. Truncamento permanece erro, mesmo quando o JSON aparenta ser válido.

## Decisions already made

1. Serviço comum é **módulo no backend existente**, com adaptadores de protocolo e configuração de implantação separada. Não adicionar dependência de um gateway comercial.
2. Identificadores novos são `fixed_evidence` e `data_access`. Contratos antigos permanecem históricos, não aliases silenciosos de semântica nova.
3. Os cinco papéis são compartilhados. Especialistas DW/industrial/financeiro são variantes do mesmo papel por domínio; só são invocados quando relevantes. Sem fonte ou orçamento, há encerramento explícito, não chamadas artificiais para completar a lista.
4. A análise de pacote e o plano de consulta são saídas distintas do Especialista, discriminadas por `action`. UI não oferece `agent_harness_pilot` para novos runs.
5. Não forçar número igual de chamadas em A/B: seleção, correção e aprofundamento têm custos registrados. Mesmo orçamento máximo de chamadas e política de correção, com A tendo zero consultas.
6. Engenharia encerra com critérios AC atendidos, evidência local de integração e auditoria técnica independente. Avaliação científica humana posterior permanece obrigatória para pontuação, separada de `done` de engenharia.
7. Nova thread implementa a SPEC inteira por marcos locais. Não iniciar ou despachar essa thread automaticamente.

## Constraints

Seguir AGENTS.md, documentação da frente e protocolo humano. Checkout compartilhado contém trabalho prévio não commitado: baseline representa o conteúdo observado, não somente HEAD. Não resetar, sobrescrever ou retirar arquivos por aparência de legado. Verificar consumidores antes de remoção e preservar evidências fora de uso em arquivo externo com inventário verificável, quando a retirada for necessária.

Nenhuma consulta remota, custo, RunPod ou envio de dados é necessário para desenvolver os testes desta SPEC. Autorizações anteriores são por destino/dados/limites; conferir seu alcance antes de ensaio externo e pedir somente eventual ampliação ainda não autorizada. Não copiar segredos para manifest, histórico, frontend ou evidências.

## Acceptance criteria

- **AC-001 / REQ-001,010:** UI e API expõem duas opções novas. Endpoints de criação recusam modos legados com erro explícito; histórico antigo continua abrindo/exportando.
- **AC-002 / REQ-002,005,006:** executar a mesma fixture pelos três adaptadores com transportes fake produz o mesmo contrato normalizado; adicionar configuração de endpoint compatível não exige mudar engine, papéis ou UI. Parâmetros incompatíveis geram zero chamadas HTTP.
- **AC-003 / REQ-003,007:** teste A atravessa os cinco papéis com pacote completo; spies que lançam erro em qualquer acesso ao DB de pesquisa permanecem intactos. Pedido malicioso de consulta, fonte externa e pacote alterado não escapam ao bloqueio. Pacote incompleto resulta em lacuna, sem consulta.
- **AC-004 / REQ-004,007:** teste B consulta DW, industrial e financeiro por três rodadas, sem Planejador, com resultados e proveniência chegando ao Revisor e Redator. Recuperação de plano recusado volta ao mesmo Especialista com erro/plano/saldo.
- **AC-005 / REQ-005,008:** testes cobrem JSON inválido, truncamento, recusa, timeout, erro 429, desconexão de stream, falta de usage, payload excessivo e cancelamento. Cada tentativa tem recibo; não há duplicação, fallback ou retry de provedor oculto.
- **AC-006 / REQ-008,009:** exportação mantém contrato original de runs antigos e novo snapshot versionado. Comparação detecta diferenças de cenário, pacote, fontes, runtime, capacidades e parâmetros; autorizações/revisões antigas não são herdadas por novos hashes.
- **AC-007 / REQ-010:** integração local pelo navegador, com provider fake declarado como fixture e banco local de teste, valida preparar → executar → acompanhar → resposta → histórico/reabertura nos dois cenários, inclusive erro visível. Nada sintético aparece como execução real.
- **AC-008 / REQ-008,011:** evidências de tests/typecheck/lint/build e auditoria independente aprovadas, sem exposição de gabaritos/segredos; `not_scored` preservado. Documentação descreve suporte verificado por adaptador, distinguindo mock, local e remoto.

## Affected areas

Implementação futura: `inference_api/src/inference_api/service.py`, `models.py`, `config.py`, `jobs.py`, `server.py`; `agent_harness/engine.py`, contratos, adapters atuais, runtime identity e limites; novo pacote `inference_api/src/inference_api/model_service/`; frontend `src/features/bench/` e tipos/serviço de modelos; export/comparação em `model_evaluation/` e testes. Infraestrutura `runpod/serving/` só recebe documentação de integração, sem provisionamento.

Ver [migração e marcos](implementation-handoff.md). A implementação foi posteriormente autorizada e concluída no escopo local documentado.

## References

- [Contrato funcional](architecture-contract.md): inputs/outputs, estados, capacidades, erros, contexto e comparação.
- [Handoff](implementation-handoff.md): sequência, validações e leitura inicial da outra thread.
- [Baseline estrutural](evidence/structural-baseline.json) e [snapshot](evidence/baseline-snapshot.json).
- [SPEC-013 concluída](../SPEC-013/SPEC.md), [contrato do Especialista](../SPEC-013/specialist-query-contract.md), [fechamento de engenharia](../SPEC-013/engineering-closeout-contract.md).
- [Arquitetura local](../../../docs/arquitetura_inferencia_compartilhada.md) e [protocolo humano](../../../docs/protocolo_validacao_humana_avaliacao.md).
- [Diagrama editável](evidence/diagram-spec014.drawio), backup e readback na mesma pasta.

## Skills

Planejamento feito com `project-spec-architect`. A thread implementadora deve seguir contratos locais e comandos do handoff; não exige skill adicional para produzir código. Não usar skill de arquitetura para reabrir decisões resolvidas sem evidência de incompatibilidade.

## Validation requirements

**VAL-001:** validação estrutural de SPEC/manifest ready. **VAL-002:** testes backend. **VAL-006:** testes model_evaluation. **VAL-003:** testes frontend. **VAL-007/008/009:** tipos, lint e build frontend. **VAL-004:** matriz local e navegação A/B, com relatório por AC e identidade dos fixtures. **VAL-005:** reconciliação da baseline, contratos e consumidores legados. Comandos e evidências exigidos no handoff e no manifest. Os testes futuros não foram executados por esta etapa de planejamento.

## Review requirements

Revisão técnica independente do diff e das evidências, sem editar implementação. Verificar isolamento A, adaptação de protocolos, bloqueios de autorização, contabilidade de tentativas, preservação histórica e inexistência de branches de provedor nos agentes. Não aceitar só testes de mocks como comprovação de disponibilidade real do provedor. Não usar esta revisão como adjudicação científica.

## Execution and runtime

`SPEC.execution.json` é o contrato de execução; `automatic_handoff=false`, nova thread sem ID pré-atribuído. Runtime de implementação conforme política da skill: `gpt-5.6-terra/medium`; revisão independente `gpt-5.6-sol/high`. Esses são runtimes dos executores Codex, **não** os modelos candidatos da pesquisa. Se indisponíveis no ambiente da outra thread, resolver o runtime explicitamente e registrar o motivo, sem trocar perfil científico silenciosamente. Escalonamento a desenho somente para decisão material ausente ou incompatibilidade comprovada.
