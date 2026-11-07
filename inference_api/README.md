> **Ensaio real A/B em 06/11/2026:** [resultado pela Bancada](../specs/active/SPEC-014/evidence/openai-ab-real-ui-2026-11-06.md). B concluiu com duas consultas e resposta; A terminou em `invalid_review_gap`, sem resposta final. Houve recuperação do PostgreSQL e da trajetória A, sem reenvio. Sem pontuação científica.
>
> **Aceite anterior da SPEC-014 em engenharia local (06/11/2026):** preflight do catálogo e bloqueio de fonte corrigidos e aprovados em revisão independente com fixtures. Esse aceite não comprova funcionamento completo do cenário A no ensaio real acima.

# Inferência compartilhada: Observatório e Bancada local


**SPEC-013 · Done de engenharia em 06/11/2026:** [parecer global Astra aprovado](../specs/active/SPEC-013/evidence/review.json),
[completion](../specs/active/SPEC-013/evidence/completion.json) e [validação final](../specs/active/SPEC-013/evidence/engineering-closeout-2026-11-06.md).
O harness de cinco papéis está implementado na Bancada, com leitura controlada
na DW, industrial e financeiro. O ensaio real completo, testes locais, replays
e histórico foram verificados. A matriz científica e a revisão humana de cada
resposta continuam posteriores, sem score atribuído. Este estado substitui
as descrições históricas de implementação pendente abaixo.

**Controles de fechamento em 06/11/2026:** [contrato técnico](../specs/active/SPEC-013/engineering-closeout-contract.md).
O limite de entrada mede o corpo HTTP UTF-8 completo; sucesso e falha do provedor
registram tamanho/hash, sem credenciais nem retry automático. A comparação
confronta contratos, mapas, configuração e componentes executáveis, além da DW
e dos manifestos industrial/financeiro antes/depois da execução. Rotas escolhidas
são resultados observados; dados ausentes tornam a compatibilidade indeterminada.
A adjudicação exige o hash do run integral recebido pelo avaliador. A versão
científica continua separada: respostas sem revisão permanecem sem score.
[Evidências do fechamento](../specs/active/SPEC-013/evidence/engineering-closeout-2026-11-06.md).

**Contrato vigente em 06/11/2026:** [consulta construída pelo Especialista](../specs/active/SPEC-013/specialist-query-contract.md).
Cinco papéis: Analista → Selecionador → Especialista → Revisor → Redator,
com validação e leitura no backend. O Especialista recebe schema completo da
fonte e corrige seu plano quando recusado. Substitui o Planejador separado;
[implementação e testes locais concluídos](../specs/active/SPEC-013/evidence/specialist-query-implementation-2026-11-06.md).
O [novo ensaio autorizado pela Bancada](../specs/active/SPEC-013/evidence/specialist-query-openai-ui-2026-11-06.md)
completou DW, industrial e financeiro com OpenAI: 12 chamadas, três consultas,
uma correção de plano e resposta persistida `answered_unverified`.
SPEC-013 está `done` em engenharia. Estados datados abaixo
são históricos quando divergirem deste contrato.

**Correções validadas em 06/11/2026:** [rastreabilidade e resposta completa](../specs/active/SPEC-013/evidence/dependencies-answer-validation-2026-11-06.md).
Novas execuções usam `dependency_policy=direct_input_events_v1`: IDs dos produtores
reais de contexto/evidências, incluindo a tentativa recusada. A Bancada mostra
ressalvas, cálculos, fontes e todas as tentativas do Redator. Replay local e
histórico na UI verificados, sem reescrita dos snapshots nem nova inferência externa.


**Três repetições OpenAI em 05/11/2026:** [evidência da UI e persistência](../specs/active/SPEC-013/evidence/openai-ui-three-runs-2026-11-05.md).
Uma resposta parcial, uma cadeia DW/industrial/financeiro completa e uma falha
`row_limit_exceeded`, com configuração idêntica. Sem nova queda observada nessa
bateria, sem pontuação científica e sem aprovação final da SPEC.

**Tentativa real pela UI em 05/11/2026:** o [job OpenAI foi interrompido antes do modelo](../specs/active/SPEC-013/evidence/openai-ui-postgres-interruption-2026-11-05.md)
por queda do PostgreSQL ao registrar o início. Não houve chamada OpenAI nem
resposta final; as três repetições não foram completadas. Não houve reenvio.

**Rodada OpenAI de validação em 05/11/2026:** o [adendo de saída](../specs/active/SPEC-013/evidence/output-budget-validation-2026-11-05.md)
retira o teto de tokens e bytes de saída somente do piloto OpenAI. O POST omite
`max_output_tokens`; os limites nativos do provedor, entrada e consultas continuam.
O envio real continua aguardando autorização para Executar.

**Bancada preparada em 05/11/2026:** [OpenAI no piloto e UI verificada](../specs/active/SPEC-013/evidence/openai-ui-prepared-2026-11-05.md).
O usuário fez login e a pergunta integrada está preenchida. Nenhum envio real
à OpenAI foi iniciado; aguardar comando explícito para Executar. O contador
de tentativas foi corrigido; outros achados da auditoria continuam abertos.

**Escopo vigente em 05/11/2026:** a [decisão do pesquisador](../specs/active/SPEC-013/evidence/engineering-scope-2026-11-05.md)
separa conclusão de engenharia e avaliação científica. SPEC-013 contrato 2
exige testes técnicos, cadeia real completa pela Bancada e auditoria Astra.
A matriz científica e a adjudicação humana das respostas ficam posteriores;
sem elas, não há score científico. OpenAI está autorizada para o piloto de
engenharia. Os estados e critérios datados abaixo são históricos quando
contrariarem essa decisão. A SPEC permanece `in_progress`.


**Novo ensaio em 04/11/2026:** o [I3 v7 com duas consultas](../specs/active/SPEC-013/evidence/m2-i3-v7-postgres-readback-groq-limit-2026-11-04.md)
concluiu leituras industrial e DW, persistiu o trace e confirmou o PostgreSQL
acessível durante e após o teste. O Revisor pediu aprofundamento e depois
julgou as evidências suficientes. A Groq respondeu HTTP 429 na chamada final
do Redator; não houve resposta nem score, e o run não foi repetido.

**Diagnóstico de 04/11/2026:** o
[I3 v7](../specs/active/SPEC-013/evidence/m2-i3-v7-postgres-interruption-2026-11-04.md)
foi interrompido quando o PostgreSQL isolado caiu antes da primeira consulta.
O trace privado de emergência foi preservado e o job reconciliado, sem novo
envio à Groq. O verificador HTTP agora trata `interrupted` como estado final
após essa reconciliação.

**Atualização de 02/11/2026:** o modo `agent_harness_pilot` usa
`model_alias=groq_harness_pilot`. O [recibo de transmissão](../specs/active/SPEC-013/evidence/m2-groq-real-data-approval.json)
foi aprovado para Groq/Qwen; a chave `INFERENCE_SPEC013_GROQ_REAL_DATA=1`
continua necessária no processo. Uma [sonda real de um papel](../specs/active/SPEC-013/evidence/m2-groq-i1-one-call-probe-2026-11-02.json)
passou, mas o [ensaio HTTP I1](../specs/active/SPEC-013/evidence/m2-groq-i1-http-interruption-2026-11-02.md)
foi interrompido pela queda do PostgreSQL 5544 antes do readback do run. A
persistência do piloto agora salva o snapshot em
`inference_api/.local/spec013_failed_persistence/` se a gravação falhar; esse
arquivo privado exige reconciliação manual e não autoriza repetição. Não há
trajetória real persistida ou score do primeiro ensaio.

