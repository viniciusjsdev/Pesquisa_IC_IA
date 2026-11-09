---
id: SPEC-015
title: Orquestração LangGraph e módulos de agentes e ferramentas
status: done
contract_version: 2
---

# SPEC-015: Orquestração LangGraph e módulos de agentes e ferramentas

## Goal

Substituir a orquestração própria por LangGraph, com um módulo por agente, interfaces comuns, ferramentas separadas e contexto explícito por papel. Preservar contratos públicos, provedores e comportamento dos cenários A/B. Incluir integração opcional com LangSmith para observabilidade. Implementação autorizada na sessão em 08/11/2026, incluindo uso do painel LangSmith. Envio de dados reais continua fora do escopo; a verificação hospedada será sintética e depende do acesso local à conta.

## Fechamento de engenharia em 08/11/2026

Implementação local aprovada em [revisão independente](evidence/review.json), com [validação por critério](evidence/engineering-validation.md). A/B, ModelService e histórico preservados; falha conhecida de A permanece separada. Envio hospedado sintético A/B confirmado posteriormente por leitura da API, com 11/26 spans e hierarquia completa (`evidence/hosted-readback.json`); renderização na sessão do usuário não inspecionada. Sem envio de dados reais nem score científico.

## Context

Baseline: commit `e93b816ef6df667992f3bfd0f632aaf7875f78e2`, inspecionado em 08/11/2026. `scenarios.py` concentra chamadas, contexto, validação, loops e estados; depende de contratos/helpers em `engine.py`. `ModelService` já abstrai provedores. A organização anterior por pastas não introduziu framework.

SPEC-013 e SPEC-014 têm aceites de engenharia anteriores; não representam avaliação científica. O ensaio real de A terminou em `invalid_review_gap`, conforme relatório da SPEC-014. Esta migração preserva e caracteriza esse problema; não é a correção funcional de A. Não houve execução de testes de produto nesta elaboração; o inventário é baseline, não novo resultado de teste.

## Scope

- Grafo explícito LangGraph, agentes, ferramentas, contexto e políticas por cenário.
- Extração dos contratos efetivos e serviços de consulta; migração de consumidores ativos.
- Identidade recursiva, metadados do framework, compatibilidade de histórico e trajetória.
- Fixtures de equivalência, testes negativos, integração local via Bancada e revisão independente.
- LangSmith opcional: telemetria de agentes/tools/LLM, sanitização, isolamento de falhas e link na Bancada.
- Documentação e desenho técnico [architecture.mmd](architecture.mmd), anteriores à implementação.

## Non-scope

- Redesenhar/corrigir A, remover Selecionador, alterar prompts ou adicionar papéis LLM.
- Trocar ModelService, protocolos dos provedores ou configuração científica.
- SQL livre, novos mapas, tabelas, permissões, joins entre bancos ou ingestão.
- Retomada automática, execução paralela de agentes, memória entre runs ou RAG. Ativação de tracing hospedado e transmissão de dados reais ficam fora desta entrega; a implementação e os testes locais da integração LangSmith estão incluídos.
- Inferência paga, RunPod, ngrok, provisionamento, publicação, commit/push automático.
- Notas científicas, aprovação de respostas, acesso a gabaritos ou alteração de artefatos congelados.

## Requirements

- REQ-001: Implementar StateGraph real com nós por etapa e transições previstas no contrato; o motor antigo não pode sobreviver como loop interno ao nó.
- REQ-002: Cada agente deve ter módulo e interface comum; separar três especialistas de domínio mantendo papel externo e número de chamadas.
- REQ-003: Cada tool deve ter módulo/interface comum; apenas serviços de dados executam SQL, sob as validações existentes.
- REQ-004: Montar contexto por papel, sem despejar estado completo, segredos, gabarito ou histórico de outra run no prompt.
- REQ-005: Preservar JSON, schemas efetivos, semântica, reparos, orçamento, cancelamento e classificação de erros; nenhuma repetição implícita do framework.
- REQ-006: Preservar interface ModelService e configuração congelada; todos os papéis usam o mesmo perfil da run.
- REQ-007: A não consulta bancos; B consulta somente fontes aprovadas. Política de escolha e aprofundamento permanece a vigente.
- REQ-008: Preservar API, jobs, exportações e snapshots históricos; identificar novo runtime com hashes recursivos e dependências fixadas.
- REQ-009: Comprovar equivalência com baseline e integração pela UI usando transportes falsos e banco descartável; separar falha de infraestrutura, contrato e julgamento.
- REQ-010: Remover duplicação ativa após inventário de consumidores; atualizar documentos sem reescrever evidências anteriores.

