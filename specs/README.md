> **SPEC-015 contrato 3, engenharia local em 08/11/2026:** [correção de A e dois ajustes do LangSmith](active/SPEC-015/corrections-v3.md). Implementado e [aprovado em revisão independente local](active/SPEC-015/evidence/v3/review.json), com [conclusão v3](active/SPEC-015/evidence/v3/completion.json). [Ativação local A/B e LangSmith verificada](../docs/bancada_operacao.md), sem score científico. O aceite anterior do contrato 2 permanece histórico.

> **Proposta de migração em 08/11/2026:** [SPEC-015 — LangGraph, agentes, ferramentas e LangSmith opcional](active/SPEC-015/SPEC.md). Implementação do contrato 2 autorizada em 08/11/2026: grafo real e LangSmith opcional implementados, engenharia local aprovada em revisão independente. Exportação desligada por padrão; envio hospedado sintético A/B confirmado por leitura da API (11/26 spans); renderização na sessão do usuário não inspecionada. Preserva ModelService e A/B; a correção funcional de A permanece separada.

> **Fontes consolidadas em 07/11/2026:** a DW V2, seus 166 CSVs, contrato, DER e scripts agora estão no checkout principal. O worktree anterior é histórico. [Mapa de fontes e arquivo](../docs/fontes_ativas_e_arquivo.md). A integração não recarregou bancos nem atribuiu score.

> **SPEC-014 concluída em engenharia local (06/11/2026):** preflight do catálogo e bloqueio de fonte corrigidos e aprovados em nova revisão independente. Não há nova inferência remota nem pontuação científica. Ver `specs/active/SPEC-014/evidence/local-integration.json`.

# Frentes de inferência e dados


**SPEC-013 · Done de engenharia em 06/11/2026:** [parecer global Astra aprovado](active/SPEC-013/evidence/review.json),
[completion](active/SPEC-013/evidence/completion.json) e [validação final](active/SPEC-013/evidence/engineering-closeout-2026-11-06.md).
O harness de cinco papéis está implementado na Bancada, com leitura controlada
na DW, industrial e financeiro. O ensaio real completo, testes locais, replays
e histórico foram verificados. A matriz científica e a revisão humana de cada
resposta continuam posteriores, sem score atribuído. Este estado substitui
as descrições históricas de implementação pendente abaixo.

**Controles de fechamento em 06/11/2026:** [contrato técnico](active/SPEC-013/engineering-closeout-contract.md).
O limite de entrada mede o corpo HTTP UTF-8 completo; sucesso e falha do provedor
registram tamanho/hash, sem credenciais nem retry automático. A comparação
confronta contratos, mapas, configuração e componentes executáveis, além da DW
e dos manifestos industrial/financeiro antes/depois da execução. Rotas escolhidas
são resultados observados; dados ausentes tornam a compatibilidade indeterminada.
A adjudicação exige o hash do run integral recebido pelo avaliador. A versão
científica continua separada: respostas sem revisão permanecem sem score.
[Evidências do fechamento](active/SPEC-013/evidence/engineering-closeout-2026-11-06.md).

**Contrato vigente em 06/11/2026:** [consulta construída pelo Especialista](active/SPEC-013/specialist-query-contract.md).
Cinco papéis: Analista → Selecionador → Especialista → Revisor → Redator,
com validação e leitura no backend. O Especialista recebe schema completo da
fonte e corrige seu plano quando recusado. Substitui o Planejador separado;
[implementação e testes locais concluídos](active/SPEC-013/evidence/specialist-query-implementation-2026-11-06.md).
O [novo ensaio autorizado pela Bancada](active/SPEC-013/evidence/specialist-query-openai-ui-2026-11-06.md)
completou DW, industrial e financeiro com OpenAI: 12 chamadas, três consultas,
uma correção de plano e resposta persistida `answered_unverified`.
SPEC-013 está `done` em engenharia. Estados datados abaixo
são históricos quando divergirem deste contrato.