Um [novo job I1](../specs/active/SPEC-013/evidence/m2-groq-i1-http-rate-limit-2026-11-02.md)
persistiu o trace v6 após a recuperação. Quatro chamadas Groq foram registradas;
o quarto papel recebeu `429` na correção de uma referência fora do mapa.
`queries=0`, run `provider_rate_limited`, avaliador `not_scored`. O job
`completed` significa que o worker registrou o resultado, não que a resposta
foi concluída. Uma cadeia real foi completada em diagnóstico posterior; a
matriz científica segue pendente.
O adaptador agora espera pelo menos 20 segundos entre inícios de chamadas
Groq no mesmo run, sem repetir uma chamada rejeitada por `429`. O script
Historicamente, `verify_spec013_pilot_http_groq.py` (retirado do fluxo ativo pela SPEC-014) exigia `--case-id` e `--run-label` únicos;
`--repetition 1|2|3` identifica entradas da matriz, enquanto a omissão marca
ensaio diagnóstico. A chave de transmissão continua desligada por padrão.
O [diagnóstico com espaçamento](../specs/active/SPEC-013/evidence/m2-specialist-contract-v3-2026-11-02.md)
mostrou `machine.year` usado indevidamente como `map_refs`. O contrato do
Especialista foi versionado em 3: a saída só pode citar o ID da fonte e
colunas de `fields`, e o feedback de correção lista os IDs exatos aceitos.
Runs com contrato 2 permanecem diagnósticos e não são comparáveis à matriz 3.
O [primeiro ensaio v3](../specs/active/SPEC-013/evidence/m2-v3-http-readback-interruption-2026-11-02.md)
terminou sem trace porque o GET local do job recebeu 503 e o script encerrou;
o PostgreSQL permaneceu ativo. O script agora grava `request_key` privado antes
do POST e tolera erros transitórios apenas nos GETs. Não há repetição do POST.
O [diagnóstico v3b](../specs/active/SPEC-013/evidence/m2-planner-filter-context-v4-2026-11-02.md)
revelou outra perda de contexto: o Planejador não recebia os filtros da fonte
selecionada. O contrato de entrada v3 agora entrega `filter_specs` apenas dessa
fonte; a tarefa v4 e o feedback exigem chaves e tipos literais. O backend ainda
rejeita filtros inválidos. Nenhuma consulta I1 foi concluída nesse diagnóstico.
Um [diagnóstico posterior com contrato v4](../specs/active/SPEC-013/evidence/m2-i1-complete-diagnostic-v4-2026-11-02.md)
completou I1: dez chamadas Groq, uma consulta DW, resposta e snapshot v6
persistido. Rota e citação passaram nos checks automáticos; cálculo e
conclusão continuam `awaiting_run_review`.
O [I2-r1 anterior](../specs/active/SPEC-013/evidence/m2-range-filter-contract-v5-2026-11-02.md)
mostrou que `:range` não explicava ao Planejador o JSON `from`/`to` exigido
pela tool. O contrato de entrada v4 e a tarefa v5 agora incluem o formato;
a tool segue rejeitando operadores não permitidos. Os runs com protocolo
anterior ficam preservados como ensaios de engenharia.

A [projeção v6 do Revisor](../specs/active/SPEC-013/evidence/m2-reviewer-context-v6-2026-11-02.md)
envia o resultado atual em `query_result` e somente resultados anteriores em
`evidence_state`. O teste local passou com três bancos; a causa do erro Groq
em I3-r1 v5 ainda é desconhecida. O adaptador registra status HTTP quando
disponível, sem corpo bruto e sem repetição automática. A matriz comparável
agora exige hashes v6.
O [diagnóstico I3 v6](../specs/active/SPEC-013/evidence/m2-i3-v6-rate-limit-2026-11-02.md)
validou o Revisor após uma consulta industrial, mas recebeu HTTP 429 na
chamada do Redator. Para novos runs, o início de chamadas Groq está espaçado
em pelo menos 35 segundos. O run falho foi preservado, sem repetição.
O [ajuste v7](../specs/active/SPEC-013/evidence/m2-reviewer-question-context-v7-2026-11-02.md)
inclui pergunta literal e domínios identificados por A1 na entrada do Revisor.
Isso corrige a perda de contexto observada em I3-r1 v6. Os runs v6 não entram
na matriz v7; a mudança passou em testes locais e ainda requer run real.
Dois diagnósticos v7 pararam por HTTP 429 antes de consultar dados; o
segundo, após aguardar o prazo do primeiro, indicou `Retry-After: 363`.
As chamadas externas foram interrompidas. O trace privado de cada run foi
preservado, sem repetição automática.

## SPEC-013: modo sintético multiagente e preparação local (02/11/2026)

O backend agora reconhece `agent_harness_pilot` com pergunta real, catálogo
aprovado e consultas locais em camadas. A entrada exige protocolo fixo,
`provider=groq` e `model_alias=groq_harness_pilot`; o modo é recusado antes de abrir
job ou chamar modelo enquanto faltar o
[recibo de transmissão específico](../specs/active/SPEC-013/evidence/m2-groq-real-data-approval.json)
e `INFERENCE_SPEC013_GROQ_REAL_DATA=1`. O recibo foi registrado em 02/11;
a UI mostra o piloto indisponível enquanto a chave local estiver fechada. Testes cobrem o bloqueio e o despacho com
provedor e consulta simulados. `agent_harness` continua como modo sintético.
Em 02/11, typecheck, lint, 9 testes de componentes e build passaram com o Node
local. Os quatro gates também podem ser repetidos sem `npm` com
`inference_api/.venv/Scripts/python.exe inference_api/scripts/validate_frontend.py`
seguido de `typecheck`, `lint`, `test` ou `build`. O POST HTTP do piloto sem
aprovação devolveu 400 antes de criar job.

O [serviço local de consultas](../specs/active/SPEC-013/evidence/m0-semantic-activation-review-2026-11-02.md)
já valida planos tipados para DW, `contributors`/`trace` e detalhe industrial/
financeiro com a role `spec013_reader`; o contrato de dados fixa os hashes do
catálogo candidato e do código das consultas. Uma
[cadeia local com modelo programado](../specs/active/SPEC-013/evidence/m2-local-chain-readback-2026-11-02-v2.json)
executou três consultas e 17 chamadas de papel; não testou decisão de LLM.
O modo `agent_harness` da Bancada segue exclusivamente sintético, e o catálogo
real em disco permanece desabilitado. A aprovação semântica detalhada e o gate
de transmissão são independentes da leitura local; não houve envio de dados
reais a provedor nessa verificação.

A preparação da Bancada apresenta dois cenários de pesquisa: **A, evidência
fixa sem tools de navegação** (`dw_snapshot`), e **B, consulta à DW com tools**
(`dw_tools`). A escolha vem antes do caso/pergunta e do modelo; a tela mostra
somente modelos compatíveis e resume o protocolo antes do envio. Prompt e
critérios exploratórios continuam editáveis em uma seção avançada. Diagnósticos
com fixture (`agent_harness`, `synthetic_snapshot`, `synthetic_tools`) ficam em
outra seção e não são apresentados como um terceiro cenário científico.
Snapshots v3–v5 dos cenários A/B exibem uma trajetória de leitura: pergunta,
pacote fixo quando houver, turnos do modelo, pedidos/resultados de tools
registrados e resposta. Esses snapshots não identificam papéis multiagentes;
a UI não lhes atribui agentes nem rodadas formais. Um pacote fixo não é mostrado
como consulta durante o run. O detalhe de cada etapa abre com um resumo legível;
o payload exato fica disponível em uma área expansível. A resposta final apresenta
negrito, código e listas simples do texto gerado. O histórico rotula A, B, diagnóstico ou fluxo
anterior e continua separado da trajetória. Em 01/11/2026, build, TypeScript,
lint, testes dos componentes e browser smoke com APIs simuladas passaram;
os históricos A (`f7beaf30`) e B (`3261aca7`) foram inspecionados no navegador autenticado em
`127.0.0.1:8765`. Nenhuma execução real foi iniciada por esta mudança.

A UI da Bancada separa agora **Preparar execução**, **Trajetória da execução** e **Histórico**.
Na Trajetória, snapshots v6 de `agent_harness` mostram os eventos registrados
agrupados pelo campo `round`, com resumo legível, entrada projetada, saída
validada, saída bruta, erro e metadados consultáveis por chamada. O painel informa quando uma
chamada foi rejeitada ou corrigida e mantém o evento integral e os hashes em
áreas expansíveis. Na trajetória, a pergunta inicial é apresentada como entrada do
**Usuário** fora do trace; cada chamada de modelo aparece como **Assistente**
com o nome do papel interno, e a consulta aparece como **Ferramenta** do
backend. A identidade do modelo é mostrada uma vez para a execução: os papéis
internos usam a mesma IA, e o serviço de consulta não é outro agente.
Na trajetória, cada rodada pode ser expandida; a etapa escolhida mostra o que
recebeu, devolveu e qual evento foi registrado em seguida. A resposta final
aparece após as rodadas. Para cada especialista, a UI distingue escolha de IDs
no índice, validação/projeção do backend e análise do detalhe. Os JSONs exatos
permanecem acessíveis nas abas da etapa. A sequência usa só o trace salvo;
não infere uma ação futura quando o run termina.
O Histórico oferece uma lista pesquisável de execuções
anteriores e abre o resultado selecionado na área de Trajetória; seleção, feedback e comparação ficam no
Histórico. Snapshots antigos continuam legíveis e exibem um aviso de que não
registram rodadas por papel. A interface não calcula tempos ausentes no trace,
não inventa etapas e não atribui validade científica ao status `validated`.
Em 01/11/2026, o TypeScript, build Vite, lint dos arquivos alterados e a
navegação autenticada pelo Chrome passaram; o componente de trajetória foi
verificado com fixture local, sem nova inferência paga. Ainda não há run v6 de
inferência real preservado neste banco host para inspeção visual;
um [ensaio direto posterior](../specs/active/SPEC-013/evidence/m1-postgres-storage-2026-11-01.md)
confirmou a gravação e o readback de run/job sintéticos no PostgreSQL local,
com limpeza dos registros de teste.
Um smoke posterior em Chrome com API mockada percorreu o Histórico e conferiu
a trajetória v6 com seleção de etapa e resposta; não exercitou persistência
PostgreSQL nem inferência remota.

