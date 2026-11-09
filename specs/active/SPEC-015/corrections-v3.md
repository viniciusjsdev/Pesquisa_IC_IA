# Contrato 3 · cenário A e correções de observabilidade

Desenho em 08/11/2026, solicitado pelo usuário após [auditoria de uso](evidence/usage-audit-2026-11-08.md). Este documento e [seu fluxo](corrections-v3.mmd) prevalecem sobre trechos de arquitetura/observabilidade do contrato 2 que preservavam o defeito de A ou congelavam o estado de exportação. Na etapa original de desenho não havia autorização de implementação. Autorização posterior explícita do usuário permitiu implementar, testar localmente e submeter à revisão independente nesta sessão. A versão anterior está preservada em `revisions/contract-2/`; seus pareceres e resultados não aprovam automaticamente a versão 3.

## A: representação correta sem alterar os dados congelados

O pacote v1 atual contém até cinco itens das consultas fixas `machine`, `product`, `financial`, `quality`, `material`, com rows, filtros, grão, cobertura e proveniência. É extraído da DW antes da inferência. Seu campo global `domain` não descreve necessariamente cada item; a atribuição de `dw` a todos os itens pelo runtime confunde origem física com domínio semântico.

Não alterar schema, bytes, hash, conteúdo ou exportador dos pacotes v1 nesta correção. Construir uma projeção determinística em memória após a validação existente e congelá-la por run, com `packet_projection_version=2`, hash do índice e hash do pacote original. Não reabrir o banco nem coletar schema para construir essa projeção. Pacote com query desconhecida/inválida é rejeitado pela validação anterior à inferência; não usar LLM para adivinhar domínio.

| query do item | semantic_domains | especialista responsável |
|---|---|---|
| machine | industrial | industrial |
| quality | industrial | industrial |
| financial | financeiro | financeiro |
| product | industrial, financeiro | consolidado (`dw` no registry interno) |
| material | industrial, financeiro | consolidado (`dw` no registry interno) |

`product` combina produção e vendas; `material` combina consumo e preços. O mapeamento é classificação de conteúdo, não aprovação de causalidade, qualidade ou resposta. `source_origin` permanece derivado de `source_snapshot.database` e `item.sources` (DW), nunca convertido ficticiamente em acesso ao banco industrial/financeiro.

Cada entrada do índice tem `item_id` (formato atual `packet:<case_id>:<posição>`), query, semantic_domains, specialist_role, source_origin, grain, fields (derivados do contrato local da query, inclusive com rows vazias), filtros/período, coverage e units. Não incluir linhas completas no índice global. A projeção distingue `item_disponivel`, `item_examinado` e `no_observation`; rows vazias não significam zero nem ausência do item. Múltiplos itens da mesma query e anos diferentes conservam IDs distintos.

Não basta mudar a string `domain`: atualizar prompts, contratos de entrada, validação semântica, roteamento e apresentação de A de maneira coerente. Não mudar contrato ou prompt efetivo de B.

## A: contratos dos papéis e contexto

Todos os papéis continuam existindo e usam o mesmo ModelService/perfil da execução. Agentes A só podem analisar o pacote; nenhum executor SQL, catálogo vivo, RAG ou ferramenta de busca é injetado.

