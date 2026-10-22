# Inferência compartilhada: Observatório e Bancada local

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

Groq aceita somente `synthetic_snapshot` e `synthetic_tools`. Ambos usam a
pergunta e o prompt fixos de `synthetic_data.py`; o segundo modo anuncia a
tool local `synthetic_metric`, cuja chamada deve ser escolhida pela LLM e
validada antes de a fixture inventada responder. A API recusa pacotes privados,
perguntas livres e critérios editáveis nesses runs. A DW real não é consultada
nem enviada à Groq. Runs Groq são snapshots v4 com provedor, ID configurado,
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