`src/inference_api/agent_harness/` implementa os cinco papéis do contrato 3.
O Selecionador recebe índice estático e escolhe fonte; `map_projection` registra
o contrato completo entregue ao Especialista, que monta a consulta. Tipos e
filtros não são resumidos por outra chamada. O backend valida e executa; o
Revisor decide aprofundamento. Pergunta, evidências e tentativa recusada ficam
explícitas no JSON. O motor não abre conexões: aceita adaptadores injetados para
fixture ou piloto local, com protocolos e gates distintos.
O desenho anterior em duas chamadas foi substituído em 06/11/2026; seus traces
e evidências permanecem históricos, sem reescrita.
O alias `groq_harness` e o modo `agent_harness`
ligam esse núcleo aos jobs e à UI da Bancada. O modelo padrão desse modo é
`qwen/qwen3.8-27b` via Groq; `GROQ_HARNESS_MODEL` permite outro modelo Groq
não GPT, separado de `GROQ_MODEL`. Sem `GROQ_API_KEY`, a opção fica indisponível.
O prompt do protocolo é fixo, a pergunta e os mapas são inventados, e cada
papel recebe apenas sua projeção JSON. O snapshot v6 guarda o trace integral,
hashes dos contratos e mapas, limites e resposta. Os testes locais cobrem a
integração sem acesso à DW. Um
[teste HTTP posterior](../specs/active/SPEC-013/evidence/m1-http-input-contracts-2026-11-01.md)
cobriu autenticação, job idempotente e leitura do snapshot v6 usando
transporte e armazenamento em memória. A persistência no banco da aplicação
foi verificada separadamente, em chamada direta do serviço com transporte
simulado. Um [ensaio integrado posterior](../specs/active/SPEC-013/evidence/m1-http-postgres-2026-11-01.md)
uniu HTTP autenticado, job idempotente e PostgreSQL da Bancada com modelo
simulado; falta executar a cadeia completa com provedor real pela Bancada.
Um ensaio Groq anterior com
`qwen/qwen3.8-27b` validou A1, mas A2a recebeu `429`; veja a
[evidência](../specs/active/SPEC-013/evidence/groq-synthetic-m1-2026-11-01.md).
Após autorização específica do pesquisador, uma
[auditoria sintética direta via API OpenAI](../specs/active/SPEC-013/evidence/openai-synthetic-architecture-audit-2026-11-01.md)
com `gpt-6-luna` completou os seis tipos de papel, duas consultas à fixture e
o aprofundamento financeiro em 11 chamadas. Três runs diagnósticos anteriores
revelaram ambiguidades de contrato que foram corrigidas; os quatro traces
ficaram preservados. O adaptador OpenAI é um script de auditoria, não um modo
novo da Bancada. Nenhum dado de pesquisa foi enviado nesse teste.
Nenhum resultado desse núcleo é pontuação científica. Em 02/11, a SPEC passou
a `in_progress`; o mapa foi aprovado para leitura local, mas o modo real segue
bloqueado para transmissão e os casos ainda não estão liberados para score.
Um [recorte candidato de 12 fontes](../specs/active/SPEC-013/evidence/m0-catalog-review-2026-11-01.md)
foi conferido offline contra o inventário físico atualizado dos três bancos;
todas as fontes continuam desabilitadas e o modo `agent_harness` ainda usa
somente fixtures inventadas.
Um [serviço de detalhe tipado local](../specs/active/SPEC-013/evidence/m2-typed-detail-local-2026-11-01.md)
foi testado isoladamente com as cinco tabelas de origem do piloto, em transações
somente leitura e sem provedor. Ele não está ligado à Bancada. Uma
[role local dedicada de SELECT](../specs/active/SPEC-013/evidence/m2-reader-role-2026-11-01.md)
foi criada e verificada nos três bancos, mas ainda não é usada pelo harness;
faltam o contrato das fontes DW/linhagem e o gate de transmissão.
O ensaio de leitura tipada foi repetido sob essa role nas cinco fontes, com
[readback próprio](../specs/active/SPEC-013/evidence/m2-typed-detail-reader-readback-2026-11-01.json).
Antes da seleção de linhas, o serviço também confere o nome do banco conectado
e os tipos físicos de todas as colunas permitidas da fonte; divergência bloqueia
a consulta. O ensaio local foi repetido após essa guarda nas cinco tabelas.

As cinco tools exploratórias da DW agora aceitam a migração V2 apenas com o
fingerprint canônico conferido em 31/10/2026; V1 segue aceito. A consulta
`machine` monta as fontes de paradas a partir dos fatos efetivamente incluídos
no filtro, inclusive `paradas_maquinas_geradas`. Isso não habilita o novo
harness nem o exportador de pacotes na V2.

## SPEC-012: OpenAI na Bancada (implementação local de 25/10/2026)

O backend possui alias `openai` para `gpt-6-luna` via
`https://api.openai.com/v1/responses`. Configure `OPENAI_API_KEY` somente no
ambiente do servidor; sem a chave o catálogo indica indisponibilidade e o
backend recusa o run antes de consultar dados. A chave não entra no browser,
snapshot ou logs. A implementação local usa streaming SSE, `store: false`,
reenvio em memória dos itens de raciocínio criptografados e retorno de tools
por `function_call_output`. `temperature` não é aplicado ao Luna com esforço
de raciocínio `medium`; o limite padrão é 4.096 tokens de saída por turno,
com máximo aceito de 8.192. Não há repetição automática de geração.

Modos do provedor: `synthetic_snapshot` envia pergunta, prompt fixo e fixture
inventada; `synthetic_tools` anuncia somente `synthetic_metric` e envia seu
resultado se a LLM solicitar; `dw_snapshot` envia a pergunta e o JSON integral
de **um** pacote candidato selecionado por ID e SHA-256; `dw_tools` anuncia as
cinco consultas fixas e envia somente os resultados das chamadas escolhidas
pela LLM. Ambos os modos DW usam a autorização específica de 25/10/2026.
Eles permanecem bloqueados por padrão. O banco da aplicação guarda o snapshot
integral em `runs.snapshot` sem TTL automático e o histórico é acessível aos
pesquisadores autenticados. Em 26/10/2026, o pesquisador aprovou manter a
regra existente: cópia integral sem expiração nem remoção automática, acessível
a Vinicius e Nicoli. A [revisão independente específica dos modos
DW](../specs/active/SPEC-012/evidence/review_dw.json) foi aprovada em
26/10/2026. Depois desses gates, o operador pode definir
`INFERENCE_OPENAI_DW_ENABLED=1`
no processo backend (ou no ambiente do Docker Compose); o catálogo e a UI
então os anunciam. O backend confere o gate antes de criar job ou ler a DW.
`dw_tools` consulta apenas `db_pesquisa_dw` em transação `READ ONLY`, com até
cinco chamadas, seis turnos, 200 linhas e 16 KiB de resultados acumulados.
Nenhum SQL livre, banco inteiro, gabarito, peso ou resultado bruto de treino é
enviado. Snapshots OpenAI são v5 e registram provedor, destino, classe de dado,
hash/fingerprint aplicável, bytes da evidência incluídos nas requisições
tentadas (contando o reenvio do histórico stateless), uso e IDs
de resposta quando disponíveis. Os v1–v4 continuam legíveis.

O preço Standard publicado em 25/10/2026 para o Luna era US$ 0,10 por milhão
de tokens de entrada e US$ 0,50 por milhão de saída. Confira preço, acesso,
saldo e estado da recarga automática na conta antes de outros ensaios pagos.
O pesquisador decidiu usar os créditos pré-pagos disponíveis, com recarga
automática desligada, sem teto monetário adicional na Bancada. A aplicação
não compra créditos nem altera limites da conta. A
[primeira revisão independente](../specs/active/SPEC-012/evidence/review.json)
aprovou somente o fluxo sintético local; a
[revisão DW posterior](../specs/active/SPEC-012/evidence/review_dw.json) aprovou
o escopo técnico dos dois modos. Isso não confirma qualidade científica.

Em 25/10/2026, um [único ensaio real sintético](../specs/active/SPEC-012/evidence/openai-synthetic-real-2026-10-25.md)
por chamada direta a `service.execute_run` confirmou `gpt-6-luna` na Responses
API, resposta à fixture inventada e snapshot v5 persistido. O run terminou em
`answered_unverified`; o ensaio não passou por login HTTP, jobs ou UI e não
enviou dados da DW.