**Escopo vigente em 05/11/2026:** a [decisão do pesquisador](active/SPEC-013/evidence/engineering-scope-2026-11-05.md)
separa conclusão de engenharia e avaliação científica. SPEC-013 contrato 2
exige testes técnicos, cadeia real completa pela Bancada e auditoria Astra.
A matriz científica e a adjudicação humana das respostas ficam posteriores;
sem elas, não há score científico. OpenAI está autorizada para o piloto de
engenharia. Os estados e critérios datados abaixo são históricos quando
contrariarem essa decisão. A SPEC permanece `in_progress`.


**Atualização em 04/11/2026:** o
[diagnóstico I3 v7](active/SPEC-013/evidence/m2-i3-v7-postgres-interruption-2026-11-04.md)
foi interrompido por falha do PostgreSQL isolado. Há snapshot privado de
emergência e job reconciliado, sem consulta concluída. A matriz v7 e a revisão
humana dos runs continuam pendentes; SPEC-013 `in_progress`.

**Estado mais recente da SPEC-013 em 02/11/2026:** o
[protocolo v7](active/SPEC-013/evidence/m2-reviewer-question-context-v7-2026-11-02.md)
passou em testes locais, mas seu primeiro diagnóstico real encontrou HTTP 429
antes da consulta; um segundo diagnóstico após o prazo indicado encontrou
outro 429. Os três runs v6 são diagnósticos de engenharia e não
constituem a matriz comparável. A SPEC permanece `in_progress` e sem score
científico.

**Atualização SPEC-013 de 02/11:** os [nove contratos v4 foram ativados em v5](active/SPEC-013/evidence/m3-executable-case-activation-2026-11-02.md)
e a [transmissão limitada à Groq foi aprovada](active/SPEC-013/evidence/m2-groq-real-data-approval.json).
A primeira chamada real do Analista passou; o [ensaio I1 integrado](active/SPEC-013/evidence/m2-groq-i1-http-interruption-2026-11-02.md)
perdeu a conexão com o PostgreSQL isolado antes de persistir o run. Estado
`in_progress`, sem score e sem revisão independente.
Um [novo I1](active/SPEC-013/evidence/m2-groq-i1-http-rate-limit-2026-11-02.md)
persistiu job e trace v6; a quarta chamada recebeu limite `429`, antes da
primeira consulta. O avaliador manteve `not_scored`.

Em 02/11/2026, a SPEC-013 recebeu um serviço local de consultas DW, linhagem e
detalhe tipado, preso ao catálogo candidato e à role `spec013_reader`. Um
[smoke com modelo programado](active/SPEC-013/evidence/m2-local-chain-readback-2026-11-02-v2.json)
passou por DW, industrial e financeiro em 17 chamadas e 3 consultas, sem
provedor. Os [nove contratos privados de caso](active/SPEC-013/evidence/m3-case-contract-binding-2026-11-02.md)
foram gerados e suas referências reproduzidas; continuam sem pontuação.
O [contrato semântico detalhado](active/SPEC-013/evidence/m0-semantic-local-approval-2026-11-02.md)
foi aprovado para uso local. Uma cópia habilitada do catálogo passou em
[12 leituras locais](active/SPEC-013/evidence/m2-approved-catalog-activation-2026-11-02.md),
e o exportador de pacotes ganhou um
[caminho V2 explícito](active/SPEC-013/evidence/m2-dw-v2-packet-export-2026-11-02.md).
Naquele marco o estado era `in_progress`: ainda não havia run de modelo real
sobre os três bancos nem revisão independente.
O backend tem um modo piloto condicionado por
[gate explícito de transmissão](active/SPEC-013/evidence/m2-groq-real-data-transmission-review-2026-11-02.md);
a interface o mostra indisponível enquanto o gate local estiver fechado.

