---
id: SPEC-015
title: Orquestração LangGraph e módulos de agentes e ferramentas
status: done
contract_version: 3
---

# SPEC-015: Orquestração LangGraph e módulos de agentes e ferramentas

## Goal

Corrigir o funcionamento de A com pacote fixo multidomínio e resolver AUD-01/AUD-02 do LangSmith, preservando o grafo implementado, ModelService, cenário B e histórico imutável. Estado desta entrega: contrato 3 implementado, validado localmente e aprovado em revisão independente em 08/11/2026. Parecer e conclusão em evidence/v3/. O aceite inicial v3 era local; a [ativação posterior de A/B e LangSmith](../../../docs/bancada_operacao.md) foi autorizada e verificada em 08/11/2026. Delta em evidence/activation-2026-11-08/, sem reescrever evidence/v3/. Sem score científico.

## Context

O contrato 2 foi implementado e recebeu aceite de engenharia; sua versão exata está em [revisions/contract-2/](revisions/contract-2/SPEC.md) e seus pareceres permanecem intactos em evidence/. Não confundir esse aceite com aprovação do contrato 3. A auditoria de 08/11/2026 confirmou B real com oito chamadas, duas consultas e 19 spans, além de dois defeitos de observabilidade e da limitação funcional anterior de A.

O baseline atual é a implementação ainda não commitada sobre e93b816ef6df667992f3bfd0f632aaf7875f78e2, inventariada em evidence/baseline-snapshot-v3.json. O baseline v1/v2 e resultados anteriores não serão reescritos. A mudança de comportamento de A é agora explicitamente autorizada no desenho; execução de código foi posteriormente autorizada pelo usuário nesta sessão.

## Scope

- Grafo explícito LangGraph, agentes, ferramentas, contexto e políticas por cenário.
- Extração dos contratos efetivos e serviços de consulta; migração de consumidores ativos.
- Identidade recursiva, metadados do framework, compatibilidade de histórico e trajetória.
- Fixtures de equivalência, testes negativos, integração local via Bancada e revisão independente.
- LangSmith opcional: telemetria de agentes/tools/LLM, sanitização, isolamento de falhas e link na Bancada.
- Correção de A: índice semântico de pacote, contexto/contratos por papel, seleção interna e encerramento por lacunas.
- AUD-01: raiz com erro técnico correto e finalização alinhada à execução/persistência.
- AUD-02: receipt separado, reconciliação autenticada somente leitura e atualização de estado/link na Bancada.
- Desenho do contrato 3 em [corrections-v3.mmd](corrections-v3.mmd), anterior ao código; requisitos de migração abaixo permanecem como invariantes de regressão.

## Non-scope

- Remover Selecionador, adicionar papéis LLM, alterar prompts/contratos efetivos de B. Prompts e contratos de A mudam somente conforme corrections-v3.md.
- Trocar ModelService, protocolos dos provedores ou configuração científica.
- SQL livre, novos mapas/fontes, tabelas ou permissões nos bancos de pesquisa, joins entre bancos ou ingestão. Migração aditiva da tabela de observabilidade no banco da aplicação é parte deste escopo; executada apenas no banco descartável de teste nesta entrega.
- Retomada automática, execução paralela de agentes, memória entre runs ou RAG. Ativação de tracing hospedado e transmissão de dados reais ficam fora desta entrega; a implementação e os testes locais da integração LangSmith estão incluídos.
- Inferência paga, RunPod, ngrok, provisionamento, publicação, commit/push automático.
- Notas científicas, aprovação de respostas, acesso a gabaritos ou alteração de artefatos congelados.

## Requirements

- REQ-001: Implementar StateGraph real com nós por etapa e transições previstas no contrato; o motor antigo não pode sobreviver como loop interno ao nó.
- REQ-002: Cada agente deve ter módulo e interface comum; separar três especialistas de domínio mantendo papel externo e número de chamadas.
- REQ-003: Cada tool deve ter módulo/interface comum; apenas serviços de dados executam SQL, sob as validações existentes.
- REQ-004: Montar contexto por papel, sem despejar estado completo, segredos, gabarito ou histórico de outra run no prompt.
- REQ-005: Preservar contratos efetivos de B e reparos/orçamento/cancelamento comuns. Versionar explicitamente alterações de JSON, semântica e prompts de A; nenhuma repetição implícita do framework.
- REQ-006: Preservar interface ModelService e configuração congelada; todos os papéis usam o mesmo perfil da run.
- REQ-007: A não consulta bancos; B consulta somente fontes aprovadas. A aprofunda somente dentro do pacote congelado conforme contrato 3; B conserva política vigente.
- REQ-008: Preservar API, jobs, exportações e snapshots históricos; identificar novo runtime com hashes recursivos e dependências fixadas.
- REQ-009: Comprovar equivalência de B com baseline, diferenças intencionais de A e integração pela UI usando transportes falsos e banco descartável; separar falha de infraestrutura, contrato e julgamento.
- REQ-010: Remover duplicação ativa após inventário de consumidores; atualizar documentos sem reescrever evidências anteriores.

