> **Ensaio real A/B em 06/11/2026:** [resultado pela Bancada](specs/active/SPEC-014/evidence/openai-ab-real-ui-2026-11-06.md). B concluiu com duas consultas e resposta; A terminou em `invalid_review_gap`, sem resposta final. Houve recuperação do PostgreSQL e da trajetória A, sem reenvio. Sem pontuação científica.
>
> **Aceite anterior da SPEC-014 em engenharia local (06/11/2026):** preflight do catálogo e bloqueio de fonte corrigidos e aprovados em revisão independente com fixtures. Esse aceite não comprova funcionamento completo do cenário A no ensaio real acima.

# Pesquisa IC IA


**SPEC-013 · Done de engenharia em 06/11/2026:** [parecer global Astra aprovado](specs/active/SPEC-013/evidence/review.json),
[completion](specs/active/SPEC-013/evidence/completion.json) e [validação final](specs/active/SPEC-013/evidence/engineering-closeout-2026-11-06.md).
O harness de cinco papéis está implementado na Bancada, com leitura controlada
na DW, industrial e financeiro. O ensaio real completo, testes locais, replays
e histórico foram verificados. A matriz científica e a revisão humana de cada
resposta continuam posteriores, sem score atribuído. Este estado substitui
as descrições históricas de implementação pendente abaixo.

**Controles de fechamento em 06/11/2026:** [contrato técnico](specs/active/SPEC-013/engineering-closeout-contract.md).
O limite de entrada mede o corpo HTTP UTF-8 completo; sucesso e falha do provedor
registram tamanho/hash, sem credenciais nem retry automático. A comparação
confronta contratos, mapas, configuração e componentes executáveis, além da DW
e dos manifestos industrial/financeiro antes/depois da execução. Rotas escolhidas
são resultados observados; dados ausentes tornam a compatibilidade indeterminada.
A adjudicação exige o hash do run integral recebido pelo avaliador. A versão
científica continua separada: respostas sem revisão permanecem sem score.
[Evidências do fechamento](specs/active/SPEC-013/evidence/engineering-closeout-2026-11-06.md).

**Contrato vigente em 06/11/2026:** [consulta construída pelo Especialista](specs/active/SPEC-013/specialist-query-contract.md).
Cinco papéis: Analista → Selecionador → Especialista → Revisor → Redator,
com validação e leitura no backend. O Especialista recebe schema completo da
fonte e corrige seu plano quando recusado. Substitui o Planejador separado;
[implementação e testes locais concluídos](specs/active/SPEC-013/evidence/specialist-query-implementation-2026-11-06.md).
O [novo ensaio autorizado pela Bancada](specs/active/SPEC-013/evidence/specialist-query-openai-ui-2026-11-06.md)
completou DW, industrial e financeiro com OpenAI: 12 chamadas, três consultas,
uma correção de plano e resposta persistida `answered_unverified`.
SPEC-013 está `done` em engenharia. Estados datados abaixo
são históricos quando divergirem deste contrato.

**Correções validadas em 06/11/2026:** [rastreabilidade e resposta completa](specs/active/SPEC-013/evidence/dependencies-answer-validation-2026-11-06.md).
Novas execuções registram dependências diretas; a Bancada mostra ressalvas,
cálculos e referências, inclusive no histórico. Testes locais e replay aprovados,
sem nova inferência externa. Snapshots anteriores preservados.


**Bateria pela Bancada em 05/11/2026:** [três repetições OpenAI](specs/active/SPEC-013/evidence/openai-ui-three-runs-2026-11-05.md)
produziram uma resposta parcial, uma resposta após consultar DW/industrial/financeiro
e uma falha por limite de linhas. Os três resultados ficaram no histórico.
A cadeia real foi demonstrada; a SPEC-013 permanece `in_progress`, sem score.

**Escopo vigente em 05/11/2026:** a [decisão do pesquisador](specs/active/SPEC-013/evidence/engineering-scope-2026-11-05.md)
separa conclusão de engenharia e avaliação científica. SPEC-013 contrato 2
exige testes técnicos, cadeia real completa pela Bancada e auditoria Astra.
A matriz científica e a adjudicação humana das respostas ficam posteriores;
sem elas, não há score científico. OpenAI está autorizada para o piloto de
engenharia. Os estados e critérios datados abaixo são históricos quando
contrariarem essa decisão. A SPEC permanece `in_progress`.


