# Inferência compartilhada: primeira implementação local

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
modelo. A API atual escolhe suas duas consultas pelo escopo declarado pelo
pesquisador; a [SPEC-007](../specs/active/SPEC-007/SPEC.md) prepara pacotes
fixos fora da API e não muda esse comportamento.

**SPEC-005 em 16/10/2026:** `session_checks.py` acrescenta pré-voo local de
leitura, teste HTTP opt-in do túnel e ensaio opt-in das três rotas com dois
aliases. O [runbook da sessão](../docs/sessao_inferencia_curta.md) separa esses
gates da implantação paga. Nenhuma geração remota ou exposição ngrok foi feita
pela SPEC-005; a [revisão independente](../specs/active/SPEC-005/evidence/review.json)
aprovou esse escopo local.

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
- `POST /api/runs`: `question`, `model_alias`, exatamente um de
  `prompt_revision_id` ou `system_prompt`, `scope` (`financeiro`, `industrial`
  ou `integrado`), `year`, `temperature` e `max_tokens`. Aceita
  `criteria_revision_id` **ou** `criteria` estruturado como rascunho; se ambos
  faltarem, grava uma configuração padrão explícita para clientes anteriores.
  O snapshot guarda a revisão e configuração exata utilizada, inclusive quando
  a consulta ou o modelo falha. O escopo é declarado
  pelo pesquisador; não há classificação automática. Para compatibilidade,
  `evidence_route` aceita isoladamente as duas rotas antigas. `scope` e
  `evidence_route` juntos são inválidos. O campo opcional `tools`, se enviado,
  deve coincidir exatamente com a allowlist do escopo. Campos desconhecidos
  falham antes de consultar as fontes. A escolha do modelo vale só para a chamada.
  A linha da execução é gravada uma vez, após a tentativa; não é reescrita.
- `GET /api/runs` e `GET /api/runs/{id}`: histórico. `POST
  /api/runs/{id}/feedback` anexa feedback humano sem alterar o snapshot.
- A allowlist de ferramentas contém `financeiro_vendas_ano` e
  `industrial_operacoes_ano`, com ano inteiro de 2015 a 2026. `integrado`
  executa ambas para o mesmo ano. SQL é fixo e parametrizado; cada conexão de
  origem usa transação somente leitura, timeout de consulta e limite implícito
  de uma linha agregada. Não se aceita SQL do navegador.
- O servidor escuta somente `127.0.0.1:8765`. `POST /api/login` aceita somente
  os dois pesquisadores cadastrados localmente e devolve uma sessão temporária.
  Todas as demais rotas de API exigem seu bearer; `GET /api/me` identifica a
  sessão e `POST /api/logout` a revoga. O navegador mantém o bearer só em
  memória. `author` enviado no corpo não é usado: o backend grava o nome do
  pesquisador autenticado e seu ID estável no snapshot novo.
- Dois pesquisadores podem estar logados ao mesmo tempo. Um advisory lock no
  PostgreSQL permite somente uma `POST /api/runs` global; a segunda recebe
  HTTP 429 antes de consultar fontes ou chamar a LLM. Não há limite diário por
  padrão; configurações opcionais podem ativá-lo no futuro.
- `GET /api/budget` mostra o teto informativo de US$ 10 e tenta ler
  `clientBalance` e `currentSpendPerHr` da API GraphQL da RunPod com uma
  chave de leitura do backend. Sem resposta autenticada, o saldo aparece
  indisponível, nunca estimado.

O snapshot novo usa `schema_version: 2` e os contratos `question_request`,
`route_plan`, `evidence_bundle`, `model_output` e `checks`. Cada item de evidência
registra ID estável (`ferramenta:ano`), fonte, campos, filtros, ano, granularidade,
unidade, valor, fórmula, SQL fixo parametrizado, qualidade e ressalva. O bundle
integrado inclui aviso de associação temporal sem causalidade. O agente de
resposta recebe apenas pergunta, prompt exato e o bundle gravado, além do alias
e parâmetros; o retorno bruto do servidor é preservado em `model_output.serving`.
O verificador confere schema, itens obrigatórios, resposta e IDs citados no
formato `[evidence:financeiro_vendas_ano:2020]`. Verdade numérica e causalidade
ficam `not_checked`. Os critérios da SPEC-004 acrescentam somente checks
determinísticos de presença, ano, unidade literal, IDs citados e frases literais
na resposta. Um resultado `passed` nesses checks não comprova verdade numérica.

