# SPEC-015 · contrato 3 · validação de engenharia

Data: 08/11/2026. Checkout compartilhado, sem commit nesta entrega. Implementação retomada por autorização explícita do usuário após interrupção da sessão. O aceite do contrato 2 e seus ensaios hospedados não são usados como aprovação desta revisão.

## Resultado e escopo

A usa protocolo `fixed_evidence_v2` e projeção de pacote versão 2. O índice distingue domínios semânticos industrial/financeiro da origem física DW; não contém rows. Especialistas recebem o item selecionado e evidências anteriores autorizadas. O item só entra nas evidências após análise validada. O Redator recebe somente itens examinados, com revisão, lacunas e motivo de encerramento. Orçamento curto reserva a resposta final; ausência, contradição, no_observation e ciclo encerram com `insufficient_evidence`.

B mantém contratos/prompt efetivos. Os 39 casos B do baseline diferencial histórico continuam iguais; o arquivo original conserva seus 78 casos, inclusive a caracterização antiga de A. Diferenças intencionais A: vocabulário semântico, seleção `analisar_item|sem_fonte`, contexto por papel, especialista de itens mistos, encerramento com lacunas, versão/hash de contrato. Pacote original/schema/exportador não foram alterados.

A raiz gerenciada é finalizada pelo serviço após persistência; falhas técnicas usam `error`, insuficiência não. Falha de persistência preserva a exceção original e chama a preservação de emergência existente. Standalone fecha sua própria raiz. IDs de run/job/harness/trace permanecem distintos.

O estado atual do monitoramento reside em receipt separado. Worker coalescente serializa progresso sem bloquear o flush. Reconciliação autenticada somente pelo proprietário consulta destino confiável congelado, confere IDs/pais/trace/unicidade e separa aceite de envio de confirmação remota. Limites: 128 spans, três requisições, dez segundos, sem retry; leitura incremental e limite do chamador também cobrem resposta lenta. Falha de leitura/gravação mantém o último DTO autorizado e link verificado, sem devolver null nem alegar nova confirmação durável.

UI usa campo irmão `observability_current`, com fallback legado, botão manual, carregamento, horário/erro/link. Montagem, recarga e indisponibilidade não reenviam modelo/tool/telemetria. A migração 004 é aditiva e idempotente; rollback preserva recibos.

## Evidências por critério

| Critério | Evidência v3 e verificação |
|---|---|
| AC-001 | `spec015-tests.log`: estrutura do grafo e chamadas aos módulos por papel. |
| AC-002 | `v3-tests.log`: A com conexão/fingerprint/catalog bloqueados; `local-integration.json`: nove consultas B nas três combinações e nenhuma A. |
| AC-003 | `v3-tests.log`, `observability-tests.log`: contexto selecionado, itens não examinados, isolamento de duas runs, sanitização e mesmo perfil. |
| AC-004 | `spec015-tests.log`: 39 casos B históricos; regressões A negativas, reparo, ciclo e limites com expectativas separadas. |
| AC-005 | `backend.log`: orçamento, reparos, recusas, timeout/429, cancelamento e limite de recursão. |
| AC-006 | `backend.log`, `local-integration.json`: HTTP/jobs, histórico antigo, export original, detalhe e identidade recursiva. |
| AC-007 | `local-integration.json`: A/B × OpenAI Responses/Groq/Chat Completions, endpoint HTTP falso local. |
| AC-008 | `integration.log`, `local-integration.json`: oito runs pela UI, login/API/job/grafo/consultas/resposta/erro/histórico; cluster descartável parado no finally. |
| AC-009 | `clean-install.log`, `clean-backend.log`, `baseline-check.json`, documentação atualizada: instalação limpa com hashes e invariantes protegidos preservados. |
| AC-010 | Revisão independente final em `review.json`; completion/lifecycle/manifest só encerrados após parecer approved. |
| AC-011 | `observability-tests.log`: matriz, hierarquia, tokens, identidade e paridade off/on. |
| AC-012 | `observability-tests.log`, `v3-tests.log`: off global, fila cheia, falhas, concorrência, receipt lento e flush sem bloqueio por escrita. |
| AC-013 | `frontend-test.log`, `local-integration.json`: link privado, estado parcial, fallback, verificação manual com transporte falso. |
| AC-014 | `v3-tests.log`: machine+financial, product/material consolidados, períodos/IDs, campos de itens vazios, origem física preservada. |
| AC-015 | `v3-tests.log`: ausência, sem fonte, contradição, no_observation, ciclo e orçamento; referências externas bloqueadas. |
| AC-016 | `v3-tests.log`, `backend.log`, `local-integration.json`: erro técnico, insuficiência, cancelamento, persistência e raiz única; persistência observada antes do fechamento. |
| AC-017 | `v3-tests.log`, `local-integration.json`: árvore incompleta/IDs errados/pais/trace, leitura após entrega, receipt relido, URL preservada e hash do snapshot constante. |
| AC-018 | `v3-tests.log`: HTTP 401/400/403/404/409/200, destino congelado/off, leitura limitada; integração SQL com advisory lock, duas aplicações da 004 e rollback sem perda. |
| AC-019 | `local-integration.json`: A multidomínio e insuficiência, B preservado, erro raiz, atraso/404 inicial e botão que confirma árvore/link. Parecer independente exigido nesta revisão. |

## Comandos e limites da prova

Os onze gates canônicos do manifest estão registrados em `validation-results.json`, com logs próprios nesta pasta. Backend principal e instalação limpa incluem oito testes de integração antigos ignorados por flags de ambiente; a integração obrigatória v3 foi executada separadamente com PostgreSQL real descartável e as migrações 1–4. Esses skips não são declarados como testes aprovados.

`baseline-check.json` compara os 320 arquivos do baseline v3: 287 intactos e 33 modificados no escopo aprovado. Os 34 arquivos de contratos B, provedores/ModelService, consultas e exportador abrangidos pelo inventário permanecem iguais. A prova por hash limita-se aos arquivos inventariados; não se apresenta como nova auditoria dos datasets protegidos.

Achados da revisão tratados: aresta de orçamento Especialista→Redator; promoção prematura de item não analisado; progresso final do receipt após flush; deadline de leitura lenta; escrita de receipt bloqueando flush; lint do componente; DTO nulo em falha de armazenamento; contexto de reparo do Selecionador/Especialista/Revisor herdado pelo Redator quando resta somente a chamada reservada. Os testes novos cobrem os casos correspondentes. `regressions-before.log` preserva três falhas reproduzidas antes das correções; a auditoria original AUD-02 permanece em `../usage-audit-2026-11-08.md`, sem reescrita.

Não foram chamados modelos pagos, LangSmith hospedado, RunPod, ngrok ou bancos de pesquisa. O servidor real existente e o banco de aplicação de uso real não foram reiniciados/migrados. Ativar o código no servidor real e aplicar a migração ao banco real são operações posteriores; o runbook está em `docs/langsmith_bancada.md`. O aceite aqui é de engenharia local. Não houve nova adjudicação humana, avaliação científica ou score (`not_scored`).