Um [ensaio posterior pela Bancada com `dw_tools`](../specs/active/SPEC-012/evidence/openai-dw-tools-real-2026-10-25.md)
na mesma data usou `INFERENCE_OPENAI_DW_ENABLED=1` apenas no processo local.
O Luna escolheu `financial({"year":2021})`, o backend leu 13 observações da
DW e enviou o resultado à Responses API. O job e o run ficaram no histórico;
as 13 linhas da resposta foram conferidas contra a tool. O servidor foi
reiniciado com o gate desligado após esse ensaio. Em 26/10, um
[ensaio de `dw_snapshot` pela Bancada](../specs/active/SPEC-012/evidence/openai-dw-snapshot-real-2026-10-26.md)
enviou os 2.762 bytes exatos de um pacote candidato selecionado, sem nova
consulta à DW no run. O revisor conferiu o job e o snapshot em readback.
Após a revisão e a decisão de retenção, o gate foi definido como `1` no
`BancoModeloUse/.env.local` local ignorado pelo Git; um backend novo exibiu
os modos na UI autenticada. Os ensaios são exploratórios e continuam
`answered_unverified`.

## Groq e DW real por tools (22/10/2026)

Após autorização explícita do pesquisador, a Bancada passou a oferecer o modo
`dw_tools` também para o provedor Groq. Selecione **Groq** em “Provedor e
modelo” e **Groq consulta a DW real por tools** em “Modo de evidência”; escreva
uma pergunta livre e execute uma vez. O prompt e os critérios da Bancada são
usados nesse modo. A LLM escolhe entre as cinco consultas fixas; o backend
valida nome e argumentos, executa somente leitura em `db_pesquisa_dw` e envia
à API HTTPS da Groq o resultado da consulta escolhida. A pergunta e o prompt
também são enviados. Não há SQL livre nem acesso aos bancos de origem. Os
limites permanecem cinco chamadas, seis turnos, 200 linhas e 16 KiB de
resultados cumulativos. A ausência de DW bloqueia a geração; tool inválida,
consulta falha e limite excedido ficam como erro no run.

O histórico registra provedor, modelo, fingerprint da DW, catálogo, argumentos,
resultados, turnos e destino externo configurado. `answered_unverified` indica
somente conclusão exploratória; a resposta e os números não receberam gabarito
nem avaliação científica. O modo `dw_snapshot` com pacote privado continua
disponível apenas para RunPod; os modos sintéticos da Groq continuam isolados.
Esta extensão posterior não integra a validação sintética original da SPEC-010.
Um [ensaio real autenticado em 22/10/2026](../specs/active/SPEC-010/evidence/groq-dw-real-2026-10-22.md)
confirmou um job persistido: Groq escolheu `product(2020, 1000001)`, recebeu
uma linha da DW e respondeu. Não houve revisão independente dessa extensão.

## SPEC-010: Groq sintética e sessão de navegador (19/10/2026)

**Leitura do histórico em 22/10/2026 (checkout base `2d507a9`, alteração
local sem commit):** a lista e o detalhe da Bancada passaram a priorizar data
local, estado em português, pergunta, resposta, origem, tools e verificações
exploratórias. Metadados e JSON permanecem em **Detalhes técnicos e
rastreabilidade**. O build React,
typecheck e lint passaram; a interface foi conferida com um run Groq real já
salvo e um run RunPod histórico com erro, sem nova inferência. Os snapshots e
as tabelas não foram alterados.

A Bancada anuncia `groq` como provedor separado dos sete aliases RunPod.
Sem `GROQ_API_KEY` e `GROQ_MODEL` no **processo backend**, o item fica
indisponível com motivo. A URL de produção do cliente é fixa em
`https://api.groq.com/openai/v1/chat/completions`; o navegador não recebe
a chave. Em modo host, configure as variáveis no terminal local ou no arquivo
ignorado `BancoModeloUse/.env.local` antes de iniciar a API. Em Docker Compose,
configure as variáveis no ambiente usado para iniciar o Compose. Confirme na
conta Groq que o ID escolhido está disponível no plano Free; modelo e cotas
podem mudar. Não cole a chave no chat, no Git nem em logs.

No escopo original da SPEC-010, Groq aceitava somente `synthetic_snapshot` e
`synthetic_tools`. Ambos usam a
pergunta e o prompt fixos de `synthetic_data.py`; o segundo modo anuncia a
tool local `synthetic_metric`, cuja chamada deve ser escolhida pela LLM e
validada antes de a fixture inventada responder. A API recusa pacotes privados,
perguntas livres e critérios editáveis nesses runs. Nesses dois modos, a DW
real não é consultada nem enviada à Groq. Runs Groq são snapshots v4 com
provedor, ID configurado,
parâmetros, origem sintética, uso quando retornado, status e erro; não recebem
hash de adapter, revisão Qwen ou recibo de sessão RunPod. Snapshots v1-v3
continuam legíveis. `answered_unverified` só indica resposta exploratória
concluída; 429, limite de contexto, stream incompleto e falha de tool conservam
estados de erro. `Retry-After` aparece no detalhe de 429 quando retornado.

O login do navegador grava a sessão revogável em cookie `HttpOnly`,
`SameSite=Strict`, `Path=/api`; a origem HTTPS recebe também `Secure`.
POSTs autenticados por cookie exigem `Origin` igual ao `Host` público HTTPS,
ou ao `localhost`/`127.0.0.1` HTTP. O logout revoga no servidor e limpa o
cookie; refresh consulta `/api/me` e recupera a identidade. Clientes legados
que não enviam `X-Browser-Session: 1` no login continuam recebendo bearer e
podem usar `Authorization: Bearer ...` sem cookie. O job preserva a chave de
idempotência em `sessionStorage` e é consultado após refresh, sem reenvio.

**Estado em 22/10/2026:** implementação, testes unitários/HTTP e navegador
com Groq simulado foram executados localmente em 19/10, e a
[revisão independente](../specs/active/SPEC-010/evidence/review.json) aprovou
esse escopo local. Em 22/10, o [ensaio real somente com fixture sintética](../specs/active/SPEC-010/evidence/groq-real-2026-10-22.md)
confirmou dois jobs pela Bancada autenticada, resposta do pacote, escolha da
tool `synthetic_metric` pelo modelo, persistência no histórico e limites da
conta Free. O refresh manteve o login e o run no histórico; a recuperação
visual de um job ainda pendente foi coberta pelo teste simulado. Não houve
RunPod, ngrok, Terraform ou DW real neste ensaio. Veja também a
[evidência local](../specs/active/SPEC-010/evidence/local-2026-10-19.md).

**Estado remoto em 17/10/2026:** o
[smoke na RTX A5000](../runpod/serving/evidence/2026-10-17-a5000.md)
confirmou sete gerações curtas por HTTPS. Uma
[sessão posterior de integração](../runpod/serving/evidence/2026-10-17-integracao-bancada.md)
validou a Bancada → ngrok → backend → RunPod nos modos de pacote fixo e tools
com `qwen-base`, guardando snapshots v3. Um run com `ft-finqa-a` terminou em
`response_error` por geração truncada e alheia à evidência. A Pod foi parada
sem volume persistente; a API local voltou a operar sem endpoint remoto e o
catálogo marca os modelos indisponíveis. O harness científico continua
pendente.

Uma [validação posterior da infraestrutura](../runpod/serving/evidence/2026-10-17-validacao-infra.md)
usou outra RTX A5000 porque o host da Pod anterior não tinha GPU livre.
O driver do novo host exigiu vLLM 0.11.0 com PyTorch/CUDA 12.8 e
transformers 4.x. Os sete aliases passaram no verificador formal. O vLLM
0.11.0 devolveu `tool_calls: []` em uma resposta normal sem tools; o backend
foi corrigido para não classificar a lista vazia como chamada de tool.
Um novo run pela Bancada via ngrok terminou em `answered_unverified`.
A nova Pod também foi parada a US$ 0,00/h; modelos indisponíveis enquanto
não houver sessão remota. Isso atesta conectividade e execução exploratória,
não acurácia dos modelos.

Um [teste adicional dos sete aliases pela Bancada](../runpod/serving/evidence/2026-10-17-bancada-sete-aliases.md)
usou outra A5000 em 17/10/2026. Todos foram roteados e salvos: base, Failure
A/B e Híbrido A/B terminaram `answered_unverified`; FinQA A/B atingiram o
limite de 500 tokens e foram registrados `response_error`. A base também
executou `product` no modo tools. A Pod foi parada sem volume persistente e o
backend local voltou a anunciar os modelos como indisponíveis. Esses estados
não constituem comparação científica.

**Mudança local posterior em 17/10/2026:**
a Bancada deixou de enviar `max_tokens` por padrão. A API também não define
um valor padrão nem um teto próprio de 1.024 tokens; se um cliente de API enviar
um inteiro positivo explicitamente, ele será repassado ao serving e ficará no
snapshot. Sem o parâmetro, `max_tokens: null` no snapshot indica que a
aplicação não impôs limite de saída. O serving ainda usa
`--max-model-len 4096` para entrada e saída juntas. Os runs históricos de
500 tokens não foram alterados.