**Novo ensaio em 04/11/2026:** o [I3 v7 com duas consultas](specs/active/SPEC-013/evidence/m2-i3-v7-postgres-readback-groq-limit-2026-11-04.md)
confirmou leitura industrial e DW pelo PostgreSQL isolado e trace persistido.
O Revisor abriu a segunda rodada para buscar a DW; a Groq respondeu HTTP 429
na chamada final do Redator. Não houve resposta final nem score científico;
a SPEC-013 segue `in_progress`. A causa da queda anterior do banco segue
desconhecida.

**Atualização em 04/11/2026:** o
[novo diagnóstico I3 v7](specs/active/SPEC-013/evidence/m2-i3-v7-postgres-interruption-2026-11-04.md)
foi interrompido por queda do PostgreSQL isolado antes da primeira consulta.
O trace privado foi recuperado e o job reconciliado; a matriz v7 continua
pendente. A SPEC-013 permanece `in_progress`.

**Estado mais recente da SPEC-013 em 02/11/2026:** três runs de engenharia
sob protocolo v6 foram preservados. I1-r1 passou nos checks automáticos;
I2-r1 e I3-r1 mostraram lacunas de fonte. O [diagnóstico do contrato v7](specs/active/SPEC-013/evidence/m2-reviewer-question-context-v7-2026-11-02.md)
corrigiu a perda da pergunta literal e dos domínios na chamada do Revisor em
testes locais, mas dois ensaios Groq v7 pararam por HTTP 429 antes da
consulta; o segundo registrou `Retry-After: 363`. A SPEC segue `in_progress`, sem matriz v7, revisão de respostas ou
revisão técnica independente; não há score científico.

**Estado da SPEC-013 em 02/11/2026:** o pesquisador [aprovou os nove contratos
executáveis v4](specs/active/SPEC-013/evidence/m3-executable-case-activation-2026-11-02.md)
e [autorizou o envio limitado à Groq/Qwen](specs/active/SPEC-013/evidence/m2-groq-real-data-approval.json).
Uma chamada real do primeiro papel passou. O [ensaio integrado I1](specs/active/SPEC-013/evidence/m2-groq-i1-http-interruption-2026-11-02.md)
foi interrompido por falha do PostgreSQL isolado antes da gravação do trace;
o job foi reconciliado como `interrupted`, sem repetição automática. O código
agora guarda trace privado se uma futura persistência falhar. Naquele ponto,
faltava uma cadeia real completa. A SPEC segue `in_progress` pelos gates
atuais descritos acima. Não há score científico.

Um [novo ensaio I1](specs/active/SPEC-013/evidence/m2-groq-i1-http-rate-limit-2026-11-02.md)
persistiu job e trace após a recuperação do banco, mas a Groq respondeu `429`
na correção do Especialista, antes de qualquer consulta. Esse run é
`not_scored`; uma cadeia completa foi obtida em diagnóstico posterior.

O [diagnóstico I1 v4](specs/active/SPEC-013/evidence/m2-i1-complete-diagnostic-v4-2026-11-02.md)
completou depois a primeira cadeia real com DW e Groq, com trace persistido.
É um run `answered_unverified` fora da matriz e ainda exige revisão humana.

Em 02/11/2026, a SPEC-013 avançou em **preparação local**, mas ainda não está
`done`: o [serviço de leitura tipada](specs/active/SPEC-013/evidence/m0-semantic-activation-review-2026-11-02.md)
passou por DW, linhagem, industrial e financeiro com a role restrita, e uma
[cadeia completa local](specs/active/SPEC-013/evidence/m2-local-chain-readback-2026-11-02-v2.json)
usou três bancos com modelo programado de teste (17 chamadas, 3 consultas,
22.110 bytes no maior input). Os [nove casos aprovados em conteúdo](specs/active/SPEC-013/evidence/m3-case-contract-binding-2026-11-02.md)
agora têm contratos privados vinculados a referências reexecutadas, ainda sem
score. O [contrato semântico detalhado foi aprovado para uso local](specs/active/SPEC-013/evidence/m0-semantic-local-approval-2026-11-02.md);
na etapa anterior, o modo real da Bancada continuava desabilitado e ainda não
havia autorização para enviar detalhe industrial/financeiro a provedor.
O backend possui agora o caminho `agent_harness_pilot`, bloqueado por padrão
até o recibo específico de transmissão à Groq e chave local de ativação;
despacho e snapshot foram testados com mocks, sem envio externo.
O [exportador de pacotes](model_evaluation/README.md) também tem um caminho
explícito para a DW V2, conferido em leitura local; sua verificação V2 é um
readback delimitado, não a reconciliação completa dos CSVs.