`answered_unverified` significa apenas resposta gerada e checagem exploratória;
um ID citado inexistente gera check `failed` sem reescrever a resposta. Falhas
ficam distintas como `route_error`, `query_error`, `evidence_error`,
`insufficient_evidence`, `model_error`, `response_error` ou
`verification_error`. Sem evidência obrigatória, a LLM não é chamada. Sem
endpoint/modelo servido, a tentativa guarda o bundle e `model_error`; não se
fabrica resposta. JSON inválido ou resposta fora do contrato do servidor gera
`response_error` e preserva o corpo recebido em `model_output.serving`, inclusive
os bytes originais em Base64. Snapshots anteriores com `schema_version: 1` continuam
legíveis sem migração ou reescrita. A comparação lado a lado é somente visual:
ela lê runs existentes, avisa quando pergunta, período, evidência, prompt,
critérios, parâmetros ou versão do modelo diferem e não calcula acurácia.
As verificações formais, o gold set, a integração do [DW local v1](../BancoModeloUse/dw/README.md)
e consultas científicas adicionais permanecem
fora desta primeira fatia. O snapshot só preenche revisão exata da base,
run e SHA-256 do adapter quando a resposta vem com os headers de sessão do
gateway que coincidem com o manifesto local. Sem eles, esses campos ficam
`null` e `provenance_status: unverified`. Mesmo com headers, o estado
`session_manifest_checked` descreve o preflight daquela sessão; somente um
recibo remoto `passed` da mesma sessão marca `generation_confirmed`.
Ainda não há recibo real ou reprodução científica de inferência.

## Mapa do código

| Caminho | Responsabilidade atual |
| --- | --- |
| `run.py` e `src/inference_api/server.py` | Entrada por linha de comando, servidor HTTP, rotas e entrega do front. |
| `web/index.html` | Bancada local responsiva para revisões de prompt/critério, modelos por run, detalhes do snapshot e comparação exploratória. |
| `src/inference_api/auth.py`, `limits.py` e `budget.py` | Login de dois pesquisadores, sessão revogável, vaga única de inferência e leitura separada do saldo RunPod. |
| `src/inference_api/service.py` | Coordena uma execução e grava seu snapshot final. |
| `src/inference_api/orchestrator.py` | Valida a entrada e planeja as consultas permitidas conforme o escopo declarado. |
| `src/inference_api/evidence.py` | Executa as consultas fixas de leitura e monta o bundle com origem e ressalvas. |
| `src/inference_api/response_agent.py`, `models.py` e `serving_catalog.py` | Montam a entrada do modelo, consultam vLLM e vinculam a proveniência da sessão ao manifesto. O serving remoto ainda não foi implantado. |
| `src/inference_api/verifier.py` e `criteria.py` | Confere estrutura, IDs e critérios declarativos; não valida verdade numérica ou causalidade. |
| `src/inference_api/contracts.py`, `config.py` e `storage.py` | Contratos versionados, configuração local e persistência de prompts, execuções e feedback. |
| `tests/test_contract.py`, `test_serving.py`, `test_identity.py`, `test_criteria.py` e `browser_spec004.cjs` | Testes locais dos contratos, identidade, critérios e navegador simulado; os de banco usam banco temporário isolado. |
| `session_checks.py` e `tests/test_session_checks.py` | Pré-voo somente leitura, ensaio HTTP e prova local/mock de que a execução padrão não chama rede externa. |