Em 01/11/2026, a SPEC-013 estava `design`. O recorte de 12 fontes e a
[política piloto](active/SPEC-013/evidence/m0-pilot-policy-approval-2026-11-01.md)
foram aprovados, mas o catálogo real ainda estava desabilitado. A leitura local
tipada passou com uma [role restrita de SELECT](active/SPEC-013/evidence/m2-reader-role-2026-11-01.md)
nos três bancos; o harness da Bancada ainda usa somente fixtures inventadas.

O núcleo sintético de seis papéis está ligado a jobs e UI. O
[ensaio HTTP/PostgreSQL](active/SPEC-013/evidence/m1-http-postgres-2026-11-01.md)
usou modelo simulado. Um [ensaio direto autorizado com GPT-6 Luna](active/SPEC-013/evidence/openai-synthetic-architecture-audit-2026-11-01.md)
completou a cadeia sintética; os ensaios Groq não a completaram por contrato
e limite `429`. Nenhum desses testes valida a consulta real do novo harness.

O pesquisador [aprovou o conteúdo dos nove casos piloto](active/SPEC-013/evidence/m3-human-case-content-approval-2026-11-01.md)
I1–I3, F1–F3 e X1–X3, ligado ao hash do pacote privado revisado. O avaliador
pós-run permanece isolado; há contratos candidatos vinculados a referências,
mas ainda faltam ativação dos casos, medição de runs reais e revisão de cada resposta
de modelo e revisão técnica independente. Sem esses gates não há score
científico. O [protocolo de validação humana](../docs/protocolo_validacao_humana_avaliacao.md)
descreve o trabalho que novos pesquisadores precisam repetir.

Cada SPEC é uma unidade de implementação. O estado das frentes deve ser lido em
`SPEC.md` e `SPEC.execution.json`; este índice mostra somente a ordem e os
limites. As SPECs 001–006 têm threads dedicadas registradas nos manifests;
retomadas devem usar seus IDs. A SPEC-007 foi implementada localmente em
16/10/2026 e tem thread efetiva registrada no manifest. As
[revisões independentes da SPEC-006](active/SPEC-006/evidence/review.json) e da
[SPEC-007](active/SPEC-007/evidence/review.json) aprovaram o escopo local nessa data.
A SPEC-008 foi revisada em 16/10/2026 (contrato v2) para incluir execução
local via Docker Compose com banco isolado. A implementação local na thread
registrada no manifest foi [aprovada na quinta rodada de revisão independente](active/SPEC-008/evidence/review.json)
em 16/10/2026. O front ativo agora é React, com snapshot BI protegido pela
sessão. Os bancos reais não foram copiados.
A primeira API e os contratos foram incluídos em `622fc0f`; a SPEC-002 foi
registrada em `513114d`. As implementações e revisões locais das SPECs 006–008
em 16/10/2026 têm evidências próprias nos respectivos diretórios.