Em 01/11/2026, a [SPEC-013](specs/active/SPEC-013/SPEC.md) recebeu um núcleo
simulado do harness multiagente e um modo sintético próprio nos jobs e na UI
da Bancada. A integração passou em testes locais com transporte simulado;
um ensaio Groq anterior parou por limite `429` após o primeiro papel.
O novo modo não lê bancos reais nem produz avaliação científica. As tools exploratórias
da DW reconhecem agora a carga V2 de fingerprint conhecido; o exportador de
pacotes e o verificador completo continuam restritos à V1.
Uma [auditoria sintética direta com GPT-6 Luna](specs/active/SPEC-013/evidence/openai-synthetic-architecture-audit-2026-11-01.md)
completou a cadeia de agentes com duas consultas fictícias. Um
[ensaio HTTP simulado](specs/active/SPEC-013/evidence/m1-http-input-contracts-2026-11-01.md)
cobriu autenticação, job idempotente e leitura de snapshot v6. Um
[readback posterior](specs/active/SPEC-013/evidence/m1-postgres-storage-2026-11-01.md)
verificou persistência PostgreSQL por chamada direta do serviço, com fixture e
limpeza dos registros do teste. Um
[ensaio integrado posterior](specs/active/SPEC-013/evidence/m1-http-postgres-2026-11-01.md)
passou pelo HTTP autenticado e PostgreSQL com modelo simulado. Provedor real pela Bancada e consulta real do
novo harness continuam pendentes.

Em 01/11/2026, o [DER integrado](BancoModeloUse/docs/reconciliacao_der_2026-10-31.md)
foi atualizado para mostrar a carga local DW V2 verificada (35 tabelas e
1.290 paradas). O [desenho do harness](specs/active/SPEC-013/SPEC.md) passou
a especificar duas chamadas por especialista de domínio: seleção de IDs em
índice compacto e análise do detalhe validado. A divisão está implementada no
motor **sintético** e aparece na trajetória da Bancada, com validação/projeção
do backend entre as chamadas. Um [recorte de 12 fontes foi conferido
estruturalmente](specs/active/SPEC-013/evidence/m0-catalog-review-2026-11-01.md)
contra o inventário atual dos três bancos e permanece desabilitado até revisão
semântica. O pesquisador [aprovou o recorte e a política
piloto](specs/active/SPEC-013/evidence/m0-pilot-policy-approval-2026-11-01.md);
os limites ainda precisam ser medidos antes de ativação. Um serviço de detalhe
tipado passou em leitura local isolada de cinco tabelas, e um
[avaliador pós-run](specs/active/SPEC-013/evidence/m3-offline-evaluator-2026-11-01.md)
usa apenas controles fictícios. O pesquisador
[aprovou o conteúdo dos nove casos piloto](specs/active/SPEC-013/evidence/m3-human-case-content-approval-2026-11-01.md),
vinculado ao hash do pacote revisado. Os contratos executáveis de cada caso,
a revisão das respostas dos modelos e a avaliação científica seguem pendentes;
  a SPEC estava `design` em 01/11 e passou a `in_progress` após a aprovação
  semântica para uso local em 02/11. O [protocolo de validação humana](docs/protocolo_validacao_humana_avaliacao.md)
registra os gates que outros pesquisadores deverão repetir.

Mapa do checkout para a pesquisa com Qwen, dados industriais e financeiros. As frentes abaixo compartilham o repositório, mas têm contratos e estados próprios.