- REQ-011: Implementar observabilidade opcional conforme observability-contract.md, desligada por padrão e sem alterar inferência ou depender de disponibilidade externa.
- REQ-012: Registrar hierarquia, entradas/saídas permitidas, tokens/erros e link correlacionado na Bancada, com sanitização e histórico local preservado.

- REQ-013: Projetar domínios semânticos, origem, cobertura e itens disponíveis/examinados sem mudar bytes/hash do pacote v1.
- REQ-014: Ajustar contratos/projeções/validação/roteamento de A para analisar itens ou terminar com insuficiência explícita, sem invalid_review_gap por domínio suportado ausente.
- REQ-015: Finalizar raiz LangSmith com erro técnico padronizado e após resultado/persistência, sem fechar duas vezes.
- REQ-016: Reconciliar receipt de observabilidade durável separado, com controle de proprietário/destino e limites de leitura, sem dispatch de modelo/tool/exportação.
- REQ-017: Expor estado atualizado e link na UI sem modificar snapshot histórico ou reenviar inferência.

## Business or domain rules

- BR-001: Modelo escolhe fonte, plano e suficiência; backend valida autorização e limites. Roteamento determinístico aplica decisões validadas, sem substituir julgamento por heurística nova.
- BR-002: Ausência de dado não é zero; referências devem apontar para evidências recebidas; resultados continuam `answered_unverified`/`not_scored` conforme contrato.
- BR-003: Reparo permitido consome orçamento; recusa de consulta também conta. Fonte proibida não vira reparo para contornar autorização.
- BR-004: Uma run não compartilha estado mutável nem memória com outra. Um módulo de agente não implica outro modelo nem nova chamada.
- BR-005: Validação de engenharia não exige adjudicar cientificamente as respostas; avaliação científica futura segue o protocolo humano do projeto.

- BR-006: Falha de telemetria não repete modelo/consulta, não altera resultado e não habilita transmissão sem configuração explícita.

- BR-007: Domínio semântico não é origem física; um item financeiro do pacote extraído da DW continua proveniente da DW.
- BR-008: A não fabrica evidência ausente: retornar insuficiência com resposta parcial quando possível. Pacotes/gabaritos aprovados e seus hashes permanecem intactos.
- BR-009: Estado de monitoramento pode mudar, mas o snapshot científico salvo é imutável; leitura remota não recria run nem eventos.

## Decisions already made

O [contrato de correções v3](corrections-v3.md) e [seu desenho](corrections-v3.mmd) são normativos para esta revisão. Eles prevalecem sobre cláusulas antigas que preservavam o defeito A ou tratavam metadados de monitoramento como atualização do snapshot. [Arquitetura](architecture-contract.md) e [observabilidade](observability-contract.md) continuam válidas onde não alteradas pelo contrato 3.

A permanece sem ferramentas de consulta e usa os mesmos papéis; B conserva comportamento. LangGraph 1.2.20 e ModelService permanecem, sem checkpoint persistente/retry implícito. Uma projeção local versionada resolve domínios do pacote, sem criar novo pacote ou exigir nova revisão de conteúdo congelado. Nova avaliação científica exigirá controle da versão do protocolo.

Documentação precedeu código. Após autorização explícita do usuário, a implementação foi retomada nesta sessão. A página remota do diagrams.net não foi alterada. Ensaios hospedados anteriores não foram repetidos; validação v3 usa somente fixtures e PostgreSQL descartável.

## Constraints

Preservar checkout compartilhado e artefatos protegidos do baseline. Executar somente uma implementação por vez. Não reaproveitar scripts de verificação que sobrescrevem evidência histórica da SPEC-014: criar verificador SPEC-015 com destino próprio. Lock de dependências e disponibilidade do runtime de implementação devem ser verificados antes de despachar execução; readiness documental não prova ambiente preparado.

