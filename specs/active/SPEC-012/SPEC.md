---
id: SPEC-012
title: Provedor OpenAI por API na Bancada exploratória
status: done
contract_version: 1
---

# SPEC-012: Provedor OpenAI por API na Bancada exploratória

## Goal

Adicionar à Bancada um provedor OpenAI explícito, integrado ao login, aos jobs,
à escolha de tools pela LLM e ao histórico, sem confundi-lo com Groq ou com os
sete aliases Qwen da RunPod. Primeiro demonstrar o fluxo com transporte e dados
sintéticos locais. Uma eventual chamada real à OpenAI e qualquer envio de
dados reais são etapas separadas, condicionadas às decisões abaixo.

## Context

- A [SPEC-009](../SPEC-009/SPEC.md) definiu os modos `dw_snapshot` e
  `dw_tools`. Neste último, a LLM pede uma das cinco consultas fixas
  (`machine`, `product`, `financial`, `quality`, `material`); o backend valida
  os argumentos e lê `db_pesquisa_dw` em transação somente leitura. Os limites
  operacionais atuais são cinco chamadas, seis turnos, 200 linhas e 16 KiB de
  resultados acumulados. Isso é exploração, sem harness científico.
- A [SPEC-010](../SPEC-010/SPEC.md) acrescentou Groq com snapshots v4,
  fixture sintética, jobs e tratamento de erros. Em 22/10/2026, um diff local
  posterior abriu `groq` + `dw_tools` para dados reais mediante autorização
  específica. O [recibo](../SPEC-010/evidence/groq-dw-real-2026-10-22.md)
  informa um ensaio autenticado; essa extensão ainda não recebeu revisão
  independente. Essa autorização foi para Groq, não para OpenAI.
- No checkout inspecionado em 23/10/2026, HEAD
  `13d7df5c748f79387d34f39cd30b6cf82c96c869` mais diff local,
  `service.py` aceita apenas os
  provedores `runpod` e `groq`; `models.py` expõe alias `groq` e aliases
  RunPod; `groq.py` fixa a URL HTTPS da Groq. `BenchPage.tsx` oferece modos
  por provedor e `RunDetail.tsx` lê snapshots v3/v4. Há alterações locais
  não commitadas nessas áreas. O executor precisa reconciliá-las antes de
  escrever; esta SPEC não atesta uma revisão independente da extensão.
- O [desenho da avaliação](../../../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md)
  separa evidência fixa de pesquisa com tools e deixa o harness formal
  pendente. Um modelo externo não se torna comparável aos Qwen só por aparecer
  na mesma Bancada.

## Scope

- Após resolver as decisões de desenho, integrar um alias `openai` e um
  adaptador de backend separado, com credencial e modelo configurados apenas
  no servidor. Preservar RunPod, Groq, autenticação, reserva global, jobs,
  idempotência, prompts, critérios, feedback, histórico e os painéis do BI.
- Disponibilizar inicialmente `synthetic_snapshot` e `synthetic_tools`, com
  fixture inventada e prompt aprovado no servidor, usando a mesma semântica
  exploratória da SPEC-010. O pedido da tool deve vir da resposta do modelo;
  o backend nunca escolhe a rota em nome dele.
- Adaptar protocolo de requisição/resposta, streaming ou job, tool calling,
  uso e erros à Responses API com `gpt-6-luna`. A semelhança do
  endpoint da Groq com a API OpenAI não prova compatibilidade.
- Preparar um gate explícito para qualquer modo com DW ou pacote privado:
  somente os modos e classes de dados autorizados para OpenAI poderão ser
  habilitados. A autorização de 25/10/2026 cobre `dw_tools` e `dw_snapshot`
  nos limites descritos abaixo, após a validação sintética inicial.
- Versionar os novos snapshots sem reescrever v1–v4; atualizar README da API,
  arquitetura e índice quando o fluxo for implementado.

## Non-scope

- Chamar OpenAI, Groq, RunPod ou DW real durante o desenho desta SPEC; abrir
  ngrok, executar Terraform, cadastrar chave, ativar cobrança ou fazer commit.
- Corrigir ou aprovar a extensão Groq + DW real ainda sem revisão independente.
- Criar gold set, pontuação, harness científico, inferir qualidade dos Qwen ou
  declarar equivalência entre provedores.
- Enviar dados reais, resultados de DW, pacotes privados, dados de pesquisa,
  gabaritos, pesos, resultados brutos ou segredos à OpenAI sem autorização
  específica para esse destino e para o payload delimitado.