- **Analista:** recebe pergunta, vocabulário semântico `industrial|financeiro`, índice dos itens e domínios efetivamente disponíveis separados. `dominios` identifica os domínios necessários à pergunta, mesmo quando ausentes do pacote; ausência é lacuna. `tratavel` indica possibilidade de analisar alguma parte com o pacote, não garantia de resposta completa.
- **Selecionador:** recebe necessidade, índice, itens examinados, evidências acumuladas, lacuna e orçamento. Em A, `decisao` passa a `analisar_item|sem_fonte`; não existe `pedir_dominio` ou execução `consultar`. Mantém `fonte_id`, `map_refs`, `selection_kind=packet_source`, justificativa e `dominio_adicional=null`. IDs válidos devem pertencer ao pacote e corresponder à seleção. Sem item adequado, devolve sem_fonte; citar fonte externa/inventada continua erro terminal.
- **Especialistas:** recebe somente item escolhido, metadados/linhas originais, necessidade, evidências anteriores autorizadas e feedback de reparo. Entrada distingue semantic_domains e source_origin; saída mantém `action=analyze_packet`, evidence_refs, findings e gaps. O consolidado atende itens mistos; não disparar dois especialistas para o mesmo item por ter dois domínios.
- **Revisor:** recebe as evidências analisadas, necessidade e índice completo com itens examinados/restantes; o índice não adiciona fatos às evidências utilizadas. Saída mantém decisões `suficiente|precisa_aprofundar|contraditoria|indisponivel`, justificativa, referências, lacuna, proximo_dado_necessario e dominio_sugerido. Em A, dominio_sugerido aceita `industrial|financeiro|null`; `dw` deixa de ser domínio semântico. `precisa_aprofundar` significa pedir ao Selecionador outro item/recorte existente, nunca fazer nova consulta.
- **Redator:** recebe evidências efetivamente analisadas, lacunas, suficiência e motivo de encerramento. Responde somente a parte sustentada, expõe informação ausente/contraditória e não preenche valor ausente com zero. Não pode citar item apenas visto no índice como se tivesse analisado suas linhas.

Definir `input.fixed_evidence` e `input.data_access` separadamente no loader; não ampliar permissões de B para acomodar A. `ContextView` pode oferecer `known_domains`, `available_domains` e IDs de itens distintos; usar no validador correto para cada cenário. Não validar sugestão de A apenas contra os domínios presentes: pedir finance quando só há industrial é uma lacuna válida, não `invalid_review_gap`. Domínio fora do vocabulário, JSON inválido e referências inventadas continuam sujeitos aos reparos/erros existentes.

O protocolo efetivo de A ganha versão 2 e hash novo; B mantém versão e contratos efetivos anteriores. Registrar `scenario_contract_version` e `packet_projection_version` no snapshot/runtime de forma aditiva. Histórico antigo é exibido como contrato anterior; não reinterpretar resultados existentes usando o novo comportamento.

Exemplo de saída do Selecionador A (todos os campos obrigatórios, additionalProperties=false):

```json
{
  "decisao": "analisar_item",
  "justificativa": "Falta examinar a evidência financeira já presente no pacote.",
  "fonte_id": "packet:exemplo:2",
  "dominio_adicional": null,
  "map_refs": ["packet:exemplo:2"],
  "selection_kind": "packet_source"
}
```

Exemplo de saída do Revisor A quando a informação financeira não está no pacote (todos os campos obrigatórios, additionalProperties=false):

```json
{
  "decisao": "indisponivel",
  "evidencias_utilizadas": ["packet:exemplo:1"],
  "justificativa": "O pacote contém produção, mas não contém lucro para o período solicitado.",
  "lacuna": "Lucro líquido no período solicitado.",
  "proximo_dado_necessario": "Evidência financeira do mesmo período, ausente do pacote fixo.",
  "dominio_sugerido": "financeiro"
}
```

`sem_fonte` exige fonte_id=null e map_refs vazio; `analisar_item` exige ID disponível e referência correspondente. `indisponivel`/`contraditoria`/`precisa_aprofundar` exigem lacuna não vazia; `precisa_aprofundar` exige próximo dado concreto. `suficiente` pode ter lacuna/proximo_dado_necessario/dominio_sugerido nulos. As referências apontam apenas a evidências analisadas. Os exemplos não acrescentam linhas nem representam gabarito científico.

## A: decisões e encerramento

