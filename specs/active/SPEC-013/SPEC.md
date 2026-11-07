---
id: SPEC-013
title: Harness multiagente de consulta em camadas na Bancada
status: done
contract_version: 3
---

# SPEC-013: Harness multiagente de consulta em camadas na Bancada

## Escopo vigente em 06/11/2026 — contrato 3

**Done de engenharia em 06/11/2026**, com [revisão global independente Astra aprovada](evidence/review.json),
[completion](evidence/completion.json) e [evidências finais](evidence/engineering-closeout-2026-11-06.md).
Foram concluídos o fluxo dos cinco papéis, consultas nos três domínios, feedback,
controle do payload completo, comparação por contratos/dados e vínculo da revisão
ao run exato. A avaliação científica e a adjudicação das respostas são posteriores;
nenhuma nota foi atribuída. Este estado prevalece sobre os marcos históricos abaixo.

O [contrato de limites, comparação e vínculo da revisão](engineering-closeout-contract.md)
foi documentado antes do código.

[Consulta pelo Especialista](specialist-query-contract.md) substitui o Planejador
e a descoberta em duas chamadas. Diagrama atualizado antes desta documentação;
[implementação e testes locais registrados](evidence/specialist-query-implementation-2026-11-06.md). Sem novo envio
a provedores nesta alteração. Contrato 2 e resultados anteriores são históricos;
mantêm-se os gates de engenharia e a separação da avaliação científica.

**Ensaio real posterior, em 06/11/2026:** a [execução pela Bancada com contrato 3](evidence/specialist-query-openai-ui-2026-11-06.md)
terminou `answered_unverified`, com 12 chamadas e três consultas reais nos três
domínios. O Especialista corrigiu uma recusa de grão antes da leitura financeira.
Trajetória, resposta e histórico foram conferidos. Esse ensaio integra o fechamento
técnico junto aos testes e à auditoria; não gera score científico.