## Acceptance criteria

- AC-001 (REQ-001/002): Grafo compilado expõe nós distintos; testes comprovam chamadas reais aos componentes por papel e ausência de motor antigo em produção.
- AC-002 (REQ-003/007): A produz zero acessos a banco, inclusive fingerprints; B cobre DW, contributors, trace, industrial e financeiro com filtros e limites preservados.
- AC-003 (REQ-004/006): Testes de projeção e isolamento de duas runs comprovam campos recebidos, mesmo perfil por run e ausência de segredos/gabaritos/contexto cruzado.
- AC-004 (REQ-005/009): Equivalência de B e regressões intencionais de A passam com fixtures, aprofundamento, sem fonte, JSON inválido, reparo permitido, fonte proibida, orçamento, cancelamento e falha de provedor. Caracterização antiga de A é preservada; novas expectativas do contrato 3 devem resolver o defeito e documentar as diferenças permitidas.
- AC-005 (REQ-005): Tentativas recusadas e reparos contam; limites de grafo não interrompem orçamento válido; 429/timeout não provocam reenvio automático.
- AC-006 (REQ-008): Histórico antigo, contratos HTTP, jobs/idempotência, exportação e detalhe de trajetória permanecem legíveis; mudar módulo profundo altera identidade do runtime.
- AC-007 (REQ-006/009): Matriz de seis combinações A/B × OpenAI/Groq/compatível passa com transporte falso; nenhuma API externa é chamada.
- AC-008 (REQ-009): Verificador local exercita UI → job → grafo → consultas → resposta/erro → histórico com banco descartável, registra configuração e resultado, sem acessar bancos reais.
- AC-009 (REQ-008/010): Instalação limpa pelo lock passa; árvore final, inventário de consumidores e docs reconciliados; evidências históricas e dados protegidos intactos.
- AC-010: Revisão independente aprova engenharia com evidência por AC; completion/lifecycle e manifest são atualizados só após aprovação. Sem score científico.

- AC-011 (REQ-011/012): Spans raiz/agente/LLM/tool correlacionados, sem duplicação, registram tokens conhecidos ou ausência explícita; paridade off/on preserva chamadas e resultados.
- AC-012 (REQ-011): Modo off não envia mesmo com flag global ligado; sanitização, fila cheia, indisponibilidade e concorrência passam, sem bloquear resposta ou repetir inferência.
- AC-013 (REQ-012): UI mostra link privado correlacionado e estado da exportação quando disponíveis, preservando histórico antigo. Testes locais verificam o SDK sem tráfego hospedado; painel real permanece não validado até habilitação posterior.

- AC-014 (REQ-013/014): A analisa itens machine+financial com especialistas adequados, origem DW preservada, IDs exatos e zero consulta/fingerprint de pesquisa; itens mistos, períodos e rows vazias cobertos.
- AC-015 (REQ-014): Domínio ausente, item inadequado, contradição, no_progress e orçamento encerram A com lacuna/insuficiência conforme contrato; referência inventada continua bloqueada. Não alterar B nem baseline histórico.
- AC-016 (REQ-015): Raiz registra erro técnico para timeout/contrato/consulta/cancelamento/persistência, fecha uma única vez e não marca insuficiência como falha técnica.
- AC-017 (REQ-016): Após flush/reinício, reconciliação verifica IDs/pais e recupera estado/link sem escrever no serviço remoto, repetir inferência ou mudar hash do snapshot.
- AC-018 (REQ-016/017): API rejeita outro proprietário/destino arbitrário, limita concorrência/leitura e UI mostra estado atualizado com fallback histórico; migração aditiva idempotente e rollback preservam dados.
- AC-019: Integração local UI cobre A corrigido, B inalterado, erro na raiz, envio atrasado e reconciliação; nova revisão independente do contrato 3 antes de done.

## Affected areas

Arquivos detalhados em corrections-v3.md: agent_harness/policies, context, contracts, agents e graph; observability; executions; persistence/storage.py; api/server.py; frontend da Bancada e testes. ModelService/provedores e serviços SQL de pesquisa são invariantes. A tabela aditiva pertence somente ao banco da aplicação. Pacotes/schema/exportador de evidências congeladas permanecem sem alteração.