| Frente | Onde começar | Conteúdo |
| --- | --- | --- |
| Fine-tuning e avaliação | [FineTuning/CONTEXT_SUMMARY.md](FineTuning/CONTEXT_SUMMARY.md) e [FineTuning/AGENTS.md](FineTuning/AGENTS.md) | Protocolo, configurações, dados congelados, código de treino, adapters e métricas. |
| Execução remota | [runpod/README.md](runpod/README.md) | Scripts históricos de treino/avaliação e [evidência do replay público com streaming na L4](runpod/serving/evidence/2026-10-17-streaming-bancada-l4.md); Pods paradas, sem volume persistente. |
| Bases para nova avaliação | [BancoModeloUse/README.md](BancoModeloUse/README.md) | Este checkout tem 75 CSVs originais e 48 complementares; o worktree canônico separado contém 166 CSVs, incluindo 90 paradas geradas. Um [readback local em 31/10/2026](specs/active/SPEC-013/evidence/m0-inventory-2026-10-31.md) confirmou a carga V2 dos três bancos no cluster isolado, sem validação científica. Veja a [reconciliação do DER](BancoModeloUse/docs/reconciliacao_der_2026-10-31.md), a [DW local](BancoModeloUse/dw/README.md), os [pacotes fixos](model_evaluation/README.md) e os [cenários de comparação](BancoModeloUse/docs/arquitetura_avaliacao_modelos.md); harness formal pendente. |
| Inferência compartilhada | [inference_api/README.md](inference_api/README.md) e [arquitetura](docs/arquitetura_inferencia_compartilhada.md) | [Streaming e jobs](runpod/serving/evidence/2026-10-17-streaming-bancada-l4.md) passaram pelo caminho público autenticado com base e FT-FinQA A na L4; o caso longo chegou completo, sem HTTP 524, mas terminou `length` nos 4.096 tokens de contexto e `response_error`. Avaliação científica continua pendente. |
| Contratos de implementação | [specs/README.md](specs/README.md) | SPECs 001–009 concluídas no escopo local. Em 19/10/2026, a [SPEC-010](specs/active/SPEC-010/SPEC.md) recebeu implementação, testes simulados e [revisão independente aprovada](specs/active/SPEC-010/evidence/review.json). Em 22/10, a [validação real sintética na Bancada](specs/active/SPEC-010/evidence/groq-real-2026-10-22.md) confirmou dois jobs, histórico, tool escolhida pela LLM e limites da conta Free. Isso não é avaliação científica nem validação de proxy HTTPS. A [SPEC-011](specs/active/SPEC-011/SPEC.md) tem [diagnóstico offline e matriz preparada](specs/active/SPEC-011/evidence/local-2026-10-19.md) com [revisão independente aprovada no escopo local](specs/active/SPEC-011/evidence/review.json), causa dos FT-FinQA ainda não isolada e sem nova inferência remota. A [SPEC-012](specs/active/SPEC-012/SPEC.md) concluiu a integração exploratória OpenAI com Luna via Responses API: [revisão sintética](specs/active/SPEC-012/evidence/review.json) e [revisão DW](specs/active/SPEC-012/evidence/review_dw.json) aprovadas, retenção local integral aprovada, [ensaio real sintético](specs/active/SPEC-012/evidence/openai-synthetic-real-2026-10-25.md), [ensaio `dw_tools`](specs/active/SPEC-012/evidence/openai-dw-tools-real-2026-10-25.md) e [ensaio `dw_snapshot`](specs/active/SPEC-012/evidence/openai-dw-snapshot-real-2026-10-26.md) rastreados. O gate DW foi habilitado no ambiente local privado em 26/10; os resultados são `answered_unverified` e o harness científico formal continua pendente. |
| Saídas locais anteriores | `artifacts/`, `tmp/` | Arquivadas fora deste checkout em 11/10/2026; não integram o fluxo ativo. |

Em 22/10/2026, após autorização explícita para enviar resultados da DW real
à Groq, a Bancada recebeu o modo `groq` + `dw_tools`. Um
[ensaio autenticado](specs/active/SPEC-010/evidence/groq-dw-real-2026-10-22.md)
confirmou uma tool `product` escolhida pela LLM, leitura da DW e resposta
persistida. É uma extensão posterior ao escopo sintético da SPEC-010, ainda
sem revisão independente e sem validação científica.

## Caminhos do FineTuning