1. Validar bytes/hash/schema do pacote sem acesso a dados; construir índice imutável.
2. Analista → Selecionador → Especialista escolhido pelo mapa estático → Revisor.
3. `suficiente` leva ao Redator. `contraditoria` e `indisponivel` levam ao Redator com lacuna. `precisa_aprofundar` com domínio suportado porém ausente do índice leva ao Redator com `requested_domain_absent_from_packet`; não gastar uma chamada tentando obter dados que não existem no pacote.
4. Havendo itens potencialmente disponíveis e orçamento, voltar ao Selecionador com a lacuna. O sistema verifica disponibilidade/limites, não julga relevância semântica por palavras-chave. Reanalisar item já examinado é permitido somente se o fingerprint de progresso mudar (nova necessidade/evidência/lacuna); manter detecção de ciclo e limites existentes.
5. `sem_fonte`, orçamento esgotado ou ausência de progresso levam ao Redator com motivo explícito. Manter reserva da chamada final; se nem ela couber, preservar erro técnico de orçamento. Não aumentar limites automaticamente para garantir leitura dos cinco itens.
6. Em A, `answered_unverified` exige revisão suficiente e evidência observada. Caso haja resposta parcial ou encerramento por lacuna, contradição, falta de fonte, no_observation, limite ou ausência de progresso, retornar `insufficient_evidence`, preservando a resposta parcial e ressalvas. Não confundir esses estados com `contract_error` técnico.

Exemplo sintético de aceite: pergunta “Como a produção e o lucro variaram entre os períodos informados?” com itens machine e financial. Analista reconhece industrial e financeiro; Selecionador escolhe um item; Especialista analisa; Revisor solicita o outro domínio presente; Selecionador escolhe o segundo; Revisor conclui e Redator cita ambos. Se o item financial não existir, o fluxo conclui com insuficiência financeira, sem consulta e sem invalid_review_gap. Valores e períodos das fixtures devem ser explicitamente inventados.

## LangSmith AUD-01: raiz representa o término real

Hoje o grafo fecha a raiz antes da persistência e só escreve o status em metadata. Passar a separar término do grafo e término da execução da Bancada. O serviço externo controla a raiz durante preparação já autorizada, execução, verificações finais e persistência. Criar o identificador de harness antecipadamente e passá-lo explicitamente ao grafo/observer; não regenerar IDs ao finalizar/reconciliar.

O grafo retorna resultado sem fechar raiz quando gerenciado pelo serviço; CLIs/testes diretos conservam modo standalone que fecha a raiz ao encerrar sua própria execução. Não fechar duas vezes nem alterar contagem de inferência. Só depois de conhecido o resultado final chamar a finalização do observer. A raiz recebe `error` sanitizado para timeout, cancelamento, erro de contrato/consulta, erro interno ou falha de persistência. `insufficient_evidence` é conclusão com lacunas, não erro técnico do span. Saída e metadata preservam os códigos locais sem incluir stack trace/segredos.

Ao falhar a persistência local, usar preservação de emergência existente, registrar raiz como falha técnica com o mesmo trace_id e manter job falho. Não alegar que houve run persistida. Telemetria não pode encobrir a exceção original nem acionar retry. No sucesso, ligar IDs de job/run local/harness/trace no registro de observabilidade; são identificadores diferentes, não intercambiáveis.

## LangSmith AUD-02: reconciliação separada e somente leitura

Introduzir registro durável no banco de aplicação, separado de `runs.snapshot`: tabela `run_observability`, chave `harness_run_id`, run_id/job_id opcionais até a ligação, principal_id, trace_id, destination_id, content_mode, expected_event_ids, contadores de submissão/falha/descarte, state, url validada, last_checked_at, last_check_error e revision. Nenhuma chave API ou conteúdo de prompt/resultado nesse registro. Aplicar migração aditiva idempotente somente ao banco de aplicação; não alterar DW/industrial/financeiro.

`destination_id` referencia um destino confiável do backend congelado para a run (endpoint/região + projeto + referência da configuração, sem segredo). O cliente não fornece endpoint/projeto/trace_id arbitrário. Mudança de destino atual não redireciona consulta de run antiga; se a configuração original não estiver disponível, retornar destination_unavailable sem tráfego. Usar a mesma autorização local para leitura da run; reconciliar apenas para seu principal proprietário nesta correção, sem criar bypass por ID. Não ampliar permissões existentes.