- Aceitar SQL livre, tool arbitrária, endpoint arbitrário do navegador ou
  credenciais de banco no contexto do modelo.

## Requirements

- REQ-001: O catálogo e a UI distinguem `provider=openai`, ID do modelo
  configurado e modos disponíveis. Sem configuração válida, mostrar
  indisponibilidade e recusar o run antes de acesso a dados ou rede. Não usar
  fallback silencioso para Groq ou RunPod nem atribuir alias, base, adapter,
  hash ou recibo de sessão Qwen ao modelo OpenAI.
- REQ-002: A chave OpenAI fica somente no backend, fora de Git, bundle,
  respostas HTTP, snapshots, logs e evidências. A URL de produção usa origem
  oficial HTTPS fixada para a API escolhida; o cliente não escolhe URL. Testes
  locais injetam transporte simulado sem usar credencial real. Sanitizar
  mensagens de erro e metadados antes de persistir ou mostrar.
- REQ-003: O backend aplica uma matriz explícita `provedor × modo × classe
  de dado`. Para `provider=openai`, permitir inicialmente só a fixture
  inventada em `synthetic_snapshot` e `synthetic_tools`. Após validação local
  e revisão específica do modo DW, além de decisão explícita sobre retenção
  local, permitir `dw_tools` com pergunta e prompt da Bancada, catálogo
  das cinco consultas fixas e somente os resultados JSON escolhidos pela LLM;
  permitir `dw_snapshot` com pergunta e JSON integral de um único pacote
  candidato selecionado por `case_id` e SHA-256. Registrar versão/fingerprint,
  bytes de evidência incluídos nas requisições tentadas, com reenvios do
  histórico stateless distinguidos de entrega confirmada, e destino. Rejeitar
  CSVs brutos, bancos inteiros,
  pacotes não selecionados, gabarito, pesos, resultados brutos de treino e
  segredos. A autorização de 25/10/2026 é específica para OpenAI e esses
  payloads; a permissão Groq jamais é herdada.
- REQ-004: Em `synthetic_tools` e `dw_tools`, enviar
  apenas a allowlist do modo e `tool_choice` automático ou equivalente
  comprovado da API escolhida. Aceitar no máximo uma chamada por turno;
  validar nome, JSON e argumentos sem duplicatas antes de executar. Reusar os
  limites de chamadas, turnos, linhas e bytes da SPEC-009 e falhar
  explicitamente se a API/modelo não suportar escolha de tools local.
- REQ-005: Para leitura da DW por `dw_tools`, usar somente as cinco
  consultas fixas da DW, transação `READ ONLY`, fingerprint conferido e
  resultado limitado; não acessar bancos de origem como fallback. O registro
  deve separar pedido bruto da LLM, argumentos validados, consulta e bytes
  exatos devolvidos ao modelo. Nenhuma leitura ou envio real integra a
  validação sintética inicial.
- REQ-006: Preservar sessão, limite global de uma inferência, idempotência do
  job e reconciliação após resposta HTTP incerta. Não reenviar geração
  automaticamente. Streaming parcial, timeout, erro de autenticação do
  provedor, quota/rate limit, limite de contexto, tool inválida, consulta
  falha e falta de evidência terminam em estados distinguíveis; resposta
  parcial não vira `answered_unverified`. Expor `Retry-After` apenas quando
  seguro e disponível.
- REQ-007: Novo snapshot aditivo (`schema_version: 5`) registra provedor,
  API/versão ou superfície efetiva, ID do modelo solicitado e respondido,
  endpoint de destino sem credencial, parâmetros, uso/tokens e identificador
  de requisição quando retornados, sem inventar campos ausentes. Registrar
  pergunta, prompt, modo, classificação dos dados, evidência efetivamente
  enviada, trace das tools, erro, autor, timestamps e aprovação aplicável.
  Manter v1–v4 legíveis. Segredos e headers de autenticação não entram no
  snapshot; a retenção existente deve ser revisada antes de incluir payload
  real.
- REQ-008: Antes do primeiro envio externo, informar na UI e no README o
  destino OpenAI, o tipo de dado que sairá do notebook, modelo/API escolhidos,
  custo por unidade e limites operacionais verificados na documentação e na
  conta na data do ensaio. Com a recarga automática desligada, usar os
  créditos pré-pagos disponíveis sem teto monetário adicional na Bancada e
  sem exigir a criação de outro limite de gasto na conta. Manter limites
  técnicos por requisição, turnos e tools; diante de erro de crédito, gasto
  ou quota, parar sem retry automático nem compra/recarga iniciada pela
  aplicação. Não apresentar o saldo como corte instantâneo ou garantia de
  custo exato. Não pedir chave no chat.