O contrato e a revisão independente da SPEC-001 ficam em
[`specs/active/SPEC-001/`](../specs/active/SPEC-001/SPEC.md).
O contrato e a [evidência local da SPEC-003](../specs/active/SPEC-003/evidence/local-2026-10-15.md)
ficam em [`specs/active/SPEC-003/`](../specs/active/SPEC-003/SPEC.md); a
[revisão independente](../specs/active/SPEC-003/evidence/review.json) aprovou
o escopo local em 15/10/2026.

## Rodar localmente

Use o Python de um ambiente próprio com as dependências de
[`requirements.txt`](requirements.txt). Na raiz do repositório, em PowerShell:

```powershell
BancoModeloUse/.venv/Scripts/python.exe -m venv inference_api/.venv
inference_api/.venv/Scripts/python.exe -m pip install -r inference_api/requirements.txt
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py start
inference_api/.venv/Scripts/python.exe inference_api/run.py init-db
inference_api/.venv/Scripts/python.exe inference_api/run.py migrate-db --pg-dump 'C:/Program Files/PostgreSQL/15/bin/pg_dump.exe'
inference_api/.venv/Scripts/python.exe inference_api/run.py migrate-criteria --pg-dump 'C:/Program Files/PostgreSQL/15/bin/pg_dump.exe'
inference_api/.venv/Scripts/python.exe inference_api/run.py configure-users
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
`configure-users` pede as duas senhas e confirmações em prompt oculto; após
as quatro entradas, registra os dois logins aprovados. `set-password`
permite trocar uma senha posteriormente e exige 12 a 128 caracteres para
novas senhas. Cada cadastro grava somente
hash com sal e revoga sessões anteriores. Não passe senha em argumento, variável
versionada ou chat. `revoke --username Nicoli|Vinicius` suspende o acesso sem
apagar snapshots. Essas ações não recriam nem importam bases de origem. As
credenciais do cluster são lidas do
`BancoModeloUse/.env.local` ignorado pelo Git; todas as conexões exigem host
`127.0.0.1`, porta `5544` e nomes de bancos conhecidos. Não há fallback para
`localhost:5432`.

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
Veja o [runbook de serving](../runpod/serving/README.md). Nenhuma dessas
variáveis deve ser enviada ao navegador.
O runbook também separa a conclusão local da SPEC-002 da sessão paga: a
revisão do `terraform plan`, a estimativa de GPU e discos e a confirmação
explícita do `apply` ocorrerão antes de uma implantação futura.

## Alvo futuro do ngrok

O usuário escolheu usar apenas a autenticação da aplicação: bearer opaco
revogável por pesquisador, validado no backend. Não há OAuth ou Basic Auth na
borda. Quando uma sessão posterior autorizar a exposição, o alvo previsto é
**somente** o HTTP da aplicação em `127.0.0.1:8765`:

```powershell
ngrok http 8765
```

O comando acima é documentação, não foi executado. Nunca apontar o ngrok para
`5544` nem expor PostgreSQL. Antes da primeira exposição, trocar as duas senhas
com `run.py set-password --username ...` em terminal local, pois as escolhas
originais passaram pelo chat; depois confirmar login e revogação novamente.

Testes locais sem infraestrutura remota:

```powershell
$env:INFERENCE_IDENTITY_DB_TEST = '1'
inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v
$env:NODE_PATH = 'C:/Users/vinic/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
node inference_api/tests/browser_spec004.cjs
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

## Segurança e operação pendentes

Não abra o túnel ngrok ainda. A revisão independente aprovou a identidade e
a vaga única no escopo local, sem validar exposição pública. A chave de leitura de saldo
e as senhas não entram no Git; credenciais escolhidas fora de um canal privado
devem ser trocadas antes de expor a interface. A proteção da API remota e os
aliases/versões/hashes dos pesos exigem uma sessão autorizada. O servidor HTTP
segue ferramenta local de desenvolvimento, sem SSO nem garantia de produção.
Não usar as respostas como métricas do artigo.
A varredura de segredos e a revisão independente estão registradas nos
[recibos da SPEC-003](../specs/active/SPEC-003/evidence/review.json). O teste
HTTP com os usuários efetivamente cadastrados passou em 15/10/2026, sem abrir
túnel.