Fluxo de entrega: criar receipt local quando tracing for habilitado; salvar progresso de forma limitada pelo worker, serializando atualizações com revision para evitar perda entre envio/finalização/reconciliação. Falha nessa escrita apenas degrada observabilidade. Gravar eventos esperados e vínculo com a run antes de liberar a ação de reconciliação. Preservar `runs.snapshot` integralmente; GET de run devolve o snapshot original e um campo irmão `observability_current` lido do receipt. Histórico sem receipt usa somente metadata legada, com indicação de indisponibilidade da atualização, sem inventar destino.

Adicionar `POST /api/runs/{id}/observability/reconcile`, sem corpo configurável, autenticado. Validar UUID, existência, proprietário e destino antes da leitura remota; responder 401/403/404 conforme os casos, sem tráfego em erro de autorização. Usar GET remoto de raiz e listagem dos spans já existentes, nunca create/update/run-model/query. Limitar a 128 spans, até três requisições de leitura e dez segundos totais por reconciliação, sem retry automático e sem varrer projeto inteiro. Contagem acima do limite não significa sucesso. Resposta 200 traz receipt atualizado ou último estado com last_check_error sanitizado; falha remota não transforma run em erro nem apaga URL previamente verificada. Resposta a concorrência local: 409 com código `reconciliation_in_progress`; não iniciar duas leituras da mesma run.

Verificação: conferir IDs esperados, unicidade, trace_id, raiz e parent_run_ids; igualdade só de contagem é insuficiente. Preservar distinção entre `submitted` (aceite de envio) e confirmação remota em campo adicional `remote_verified`. Presença incompleta resulta `partial`; raiz ainda não indexada/404 após envio sem confirmação resulta `pending` com motivo, não “não executado”. Sem observabilidade configurada não há exportação nova; reconciliação de receipt já existente pode ler com configuração confiável explicitamente disponível, mesmo que coleta de novas runs esteja off. Essa ação só lê e é indicada claramente na UI.

Frontend: exibir `observability_current` quando disponível, com fallback ao snapshot antigo; botão “Atualizar monitoramento” em detalhe/histórico para proprietário com receipt; estado carregando, horário da última conferência, falha de consulta e link privado quando validado. Sem polling remoto automático. Ficar offline ou recarregar a página não dispara novamente modelo, tool ou exportação. Reconciliação não ressuscita eventos perdidos: identifica a incompletude e permite ao usuário inspecionar, sem reenvio.

DTO público de observabilidade (schema próprio versionado 1, campos abaixo obrigatórios, adicionais proibidos; url/trusted_origin/last_checked_at/last_check_error podem ser null):

```json
{
  "schema_version": 1,
  "state": "pending",
  "remote_verified": false,
  "can_reconcile": true,
  "trace_id": "00000000-0000-4000-8000-000000000001",
  "submitted_events": 19,
  "failed_events": 0,
  "dropped_events": 0,
  "pending_events": 0,
  "expected_events": 19,
  "observed_remote_events": null,
  "url": null,
  "trusted_origin": null,
  "last_checked_at": null,
  "last_check_error": null,
  "revision": 1
}
```

Estado usa o enum existente; counts são inteiros não negativos (observed_remote_events admite null); revision é inteiro positivo. last_check_error é código sanitizado, nunca exceção livre. IDs de evento esperados/destination_id/credencial não aparecem nesse DTO. POST retorna `{ "observability_current": <DTO> }`; GET de run adiciona o mesmo campo irmão ao snapshot. Para run sem receipt, observability_current=null e fallback visual legado, sem criação implícita de receipt. Evidência remota completa produz remote_verified=true; até completar a lista esperada, mantém false. Limites/falha de leitura preservam a última confirmação bem-sucedida e registram hora/erro da nova tentativa, sem afirmar uma nova confirmação.

## Arquivos afetados