- REQ-009: Implementar testes locais com transporte OpenAI simulado e fixture
  sintética cobrindo resposta simples, tool escolhida pela LLM, falhas,
  idempotência, persistência, UI e leitura histórica. Somente depois dessa
  validação e da revisão independente considerar um ensaio real sintético.
  Os modos com DW usam a autorização de 25/10/2026 e só poderão ser ativados
  depois dos testes sintéticos, com recibo que identifique payload e destino.
- REQ-010: Inventariar e preservar o diff local de Groq + DW real antes da
  implementação. Inspecionar consumidores do catálogo, serviço, cliente,
  detalhes de run e testes; atualizar documentos da frente junto ao código.
  A revisão da SPEC-012 não substitui revisão independente da extensão Groq.

## Business or domain rules

- BR-001: A escolha de tool só pertence à LLM quando há pedido retornado pelo
  provedor; validação e execução pertencem ao backend. Um plano determinista
  do servidor não conta como tool choice da LLM.
- BR-002: `answered_unverified` significa conclusão exploratória, não
  verificação numérica, causal ou científica. Sem observação, não inferir zero;
  associação temporal não prova causalidade.
- BR-003: Runs de provedores, modelos, APIs, modos ou dados distintos são
  condições distintas. O gabarito não é enviado ao provedor.
- BR-004: A autorização de transmissão é específica por destino, classe de
  dado e finalidade. A autorização Groq de 22/10/2026 não cobre OpenAI.

## Decisions already made

- O pedido de desenho não inicia implementação, cadastro de chave ou chamadas
  externas nesta etapa. As decisões posteriores abaixo autorizam orçamento e
  classe de dados para a execução futura dentro do escopo contratado.
- O provedor deve ser próprio da OpenAI por API e continuar a Bancada das
  SPECs 009/010, com a LLM escolhendo tools da allowlist.