- REQ-011: Implementar observabilidade opcional conforme observability-contract.md, desligada por padrão e sem alterar inferência ou depender de disponibilidade externa.
- REQ-012: Registrar hierarquia, entradas/saídas permitidas, tokens/erros e link correlacionado na Bancada, com sanitização e histórico local preservado.

## Business or domain rules

- BR-001: Modelo escolhe fonte, plano e suficiência; backend valida autorização e limites. Roteamento determinístico aplica decisões validadas, sem substituir julgamento por heurística nova.
- BR-002: Ausência de dado não é zero; referências devem apontar para evidências recebidas; resultados continuam `answered_unverified`/`not_scored` conforme contrato.
- BR-003: Reparo permitido consome orçamento; recusa de consulta também conta. Fonte proibida não vira reparo para contornar autorização.
- BR-004: Uma run não compartilha estado mutável nem memória com outra. Um módulo de agente não implica outro modelo nem nova chamada.
- BR-005: Validação de engenharia não exige adjudicar cientificamente as respostas; avaliação científica futura segue o protocolo humano do projeto.

- BR-006: Falha de telemetria não repete modelo/consulta, não altera resultado e não habilita transmissão sem configuração explícita.

## Decisions already made

O [contrato de arquitetura](architecture-contract.md) é normativo para interfaces, árvore alvo, estados, migração e equivalência. Escolha: LangGraph 1.2.20, StateGraph Python, ModelService preservado, sem checkpoints persistentes/retries automáticos. JSON Schema existente continua validando em runtime; TypedDict não substitui essa validação.

Contrato 2 inclui [LangSmith opcional](observability-contract.md): integração obrigatória na implementação, ativação opcional. O histórico local permanece oficial; testes usam dados sintéticos e transporte local falso. Nenhuma autorização de execução ou envio foi concedida por esta revisão.

Documentação precede código. O diagrama técnico local detalha a implementação; a página remota funcional não foi alterada nesta entrega. Antes de mudar qualquer comportamento funcional desenhado, voltar ao desenho e ao contrato. A ausência de mudança remota não autoriza considerar rótulos históricos como implementação atual.

## Constraints

Preservar checkout compartilhado e artefatos protegidos do baseline. Executar somente uma implementação por vez. Não reaproveitar scripts de verificação que sobrescrevem evidência histórica da SPEC-014: criar verificador SPEC-015 com destino próprio. Lock de dependências e disponibilidade do runtime de implementação devem ser verificados antes de despachar execução; readiness documental não prova ambiente preparado.

## Acceptance criteria

- AC-001 (REQ-001/002): Grafo compilado expõe nós distintos; testes comprovam chamadas reais aos componentes por papel e ausência de motor antigo em produção.
- AC-002 (REQ-003/007): A produz zero acessos a banco, inclusive fingerprints; B cobre DW, contributors, trace, industrial e financeiro com filtros e limites preservados.
- AC-003 (REQ-004/006): Testes de projeção e isolamento de duas runs comprovam campos recebidos, mesmo perfil por run e ausência de segredos/gabaritos/contexto cruzado.
- AC-004 (REQ-005/009): Equivalência passa para sucesso A/B com fixtures, aprofundamento, sem fonte, JSON inválido, reparo permitido, fonte proibida, orçamento, cancelamento e falha de provedor. Defeito real de A tem caracterização explícita, sem alegar resolução.
- AC-005 (REQ-005): Tentativas recusadas e reparos contam; limites de grafo não interrompem orçamento válido; 429/timeout não provocam reenvio automático.
- AC-006 (REQ-008): Histórico antigo, contratos HTTP, jobs/idempotência, exportação e detalhe de trajetória permanecem legíveis; mudar módulo profundo altera identidade do runtime.
- AC-007 (REQ-006/009): Matriz de seis combinações A/B × OpenAI/Groq/compatível passa com transporte falso; nenhuma API externa é chamada.
- AC-008 (REQ-009): Verificador local exercita UI → job → grafo → consultas → resposta/erro → histórico com banco descartável, registra configuração e resultado, sem acessar bancos reais.
- AC-009 (REQ-008/010): Instalação limpa pelo lock passa; árvore final, inventário de consumidores e docs reconciliados; evidências históricas e dados protegidos intactos.
- AC-010: Revisão independente aprova engenharia com evidência por AC; completion/lifecycle e manifest são atualizados só após aprovação. Sem score científico.