| Ordem | SPEC | Frente | Dependência de execução |
| --- | --- | --- | --- |
| 1 | [SPEC-001](active/SPEC-001/SPEC.md) | Orquestração de agentes, ferramentas de dados e contrato de evidências | Primeira |
| 2 | [SPEC-002](active/SPEC-002/SPEC.md) | Serving vLLM e proveniência dos modelos na RunPod | Contrato de aliases atual; integração final com SPEC-001 |
| 3 | [SPEC-003](active/SPEC-003/SPEC.md) | Identidade individual, autorização e limites de uso | API atual; revisar interação com SPEC-001 |
| 4 | [SPEC-004](active/SPEC-004/SPEC.md) | Bancada web de prompts, verificações e comparação | SPEC-001 e SPEC-003 |
| 5 | [SPEC-005](active/SPEC-005/SPEC.md) | Validação integrada e procedimento da sessão curta | SPEC-001 a SPEC-004 |
| 6 | [SPEC-006](active/SPEC-006/SPEC.md) | DW local rastreável para análise industrial e financeira | `done` no escopo local; não altera a API das SPECs 001 a 005 |
| 7 | [SPEC-007](active/SPEC-007/SPEC.md) | Exportar pacotes fixos de evidência do DW, sem LLM ou gabarito | `done` no escopo local; gold set e caso científico oficial seguem pendentes |
| 8 | [SPEC-008](active/SPEC-008/SPEC.md) | Observatório unificado com Bancada de testes após login, modo host e Docker local | `done` no escopo local, revisão independente aprovada; cluster Windows preservado |
| 9 | [SPEC-009](active/SPEC-009/SPEC.md) | Alternância explícita na Bancada entre pacote fixo da DW e tools escolhidas pela LLM | `done` no escopo local, [revisão independente aprovada](active/SPEC-009/evidence/review.json); sem execução remota nem cópia real do DW |
| 10 | [SPEC-010](active/SPEC-010/SPEC.md) | Groq para testar o fluxo da Bancada e corrigir sessão/erros de plataforma | `done` para o contrato local: testes simulados e [revisão independente aprovada](active/SPEC-010/evidence/review.json) em 19/10/2026; [ensaio real sintético na Bancada](active/SPEC-010/evidence/groq-real-2026-10-22.md) em 22/10 confirmou dois jobs, histórico, tool e limites Free; sem RunPod ou dados reais na Groq |
| 11 | [SPEC-011](active/SPEC-011/SPEC.md) | Diagnóstico e correção demonstrável dos FT-FinQA | inventário e matriz local em 19/10/2026, [diagnóstico](active/SPEC-011/evidence/local-2026-10-19.md) causal `unresolved` e [revisão independente aprovada para o escopo local](active/SPEC-011/evidence/review.json); ensaio real pendente de autorização específica para RunPod |
| 12 | [SPEC-012](active/SPEC-012/SPEC.md) | Provedor OpenAI por API na Bancada exploratória | `done` para a integração exploratória: [testes locais](active/SPEC-012/evidence/local-2026-10-25.md), [revisão sintética](active/SPEC-012/evidence/review.json) e [revisão DW](active/SPEC-012/evidence/review_dw.json) aprovadas; [ensaio sintético direto](active/SPEC-012/evidence/openai-synthetic-real-2026-10-25.md), [ensaio `dw_tools`](active/SPEC-012/evidence/openai-dw-tools-real-2026-10-25.md) e [ensaio `dw_snapshot`](active/SPEC-012/evidence/openai-dw-snapshot-real-2026-10-26.md) com recibos; retenção local aprovada e gate habilitado no ambiente privado em 26/10. Avaliação científica pendente. |
| 13 | [SPEC-013](active/SPEC-013/SPEC.md) | Harness multiagente de consulta em camadas na Bancada | `done` em engenharia; [revisão global Astra aprovada](active/SPEC-013/evidence/review.json), ensaio real nos três domínios e fechamento técnico validados. Matriz e adjudicação científica das respostas posteriores, sem score. |

**Extensão posterior da Groq (22/10/2026):** o pesquisador autorizou enviar
resultados das consultas fixas da DW real à Groq. O modo `groq` + `dw_tools`
foi implementado e um [ensaio real autenticado](active/SPEC-010/evidence/groq-dw-real-2026-10-22.md)
confirmou escolha de `product`, leitura somente da DW, envio do resultado e
run persistido. Essa extensão está fora da validação sintética aprovada da
SPEC-010 e ainda não recebeu revisão independente; não representa avaliação
científica.