O [replay na L4](../runpod/serving/evidence/2026-10-17-finqa-sem-teto-l4.md)
testou os FT-FinQA sem `max_tokens`: B concluiu por invocação direta do serviço
backend, sem login HTTP, e foi salvo como `answered_unverified`, mas devolveu
apenas um fragmento numérico; A gerou
até os 4.096 tokens da janela e terminou `length` no acesso direto ao gateway.
O gateway HTTPS devolveu 524 no caso longo, pois naquela sessão a resposta era enviada
ao proxy somente após a geração inteira. As esperas do backend e gateway
foram ampliadas para 600 e 610 segundos, respectivamente; isso não remove o
prazo do proxy. A Pod foi parada sem volume persistente, com US$ 0,00/h no
console. A execução desta sessão foi pelo backend direto, sem React/ngrok;
o harness científico e o transporte público para saídas longas seguem
pendentes.

**Correção local de transporte, antes do replay remoto:** `models.py` agora
pede SSE ao vLLM e reconstrói conteúdo, tools, uso e motivo de parada, guardando
os bytes do fluxo no snapshot. `gateway.py` encaminha os eventos sem esperar a
resposta inteira. A Bancada usa `POST /api/run-jobs`, recebe HTTP 202 e consulta
`GET /api/run-jobs/{id}`; o job e sua chave de envio ficam no banco, o run final
continua no histórico imutável. Uma resposta HTTP perdida é reconciliada por
chave antes de permitir novo envio; atualizar a página não reenvia o modelo.
A migração explícita 003 com backup lógico foi aplicada ao banco host local,
com readback das versões `[1, 2, 3]`, e ainda é necessária em cada outra cópia
do banco antes de iniciar esta versão da API. Testes locais de PostgreSQL,
HTTP e navegador passaram; naquele momento Docker, RunPod HTTPS e ngrok ainda
precisavam de readback com essa versão. Veja
[evidência local](../runpod/serving/evidence/2026-10-17-transporte-assincrono-local.md).

O [replay público de 17/10/2026](../runpod/serving/evidence/2026-10-17-streaming-bancada-l4.md)
confirmou o caminho autenticado Bancada → ngrok → API host → gateway SSE →
vLLM L4 → run no PostgreSQL. Dois jobs públicos receberam HTTP 202: a base
respondeu (`answered_unverified`) e FT-FinQA A enviou todo o fluxo longo sem
HTTP 524, mas atingiu a janela de 4.096 tokens e ficou `response_error`.
Ao atualizar a página, o login foi perdido; depois de novo login, o mesmo
job/run foi recuperado sem reenvio. A Pod e os serviços locais foram parados.
Essa prova é de um job por vez; a imagem Docker desta versão e a avaliação
científica continuam pendentes.

Validação local anterior desta mudança sobre `4943257` mais alterações sem commit:
11 testes de contrato e 8 de serving passaram; o TypeScript e o build Vite
passaram. A API não estava escutando em `127.0.0.1:8765` no readback final;
naquele momento não houve nova execução pela interface, ngrok ou RunPod.

**Histórico da SPEC-008 em 16/10/2026, sobre `772ea0d` e alterações
locais preservadas:** a rota `/` entrega o React compilado, com login primeiro,
quatro abas do Observatório e Bancada na quinta aba. O snapshot sintético de
06/09/2026 é servido somente por `GET /api/bi/snapshot` autenticado. A imagem
Docker e a cópia lógica não destrutiva foram testadas somente com bancos
descartáveis; os três bancos reais não foram copiados. A
[revisão independente da SPEC-008](../specs/active/SPEC-008/evidence/review.json)
aprovou o escopo local na quinta rodada em 16/10/2026; os pareceres anteriores e a
[evidência local](../specs/active/SPEC-008/evidence/local-2026-10-16.md)
delimitam o estado. RunPod, ngrok e avaliação científica não foram executados.

**Estado em 15/10/2026 (base `1e8cb76` mais mudanças locais da SPEC-004 sem commit):**
cadeia exploratória determinística da SPEC-001 implementada localmente e aprovada
em revisão independente. A SPEC-002 também foi aprovada para seu escopo local:
código de serving e procedimento de custo e aplicação futura, ainda sem Pod ou
túnel ngrok. A SPEC-003 acrescenta login local e uma vaga global de inferência;
seus 28 testes locais passaram em 15/10/2026 e a revisão independente aprovou
esse escopo local, separado do benchmark científico. A SPEC-004 acrescentou
critérios versionados e comparação visual: 32 testes locais passaram e a
[revisão independente](../specs/active/SPEC-004/evidence/review.json) aprovou
o escopo local em 15/10/2026. A
arquitetura acordada e seus limites estão em
[`../docs/arquitetura_inferencia_compartilhada.md`](../docs/arquitetura_inferencia_compartilhada.md).
As frentes seguintes têm contratos e ordem próprios em
[`../specs/README.md`](../specs/README.md).
O [desenho da avaliação](../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md)
separa raciocínio sobre evidências fixas de pesquisa com tools escolhidas pelo
modelo. O fluxo da SPEC-001 escolhia duas consultas pelo escopo declarado pelo
pesquisador. A SPEC-009 substitui novos runs por dois modos explícitos, preservando
a leitura dos snapshots anteriores. O [exportador da SPEC-007](../model_evaluation/README.md)
continua produzindo pacotes candidatos fora da API.

**SPEC-005 histórica em 16/10/2026:** `session_checks.py` acrescentou pré-voo local,
teste HTTP opt-in do túnel e ensaio das três rotas antigas. A SPEC-009 retirou
o ensaio antigo do fluxo ativo; pré-voo e tunnel-check continuam disponíveis. O [runbook da sessão](../docs/sessao_inferencia_curta.md) separa esses
gates da implantação paga. Nenhuma geração remota ou exposição ngrok foi feita
pela SPEC-005; a [revisão independente](../specs/active/SPEC-005/evidence/review.json)
aprovou esse escopo local.

## Como uma pergunta percorre a Bancada hoje

Este é o ponto de entrada para um chat novo entender **o fluxo ativo**. A
[SPEC-009](../specs/active/SPEC-009/SPEC.md) registra o contrato da mudança;
o comportamento executado fica em `frontend/src/features/bench/BenchPage.tsx`,
`src/inference_api/server.py` e `src/inference_api/service.py`. Os módulos
`orchestrator.py`, `evidence.py` e `response_agent.py` citados em descrições
anteriores foram retirados do fluxo ativo após a SPEC-009.

1. Após login, o pesquisador escolhe **Pacote fixo da DW** ou **LLM consulta a
   DW por tools**, um alias de modelo, prompt, critérios e parâmetros. O front
   envia `POST /api/run-jobs` com `evidence_mode` e uma chave UUID. A API
   autentica, registra o job e responde HTTP 202; o worker reserva a única
   vaga global e chama `service.execute_run()`. A tela consulta o job por ID.
2. Em `dw_snapshot`, o servidor busca `case_id` mais SHA-256 no diretório
   privado de pacotes. `evidence_packets.py` valida o arquivo; a pergunta e o
   domínio vêm do corpo do pacote e não são editados nesse run. `service.py`
   envia ao modelo a pergunta e o JSON exato do pacote. **Não consulta a DW
   durante a execução**; a exportação anterior está em `model_evaluation/`.
3. Em `dw_tools`, o pesquisador digita uma pergunta livre. `service.py` anuncia
   cinco funções de leitura ao modelo por `models.chat_turn()`. Se a LLM pedir
   uma tool, `dw_tools.py` valida nome e argumentos, executa a consulta fixa
   compartilhada de `BancoModeloUse/dw/fixed_queries.py` em
   `db_pesquisa_dw` somente leitura e devolve o resultado ao modelo. O ciclo
   continua até a resposta ou um limite/erro. O backend **não escolhe a tool
   pelo escopo** e não oferece SQL livre.
4. `models.py` chama o endpoint vLLM configurado e confere modelo e identidade
   da sessão de serving. `service.py` grava no `db_inference_app` um snapshot
   v3 com pergunta, modo, prompt, modelo, pacote ou trilha de tools, resposta,
   verificações e erros. `storage.py` serve histórico; `RunDetail.tsx` mostra
   primeiro um resumo com data local do navegador, estado explicado, pergunta,
   resposta, origem e verificações exploratórias. JSON, parâmetros, hashes e
   trilhas completas ficam em
   **Detalhes técnicos e rastreabilidade**. A lista mostra as 100 execuções
   mais recentes; registros antigos continuam no banco. Runs v1/v2 continuam
   legíveis como fluxo anterior. Essa apresentação não pontua nem valida
   cientificamente as respostas.

Em 22/10/2026, uma [conferência somente leitura das cinco tools da
DW](../specs/active/SPEC-009/evidence/dw-tools-readonly-2026-10-22.md)
confirmou consultas à carga local e o caminho de `service.execute_run()` com
modelo simulado e consulta real. Dois runs anteriores da base registram uma
escolha real de `product` pela LLM na RunPod em 17/10. Esse recibo não é
ensaio Groq com DW nem avaliação científica.