- AC-011 (REQ-011/012): Spans raiz/agente/LLM/tool correlacionados, sem duplicação, registram tokens conhecidos ou ausência explícita; paridade off/on preserva chamadas e resultados.
- AC-012 (REQ-011): Modo off não envia mesmo com flag global ligado; sanitização, fila cheia, indisponibilidade e concorrência passam, sem bloquear resposta ou repetir inferência.
- AC-013 (REQ-012): UI mostra link privado correlacionado e estado da exportação quando disponíveis, preservando histórico antigo. Testes locais verificam o SDK sem tráfego hospedado; painel real permanece não validado até habilitação posterior.

## Affected areas

`inference_api/src/inference_api/agent_harness/`, `data_access/`, integração em `executions/`, requirements/lock, testes/scripts e documentação. `model_service/` conserva sua fronteira; mudanças apenas de integração comprovadamente necessárias. Adicionar observability/ e instrumentação no ModelService sem mudar payloads dos provedores. Frontend inclui link/estado opcionais do LangSmith e compatibilidade aditiva da trajetória. Sem alteração em dados/schema SQL ou avaliação científica.

## References

- [Contrato LangSmith](observability-contract.md): configuração, hierarquia, privacidade, falhas e testes.
- [Contrato de arquitetura](architecture-contract.md) e [diagrama](architecture.mmd): fonte de verdade do alvo.
- [Baseline estrutural](evidence/structural-baseline.json) e [snapshot](evidence/baseline-snapshot.json): inventário e hashes anteriores à implementação.
- `AGENTS.md`, `inference_api/README.md`, `docs/arquitetura_inferencia_compartilhada.md`, `docs/organizacao_inference_api.md`: fontes do checkout.
- SPEC-014 `architecture-contract.md` e `evidence/openai-ab-real-ui-2026-11-06.md`: comportamento vigente e limitação real de A.
- `docs/protocolo_validacao_humana_avaliacao.md`: separação entre engenharia e ciência.
- Documentação primária de LangGraph e versão PyPI estão vinculadas no contrato de arquitetura.

## Skills

SPEC elaborada com `project-spec-architect`. Não é necessária skill especializada adicional para a implementação Python. O executor deve seguir AGENTS.md e este contrato; criação de chat/dispatch não faz parte desta entrega.

## Validation requirements

Comandos na raiz; os novos arquivos de testes/verificador abaixo são entregáveis da implementação, não existem ainda.

- VAL-001: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v`
- VAL-002: `inference_api/.venv/Scripts/python.exe -m unittest discover -s model_evaluation/tests -v`
- VAL-003: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -p test_spec015_*.py -v` — deve descobrir testes, não aceitar zero testes.
- VAL-004: `inference_api/.venv/Scripts/python.exe inference_api/scripts/verify_spec015_local.py` — criar conforme AC-008, saída própria `evidence/local-integration.json`; falhas retornam código não zero.
- VAL-005: `inference_api/.venv/Scripts/python.exe inference_api/scripts/validate_frontend.py test`
- VAL-006: `inference_api/.venv/Scripts/python.exe inference_api/scripts/validate_frontend.py typecheck`
- VAL-007: `inference_api/.venv/Scripts/python.exe inference_api/scripts/validate_frontend.py lint`
- VAL-008: `inference_api/.venv/Scripts/python.exe inference_api/scripts/validate_frontend.py build`
- VAL-009: Revisão de instalação limpa/lock, inventário recursivo, consumidores, hashes protegidos e cobertura por AC em `evidence/engineering-validation.md`. Testes pulados exigem motivo e verificação alternativa para o critério; não contam automaticamente como aprovado.

- VAL-010: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -p test_spec015_observability*.py -v` — exigir testes descobertos e evidência específica conforme contrato LangSmith.

Os testes novos cobrem o protocolo de equivalência descrito no contrato; não basta reproduzir a própria implementação em mocks. Evidências guardam comandos, exit codes, versões, data, commit/diff e configuração sanitizada. Registrar resultados separadamente; nenhum teste desta lista foi afirmado como executado ao redigir a SPEC.

## Review requirements

Revisão técnica independente obrigatória por migração complexa, autorização e concorrência. Revisor inspeciona código, dependências, diff, baseline, artefatos de equivalência e integração; não apenas status do executor. Não aprovar alterações sem evidência nem confundir sucesso de transporte falso com qualidade de modelo real.

## Execution and runtime

[SPEC.execution.json](SPEC.execution.json) define handoff, validações, baseline e saídas. Não há dispatch automático. Os identificadores de runtime seguem a política legada da skill/schema instalada; são rótulos documentais, não uma comprovação de disponibilidade atual. Antes de iniciar outra thread, materializar e registrar o modelo efetivamente disponível no lifecycle, como na SPEC-014; não tentar invocar alias inexistente nem confundir esse runtime com o modelo científico da Bancada. A atualização global da política de modelos não faz parte desta refatoração.