## References

- [Correções v3](corrections-v3.md), [fluxo v3](corrections-v3.mmd) e [auditoria de origem](evidence/usage-audit-2026-11-08.md).

- [Contrato LangSmith](observability-contract.md): configuração, hierarquia, privacidade, falhas e testes.
- [Contrato de arquitetura](architecture-contract.md) e [diagrama](architecture.mmd): fonte de verdade do alvo.
- [Baseline estrutural v3](evidence/structural-baseline-v3.json) e [snapshot atual](evidence/baseline-snapshot-v3.json): inventário e hashes anteriores à implementação.
- `AGENTS.md`, `inference_api/README.md`, `docs/arquitetura_inferencia_compartilhada.md`, `docs/organizacao_inference_api.md`: fontes do checkout.
- SPEC-014 `architecture-contract.md` e `evidence/openai-ab-real-ui-2026-11-06.md`: comportamento vigente e limitação real de A.
- `docs/protocolo_validacao_humana_avaliacao.md`: separação entre engenharia e ciência.
- Documentação primária de LangGraph e versão PyPI estão vinculadas no contrato de arquitetura.

## Skills

SPEC elaborada com `project-spec-architect`. Não é necessária skill especializada adicional para a implementação Python. O executor deve seguir AGENTS.md e este contrato; criação de chat/dispatch não faz parte desta entrega.

## Validation requirements

Comandos na raiz. Suites anteriores existem; os testes/verificador v3 são entregáveis futuros. Novas evidências ficam em evidence/v3/ e nunca sobrescrevem arquivos de aceite do contrato 2.

- VAL-001: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v`
- VAL-002: `inference_api/.venv/Scripts/python.exe -m unittest discover -s model_evaluation/tests -v`
- VAL-003: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -p test_spec015_*.py -v` — deve descobrir testes, não aceitar zero testes.
- VAL-004: `inference_api/.venv/Scripts/python.exe inference_api/scripts/verify_spec015_v3_local.py` — criar conforme AC-008/019, saída própria `evidence/v3/local-integration.json`; falhas retornam código não zero.
- VAL-005: `inference_api/.venv/Scripts/python.exe inference_api/scripts/validate_frontend.py test`
- VAL-006: `inference_api/.venv/Scripts/python.exe inference_api/scripts/validate_frontend.py typecheck`
- VAL-007: `inference_api/.venv/Scripts/python.exe inference_api/scripts/validate_frontend.py lint`
- VAL-008: `inference_api/.venv/Scripts/python.exe inference_api/scripts/validate_frontend.py build`
- VAL-009: Revisão de instalação limpa/lock, inventário recursivo, consumidores, hashes protegidos e cobertura por AC em `evidence/v3/engineering-validation.md`. Testes pulados exigem motivo e verificação alternativa para o critério; não contam automaticamente como aprovado.

- VAL-010: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -p test_spec015_observability*.py -v` — exigir testes descobertos e evidência específica conforme contrato LangSmith.

- VAL-011: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -p test_spec015_v3_*.py -v` — exigir testes descobertos, fixtures anteriores preservadas e falhas reproduzidas antes da correção.

Os testes novos cobrem o protocolo de equivalência descrito no contrato; não basta reproduzir a própria implementação em mocks. Evidências guardam comandos, exit codes, versões, data, commit/diff e configuração sanitizada. Registrar resultados separadamente; nenhum teste desta lista foi afirmado como executado ao redigir a SPEC.

## Review requirements

Revisão técnica independente obrigatória por migração complexa, autorização e concorrência. Revisor inspeciona código, dependências, diff, baseline, artefatos de equivalência e integração; não apenas status do executor. Não aprovar alterações sem evidência nem confundir sucesso de transporte falso com qualidade de modelo real.

## Execution and runtime

[SPEC.execution.json](SPEC.execution.json) define handoff, validações, baseline e saídas. Não há dispatch automático nem implementação autorizada por esta atualização documental. Os identificadores de runtime seguem a política legada da skill/schema instalada; são rótulos documentais, não uma comprovação de disponibilidade atual. Antes de iniciar outra thread, materializar e registrar o modelo efetivamente disponível no lifecycle, como na SPEC-014; não tentar invocar alias inexistente nem confundir esse runtime com o modelo científico da Bancada. A atualização global da política de modelos não faz parte desta refatoração.