Correção implementada: [dependências reais e resposta completa na UI](specialist-query-contract.md#correções-de-rastreabilidade-e-apresentação--06112026),
documentada antes da alteração do código. Mesmos papéis e fluxo do diagrama;
snapshots históricos preservados. [Testes, replay offline e UI verificados](evidence/dependencies-answer-validation-2026-11-06.md),
sem nova inferência externa. Os demais achados técnicos foram encerrados no
relatório de fechamento e na revisão global acima.

## Histórico — escopo de 05/11/2026 — contrato 2

**Evidência nova:** [três repetições reais pela Bancada](evidence/openai-ui-three-runs-2026-11-05.md)
incluem uma cadeia completa nos três bancos, uma resposta parcial e uma falha
de consulta. Não substituem as correções abertas e a revisão técnica final.

Para a próxima rodada OpenAI, o [adendo de observação de saída](evidence/output-budget-validation-2026-11-05.md)
retira os tetos de tokens e bytes da saída dos agentes. Os demais limites e
gates permanecem; a execução aguarda comando explícito do pesquisador.

A [decisão de escopo de engenharia](evidence/engineering-scope-2026-11-05.md)
prevalece sobre exigências históricas de matriz e adjudicação para done.
A conclusão desta SPEC exige motor, tools, interface, persistência, tratamento
de falhas, ensaio real completo pela Bancada e revisão técnica independente.
A matriz científica e a revisão humana das respostas ficam para a fase
posterior; seus bloqueios de pontuação continuam implementados e testados.
OpenAI está autorizada para o piloto de engenharia e Astra para auditoria
separada. Nenhuma nota científica é atribuída. Status permanece in_progress.

Os registros datados abaixo preservam o histórico e não substituem este escopo.

## Estado verificado em 04/11/2026

O [novo ensaio I3 v7](evidence/m2-i3-v7-postgres-readback-groq-limit-2026-11-04.md)
persistiu duas consultas reais, industrial e DW, com o PostgreSQL acessível
durante e após o teste. O Revisor pediu aprofundamento na primeira rodada e
julgou as duas evidências suficientes na segunda. A Groq limitou a chamada
final do Redator com HTTP 429; não houve resposta final nem pontuação.
A SPEC permanece `in_progress` pelos [gates de conclusão](evidence/completion-gates-2026-11-02.md).

## Estado verificado em 02/11/2026

O pesquisador [aprovou a v4 exata dos nove contratos de caso](evidence/m3-executable-case-activation-2026-11-02.md)
e [autorizou a transmissão delimitada à Groq/Qwen](evidence/m2-groq-real-data-approval.json).
A v5 privada liga os casos aprovados aos mapas, consultas e referências sem
alterar a v4. A [primeira chamada real](evidence/m2-groq-i1-one-call-probe-2026-11-02.json)
do Analista passou; o [ensaio integrado I1](evidence/m2-groq-i1-http-interruption-2026-11-02.md)
foi interrompido por queda do PostgreSQL isolado antes de gravar o trace. O
job foi reconciliado como `interrupted`; o número de chamadas do ensaio
integrado não é comprovável. Falha futura de persistência agora guarda trace
privado de emergência. Naquele ponto faltava um run integrado persistido;
diagnósticos posteriores o obtiveram. O status atual permanece `in_progress`:
faltam matriz comparável, adjudicações humanas dos runs e revisão técnica
independente. Nenhuma nota científica foi atribuída.

Um [novo ensaio I1](evidence/m2-groq-i1-http-rate-limit-2026-11-02.md)
persistiu job e trace v6 após a recuperação do cluster. A correção da quarta
chamada ao modelo encontrou limite `429`, antes da primeira consulta (`queries=0`).
O run permanece `not_scored`; ainda falta uma cadeia real completa com dados.

Para investigar o limite do provedor sem repetição automática, o adaptador
Groq do piloto agora espaça o início das chamadas em pelo menos 20 segundos.
Isso não altera pergunta, prompt, schemas, mapas, limites de consulta ou modelo;
apenas o tempo de envio. Cada novo ensaio usa um rótulo próprio e preserva o
run anterior. O script aceita um `case_id` aprovado e uma repetição opcional;
sem repetição, o ensaio é diagnóstico e fica fora da matriz científica.

O [diagnóstico seguinte](evidence/m2-specialist-contract-v3-2026-11-02.md)
eliminou o `429`, mas mostrou que o Especialista repetia `machine.year` em
`map_refs`, embora `year` seja filtro e não coluna selecionável. O contrato
do papel passou à versão 3 e o feedback agora entrega a lista literal de
referências permitidas. Os runs v2 anteriores não integram a matriz v3.

O [primeiro diagnóstico v3](evidence/m2-v3-http-readback-interruption-2026-11-02.md)
foi interrompido por um GET local 503 transitório; o cluster permanecia ativo,
mas o script encerrou seu worker antes de persistir um run. Esse job foi
reconciliado como `interrupted`. O script agora tolera 502/503/504 e erros
transitórios apenas nos GETs, mantendo o POST único.

O [diagnóstico v3b](evidence/m2-planner-filter-context-v4-2026-11-02.md)
chegou ao Planejador, mas revelou que as especificações de filtro da fonte
não eram incluídas em seu input. O contrato de entrada agora projeta
`filter_specs` somente da fonte escolhida; tarefa v4 e feedback exigem as
chaves e tipos literais, com validação final do backend. Os runs anteriores
não podem entrar na matriz sob os novos hashes de contrato.

O [diagnóstico I1 com contrato v4](evidence/m2-i1-complete-diagnostic-v4-2026-11-02.md)
completou a cadeia real com uma leitura DW, dez chamadas Groq e trace v6
persistido. Rota e referência passaram no avaliador automático, que deixou
`awaiting_run_review`. O diagnóstico não é uma das três repetições da matriz.

O executor da matriz em `model_evaluation/run_spec013_pilot_matrix.py` fixa os
nove IDs, três repetições, Qwen, manifesto v5 e hashes dos contratos v4/v3.
Executa um caso por vez, preserva recibos privados e para no primeiro run
falho ou incerto, sem repetição automática. `--resume` confere os bytes de
runs concluídos e os pula; `--check-only` confere o contrato sem inferência.
Mesmo com 27 runs, o avaliador deixa cálculo e conclusão pendentes de revisão
humana por run.

O [primeiro I2-r1](evidence/m2-range-filter-contract-v5-2026-11-02.md)
revelou que a sintaxe `from`/`to` de filtros `:range` ainda não chegava ao
Planejador. Entrada v4 e tarefa v5 agora a expõem. I1-r1 e I2-r1 anteriores
ficam como ensaios de engenharia; a matriz comparável usa rótulos `v5-*`.

Na matriz v5, I1-r1 completou, I2-r1 devolveu evidência insuficiente após
escolher rota diferente da referência e I3-r1 terminou com erro do provedor
na chamada do Revisor após uma leitura industrial. A
[revisão da projeção de contexto](evidence/m2-reviewer-context-v6-2026-11-02.md)
retirou uma cópia duplicada do resultado atual da entrada do Revisor e passou
a registrar o código HTTP quando disponível. A causa do erro I3 não foi
demonstrada. O protocolo comparável atual é v6; os runs anteriores permanecem
diagnósticos. A SPEC continua `in_progress` até completar a matriz,
adjudicar as respostas e obter revisão técnica independente.

O [diagnóstico I3 v6](evidence/m2-i3-v6-rate-limit-2026-11-02.md) validou o
Revisor após a leitura industrial, mas a 11ª chamada, do Redator, recebeu
HTTP 429 com `Retry-After: 9`. O intervalo mínimo entre chamadas de novos
runs passou a 35 segundos. Não houve repetição do run; ele permanece
`not_scored` e fora da matriz.

A [primeira leva v6](evidence/m2-reviewer-question-context-v7-2026-11-02.md)
expôs perda de contexto no Revisor: em I3, ele não recebeu a pergunta literal
nem os domínios que A1 identificou, e julgou suficiente só a contagem
industrial para uma pergunta que também exige total da DW. O contrato v7
passa esses dois campos. Os três runs v6 ficam como diagnósticos históricos;
a matriz comparável deve usar o novo hash de contrato e rótulos v7.
Dois diagnósticos v7 terminaram em HTTP 429 antes da primeira consulta,
inclusive após aguardar o primeiro `Retry-After`; o segundo indicou 363
segundos. Nenhum recebeu nota e as chamadas externas foram interrompidas.
Faltam matriz v7, revisão humana dos runs e revisão técnica independente.

Em 04/11, uma [nova tentativa diagnóstica I3 v7](evidence/m2-i3-v7-postgres-interruption-2026-11-04.md)
foi interrompida por falha do PostgreSQL isolado antes da primeira consulta.
O trace privado de emergência foi preservado, e o job foi reconciliado sem
reenviar a pergunta. Ainda não há run v7 completo.

## Goal

Implementar um novo modo explícito da Bancada no qual chamadas especializadas do
mesmo modelo candidato analisam a pergunta, selecionam trechos de um mapeamento
versionado dos bancos, planejam consultas, julgam a suficiência da evidência e
respondem.
Um orquestrador determinístico executa os contratos, acessa dados apenas por
tools controladas e registra cada etapa. A mesma SPEC seleciona e valida uma
bateria de casos da pesquisa, com gabaritos revisados fora do contexto dos
agentes. Um avaliador separado consome esses gabaritos e os traces para medir
rota, evidência, cálculo e conclusão. O resultado deve permitir atribuir
diferenças entre runs à troca deliberada do modelo, quando as demais condições
forem fixas.

## Context

- Progresso em 01/11/2026: o núcleo `inference_api/src/inference_api/agent_harness/`
  implementa **somente um protótipo M1 com fixture sintética** e testes locais.
  O modo `agent_harness` foi ligado aos jobs e à UI e validado localmente com
  transporte simulado. Um [teste HTTP autenticado](evidence/m1-http-input-contracts-2026-11-01.md)
  cobriu job idempotente e leitura de snapshot v6 com armazenamento em memória;
  os JSON Schemas de entrada por papel e uma fixture industrial foram acrescentados.
  Não consulta bancos reais; uma [verificação posterior](evidence/m1-postgres-storage-2026-11-01.md)
  provou persistência e readback locais do run/job com transporte simulado.
  Um [ensaio integrado](evidence/m1-http-postgres-2026-11-01.md) também passou
  por HTTP autenticado e PostgreSQL local, sem provedor. Não houve ensaio
  Groq completo via Bancada e não satisfaz o M1 completo. Um ensaio Groq com Qwen validou A1;
  A2a foi limitado por `429` no primeiro ensaio. Tentativas posteriores
  mostraram correções explícitas de contrato e novo `429`, sem cadeia completa
  ([evidência](evidence/groq-synthetic-m1-followup-2026-11-01.md)). A migração V2 conhecida
  foi habilitada nas tools exploratórias da DW, e `machine` agora informa a
  proveniência das paradas geradas no recorte. O escopo piloto de DEC-001 foi
  aprovado posteriormente, assim como a política piloto de DEC-002–005;
  implementação, medição e revisão dos casos ainda permanecem abertas;
  a SPEC segue em implementação; o catálogo aprovado pode ser lido localmente.

- Apresentação local em 01/11/2026: a Bancada separou preparação, trajetória e
  histórico. Para snapshots v6, cada evento do trace é agrupado pela rodada
  registrada e permite inspecionar entrada, saída, rejeições e proveniência.
  A interface não cria etapas nem tempos ausentes e distingue validação de
  contrato de avaliação científica. Essa melhoria de leitura não fecha M1 nem
  fecha os gates de implementação de DEC-001–005. A pergunta inicial é mostrada como
  Usuário fora do trace; eventos de modelo são Assistente com o papel interno
  identificado, e consultas são Ferramenta do backend. Um único modelo é
  identificado para a execução, sem sugerir uma IA distinta por papel.
  A preparação apresenta os dois cenários de pesquisa já suportados pelo
  fluxo exploratório (`dw_snapshot` sem tools durante o run; `dw_tools` com
  leitura controlada da DW) e reserva uma seção distinta aos diagnósticos
  sintéticos. Snapshots v3–v5 mostram seus turnos e ferramentas registradas,
  sem atribuir-lhes agentes ou rodadas formais. Essa organização da UI não
  implementa a consulta real à DW pelo novo harness nem fecha decisões da SPEC.

- Auditoria autorizada em 01/11/2026: o mesmo núcleo com fixture inventada
  completou a cadeia diretamente com `gpt-6-luna` via Responses API após
  correções de contratos de A1, A3, A4 e A5. O quarto run teve 11 chamadas,
  duas consultas sintéticas, aprofundamento financeiro e resposta com IDs
  exatos ([evidência](evidence/openai-synthetic-architecture-audit-2026-11-01.md)).
  Não houve acesso a bancos reais, job persistido, UI ou avaliação científica.
  Os contratos de entrada e o prompt foram alterados depois desse run; a
  versão atual não foi reensaiada com provedor real.

- O [inventário físico M0 de 01/11](evidence/m0-physical-schema-2026-11-01.md)
  mostrou que cada domínio excede o teto de 16 KiB da entrada M1. O desenho
  desta SPEC passa a exigir duas chamadas A2a do **mesmo modelo** por domínio:
  seleção de IDs pelo índice semântico compacto e análise do trecho detalhado
  após validação dos IDs pelo backend. O escopo e a política piloto foram
  aprovados, mas o mapa detalhado e a medição dos limites continuam pendentes.
  O núcleo M1 sintético já executa as duas
  chamadas e registra a validação/projeção intermediária
  ([verificação local](evidence/m1-index-detail-navigation-2026-11-01.md)). Isso não autoriza
  usar o inventário físico bruto como mapa semântico de produção.

- O fluxo ativo da Bancada está em `inference_api/frontend/src/features/bench/`,
  `inference_api/src/inference_api/server.py`, `jobs.py` e `service.py`. O modo
  `dw_tools` anuncia cinco chamadas fixas em `dw_tools.py`; a LLM escolhe nome e
  argumentos e `fixed_queries.py` lê somente `db_pesquisa_dw`. Há vários turnos
  do mesmo modelo, mas não há papéis especializados, catálogo semântico de bancos
  nem harness científico. `answered_unverified` é exploratório.
- `db_industrial` e `db_financeiro` contêm importações locais dos CSVs, nas
  camadas `public` tipada e `raw_pN`. Não são fontes operacionais em tempo real.
  A DW v1 tem sete fatos, consultas agregadas, `contributors` e `trace`, mas
  estes dois últimos ainda não são tools da Bancada. Acesso a detalhe não pode
  inventar uma relação entre resultado financeiro e máquina, ordem ou produto.
- A arquitetura científica em `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`
  separa evidência fixa (cenário A) de pesquisa com tools (cenário B). Esta SPEC
  trata do cenário B. O exportador da SPEC-007 e os runs `dw_snapshot` permanecem
  como cenário A; pacotes candidatos não são casos oficiais.
- `model_evaluation/examples/cases_2020.json` e seu schema são apenas exemplo
  de exportação, sem gabarito ou aprovação científica. O antigo rascunho de
  Gold Set foi arquivado por incompatibilidade com a DW v1; não promovê-lo.
- Checkout de desenho em 29/10/2026: HEAD `13d7df5` com alterações anteriores
  não commitadas em API, frontend, documentação e SPEC-012. Reconciliar o diff
  antes de qualquer implementação; uma única thread escreve no checkout.
- A [reconciliação do DER em 31/10/2026](../../../BancoModeloUse/docs/reconciliacao_der_2026-10-31.md)
  encontrou 123 CSVs neste checkout e 166 no worktree canônico separado,
  incluindo 90 paradas geradas em três arquivos. Uma leitura posterior, ainda
  em 31/10/2026, confirmou os três bancos de pesquisa no cluster isolado:
  56 tabelas de origem com colunas e tipos iguais ao contrato canônico, 35
  tabelas na DW (15 V1 + 20 novas), 167 partições de origem e 1.565.666 linhas
  declaradas no inventário. `fact_downtime` contém 1.200 paradas originais e
  90 geradas. O fingerprint da migração V2 corresponde ao manifesto e contrato
  atuais do worktree canônico. Veja a [evidência M0](evidence/m0-inventory-2026-10-31.md);
  o código e os arquivos canônicos ainda precisam ser reconciliados com este
  checkout antes das consultas reais do harness. A lista `sources` da tool
  `machine` foi corrigida em 01/11 para incluir a fonte gerada quando ela
  contribui no recorte, e as cinco tools exploratórias aceitam a V2 de
  fingerprint conhecido. O verificador completo de CSVs da DW continua V1.
  O exportador de pacotes tem [caminho V2 explícito](evidence/m2-dw-v2-packet-export-2026-11-02.md)
  com readback delimitado da carga local e preserva pacotes V1.

## Fluxo de execução vigente — contrato 3

O contrato completo de papéis, contexto, JSON, correção e critérios está em
[consulta construída pelo Especialista](specialist-query-contract.md).
Ele substitui as duas chamadas de descoberta e o Planejador separado.

**Bancada → Analista → Selecionador → Especialista do domínio → backend →
Revisor → Redator.** O Selecionador recebe índice estático; o Especialista
recebe o schema completo da fonte escolhida e monta o plano tipado. Erro
corrigível retorna ao mesmo Especialista com o plano recusado; aprofundamento
retorna ao Selecionador com a lacuna e evidências acumuladas.

## Scope

- Adicionar um modo `agent_harness` explicitamente selecionado, sem alterar a
  semântica dos modos exploratórios atuais nem reescrever snapshots históricos.
- Criar cinco papéis em chamadas separadas: Analista, Selecionador,
  Especialista, Revisor e Redator, com o mesmo modelo candidato. O Especialista
  constrói o plano; não há Planejador separado.
- Manter em arquivos declarativos versionados no backend um mapeamento das fontes
  habilitadas e realmente carregadas, com tabelas, colunas, tipos, chaves,
  relações aprovadas e descrições revisadas de grão, significado, unidades,
  cobertura e atualização. O harness entrega índice de fontes ao Selecionador,
  valida a fonte escolhida e entrega seu contrato completo ao Especialista.
  Nenhuma dessas chamadas consulta o banco ou pede uma tool de
  catálogo. Inventário físico somente leitura confere o mapa antes do
  run; divergência bloqueia a fonte, sem alterar o mapa automaticamente.
- Expor leitura em camadas: consultas atuais da DW, seus caminhos de linhagem
  `contributors`/`trace` e consultas de detalhe aprovadas às tabelas tipadas dos
  bancos industrial e financeiro. A seleção da próxima fonte pertence ao modelo;
  o backend valida e executa o plano, podendo recusar uma relação não comprovada.
- Selecionar e documentar, nesta SPEC, uma bateria auditável de perguntas
  financeiras, industriais e integradas, inclusive evidência suficiente,
  insuficiente e contraditória. Para cada caso, produzir gabarito independente
  com rotas válidas, evidências, cálculos, tolerâncias, interpretação aceitável e
  limites. Exigir revisão humana dos casos, números e rubrica antes de tratá-los
  como conjunto oficial da pesquisa.
- Registrar entrada, saída, modelo efetivo, dados, versões, limites e falhas de
  cada papel e tool. Implementar avaliação por etapa usando os gabaritos
  aprovados, sem vazá-los aos agentes. Relatar resultados estratificados por
  domínio, estado da evidência e tipo de falha; não publicar conclusão científica
  antes de executar e revisar o protocolo completo.
- Atualizar o README da API, a arquitetura científica e o índice de SPECs junto
  à implementação. Testar localmente com transporte de modelo e bancos simulados
  antes de qualquer acesso real ou inferência externa.

## Non-scope

- Declarar superioridade de qualquer modelo antes de executar a bateria com
  protocolo fechado, proveniência verificada e revisão dos resultados.
- Misturar pontuação do cenário B com a do cenário A de pacote fixo; o protocolo
  de evidência fixa permanece separado.
- Recarregar DW/CSV, migrar ou corrigir dados fonte, consolidar IDs entre
  partições ou criar chaves de negócio sem evidência.
- SQL livre gerada pela LLM, credenciais/DDL/DML no contexto do modelo, joins
  não aprovados, acesso genérico a `raw_pN` ou fallback silencioso entre fontes.
- Ligar RunPod, abrir ngrok, usar créditos pagos, executar Terraform, copiar
  bancos reais ao Docker ou enviar novos dados de origem a provedores externos
  por efeito desta SPEC. Autorizações anteriores para DW não cobrem resultados
  adicionais dos bancos de origem.

## Requirements

- REQ-001: O modo novo é opt-in e preserva login, limite global, jobs
  idempotentes, histórico e modos `dw_snapshot`/`dw_tools`. Ausência de modelo,
  mapa versionado ou fonte exigida deve falhar com estado explícito, sem
  reroteamento. Reconciliar a verificação da DW e o exportador de pacotes com
  a carga V2, sem aceitar silenciosamente fingerprints ou versões incompatíveis
  e sem alterar o significado dos pacotes V1 já emitidos.
- REQ-002: O orquestrador executa cinco papéis em chamadas separadas: Analista, Selecionador, Especialista do domínio, Revisor e Redator. O backend projeta o schema completo da fonte escolhida; não há Planejador ou descoberta LLM em duas chamadas. Cada saída é validada; correções explícitas voltam ao mesmo papel e consomem orçamento.
- REQ-003: Todos os papéis cognitivos de um run usam o mesmo modelo candidato
  e registram ID solicitado/efetivo, parâmetros e proveniência por chamada.
  Fixar pergunta, mapas, prompts por papel, tools, dados e limites ao comparar
  modelos. Falha de suporte a saída estruturada não recebe fallback oculto.
- REQ-004: O mapa versionado mantém as fontes aprovadas, campos, tipos, grão, chaves, unidades, cobertura e relações disponíveis. Analista recebe índice de domínios; Selecionador recebe índice compacto de fontes; Especialista recebe contrato completo somente da fonte selecionada, com filter_contracts derivado do executor. Divergência de carga/schema continua bloqueada. Não há escolha semântica oculta pelo backend.
- REQ-005: O Especialista emite plano tipado com fonte, campos, filtros, limite e grão. Não há SQL livre, agregações arbitrárias ou joins entre bancos no piloto. O backend valida e executa somente leituras permitidas com timeout e limites.
- REQ-006: A primeira fonte pode ser DW, linhagem, industrial ou financeiro. O Selecionador pode pedir domínio adicional, recebido como índice estático, ou declarar sem_fonte. O Revisor pode pedir aprofundamento, que volta ao Selecionador; sem saldo o Redator explicita a lacuna.
- REQ-007: A camada de detalhe preserva banco, schema, tabela, chave da linha,
  partição, filtros, fórmula e unidade. A lista de fontes de uma tool deve
  refletir as linhas efetivamente incluídas na consulta, inclusive as paradas
  geradas da carga V2, sem depender de metadados estáticos da carga V1.
  Consultas entre domínios só seguem
  relações explicitamente aprovadas. Resultado financeiro por data não vira
  custo ou receita de máquina/produto por coincidência temporal. `no_observation`
  não equivale a zero.
- REQ-008: O snapshot aditivo preserva, por etapa, request/response brutos
  sanitizados, saída validada, resultado exato da tool, status, erro, tempo,
  tokens/uso quando disponíveis, hashes de prompt/mapa/trecho/consulta/dados e
  destino dos dados. Runs antigos seguem legíveis; painel e exportação distinguem
  erro de entendimento, descoberta, plano, consulta, suficiência e resposta.
- REQ-009: Produzir manifesto versionado da bateria do cenário B. Cada caso
  registra ID estável, pergunta, domínio, recorte/fingerprint de dados, estado
  esperado da evidência e tipo de raciocínio exigido. A seleção cobre financeiro,
  industrial e integrado, com suficiência, insuficiência e contradição. Registrar
  critérios de inclusão/exclusão e origem de cada pergunta; exemplo de exportação
  ou run exploratório não é promovido automaticamente a caso oficial.
- REQ-010: Produzir gabarito separado e versionado por caso com rotas válidas
  alternativas quando houver, evidências/IDs e fontes esperadas, fórmulas,
  valores e tolerâncias verificáveis, interpretações aceitáveis, inferências
  proibidas e critérios de resposta. Derivar números por consultas determinísticas
  reexecutáveis e conferir manualmente casos, vínculos e ressalvas. Guardar
  aprovação humana e hash da versão antes de usá-la para score científico.
- REQ-011: A avaliação roda depois da resposta e fora do contexto dos agentes.
  Compara trace e resposta com gabarito aprovado e informa pontuação separada de
  rota, evidência, cálculo e conclusão, aceitando caminhos equivalentes. Sem
  gabarito aprovado ou sem dado/proveniência exigido, usar `not_scored` com
  motivo; checks literais exploratórios não viram verdade numérica. Agregar ou
  ranquear modelos apenas segundo pesos, repetições e estratos definidos no
  protocolo aprovado.
- REQ-012: Testes locais cobrem escolha direta de fonte, DW seguida de detalhe,
  `no_observation`, contradição, relação proibida, schema divergente, saída
  inválida, orçamento esgotado, idempotência, snapshots antigos e igualdade de
  insumos entre modelos. Teste com fixture não é validação dos pesos reais.
- REQ-013: Não enviar resultados detalhados de `db_industrial`/`db_financeiro`
  a Groq, OpenAI ou outro destino externo sem autorização específica para
  destino, classe de dado e payload. O gate é aplicado antes da primeira
  consulta ou transmissão; configuração padrão é bloqueada.
- REQ-014: Todas as passagens entre papéis e retornos de tools do novo modo
  usam JSON tipado com schema e template versionados por papel. O backend
  carimba identidade e metadados de cada chamada, valida a saída antes de
  encaminhá-la e monta a entrada seguinte somente de campos validados e
  referências explícitas. Pergunta e resposta humana podem ser strings JSON.
- REQ-015: O orquestrador implementa apenas transições do protocolo e gates
  de schema, referências, acesso, orçamento e consulta. Tratabilidade, domínio,
  seleção do trecho, rota, plano, suficiência e resposta vêm das chamadas do
  modelo candidato; não há regra de negócio oculta escolhendo em seu nome.
  Histórico completo fica no trace, enquanto cada papel recebe a projeção
  declarada acima. Falha de contrato, referência inválida ou estouro de
  contexto tem status explícito, sem truncamento ou reparo silencioso.
- REQ-016: O validador de plano classifica `aprovado`, `corrigivel_plano`,
  `corrigivel_rota` e `bloqueado` conforme regras versionadas. Respostas
  corrigíveis devolvem feedback JSON limitado ao mapa já autorizado e voltam,
  respectivamente, ao Especialista ou Selecionador do mesmo candidato; nenhum SQL é executado
  antes de aprovação. Saída JSON malformada pode receber uma tentativa explícita
  do mesmo papel sob o mesmo orçamento. Bloqueios de acesso, escrita, divergência
  do mapa/carga e esgotamento encerram sem replanejamento para contorná-los.
  Resultado válido sem linhas segue a A4. Todas as tentativas e feedbacks são
  persistidos e avaliados separadamente da resposta final.

## Business or domain rules

- BR-001: O modelo candidato decide a próxima consulta; o backend decide apenas
  se o pedido cumpre o contrato e se a execução pode continuar.
- BR-002: O mapeamento fixo não é só um dump do schema SQL: granularidade,
  relações válidas e lacunas da carga fazem parte do contrato. Fonte física nova
  ou alterada exige revisão do mapa versionado; o modelo não introspecta o banco.
- BR-003: A avaliação do fluxo completo troca o mesmo modelo em todos os papéis
  cognitivos. Experimentos que fixem modelos auxiliares medem outra condição e
  recebem identificação separada.
- BR-004: Evidência ausente, inconsistente e incompleta são estados distintos.
  Associação temporal não autoriza atribuição causal ou financeira entre
  entidades sem chave comprovada.
- BR-005: O gold set não entra em prompt, mapa, tool result ou trace que
  seja reenviado ao modelo. O avaliador não corrige a execução retroativamente.
- BR-006: Gabarito humano não precisa impor uma única sequência de tools quando
  diferentes caminhos obtêm evidência equivalente e autorizada. Uma rota que
  inventa vínculo entre bancos nunca é equivalente.
- BR-007: JSON estabiliza a interface e permite validação estrutural; não
  garante acerto semântico do modelo. O avaliador e os testes verificam a
  qualidade das decisões separadamente do cumprimento do contrato.
- BR-008: Feedback de validação serve para corrigir um plano ou rota dentro do
  universo já autorizado. Não amplia o mapa, a allowlist ou o destino, não
  executa proposta recusada e não transforma erro de permissão em tentativa de
  contorno. Correção bem-sucedida não apaga a tentativa inicial do trace.

## Decisions already made

- O usuário definiu nesta conversa uma cadeia de chamadas individuais para
  entender a pergunta, confrontá-la com o mapeamento dos bancos, planejar a consulta,
  analisar o retorno e responder; o backend mantém ferramentas estáveis.
- Para comparar o sistema completo, o mesmo candidato ocupa os papéis do run;
  os demais contratos são congelados. Este é um desenho a confirmar na revisão
  da SPEC, não resultado experimental.
- As fontes atuais são cargas locais de CSV, não bancos operacionais ao vivo;
  usar os limites de grão e vínculo documentados pela DW v1.
- Em 29/10/2026, o usuário decidiu que a mesma SPEC deve englobar a seleção
  dos casos científicos e a criação/revisão dos gabaritos, além do motor.
- Em 29/10/2026, o usuário decidiu substituir o pedido de catálogo pela LLM
  por um mapeamento versionado dos bancos no backend. Agentes A2a especializados
  por domínio, sempre com o mesmo modelo candidato do run, recebem seu mapa
  fixo e montam o trecho necessário; A2b escolhe a rota a partir dos trechos.
  Em 01/11, o inventário físico mostrou que cada mapa completo excede o
  limite de entrada M1; por isso o desenho passou a dividir A2a em seleção
  pelo índice e análise do detalhe. O conteúdo autorizado do mapa e o orçamento
  ainda dependem da revisão detalhada do mapa e da medição dos tetos aprovados.
- Em 29/10/2026, o usuário confirmou contratos JSON e templates por papel para
  cada comunicação. O código mantém o estado e valida transições, enquanto
  as decisões semânticas ficam nas chamadas do modelo candidato.

## Histórico das decisões M0 e estado atual

Os itens DEC-001–005 abaixo registram as questões originais de desenho. Em
02/11/2026, o recorte, a política e o contrato semântico detalhado foram
aprovados para **leitura local**. A cópia habilitada do catálogo passou nas
[12 fontes com `spec013_reader`](evidence/m2-approved-catalog-activation-2026-11-02.md).
Os gates ainda abertos são a integração do modo real da Bancada, a autorização
separada para transmitir detalhe a um provedor, a ativação dos casos para
score, a revisão humana de cada run e a revisão técnica independente. A SPEC
está `in_progress`.

Uma [proposta de resolução M0](evidence/m0-decision-proposal-2026-11-01.md)
organiza recorte, orçamento piloto, casos, acesso e rubrica com base na carga
existente. O [inventário físico dos três schemas](evidence/m0-physical-schema-2026-11-01.md)
apoia um [mapa candidato desabilitado](evidence/m0-semantic-map-candidate-2026-11-01.json).
Esses artefatos iniciais foram depois complementados pelas aprovações abaixo.
O [pacote de revisão do catálogo](evidence/m0-catalog-review-2026-11-01.md)
registra o recorte de 12 fontes, o validador offline e a conferência atual do
inventário no cluster, ainda sem habilitar consultas reais.
Em 01/11/2026, o pesquisador [aprovou o recorte piloto de 12 fontes sem joins
entre bancos](evidence/m0-pilot-scope-approval-2026-11-01.md). A aprovação é
do escopo. O pesquisador também [aprovou a política piloto e assumiu a revisão
dos gabaritos](evidence/m0-pilot-policy-approval-2026-11-01.md). Campos de
retorno de linhagem, cobertura detalhada, medição dos limites, casos
individuais e ligação segura da credencial à Bancada ainda impedem a ativação. O JSON permanece
desabilitado.
Um [ensaio M2 local isolado](evidence/m2-typed-detail-local-2026-11-01.md)
leu uma linha de cada tabela tipada aprovada no recorte, com filtro por PK e
proveniência, sem enviar valores a provedor e sem habilitar o harness real.
Uma [role dedicada de SELECT](evidence/m2-reader-role-2026-11-01.md) foi
provisionada e verificada no cluster local para as tabelas do piloto. Ela
continua desconectada da Bancada; o catálogo real não foi ativado.

O catálogo de M0 tem duas partes versionadas: o inventário físico completo,
que registra objetos e restrições dos três bancos, e um recorte semântico
candidato com fontes que o harness poderá oferecer aos especialistas. O índice
compacto de A2a.1 deve listar apenas fontes **habilitadas após revisão**, nunca
converter automaticamente todo o inventário em tools. Um validador offline
deve comparar IDs, campos, chaves, FKs, consultas fixas, versão da DW e hash do
inventário antes de qualquer habilitação. Essa conferência prova consistência
estrutural; grão, unidade, cobertura e significado exigem revisão explícita.
Para fontes tipadas da carga local, a proveniência por período deve ser
conferida contra a regra do importador `source_id + period_index * 1000000` e
`canonical_source_file`, em transações somente leitura. A inferência desse
período só pode ser usada se cada linha do recorte corresponder a uma partição
registrada e as contagens fecharem; não aplicar a regra a outros bancos ou
cargas sem nova verificação.
O serviço inicial de detalhe tipado aceita uma fonte do recorte por consulta,
campos explícitos e filtros de igualdade por ID ou intervalo temporal
declarados no mapa, sem agregação, join ou SQL fornecido pelo modelo. O backend
compõe identificadores a partir da allowlist, vincula valores como parâmetros,
ordena pela PK, limita linhas/bytes e lê em transação `READ ONLY`. Cada linha
deve trazer banco, schema, tabela, PK, período e arquivo/hash registrados; uma
origem ausente é erro de proveniência, nunca linha sem origem entregue ao
modelo. Esta implementação local não habilita por si só o modo real da Bancada.
Antes de ler linhas, o serviço confere `current_database()` e os tipos físicos
das colunas autorizadas contra o mapa; divergência bloqueia a leitura. A
conferência não substitui uma credencial PostgreSQL dedicada de `SELECT` nem
o fingerprint da carga inteira exigido para habilitar o modo real.

- DEC-001: Recorte inicial das fontes habilitadas, tabelas, colunas e relações
  aprovadas em cada mapa de domínio; quais perguntas obrigatórias devem ser
  resolvidas por esse recorte. O inventário físico confirmou 56 tabelas de
  origem e 35 da DW, incluindo as 90 paradas geradas, no cluster local; isso
  ainda não define quais fontes/relações são semanticamente autorizadas para
  o modelo. Reconciliar os 123 arquivos deste checkout com os 166 do worktree
  canônico e fixar o recorte do mapa. O formato versionado e os campos
  obrigatórios do mapa estão definidos acima, mas o conteúdo aprovado não.
- DEC-002: Orçamento fixo do pipeline: máximo de rodadas de aprofundamento,
  domínios A2a por rodada, duas chamadas A2a por domínio, número máximo de
  tabelas selecionáveis, chamadas de modelo, consultas, linhas, bytes e
  correções de JSON/plano/rota por papel e por run, inclusive o que ocorre ao
  esgotá-las; tamanho por papel, seleção de
  evidências acumuladas e comportamento explícito quando o payload não couber.
  Os limites atuais de `dw_tools` não cobrem automaticamente seis tipos de papel,
  múltiplos especialistas e retornos.
- DEC-003: Quantidade de casos por domínio e estado de evidência, critérios de
  amostragem/exclusão, regras para casos integrados e quem revisa cada gabarito.
- DEC-004: Forma de habilitar leitura real dos bancos de origem e de prover
  credencial com privilégio somente leitura no host/Compose, sem copiar ou
  modificar dados por consequência do desenho.
- DEC-005: Fórmulas e tolerâncias por caso, rubrica de interpretação, pesos (ou
  decisão de não agregar), número de repetições, tratamento de variação e
  política para modelos que não completam algum papel. Não inferir essas
  escolhas do exemplo de manifesto nem do antigo Gold Set.

A [política piloto](evidence/m0-pilot-policy-for-review-2026-11-01.md) para
perguntas, tetos, matriz de casos, acesso e pontuação foi
[aprovada pelo pesquisador](evidence/m0-pilot-policy-approval-2026-11-01.md).
Ele assumiu a revisão humana individual dos gabaritos. A aprovação não prova
que os limites cabem nos payloads nem cria os casos. O catálogo candidato
original continua desabilitado; a cópia aprovada é restrita à leitura local.

## Marcos de resolução e implementação

Os marcos abaixo pertencem à **mesma SPEC** e não substituem seu estado de
ciclo de vida. Antes de `ready`, é preciso fechar as **políticas** de DEC-001–005
em artefatos versionados; os gabaritos individuais e os resultados dos runs são
produzidos e revisados nos marcos posteriores. Exemplos JSON do diagrama não
são schemas executáveis nem mapas aprovados.

1. **M0 — fechar o contrato (`design`):** inventariar em leitura somente a
   carga e o schema das três fontes; reconciliar o inventário de arquivos e
   as fontes geradas com o DER. A leitura local de 31/10 confirmou a carga e
   a estrutura física das 56 fontes e 35 tabelas da DW, mas não aprovou o
   catálogo semântico nem o acesso do harness. Aprovar tabelas, colunas, grãos, unidades,
   cobertura e relações de cada mapa (DEC-001). Fixar limites de chamadas,
   rodadas, correções, linhas, bytes, tempo e contexto, inclusive erro explícito
   quando um payload não couber (DEC-002). Definir amostragem e responsáveis
   pela revisão dos casos (DEC-003), política de acesso somente leitura e gates
   de transmissão (DEC-004), fórmulas, tolerâncias, rubrica, repetições e falhas
   de modelo (DEC-005). Validar `SPEC.md` e `SPEC.execution.json` com
   `--require-ready` somente depois dessas decisões; reconciliar o checkout
   compartilhado antes de qualquer edição de implementação.
2. **M1 — motor local simulado (após `ready`):** criar templates e JSON Schemas
   versionados por papel, adaptar o cliente de modelo para os contratos de
   saída, implementar projeções de contexto, orquestrador, validação, feedback
   corrigível, orçamento e trace. Integrar o modo opt-in `agent_harness` com
   login, jobs, histórico e UI existentes. Exercitar a cadeia inteira com
   transporte de modelo e bancos simulados, incluindo erro de formato,
   aprofundamento, bloqueio e replay. A aprovação dos gabaritos individuais
   não é pré-requisito para este teste do motor; nenhum score científico é
   produzido nele.
3. **M2 — consultas reais controladas:** conferir cada mapa aprovado contra
   schema e carga físicos, prover credenciais de somente leitura e habilitar
   as consultas autorizadas de DW/linhagem e detalhe tipado industrial e
   financeiro. Testar leitura local, filtros, limites, proveniência e relações
   permitidas sem carga ou cópia de dados. Transmissão de detalhe a provedor
   externo continua bloqueada até autorização específica para destino, classe
   e payload, conforme REQ-013; esse gate não é satisfeito por testes mockados.
   Em 02/11, o [adaptador local](evidence/m2-local-query-adapter-readback-2026-11-02-v2.json)
   leu seis caminhos das três bases com a role restrita e um catálogo habilitado
   apenas em memória. A [cadeia de papéis e três consultas reais](evidence/m2-local-chain-readback-2026-11-02-v2.json)
   completou com modelo programado, sem provedor. O contrato semântico
   detalhado foi [aprovado para uso local](evidence/m0-semantic-local-approval-2026-11-02.md).
   A [cópia habilitada e as 12 leituras locais](evidence/m2-approved-catalog-activation-2026-11-02.md)
   passaram com o leitor restrito. Nenhum modo real da Bancada ou transmissão
   a provedor foi ativado por essa aprovação.
   Uma [cadeia posterior com o catálogo aprovado](evidence/m2-approved-catalog-local-chain-2026-11-02.json)
   repetiu 17 chamadas e 3 consultas locais nos três bancos com modelo
   programado, sem provedor ou score.
   O backend ganhou um modo `agent_harness_pilot` ligado ao catálogo aprovado,
   mas [fechado por recibo e chave local](evidence/m2-groq-real-data-transmission-review-2026-11-02.md).
   O despacho foi testado com transporte e consulta simulados; a UI mostra o
   modo como indisponível até a autorização. Nenhum dado real foi enviado à Groq.
4. **M3 — instrumentos de avaliação (engenharia):** selecionar os casos pelo protocolo de M0,
   derivar números de consultas reexecutáveis, produzir gabaritos separados e
   registrar revisão humana de cada caso. Implementar o avaliador e seus
   controles sintéticos; caso sem gabarito aprovado fica `not_scored`. Só
   executar comparação de modelos e apresentar resultado científico na fase
   posterior, após conferir dados, proveniência, versões, repetições e revisão
   independente. A execução da matriz e a adjudicação de respostas não são
   critérios de done da engenharia.

Um avaliador pós-run isolado foi iniciado em `model_evaluation/harness_score.py`:
caso sem recibo de revisão retorna `not_scored`; caso aprovado ainda requer
adjudicação do run para cálculo e conclusão. Os testes usam fixture inventada.
Isso não fecha M3 nem autoriza score científico.
A [matriz candidata de nove perguntas](evidence/m3-case-matrix-draft-2026-11-01.md)
foi preparada com [perfil local de contagens v3](evidence/m3-candidate-profile-2026-11-01-v3.json),
sem valores de linhas no relatório.
Um [pacote privado de revisão](evidence/m3-case-review-packet-2026-11-01.md)
agora reúne referências DW e detalhe/linhagem para os nove rascunhos. I3 e X3
foram reformulados para o teto de três consultas. O pesquisador
[aprovou o conteúdo dos nove casos enumerados](evidence/m3-human-case-content-approval-2026-11-01.md)
na versão exata do pacote revisado. Esse recibo individualiza I1–I3, F1–F3
e X1–X3, sem inventar justificativas separadas que não foram fornecidas.
 Um manifesto privado candidato já vincula filtros, carga, fórmulas,
 tolerâncias e referências aos hashes aprovados. Ainda falta vinculá-lo ao
 mapa semântico habilitado e às execuções reais; nenhum run foi adjudicado ou
 pontuado por essa aprovação.
O manifesto M3 é privado e gerado somente dos bytes do pacote aprovado e dos
resultados de referência registrados no recibo. Deve identificar cada plano
de consulta tipado, hash do resultado e critério de comparação; a geração
falha se os hashes aprovados divergirem. O gabarito continua fora dos agentes.
Em 02/11, o [vínculo técnico privado e o replay local das referências](evidence/m3-case-contract-binding-2026-11-02.md)
foram produzidos para os nove IDs. Os replays reproduziram os hashes dos dois
arquivos privados aprovados. A cópia do catálogo está habilitada somente para
consulta local; o modo real da Bancada continua desabilitado;
o manifesto marca `content_approved_pending_execution` e não habilita score.
Uma [versão v4 privada vinculada aos mapas aprovados](evidence/m3-approved-map-binding-2026-11-02.md)
confere fontes, campos, filtros, grão e hashes dos três domínios. Seu estado é
`approved_map_bound_pending_case_review`; ainda exige revisão do contrato
executável e de cada resposta antes de qualquer score.
 Uma [medição de tamanhos](evidence/m0-pilot-result-size-2026-11-01.md) mostrou
 que os resultados individuais desses exemplos cabem em 32 KiB. No smoke local
 com modelo programado, o maior envelope de entrada mediu 22.110 bytes;
 ainda falta medir a variação com saídas de candidatos reais.

### Validação humana obrigatória

O [protocolo do projeto](../../../docs/protocolo_validacao_humana_avaliacao.md)
e a [ficha reutilizável](../../../model_evaluation/templates/revisao_humana_caso_e_run.md)
definem cinco gates distintos: revisão semântica dos mapas, aprovação do
conteúdo e do contrato executável de cada caso/gabarito, adjudicação de
cálculo e conclusão em cada run, revisão do relatório científico e autorização
específica para transmitir dados a provedores. Checks de schema, SQL, hash,
rota ou referência não substituem essas decisões. Qualquer mudança do pacote
aprovado exige nova versão e revisão; o gabarito fica fora de A1–A5 e das
tools. Um caso sem vínculo técnico completo ou run sem adjudicação humana
permanece `not_scored`.

Inventário, aprovação dos mapas, limites, acesso e rubrica são trabalho de
preparação e revisão humana, fora dos papéis cognitivos A1–A5. Durante um run,
os agentes decidem apenas interpretação, trecho pertinente, rota, plano,
suficiência e resposta dentro dos contratos fixados em M0.

## Constraints

- Reconciliar alterações não commitadas antes de implementar; não sobrescrever
  trabalho de outra thread. Uma thread escritora por vez no checkout.
- Preservar CSVs, DW, splits, pesos, checkpoints, resultados brutos e artigos.
- Nenhuma validação sintética autoriza inferência paga, exposição pública,
  escrita em banco de pesquisa ou afirmação de qualidade científica.

## Acceptance criteria

- AC-001: Run registra os cinco papéis, domínio do Especialista, projeção de mapa, hashes, ordem e entradas/saídas. Não emite especialista_indice, especialista_dados ou planejador_consulta. Mesmo modelo efetivo em todos os papéis.
- AC-002: Um caso de fixture segue DW → detalhe industrial; outro parte direto
  do detalhe financeiro por decisão registrada do modelo, sem rota escolhida
  pelo backend.
- AC-003: Mapa físico/semântico divergente, relação não aprovada, SQL não
  permitida e falta de observação geram estados distintos sem consulta insegura.
  Consulta `machine` com parada gerada mantém `sources`, `contributors` e
  `trace` coerentes com `dw.source_file` na carga V2.
- AC-004: O agente de evidência consegue pedir uma rodada adicional com motivo
  e referências; o orçamento encerra o ciclo sem resposta sustentada fictícia.
- AC-005: Bateria oficial e gabaritos de todos os casos têm IDs, versões,
  fingerprints, cálculos reexecutáveis e revisão humana registrada; nenhuma
  informação de gabarito aparece no payload dos cinco papéis ou nas tools.
- AC-006: Modos antigos e snapshots v1–v5 continuam legíveis e com semântica
  anterior; não há consulta a fonte real ou provedor externo nos testes
  simulados de M1.
  O verificador reconhece a carga V2 apenas com contrato/fingerprint
  correspondentes e a preparação de novos pacotes do cenário A tem caminho
  V2 explícito, sem reescrever pacotes V1.
- AC-007: Evidência da implementação discrimina testes mockados, leitura de
  carga existente, ensaio real autorizado e avaliação científica; revisão
  independente verifica segurança de dados e comparabilidade.
- AC-008: O avaliador pontua por rota, evidência, cálculo e conclusão em casos
  aprovados, aceita caminhos equivalentes e mantém `not_scored` para casos sem
  revisão ou dados comparáveis. Relatório separa domínios, estados da evidência,
  falhas e repetições; nenhuma média mistura cenários A e B.
- AC-009: Fixture integrada percorre três domínios. Selecionador recebe índice compacto; cada Especialista recebe somente a fonte escolhida, preservando tipos e filtros. Consulta pode começar no detalhe; domínio adicional não exige outra LLM para descobrir schema.
- AC-010: Cada chamada registra template e schemas versionados, entrada exata,
  saída bruta e saída JSON validada, papel carimbado pelo backend e referências
  aos eventos de origem. Replay com os mesmos eventos produz as mesmas entradas
  e transições; apenas as saídas do candidato podem mudar decisões semânticas.
- AC-011: Saída do Revisor `precisa_aprofundar` com lacuna e referências válidas
  aciona nova descoberta dentro do orçamento; `suficiente` aciona o Redator.
  Saída malformada, ID inventado, domínio vedado e payload acima do limite são
  distinguíveis no trace, sem roteamento, corte ou correção silenciosos.
- AC-012: Plano recusado corrigível retorna ao Especialista com rejected_plan, rejected_event_id, erro e saldo atualizado. Saída inválida inclui rejected_output. Relação não aprovada retorna ao Selecionador. Bloqueios e limites continuam terminais, sem SQL indevida. Recusas também consomem orçamento.
- AC-013: A engenharia é aceita com os gates do contrato 2: execução completa
  iniciada pela Bancada, trace/histórico persistidos, testes dos três domínios,
  falhas explícitas e auditoria técnica. A matriz científica e a adjudicação
  humana das respostas permanecem posteriores e não bloqueiam esse aceite.

## Affected areas

- `inference_api/src/inference_api/`: novo motor, carregador/validador do
  mapeamento versionado por domínio, ferramentas,
  avaliação, contratos de snapshot e integração mínima com API/jobs/storage.
- `inference_api/frontend/src/features/bench/`: escolha explícita e visualização
  do trace sem mudar a semântica dos runs antigos.
- `BancoModeloUse/`: metadados validados da DW, modelos tipados das duas fontes
  e linhagem; nenhuma carga automática.
- `model_evaluation/`: bateria oficial, gabaritos isolados do modelo, protocolo,
  avaliador, fixtures de desenvolvimento e evidência de revisão humana.
- Documentação da API, dos bancos, da arquitetura científica e índice de SPECs.

## References

- [Fluxo da Bancada e harness no diagrams.net](https://app.diagrams.net/#G1RbtLePrWCTs8GjCAmAegFv7XBcAtzN8E#%7B%22pageId%22%3A%22rC3Onoxkcgc0oOyFh0Ck%22%7D):
  referência visual para revisão. O fluxo textual e os contratos desta SPEC
  são a fonte executável; exemplos JSON desenhados não substituem schemas
  versionados nem decisões DEC-001–005.
- `AGENTS.md`, `README.md`, `specs/README.md`: regras e estado do checkout.
- `specs/active/SPEC-009/SPEC.md`, `specs/active/SPEC-012/SPEC.md`: modos,
  provedores, limites e compatibilidade de snapshots já implementados.
- `inference_api/README.md`, `docs/arquitetura_inferencia_compartilhada.md`:
  fluxo ativo, fronteira de dados e destino de payloads.
- `BancoModeloUse/README.md`, `BancoModeloUse/dw/README.md`,
  `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`: carga existente,
  vínculos válidos, dois cenários e estado científico.
- `inference_api/src/inference_api/{service,dw_tools,config,jobs,storage}.py`,
  `BancoModeloUse/dw/{fixed_queries,cli}.py`,
  `model_evaluation/{README.md,export.py,schemas/cases_manifest.schema.json}`:
  contratos executáveis atuais e diferença entre exemplo e caso científico.

## Skills

- Nenhuma skill especializada de implementação é obrigatória; a thread deve
  seguir as fontes do projeto e esta SPEC. A skill `project-spec-architect`
  foi usada apenas para preparar este contrato.

## Validation requirements

- VAL-001: `git diff --check` no checkout reconciliado.
- VAL-002: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v`
  com novos testes do pipeline e de segurança de consultas.
- VAL-003: `npm --prefix inference_api/frontend run typecheck`.
- VAL-004: `npm --prefix inference_api/frontend run lint`.
- VAL-005: `npm --prefix inference_api/frontend run test -- --run`.
- VAL-006: `npm --prefix inference_api/frontend run build`.
- VAL-007: Ensaio HTTP/browser local autenticado com modelo e bancos simulados,
  verificando job, idempotência, cinco tipos de papel, despacho do Especialista por domínio,
  aprofundamento, trace e histórico.
- VAL-008: Revisão do diff e snapshots quanto a segredos, dados de origem,
  autorização de destinos, consultas permitidas, documentação e compatibilidade.
- VAL-009: Reexecutar as consultas de referência de cada caso oficial contra a
  carga/fingerprint declarados, conferir evidências, fórmulas e tolerâncias,
  registrar revisão humana e provar que os gabaritos não foram enviados aos
  seis papéis nem retornados por tool.
- VAL-010: Executar o avaliador sobre casos aprovados e controles sintéticos com
  rota alternativa válida, dado ausente, cálculo incorreto e inferência causal
  indevida; conferir scores por etapa e `not_scored` quando faltar aprovação.
- VAL-011: Testes de mapa versionado por domínio: inventário físico igual e
  divergente, índice compacto, IDs de tabelas escolhidos pelo modelo,
  validação/projeção do detalhe pelo backend, tabela vazia, relação não
  aprovada, pergunta integrada, isolamento dos mapas em cada payload,
  ordem/limites das chamadas do Especialista por fonte e proveniência das
  paradas geradas na consulta `machine` da DW V2. Testar aceitação explícita da
  carga V2 por verificador/exportador e recusa de fingerprint divergente,
  preservando leitura dos pacotes V1.
- VAL-012: Testes dos contratos JSON por papel e domínio do Especialista,
  além do montador de contexto:
  projeções esperadas, isolamento de mapas/gabarito, IDs carimbados pelo backend,
  replay determinístico, referência inexistente, saída malformada, transições
  `precisa_aprofundar`/`suficiente`, estouro de contexto e ausência de corte
  silencioso de linhas, unidades e proveniência.
- VAL-013: Testes simulados de feedback para Especialista e Selecionador, correção bem-sucedida
  com mesmo modelo, saída JSON malformada, exaustão de tentativas, resultado
  vazio encaminhado a A4 e bloqueios de acesso/escrita/schema. Verificar que
  planos recusados nunca executam SQL e que tentativas, custos e estados ficam
  distintos no trace e na pontuação.

- VAL-015: Ensaio completo pela UI da Bancada com OpenAI autorizada, dados
  locais aprovados, job, consultas, resposta, trace e histórico; sem score.

## Review requirements

- Revisão independente Astra/high antes de `done` (escolha explícita do pesquisador em 05/11): acesso entre bancos, contrato
  público de tools, validade e isolamento dos gabaritos, rubrica, comparação
  entre modelos e possível transmissão a provedores externos são riscos de
  arquitetura, segurança e desenho científico. A revisão de código não
  substitui a aprovação humana do conteúdo de cada caso.

## Execution and runtime

- `SPEC.execution.json` é o contrato de execução. `automatic_handoff` é `false`.
  O estado atual é `done` no escopo de engenharia, com revisão independente aprovada.
  Autorizações de provedores continuam delimitadas pelos recibos existentes. A revisão dos contratos de caso e de cada run é gate
  para score científico, não para os testes locais do motor.