**Onde estão as perguntas:** o repositório versiona
[`model_evaluation/examples/cases_2020.json`](../model_evaluation/examples/cases_2020.json)
como **exemplo** de manifesto para exportar um pacote, não como bateria
científica oficial. Pacotes efetivamente exportados ficam no diretório privado
`model_evaluation/.local/packets` por padrão e são ignorados pelo Git. Perguntas
livres digitadas no modo tools e a pergunta efetiva de cada pacote ficam no
snapshot do run em `db_inference_app`; não há uma lista dessas perguntas no
checkout. Prompts editáveis são revisões separadas da pergunta. Ainda não há
catálogo oficial de casos, gold set ou pontuação científica; veja a
[arquitetura da avaliação](../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md).

## Contrato implementado

- `GET /api/models`: sete aliases candidatos (base e seis adapters), derivados
  de [`runpod/serving/manifest.json`](../runpod/serving/manifest.json).
  `available` exige o alias em `GET /v1/models` do endpoint configurado.
  `generation_confirmed` exige adicionalmente recibo `passed` da mesma URL
  e sessão. Um candidato não prova pesos carregados nem geração.
- `GET/POST /api/prompts`: revisão imutável de nome, autor e texto do sistema.
  `POST` exige `expected_revision` para recusar salvamentos simultâneos sobre
  a mesma versão. Em conflito, HTTP 409 devolve a revisão atual e a página
  preserva o rascunho local.
- `GET/POST /api/criteria`: revisões imutáveis de critérios exploratórios.
  `POST` recebe `name`, `expected_revision` e `config` com exatamente
  `schema_version: 1`, `require_evidence`, `require_period`,
  `required_units` (lista de unidades literais), `require_cited_ids` e
  `required_caveats` (lista de frases literais). Cada lista aceita até oito
  entradas; unidade tem até 80 caracteres e ressalva até 160. Campos extras,
  expressões executáveis e listas fora do contrato falham antes da execução.
  JavaScript ou SQL digitado como ressalva é somente texto literal. O backend
  não executa essas strings. Conflito também devolve HTTP 409 e a revisão atual.
- `GET /api/bench/evidence-packets`: lista pacotes privados verificados por
  `case_id` e SHA-256 somente após autenticação. O servidor recusa pacotes
  adulterados, não canônicos, fora do schema, duplicados, grandes ou ligados por
  symlink. Sem diretório ou arquivos, a lista é vazia.
- `GET /api/bench/dw-tools`: informa disponibilidade da DW isolada, fingerprint,
  schema e hash do código de consultas. Sem carga da DW no Compose, responde
  `available: false` e não consulta as origens.
- `POST /api/runs`: novos runs exigem `evidence_mode: dw_snapshot|dw_tools`,
  `model_alias`, exatamente uma revisão de prompt ou `system_prompt`, critérios
  opcionais e parâmetros. `dw_snapshot` exige `case_id` e `packet_sha256` e usa
  a pergunta/domínio do corpo do pacote já exportado. `dw_tools` exige pergunta
  livre e deixa a LLM escolher `machine`, `product`, `financial`, `quality` ou
  `material` via `tool_choice: auto`, sem chamadas paralelas. `scope`, `year`,
  `evidence_route`, SQL e campos do outro modo são recusados. Cada tool aceita
  ano inteiro de 2015 a 2026; as quatro tools de entidade exigem ID positivo;
  `financial` proíbe ID. As consultas usam SQL fixo único de
  `BancoModeloUse/dw/fixed_queries.py`, transações somente leitura e apenas
  `db_pesquisa_dw`. Não há fallback aos dois bancos de origem.
- `POST /api/run-jobs`: mesmo payload de run mais `request_key` UUID. Cria um
  job persistido e devolve HTTP 202 sem aguardar a geração. A mesma chave e o
  mesmo payload devolvem o mesmo job, sem segunda inferência; payload diferente
  com a mesma chave é recusado. `GET /api/run-jobs/{id}` e
  `GET /api/run-jobs/by-key/{request_key}` consultam apenas jobs do pesquisador
  autenticado. `completed` aponta para um run salvo; após reinício da API, jobs
  inacabados viram `interrupted` e não são reenviados automaticamente.
- O loop limita a cinco chamadas, seis turnos, 200 linhas e 16 KiB canônicos
  acumulados. Chamada/argumentos inválidos ficam em `tool_error`, resultado
  excessivo em `tool_limit_error`, fingerprint/consulta em `query_error`,
  resposta/serving e ausência de observação em seus estados próprios;
  nenhuma resposta é inventada.
- `GET /api/runs` e `GET /api/runs/{id}`: histórico. `POST
  /api/runs/{id}/feedback` anexa feedback humano sem alterar o snapshot.
- O servidor escuta somente `127.0.0.1:8765`. `POST /api/login` aceita somente
  os dois pesquisadores cadastrados localmente e devolve uma sessão temporária.
  Todas as demais rotas de API exigem seu bearer; `GET /api/me` identifica a
  sessão e `POST /api/logout` a revoga. O navegador mantém o bearer só em
  memória. `author` enviado no corpo não é usado: o backend grava o nome do
  pesquisador autenticado e seu ID estável no snapshot novo.
- Dois pesquisadores podem estar logados ao mesmo tempo. Um índice parcial de
  jobs ativos e o advisory lock no PostgreSQL permitem somente uma inferência
  global; um segundo envio recebe HTTP 429 antes de chamar a LLM. Não há limite diário por
  padrão; configurações opcionais podem ativá-lo no futuro.
- `GET /api/budget` mostra o teto informativo de US$ 10 e tenta ler
  `clientBalance` e `currentSpendPerHr` da API GraphQL da RunPod com uma
  chave de leitura do backend. Sem resposta autenticada, o saldo aparece
  indisponível, nunca estimado.

Novos runs usam `schema_version: 3`, com modo explícito, prompt/critérios,
modelo efetivo e parâmetros, pergunta, origem da DW, pacote integral em Base64 e
JSON exato entregue ou catálogo/traço de tools, requests/responses brutos,
timestamps, resposta, falhas e checks exploratórios. Os snapshots versões 1 e 2
permanecem legíveis e aparecem como “Fluxo anterior: escopo e consultas do
backend”; não são reescritos. `answered_unverified` não é resultado científico.
Os checks de verdade numérica e causalidade seguem `not_checked`. Sem gold set,
rubrica ou inferência real dos pesos, a comparação A/B é visual e estratificada.
A compatibilidade de tool calling dos adapters reais ainda depende de ensaio
RunPod autorizado; o teste local usa servidor simulado.

No host, configure `DW_DB_HOST=127.0.0.1`, `DW_DB_PORT=5544`,
`DW_DB_NAME=db_pesquisa_dw`, `DW_DB_USER` e `DW_DB_PASSWORD` no ambiente privado
do processo; somente esse destino é aceito. `INFERENCE_EVIDENCE_PACKETS_DIR`
aponta para diretório absoluto privado, por padrão
`model_evaluation/.local/packets`. Para preparar candidatos, siga
[model_evaluation/README.md](../model_evaluation/README.md). A API não exporta
pacotes durante o run. No Compose, as variáveis da DW apontam apenas para
`db:5432/db_pesquisa_dw` e o diretório de pacotes é montado `:ro`, fora da imagem.

## Mapa do código

| Caminho | Responsabilidade atual |
| --- | --- |
| `run.py` e `src/inference_api/server.py` | Entrada por linha de comando, servidor HTTP, rotas e entrega do front. |
| `frontend/src/` e `frontend/dist/` | Código React/TypeScript e build estático da única interface ativa. `dist/` é gerado localmente e ignorado pelo Git. |
| `private/bi_snapshot.json` | Retrato sintético extraído sem alteração lógica da referência da SPEC-008; nunca entregue por rota estática. |
| `Dockerfile`, `compose.yaml`, `scripts/copy_logical_databases.py` | Imagem app, PostgreSQL isolado e cópia lógica explícita por recusa de destino não vazio. |
| `src/inference_api/auth.py`, `limits.py` e `budget.py` | Login de dois pesquisadores, sessão revogável, vaga única de inferência e leitura separada do saldo RunPod. |
| `src/inference_api/service.py` | Coordena uma execução e grava seu snapshot final. |
| `src/inference_api/evidence_packets.py` e `dw_tools.py` | Selecionam pacote por ID/hash e executam as cinco consultas fixas da DW após escolha da LLM. |
| `src/inference_api/models.py` e `serving_catalog.py` | Fazem turnos de chat e vinculam a proveniência da sessão ao manifesto. O serving remoto ainda não foi ensaiado com tool calling real. |
| `src/inference_api/criteria.py`, `config.py` e `storage.py` | Validam critérios, restringem destinos e persistem prompts, runs e feedback. |
| `tests/test_contract.py`, `test_serving.py`, `test_identity.py`, `test_criteria.py`, `test_bi_http.py`, `test_spec009_http.py` e `browser_spec009.cjs` | Contratos Python, proteção do BI, paridade de navegador com referência e smoke Docker descartável. |
| `session_checks.py` e `tests/test_session_checks.py` | Pré-voo somente leitura da DW e prova HTTP do túnel; o ensaio legado foi retirado. |