- Fontes de verdade: [protocolo](FineTuning/docs/protocol_v1.md), `FineTuning/configs/train/`, `FineTuning/configs/eval/`, `FineTuning/data/manifests/` e `FineTuning/results/experiments/*/*/*/meta/run_manifest.json`, na ordem definida em `FineTuning/AGENTS.md`.
- Dados de treino e teste congelados: `FineTuning/data/processed/*_v1/`. Não editar splits manualmente.
- Código de treino e avaliação: `FineTuning/finetune_qwen_wsl/`; a configuração fica em `FineTuning/configs/`.
- Adapters, métricas, predições e manifests de cada execução: `FineTuning/results/experiments/`. Veja o [índice de resultados](FineTuning/results/README.md). Os seis pesos finais usam Git LFS; a base Qwen é obtida separadamente.
- Para localizar os pesos locais, conferir SHA-256, configurações registradas e escolher a bateria para próximos testes, veja o [catálogo de modelos e adapters](FineTuning/docs/modelos_disponiveis.md).
- Fonte local dos splits: `FineTuning/data_ft/`. A [versão editorial canônica do artigo](https://docs.google.com/document/d/1LExZ17IkPXIKYGCHLEJ3mEZSsCU2It1X/edit) está no Google Docs; [DOCX e PDF locais](FineTuning/artigo_canonico/README.md) são snapshots exportados. O [escopo do artigo](FineTuning/docs/escopo_envio_artigo.md) registra o material histórico retirado da árvore ativa.

O [DW local v1](BancoModeloUse/dw/README.md) foi implementado e carregado em um banco novo, separado dos dois bancos de origem e do banco da aplicação. O [desenho da avaliação](BancoModeloUse/docs/arquitetura_avaliacao_modelos.md) separa raciocínio com evidência fixa de pesquisa com tools. O [exportador local da SPEC-007](model_evaluation/README.md) já prepara pacotes candidatos, sem LLM ou gabarito; o harness científico formal permanece planejado. A [Bancada exploratória](inference_api/README.md) agora usa pacotes fixos ou tools escolhidas pela LLM em novos runs; snapshots antigos continuam legíveis. O [serving vLLM](runpod/serving/README.md), preparado pela SPEC-002, teve um [smoke remoto](runpod/serving/evidence/2026-10-17-a5000.md) e uma [integração exploratória da Bancada](runpod/serving/evidence/2026-10-17-integracao-bancada.md) em 17/10/2026. Um [teste posterior](runpod/serving/evidence/2026-10-17-bancada-sete-aliases.md) executou os sete aliases via ngrok: cinco terminaram com resposta não verificada e os dois FT-FinQA truncaram no limite de 500 tokens; a base também consultou a DW por tool. O [replay na L4 sem teto da aplicação](runpod/serving/evidence/2026-10-17-finqa-sem-teto-l4.md) revelou limite de contexto no adapter A e limite de espera do proxy para respostas longas; B respondeu, mas sem conteúdo útil. As Pods foram criadas pelo console e paradas sem volume persistente, sem `terraform plan/apply`; a avaliação científica ainda falta. Nenhuma pasta de treino ou de RunPod foi movida: scripts, configurações, manifests e referências de artigo ainda dependem dos caminhos atuais. Qualquer mudança física futura exige inventário de referências, migração explícita e validação dos consumidores.

O [replay posterior com streaming e jobs](runpod/serving/evidence/2026-10-17-streaming-bancada-l4.md) validou em 17/10/2026 a Bancada autenticada via ngrok com a base e FT-FinQA A na L4. O caso longo chegou em SSE completo, sem HTTP 524, mas repetiu texto até 4.096 tokens totais e foi marcado `response_error`. O job persistiu após refresh e novo login; a Pod e o túnel foram parados.

Código e documentação fora de uso não ficam como orientação ativa. As antigas árvores `agentes/`, `crawler-relacao-investidor/` e `BancoModeloUse/references/bi/` foram preservadas fora do checkout em 11/10/2026. O rascunho de “Gold Set” incompatível com a DW v1 foi arquivado em 16/10/2026 fora do checkout com hash e inventário próprios. Na máquina de origem, o arquivo externo é `D:\Projetos\Github_ViniciusJ\Pesquisa_IC_IA_legacy_archive_20261011`; esse caminho não é portátil para outros clones.