- Em 25/10/2026, o pesquisador escolheu `gpt-6-luna` para o provedor OpenAI
  da Bancada. A superfície é `POST /v1/responses`, pois a
  [documentação oficial do modelo](https://developers.openai.com/api/docs/models/gpt-6-luna)
  indica Responses API para function calling com reasoning; Chat Completions
  só oferece function calling nesse modelo com `reasoning_effort=none`.
  Streaming e function calling constam como suportados. O preço Standard de
  texto consultado na mesma data foi US$ 0,10/1 milhão de tokens de entrada e
  US$ 0,50/1 milhão de saída; reconferir preço e acesso da conta antes de um
  ensaio pago. A escolha não comprova qualidade nos casos da pesquisa e não
  define um baseline científico sem o harness formal.
- A primeira validação deve ser local e sintética, antes de qualquer ensaio
  real. A avaliação científica continua fora da Bancada exploratória.
- Em 25/10/2026, o pesquisador decidiu usar os créditos pré-pagos disponíveis
  na API com a recarga automática desligada, sem teto monetário adicional na
  Bancada nem novo limite de gasto na conta. A disponibilidade de créditos
  não é uma decisão pendente de desenho. Essa decisão isolada não autorizava
  chamadas pagas; a autorização de dados abaixo cobre os ensaios posteriores
  dentro do escopo contratado. Ela não autoriza compra de créditos ou alteração
  de limites da conta. A [documentação oficial de
  limites de gasto](https://developers.openai.com/api/docs/guides/spend-limits)
  distingue alertas, limites rígidos e limite de uso aprovado; a aplicação
  não conhece o saldo real sem conferência da conta. Uma leitura da conta em
  25/10/2026 confirmou créditos pré-pagos disponíveis, recarga automática
  desligada, limite de gasto da organização não aplicado e nenhum limite de
  gasto do projeto. Esse inventário pode envelhecer, mas não cria outro gate
  de orçamento para a implementação.
- Em 25/10/2026, após receber a descrição dos payloads, o pesquisador
  autorizou enviar à OpenAI a pergunta, o prompt e as evidências da DW do
  projeto em `dw_tools` e `dw_snapshot`. Em `dw_tools`, a primeira requisição
  inclui a pergunta e a allowlist; somente o JSON de consultas efetivamente
  escolhidas pela LLM segue nos turnos seguintes, limitado a cinco chamadas,
  seis turnos, 200 linhas e 16 KiB acumulados. Em `dw_snapshot`, segue o JSON
  integral de um pacote candidato selecionado e conferido por hash, junto à
  pergunta nele contida. As fontes são as bases simuladas do projeto reunidas
  em `db_pesquisa_dw`, mas o payload é evidência efetiva da carga local e não
  a fixture inventada. A autorização não cobre envio dos 75 CSVs brutos,
  bancos completos, gabaritos, pesos, resultados brutos de treino, segredos ou
  dados adicionados futuramente fora desses contratos. O histórico local já
  guarda prompt, pergunta, pacote ou trace das tools. `runs.snapshot` é JSONB
  sem expiração automática; o histórico fica disponível aos pesquisadores
  autenticados. Em 26/10/2026, o pesquisador aprovou manter essa regra:
  snapshot integral sem expiração automática, acessível a Vinicius e Nicoli,
  sem remoção automática. A decisão não substitui a revisão técnica DW.

## Decisions and execution state

DEC-001 foi resolvida em 25/10/2026 como `gpt-6-luna` pela Responses API.
Na implementação, conferir formato efetivo dos eventos, parâmetros,
metadados e limites da conta antes de declarar compatibilidade validada.
DEC-003 foi resolvida em 25/10/2026 com os dois modos de DW e o escopo de
payload acima. A decisão de retenção local foi resolvida em 26/10/2026 como
manutenção da regra existente, descrita acima. A revisão técnica específica
dos modos DW foi aprovada em 26/10/2026, com adendo de readback do ensaio
`dw_snapshot` posterior.

O contrato está em `done` para integração exploratória após implementação,
testes locais, revisão sintética e revisão DW independentes, e ensaios reais
com recibos. `INFERENCE_OPENAI_DW_ENABLED` tem padrão desligado no código e
está em `1` no ambiente local privado; um processo novo confirmou a UI.
Na etapa de implementação local, nenhuma chamada externa ou leitura da DW
real foi executada. O ensaio real sintético posterior conferiu recarga
automática desligada e registrou saldo exibido, preço, modelo, destino e
payload efetivo em recibo separado. Esse inventário de 25/10/2026 pode
envelhecer; conferir novamente a conta antes de outras sessões externas.

## Constraints

- Checkout compartilhado: um escritor por vez. Preservar alterações não
  commitadas da extensão Groq + DW real e não editar os dados/artefatos
  protegidos de `FineTuning/`, `BancoModeloUse/` ou `runpod/`.
- Manter origem de dados, destino externo, cópias persistidas e classe de
  evidência identificáveis. Uma configuração ausente falha fechada.
- A implementação começa com transporte simulado e fixture sintética. A revisão
  independente antecede qualquer ensaio externo.

## Acceptance criteria

- AC-001: Em teste local autenticado, `openai` aparece como provedor distinto;
  sem configuração, antes dos gates técnicos ou com classe de dado fora do
  escopo autorizado, o run é recusado antes de rede ou DW. RunPod e Groq
  continuam selecionáveis conforme seus contratos.
- AC-002: Provedor simulado responde à fixture fixa e pede uma tool
  sintética; a escolha e o resultado são auditáveis. Tool inventada, múltiplas
  chamadas, argumentos inválidos ou limite excedido falham sem consulta.
- AC-003: Jobs, sessão após refresh, idempotência e histórico mostram
  provedor, modelo, modo, destino e erro inclusive em run incompleto; snapshots
  v1–v4 continuam legíveis e o BI não muda.
- AC-004: Testes de timeout, 401/403, 429, contexto, SSE/resposta parcial,
  ausência de evidência e falha de tool não produzem sucesso falso nem retry
  automático. Nenhuma chave ou header sensível aparece em bundle, log,
  snapshot ou recibo.
- AC-005: Documentação e revisão independente confirmam matriz de dados,
  tool choice real, custo/limites decididos, proveniência e fronteira entre
  validação simulada, eventual ensaio sintético externo e dados reais.

## Affected areas

- `inference_api/src/inference_api/`: configuração, adaptador próprio,
  catálogo, serviço, jobs, rotas, persistência e testes.
- `inference_api/frontend/src/features/bench/` e sessão, conforme impacto da
  nova seleção e do detalhe do run; `inference_api/README.md`.
- `docs/arquitetura_inferencia_compartilhada.md`, `README.md` e
  `specs/README.md`. `BancoModeloUse/dw/` e `model_evaluation/` são
  referências, sem mudança de dados. `runpod/serving/` não é área de escrita.

## References

- `AGENTS.md`, `README.md`, `specs/README.md`: regras, mapa e precedência do
  checkout compartilhado.
- `specs/active/SPEC-003/SPEC.md`: identidade e limite global;
  `specs/active/SPEC-009/SPEC.md`: modos e contrato de tools;
  `specs/active/SPEC-010/SPEC.md` e sua evidência posterior de 22/10/2026:
  integração Groq e limite da revisão original.
- `inference_api/README.md`, `docs/arquitetura_inferencia_compartilhada.md`,
  `inference_api/src/inference_api/{config,models,groq,service,server,jobs,dw_tools}.py`,
  `inference_api/frontend/src/features/bench/{BenchPage,RunDetail}.tsx`:
  comportamento que deverá ser preservado e estendido.
- `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`: separação dos
  cenários e do harness. A documentação oficial OpenAI, consultada em
  25/10/2026, embasa DEC-001 e o preço de referência; rever preços no ensaio.

## Skills

Nenhuma skill especializada de implementação é obrigatória. A revisão
independente é obrigatória por tratar de segredo, saída de dados, custo e
contrato público da Bancada.

## Validation requirements

- VAL-001: `git diff --check` e inventário do diff pré-existente.
- VAL-002: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v`.
- VAL-003: `npm --prefix inference_api/frontend run typecheck`.
- VAL-004: `npm --prefix inference_api/frontend run lint`.
- VAL-005: `npm --prefix inference_api/frontend run test -- --run`.
- VAL-006: `npm --prefix inference_api/frontend run build`.
- VAL-007: Ensaio HTTP/browser local com transporte OpenAI simulado, fixture
  inventada, escolha de tool, erro, refresh, logout e idempotência; sem rede
  externa e sem DW real.
- VAL-008: Inspecionar diff, bundle, logs e snapshots sintéticos para segredos,
  dados reais, fallback entre provedores e compatibilidade v1–v4; confrontar
  README, arquitetura e matriz de dados com o código.
- VAL-009: Preparar completion, diff, resultados locais e evidências
  sanitizadas para revisão independente. Após a revisão, um eventual ensaio
  sintético externo dentro da autorização de 25/10/2026 tem recibo separado
  com custo/uso e modelo/API efetivos; não é requisito para afirmar apenas
  implementação local.

## Review requirements

Revisão independente crítica com SPEC, manifest, diff, testes e completion.
Conferir isolamento de credencial e dados, matriz de modos, escolha de tool
pela LLM, tratamento de erro/idempotência, proveniência e leitura histórica.
Revisar a extensão Groq + DW real em contrato próprio se ainda estiver sem
revisão; não promovê-la por associação com esta SPEC.

## Execution and runtime

Ver `SPEC.execution.json`. O estado é `done` para a integração exploratória,
com `automatic_handoff: false`.
A [implementação local](evidence/local-2026-10-25.md) e a
[completion](evidence/completion.json) receberam
[revisão independente aprovada somente para o escopo sintético](evidence/review.json).
Os modos DW da OpenAI receberam [revisão independente específica
aprovada](evidence/review_dw.json) em 26/10/2026, após a decisão do
pesquisador de manter a retenção local integral sem expiração automática,
acessível a Vinicius e Nicoli. O [primeiro ensaio real sintético](evidence/openai-synthetic-real-2026-10-25.md)
foi executado em 25/10/2026 por chamada direta ao serviço e readback do run
persistido. Ele confirmou um turno Responses com `gpt-6-luna`, somente a
fixture inventada e estado `answered_unverified`; não passou por login HTTP,
jobs ou UI. A avaliação científica segue pendente.

Depois, a pedido do pesquisador, um [ensaio real pela Bancada com
`dw_tools`](evidence/openai-dw-tools-real-2026-10-25.md) em 25/10/2026
confirmou job autenticado, escolha de `financial({"year":2021})` pelo Luna,
consulta fixa de leitura à DW, envio de 13 observações à OpenAI e trace
persistido. O gate foi habilitado somente no processo desse ensaio e voltou a
`0` em seguida. Em 26/10/2026, um [ensaio real de `dw_snapshot` pela
Bancada](evidence/openai-dw-snapshot-real-2026-10-26.md) enviou os 2.762 bytes
exatos de um único pacote candidato selecionado por ID/hash, sem nova consulta
à DW no run; job, resposta e snapshot foram conferidos. Depois da revisão DW,
o gate foi definido como `1` em `BancoModeloUse/.env.local` ignorado pelo Git;
um processo novo confirmou os modos na UI. Ambos os resultados são
`answered_unverified`: a validação científica e o harness formal permanecem
fora do escopo concluído desta SPEC.