O contrato e a revisão independente da SPEC-001 ficam em
[`specs/active/SPEC-001/`](../specs/active/SPEC-001/SPEC.md).
O contrato e a [evidência local da SPEC-003](../specs/active/SPEC-003/evidence/local-2026-10-15.md)
ficam em [`specs/active/SPEC-003/`](../specs/active/SPEC-003/SPEC.md); a
[revisão independente](../specs/active/SPEC-003/evidence/review.json) aprovou
o escopo local em 15/10/2026.

## Rodar localmente

Use o Python de um ambiente próprio com as dependências de
[`requirements.txt`](requirements.txt). Na raiz do repositório, em PowerShell:

O modo direto requer um build de `frontend/` com Node 24 e npm 11 antes de
`serve`; o build local fica em `frontend/dist/`. Com o cluster Windows, o
ambiente Python e esse build **já preparados**, basta iniciar a aplicação na
raiz do repositório:

```powershell
$env:INFERENCE_RUNTIME_MODE = 'host'
inference_api/.venv/Scripts/python.exe inference_api/run.py serve
```

O modo host lê os três bancos existentes em `127.0.0.1:5544`; não requer a
cópia para o volume Docker. O servidor escuta somente `127.0.0.1:8765`.
Os comandos seguintes são para **provisionar um ambiente novo**. Não repita
`init-db`, migrações nem `configure-users` apenas para reiniciar: este último
troca as senhas cadastradas e revoga sessões. O modo Docker abaixo faz o build
do front na imagem, sem Node ou Python instalados no host.

```powershell
BancoModeloUse/.venv/Scripts/python.exe -m venv inference_api/.venv
inference_api/.venv/Scripts/python.exe -m pip install -r inference_api/requirements.txt
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py start
inference_api/.venv/Scripts/python.exe inference_api/run.py init-db
inference_api/.venv/Scripts/python.exe inference_api/run.py migrate-db --pg-dump 'C:/Program Files/PostgreSQL/15/bin/pg_dump.exe'
inference_api/.venv/Scripts/python.exe inference_api/run.py migrate-criteria --pg-dump 'C:/Program Files/PostgreSQL/15/bin/pg_dump.exe'
inference_api/.venv/Scripts/python.exe inference_api/run.py migrate-run-jobs --pg-dump 'C:/Program Files/PostgreSQL/15/bin/pg_dump.exe'
inference_api/.venv/Scripts/python.exe inference_api/run.py configure-users
npm --prefix inference_api/frontend ci
npm --prefix inference_api/frontend run build
inference_api/.venv/Scripts/python.exe inference_api/run.py serve
```

Para conferir os dois logins registrados sem expor senhas nem abrir o ngrok,
execute `inference_api/.venv/Scripts/python.exe inference_api/verify_local_users.py`
em um terminal interativo. O script pede as senhas com eco desativado, abre uma
porta HTTP efêmera apenas em `127.0.0.1`, confirma as duas sessões simultâneas
e faz logout das duas. Ele não cria prompts, execuções ou feedback.

`init-db` cria apenas `db_inference_app` e suas três tabelas originais se faltarem.
`migrate-db` faz backup lógico custom em `inference_api/.local/` antes de
acrescentar as tabelas de identidade, sessão e uso. O SQL reverso está em
`migrations/001_identity_down.sql`; não o aplique sem preservar o backup.
`migrate-criteria` exige a versão 1, cria outro backup lógico antes de adicionar
`verification_criteria_revisions` e registra a versão 2. O SQL reverso está em
`migrations/002_criteria_down.sql`. A migração da SPEC-004 passou em banco
descartável e foi aplicada em `db_inference_app` em 15/10/2026 após backup
lógico. O readback confirmou versões 1 e 2 e tabela de critérios vazia.
`migrate-run-jobs` exige exatamente as versões 1 e 2, faz outro backup lógico
e registra a versão 3 e a tabela `run_jobs`; o SQL reverso está em
`migrations/003_run_jobs_down.sql`. Execute uma vez em cada banco da aplicação
que receber esta versão do backend. A migração 003 foi executada no banco host
local em 17/10/2026, com backup e readback; a cópia Docker ainda não a recebeu.
Não execute novamente `init-db`,
`migrate-db`, `migrate-criteria` ou `configure-users` para aplicá-la.
`configure-users` pede as duas senhas e confirmações em prompt oculto; após
as quatro entradas, registra os dois logins aprovados. `set-password`
permite trocar uma senha posteriormente e exige 12 a 128 caracteres para
novas senhas. Cada cadastro grava somente
hash com sal e revoga sessões anteriores. Não passe senha em argumento, variável
versionada ou chat. `revoke --username Nicoli|Vinicius` suspende o acesso sem
apagar snapshots. Essas ações não recriam nem importam bases de origem. As
credenciais do cluster são lidas do
`BancoModeloUse/.env.local` ignorado pelo Git; no modo direto todas as conexões
exigem host `127.0.0.1`, porta `5544` e nomes de bancos conhecidos. No modo
Docker exigem exclusivamente `db:5432` e os mesmos nomes. Não há fallback para
outro host ou banco.