| Área | Arquivos atuais ou novos e trabalho |
|---|---|
| Projeção A | `agent_harness/policies/fixed_evidence.py`, novo `context/packet_index.py`, `context/views.py`, `context/projections.py` |
| Contratos e agentes | `contracts/fixed_evidence.json`, `contracts/input.json`, `contracts/loader.py`, `agents/{question_analyst,source_selector,evidence_reviewer}.py`, contratos/entrada dos especialistas e Redator |
| Grafo | `graph/{state,nodes,routing,execution}.py`, `scenarios.py`: política A, IDs e finalização gerenciada |
| Finalização raiz | `observability/{service,contracts,langsmith_sink}.py`, `executions/{service,jobs}.py`: correlação e término após resultado/persistência |
| Reconciliação | novo `observability/reconciliation.py`, `observability/config.py`, `persistence/storage.py`, migração SQL aditiva no mecanismo de inicialização existente |
| API/UI | `api/server.py`, `frontend/src/features/bench/{benchService,ObservabilityLink,observabilityPresentation,RunDetail,HarnessRounds}` e tipos correspondentes |
| Testes/evidências | testes novos `test_spec015_v3_*.py`, fixtures A separadas, testes frontend e verificador local dedicado à revisão 3 |

Paths Python acima são relativos a `inference_api/src/inference_api/`. Não alterar `contracts/data_access.json`, SQL das fontes de pesquisa, adaptadores de provedor ou dados/exportador do pacote. A não usa banco de pesquisa, mas a Bancada continua usando banco da aplicação para login/jobs/histórico/receipt.

## Verificação, fronteiras e rollback

Antes de editar, caracterizar os achados no código atual e registrar hashes da árvore não commitada do baseline v3. Asserções de nova semântica A devem falhar no runtime atual e passar após implementação. Nunca regenerar `differential-baseline.json` para esconder diferenças: preservar as fixtures históricas e exigir equivalência B, além de diferenças esperadas documentadas de A (domínio, seleção, contexto, encerramento, versão/hash). Novo resultado não é diretamente comparável ao runtime A anterior.

Testes mínimos A: pacote industrial+financeiro; domínio ausente; dois períodos da mesma query; itens mistos product/material; item vazio; índice com linha ainda não analisada; origem DW preservada; referências externas; mesma evidência com nova lacuna versus ciclo; orçamento; reparo JSON; duas runs isoladas; zero executor/catalog refresh/fingerprint de pesquisa com tracing off/on. Não exigir que todo modelo real escolha a mesma rota; testar contratos e roteamento com respostas controladas.

Testes mínimos observabilidade: raiz de sucesso/insuficiência/timeout/erro de consulta/contrato/cancelamento/falha de persistência; fechamento único; entrega após flush; raiz indexada depois; receipt após reinício; remoto parcial; divergência de IDs com mesma contagem; falha de leitura sem apagar evidência; URL/destino inválidos; outro usuário; concorrência; off; migração idempotente; hash do snapshot original antes/depois; zero dispatch de modelo/tool/exportação durante reconciliação. Usar SDK com transporte falso, não APIs reais.

Integração obrigatória futura: UI → A multidomínio com pacote sintético → resposta/insuficiência → histórico; B inalterado → resposta; entrega atrasada e botão de reconciliação → estado/link; falha de inferência → raiz com error. PostgreSQL descartável com schema de aplicação migrado; nenhum modelo pago ou banco de pesquisa real necessário. Evidências novas sob `evidence/v3/`, sem sobrescrever aceite anterior. Rollback para runtime anterior lê snapshots antigos e ignora tabela aditiva; não apagar receipts nem pacotes para reverter. Novo contrato exige revisão independente antes de done; não exige adjudicação científica para aceite de engenharia.

A etapa original solicitava somente documentação. Posteriormente o usuário autorizou implementar, corrigir e testar o contrato 3 e realizar revisão independente. Permanecem fora desta entrega inferência paga, envios hospedados e alterações nos bancos de pesquisa; a migração é validada em banco descartável.