Em 19/10/2026, as SPECs 010 e 011 foram contratadas como duas fases separadas.
A primeira usa Groq Free e fixtures sintéticas para validar login, jobs,
streaming, tools e histórico sem GPU. A segunda confronta os outputs brutos,
parâmetros, prompts e manifests dos FT-FinQA A/B com a base antes de atribuir
causa aos adapters. A implementação local da SPEC-010, isoladamente, não
constituía teste real da Groq; o ensaio de 22/10/2026 verificou a Bancada com
fixture sintética, sem reinício de Pod nem validação científica. O checkout de partida
era `bf238ec` com mudanças anteriores sem commit; as duas threads devem
reconciliá-las e não escrever simultaneamente.

A SPEC-001 foi implementada localmente e aprovada em revisão independente em
14/10/2026. A SPEC-002 tem implementação local de manifesto, scripts e
Terraform e um [runbook de custos e aplicação futura](../runpod/serving/README.md).
Sua [revisão independente](active/SPEC-002/evidence/review.json) aprovou o
contrato local em 15/10/2026 sem Pod: geração e validação remota ficam para outra sessão,
e `terraform apply` depende de confirmação explícita. Em 15/10/2026 o usuário
definiu para a SPEC-003 somente Nicoli e Vinicius: ambos podem ficar logados,
mas apenas uma inferência global ocorre por vez, sem limite diário. O painel
mostra teto manual de US$ 10 e saldo RunPod confirmado por leitura quando
disponível. A implementação local e os testes da SPEC-003 constam da
[evidência de 15/10/2026](active/SPEC-003/evidence/local-2026-10-15.md);
a [revisão independente](active/SPEC-003/evidence/review.json) aprovou o
escopo local. O usuário escolheu autenticação somente na aplicação, sem OAuth
ou Basic Auth no ngrok. Antes da exposição futura, as senhas escolhidas no
chat devem ser trocadas em terminal local. A aprovação não cobre ngrok ou
avaliação científica. A revisão independente da SPEC-006 foi concluída
separadamente em 16/10/2026 para a carga local.

Em 15/10/2026, a SPEC-004 foi implementada localmente sobre `1e8cb76` com
revisões declarativas de critérios e comparação visual. A migração 002 passou
em banco descartável e foi aplicada em `db_inference_app` após backup lógico;
a UI passou em navegador com API simulada. A
[revisão independente](active/SPEC-004/evidence/review.json) aprovou o escopo
local em 15/10/2026; esses testes não provam inferência remota.

Em 16/10/2026, a SPEC-005 recebeu pré-voo local, ensaio HTTP opt-in e
[runbook da sessão curta](../docs/sessao_inferencia_curta.md). A validação
local tem recibo e [revisão independente](active/SPEC-005/evidence/review.json)
aprovada. O router não pôde abrir uma thread SDK porque falta
`.codex/references/runtime-policy.json`; a revisão foi feita por subagente
separado, em leitura. O contrato está `done` no escopo local. Geração remota,
ngrok e encerramento real de recursos continuam não executados.

As threads são separadas para manter o contexto de cada frente. Todas usam o
mesmo checkout local; só uma deve escrever nele por vez. A thread seguinte
confere o estado do Git e os contratos concluídos antes de editar. Revisão
independente é exigida onde o manifest indicar. Nenhuma SPEC autoriza iniciar
Pod, abrir ngrok, gastar créditos, publicar ou alterar dados científicos. A
SPEC-006 autorizou uma carga local em `db_pesquisa_dw` após verificar as fontes;
ela não modifica os dois bancos de origem nem o banco da aplicação. A SPEC-007
não autoriza nova carga: sua exportação local usa somente leitura. A SPEC-009
contrata a escolha de tools pela LLM **para runs exploratórios da Bancada** e
o uso dos pacotes candidatos da SPEC-007 no outro modo. Ela não define gold
set, rubrica ou pontuação científica; o harness formal ainda exige contrato
separado, conforme a arquitetura de avaliação.

Fonte de verdade científica: [`BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`](../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md).
Topologia: [`docs/arquitetura_inferencia_compartilhada.md`](../docs/arquitetura_inferencia_compartilhada.md).