Abra `http://127.0.0.1:8765` e use um dos dois logins já cadastrados.
As duas sessões podem coexistir; se uma inferência estiver em curso, a outra
deve aguardar e tentar novamente após o HTTP 429. O painel mostra o teto manual
de US$ 10 e consulta o saldo real ao entrar, a cada minuto e antes de enviar
uma inferência. Para leitura da conta, configure `RUNPOD_BALANCE_READ_KEY`
somente no ambiente do backend com escopo de leitura; sem chave o painel diz
que o saldo não foi confirmado. Esse teto não é um bloqueio de faturamento do
provedor. A [API GraphQL oficial](https://graphql-spec.runpod.io/) documenta
`myself.clientBalance` e `currentSpendPerHr`.
O login aceita até 12 tentativas por minuto e duas verificações de senha
simultâneas por processo local; quando esse limite é atingido, retorna HTTP
429. Tentativas inválidas são contabilizadas sem bloquear permanentemente uma
das duas contas. O painel distingue chave não configurada, falha na leitura e
saldo confirmado, com fonte e horário da tentativa de leitura.
Sem Pod, o catálogo mostra os modelos indisponíveis. A API pode receber
`INFERENCE_VLLM_URL` HTTPS e `INFERENCE_VLLM_TOKEN` somente no
ambiente do backend. A URL é a origem do gateway protegido, sem `/v1`,
credenciais ou parâmetros. O cliente recusa redirecionamentos para não
reenviar o bearer token a outra origem. Após uma verificação remota
autorizada, pode receber
`INFERENCE_SERVING_VERIFICATION` com caminho local para o recibo da sessão.
O cliente envia `User-Agent: PesquisaICIA/1.0`: em 17/10/2026 o proxy da
RunPod recusou o identificador padrão do `urllib` com HTTP 403, enquanto o
identificador explícito recebeu 200; veja a
[evidência de integração](../runpod/serving/evidence/2026-10-17-integracao-bancada.md).
Veja o [runbook de serving](../runpod/serving/README.md). Nenhuma dessas
variáveis deve ser enviada ao navegador.
O runbook também separa a conclusão local da SPEC-002 da sessão paga: a
revisão do `terraform plan`, a estimativa de GPU e discos e a confirmação
explícita do `apply` ocorrerão antes de uma implantação futura.

## Execução Docker local da SPEC-008

`compose.yaml` constrói um contêiner de aplicação (React compilado e Python) e
um PostgreSQL 15 em volume nomeado. Somente o HTTP da aplicação é publicado em
`127.0.0.1`, na porta `8875` por padrão; `INFERENCE_HTTP_PORT` permite outra
porta. O banco fica em `db:5432` apenas na rede do Compose. `up -d db`
inicializa o serviço PostgreSQL vazio, mas **não importa dados, não migra
esquema e não cria pesquisadores**. Inicie o app somente depois de preparar
`db_inference_app` com a versão 3.

Na raiz do repositório, com Docker Desktop e o arquivo privado
`BancoModeloUse/.env.local` já existente:

```powershell
docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml config --quiet
docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml build
docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml up -d db
docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml ps
```

**Antes de iniciar esta versão do app em uma cópia Docker existente com
versões 1/2**, aplicar a migração 003 com o app parado. O Docker Linux estava
indisponível em 17/10/2026, então estes comandos de operação ainda exigem
execução e readback no destino real. O backup fica fora do contêiner e não
deve ser substituído:

```powershell
docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml up -d db
$dbId = docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml ps -q db
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = "inference_api/.local/run-jobs-docker-$stamp.dump"
$remoteBackup = "/tmp/run-jobs-$stamp.dump"
if (-not $dbId -or (Test-Path -LiteralPath $backup)) { throw 'Banco não identificado ou backup já existe' }
docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml exec -T db sh -c ('PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d db_inference_app -Fc -f ' + $remoteBackup)
docker cp "${dbId}:$remoteBackup" $backup
if ((Get-Item -LiteralPath $backup).Length -eq 0) { throw 'Backup vazio; migração bloqueada' }
Get-FileHash -LiteralPath $backup -Algorithm SHA256
docker cp inference_api/migrations/003_run_jobs_up.sql "${dbId}:/tmp/003_run_jobs_up.sql"
docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -X -v ON_ERROR_STOP=1 -1 -U "$POSTGRES_USER" -d db_inference_app -f /tmp/003_run_jobs_up.sql'
docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -X -At -U "$POSTGRES_USER" -d db_inference_app -c "SELECT version FROM inference_schema_migrations ORDER BY version"'
docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -X -At -U "$POSTGRES_USER" -d db_inference_app -c "\dt run_jobs"'
```

Confirme versões `1`, `2`, `3` e `run_jobs` antes de iniciar o app. Se o banco
Docker ainda não tiver versões 1/2, prepare essa cópia pelo procedimento já
documentado; não aplique a 003 fora de ordem.

O Docker usa a senha local `FINANCEIRO_DB_PASSWORD` como senha do **novo** role
`pesquisa_local` no volume isolado. A imagem recebe código da API, consultas fixas da DW, verificador/schema de pacotes, manifesto
de aliases e snapshot BI privado; `.env.local`, CSVs, pesos, resultados e dumps
ficam fora do contexto de build. O modo host continua usando o cluster Windows
em `127.0.0.1:5544`, sem alterar `listen_addresses`, `pg_hba.conf` ou seus
arquivos físicos.

**Cópia real é uma ação separada, ainda não executada nesta SPEC.** Depois de
verificar que o volume Docker é o esperado e está sem bancos e objetos de
usuário, e de escolher conscientemente o
projeto `inference_api`, o operador pode executar a cópia lógica abaixo. O
script exige PostgreSQL 15 no host, lê os três bancos do cluster Windows sem
escrever neles, grava dumps temporários, calcula SHA-256 e contagens, transmite
cada dump por stdin a `docker compose exec -T db pg_restore` e confirma
readback. Ele confere labels e mount do volume, o inventário exato de bancos
e templates, dumps plain completos de `postgres` e `template1` sem DDL ou
dados de usuário, roles e tablespaces esperados, e recusa destino
já usado; falha parcial deixa recibo e bloqueia
nova execução até reconciliação manual. Também recusa substituir um recibo
anterior, mesmo se o destino tiver sido recriado. A cópia padrão inclui `db_industrial`, `db_financeiro` e `db_inference_app`.
`--include-dw` acrescenta `db_pesquisa_dw` como quarto banco apenas por comando
explícito, com as mesmas recusas, hash, contagens e readback. O recibo grava
`spec_id: SPEC-009` e `include_dw: true` nesse modo; a cópia padrão mantém
`spec_id: SPEC-008`. Nenhuma cópia real
do DW foi executada na SPEC-009; a validação Docker usa somente fixtures.

```powershell
inference_api/.venv/Scripts/python.exe inference_api/scripts/copy_logical_databases.py --execute --source-env BancoModeloUse/.env.local --compose-env BancoModeloUse/.env.local --project inference_api --receipt inference_api/.local/copy-real-receipt.json
```

Após a cópia, confira a versão 3 no banco de destino; se vier de uma cópia
antiga em 1/2, aplique a migração acima. Então inicie o app:

```powershell
docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml up -d app
```

Após o readback de saúde, abrir `http://127.0.0.1:8875`. Para
encerrar a aplicação sem perder o banco:

```powershell
docker compose -p inference_api --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml down
```

Em 16/10/2026, um **projeto Docker descartável** em portas `8878`–`8880`
validou build, login e BI protegido, sete aliases indisponíveis sem RunPod,
paridade no navegador, persistência do volume após `down`, cópia lógica de três
bancos fixture, recusa da segunda execução e falha parcial injetada. Os
recibos e capturas de tela locais ficam em `inference_api/.local/` (ignorados pelo Git),
e o resumo verificável está na evidência da SPEC-008. Esse smoke não prova
cópia dos bancos reais nem geração remota.

## Exposição da aplicação via ngrok

O usuário escolheu usar apenas a autenticação da aplicação: bearer opaco
revogável por pesquisador, validado no backend. Não há OAuth ou Basic Auth na
borda. O alvo usado na sessão exploratória de 17/10/2026 foi
**somente** o HTTP da aplicação em `127.0.0.1:8765`:

```powershell
ngrok http 8765
```

Um túnel HTTPS único para essa porta foi observado e o `tunnel-check` passou
antes e depois da integração. O ngrok permaneceu ativo após a parada da Pod;
os modelos voltaram a aparecer indisponíveis. Nunca apontar o ngrok para
`5544` nem expor PostgreSQL. A rotação das senhas de Nicoli e Vinicius não
foi verificada nesta sessão; se ainda não ocorreu desde as escolhas que
passaram pelo chat, usar `run.py set-password --username ...` em terminal
local e confirmar login e revogação novamente.

Testes locais sem infraestrutura remota:

```powershell
$env:INFERENCE_IDENTITY_DB_TEST = '1'
inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v
$env:NODE_PATH = 'C:/Users/vinic/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
node inference_api/tests/browser_spec009.cjs
```

O pré-voo da SPEC-005 pode ser chamado sem Pod ou túnel:

```powershell
inference_api/.venv/Scripts/python.exe inference_api/session_checks.py preflight
```

Ele retorna `BLOCKED` enquanto o Git estiver sujo ou URL HTTPS, revisão exata
da base e token do gateway ainda não estiverem configurados. Esse resultado
não cria recurso nem contata o endpoint; veja o
[procedimento completo](../docs/sessao_inferencia_curta.md) para os comandos
opt-in e os readbacks exigidos na sessão futura.

**Validação local em 13/10/2026:** a carga existente foi lida, sem nova importação:
o bundle integrado retornou 13 vendas em `db_financeiro.public.vendas` e
35.136 registros em `db_industrial.public.registros_operacao` para 2020.
Os testes locais da SPEC-001 cobrem rotas, limites, falhas, isolamento entre
aliases, payload da LLM e checks parciais. Antes da SPEC-001, o esquema foi criado
no cluster isolado e um teste de integração confirmou revisão de prompt,
conflito de edição, snapshot de erro sem vLLM e feedback; os registros de teste
foram retirados em seguida. O HTTP retornou página 200, catálogo com sete
aliases indisponíveis, 401 sem token e 400 para alias inválido. Três testes de
contrato passaram no ambiente próprio. O cluster foi parado ao fim. Isso é
validação local de leitura e fluxo, não nova carga das fontes nem teste de
inferência remota. Em 14/10/2026, o preflight da SPEC-002 conferiu os seis
pesos/configs e 18 testes locais passaram, incluindo redirecionamento e POST
real pelo gateway em loopback; o comando vLLM foi somente gerado,
sem Pod ou endpoint remoto.

**Validação local da SPEC-003 em 15/10/2026:** a migração foi aplicada em
`db_inference_app` após backup lógico; leitura posterior confirmou somente
Nicoli e Vinicius ativos. Os 28 testes da suíte passaram com banco de teste
isolado, incluindo autoria, revogação, limite de login, concorrência e rollback
da migração.
No servidor local, `/` respondeu 200 e `/api/me`, `/api/prompts`, `/api/runs` e
`/api/budget` responderam 401 sem sessão. O servidor foi encerrado após esse
teste. A [evidência local](../specs/active/SPEC-003/evidence/local-2026-10-15.md)
registra comandos, limites e recibo do backup. O saldo real da RunPod não foi
lido porque ainda não há chave de leitura configurada.

## Segurança e operação: limites atuais

A revisão independente da SPEC-003 aprovou identidade e vaga única somente
no escopo local. Em 17/10/2026 um ngrok HTTPS para `127.0.0.1:8765` foi
observado e usado em três runs autenticados; as rotas privadas recusaram
acesso sem sessão no `tunnel-check`. A chave de leitura de saldo não está
configurada, e a rotação das senhas de Nicoli e Vinicius não foi verificada
nesta sessão. Credenciais originalmente escolhidas fora de um canal privado
devem ser trocadas se isso ainda não ocorreu. O gateway remoto exigiu bearer
e os sete aliases responderam, mas o servidor HTTP continua sendo ferramenta
local de desenvolvimento, sem SSO nem garantia de produção. Não usar as
respostas como métricas do artigo.
A varredura de segredos e a revisão independente estão registradas nos
[recibos da SPEC-003](../specs/active/SPEC-003/evidence/review.json). O teste
HTTP com os usuários efetivamente cadastrados passou em 15/10/2026, sem abrir
túnel naquela sessão histórica.
a
