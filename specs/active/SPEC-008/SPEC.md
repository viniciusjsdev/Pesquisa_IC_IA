---
id: SPEC-008
title: Observatório unificado com Bancada de testes
status: done
contract_version: 2
---

# SPEC-008: Observatório unificado com Bancada de testes

## Goal

Depois do login já existente, oferecer um único mini sistema com o Observatório
financeiro-industrial como tela principal e uma quinta aba, **Bancada de testes**,
na navegação lateral esquerda. A bancada reúne as funções exploratórias já
implementadas na `inference_api`; as quatro abas do BI conservam sua experiência.

## Context

- No baseline anterior à migração, `/` era servido por
  `inference_api/web/index.html` e continha a bancada da SPEC-004 com login na
  mesma página. Esse HTML foi retirado do checkout ativo e permanece no commit
  base `772ea0d`. A autenticação, os endpoints,
  os snapshots de runs e a concorrência global já existem no backend Python.
- O HTML fornecido pelo usuário foi fixado em
  [`references/BI_Pesquisa_Offline.reference.html`](references/BI_Pesquisa_Offline.reference.html)
  (SHA-256 `9C4C5C16603AE2CD5EC316BFE970A611067542C6D2DFBA4B51E585196B1CD1E2`).
  Ele é **referência de aparência, interação e retrato sintético de 06/09/2026**,
  nunca estado atual do DW nem código de produção. Sua aba “Dados e método” diz
  que o DW está pendente; isso envelheceu: o DW local v1 existe, mas o painel
  offline não o consulta. A referência contém dados incorporados e nenhuma
  chamada de rede.
- A SPEC-004 cobre a bancada exploratória; a avaliação científica formal e
  os pacotes da SPEC-007 permanecem fora deste front. O baseline estrutural
  anterior à migração está em `baseline.json`.
- Revisão do contrato em 16/10/2026: a execução via Docker é parte da entrega.
  O cluster PostgreSQL atual escuta somente no loopback Windows
  (`127.0.0.1:5544`). Um teste local transitório com contêiner em rede `host`
  não alcançou essa porta, embora ela respondesse no host. Portanto, o Compose
  não deve depender de acesso àquele loopback nem alterar sua configuração.

## Scope

- Servir uma aplicação React 19 + TypeScript strict + Vite pela **mesma origem**
  do servidor Python local, em `/`, sem criar outro serviço público. O Python
  continua dono de identidade, regras, persistência, consultas e chamadas aos
  modelos. Organizar o front em `inference_api/frontend/` com shell, feature BI,
  feature bancada, cliente HTTP e testes; usar o `karya-frontend-builder` para
  arquitetura e validação, subordinado à paridade visual desta SPEC.
- Fazer do login existente a primeira tela. Após autenticar, mostrar o shell
  do Observatório; a sessão dá acesso às cinco abas. A navegação inclui, nesta
  ordem, Visão integrada, Financeiro, Industrial, Dados e método e Bancada de
  testes. Logout e expiração retornam ao login.
- Preservar nas quatro abas BI o layout, textos de análise, filtros de ano e
  granularidade, cards, gráficos, tabelas, definições, CSV e comportamento
  responsivo da referência. O retrato sintético permanece congelado e
  identificado pela data de `snapshot_at`; não recalcular métricas contra o DW
  nesta SPEC. Corrigir somente o rótulo factual obsoleto sobre o DW, informando
  que o DW local v1 existe e **este retrato offline não o consulta**.
- Extrair o JSON incorporado da referência para um arquivo privado do backend
  com mesmo conteúdo/hash lógico e servi-lo por `GET /api/bi/snapshot`, que
  exige a sessão da SPEC-003. O bundle público do React não incorpora o JSON
  nem os dados de BI. Falha de leitura aparece no BI sem vazar caminho local.
- Dentro da nova aba, reorganizar a bancada da SPEC-004 em seções de sessão e
  orçamento, prompts, critérios, execução, resultado/evidências, histórico,
  feedback e comparação. Reutilizar os contratos HTTP existentes.
- Entregar `inference_api/compose.yaml`, Dockerfile multiestágio e
  `.dockerignore` para **um contêiner da aplicação** (build React e runtime
  Python) e **um PostgreSQL 15** local em volume nomeado. O navegador acessa
  apenas a porta HTTP da aplicação publicada em `127.0.0.1`; PostgreSQL não
  publica porta no host. A LLM continua sendo serviço externo consultado pelo
  backend quando houver URL configurada; Compose não sobe modelo nem Pod.
- Tornar explícitos os dois modos de configuração: execução direta preserva
  `127.0.0.1:5544`; modo Docker aceita somente o serviço `db:5432` na rede
  privada do Compose e escuta `0.0.0.0:8765` **dentro** do contêiner. Não
  relaxar a allowlist para hosts arbitrários. A imagem inclui apenas código,
  bundle React, manifesto de aliases e snapshot BI privado; exclui `.env.local`,
  CSVs, dados do cluster, pesos, resultados e backups.
- Entregar procedimento/script de **cópia lógica explícita e não destrutiva**
  dos três bancos já carregados (`db_industrial`, `db_financeiro` e
  `db_inference_app`) do cluster Windows para um volume Docker vazio. Usar
  `pg_dump` no host e `pg_restore` por stdin em `docker compose exec -T db`
  (sem publicar porta de banco), ambos compatíveis com PostgreSQL 15; conferir nomes,
  versão, volume de destino vazio, hashes dos dumps, contagens e readback;
  recusar sobrescrita. O `docker compose up` nunca inicia importação,
  migração, criação de usuários ou restauração automaticamente. A cópia com
  dados reais é acionada separadamente pelo usuário; validar a preparação
  com bancos descartáveis de teste.
- Ao concluir a migração, retirar `inference_api/web/index.html` e qualquer
  rota, teste ou documentação que ainda o trate como front ativo, depois de
  conferir consumidores. Atualizar `inference_api/README.md`, arquitetura e
  índice do projeto com o estado comprovado.

## Non-scope

- Alterar bases de origem, DW, fórmulas científicas, gold set, manifests de
  modelos, pesos, treino, orquestração dos agentes ou contrato dos runs.
- Implantar RunPod, abrir ngrok, executar inferência paga, carregar novamente
  o DW ou criar benchmark científico na interface.
- Criar papéis, usuários, OAuth, persistência de token no navegador, SQL ou
  código editável pelo pesquisador, nova API de BI em tempo real ou tela de
  administração de infraestrutura.
- Redesenhar as quatro seções BI além da correção factual indicada acima.
- Mover ou montar diretamente o diretório físico do PostgreSQL Windows em
  um contêiner Linux, alterar `listen_addresses`/`pg_hba.conf` do cluster
  existente, expor porta de banco, provisionar nuvem ou executar restore real
  sem acionamento específico do usuário.

## Requirements

- REQ-001: A rota `/` exibe somente a tela de login quando não há sessão em
  memória. Login usa `POST /api/login`; a identidade é confirmada por
  `GET /api/me`; logout usa `POST /api/logout`. O bearer permanece somente em
  memória, nunca em URL, `localStorage`, `sessionStorage`, HTML ou logs.
- REQ-002: A navegação lateral desktop conserva a ordem e o estilo da
  referência, acrescentando “Bancada de testes” ao final. No celular, conserva
  o padrão responsivo da navegação existente, com a quinta aba acessível por
  teclado e toque, sem rolagem horizontal da página. A aba ativa é indicada
  visual e semanticamente.
- REQ-003: As quatro abas BI mantêm o mesmo retrato, cobertura, agregações,
  períodos, definições, estados vazios e colunas exportadas da referência.
  O CSV continua com BOM UTF-8, separador `;`, vírgula decimal e escopo/grão
  no nome. O texto contextual mostra `snapshot_at`, “base sintética” e que não
  há atualização automática. Não exibir “DW pendente” como estado atual.
- REQ-004: `GET /api/bi/snapshot` requer bearer válido e devolve apenas o
  retrato fixado, com `Cache-Control: no-store`; sem sessão responde 401, com
  sessão revogada responde 401. O snapshot não é servido por arquivo estático
  nem incorporado no bundle público. O endpoint não consulta DW ou origens.
- REQ-005: Na bancada, preservar edição/versionamento de prompts e critérios,
  revisão esperada e conflito 409 sem perda do rascunho; carregar modelos pelo
  backend e escolher alias por run; manter escopo, ano, temperatura e máximo de
  tokens. Um modelo indisponível não se apresenta como disponível.
- REQ-006: Resultado, histórico e comparação exibem status, resposta bruta,
  evidências e suas fontes/período/unidades, SQL fixo de proveniência, checks,
  limitações e erros de consulta/modelo. Feedback anexa comentário ao run
  existente. Diferenças de insumos e `answered_unverified` ficam explícitas.
- REQ-007: O orçamento mostra teto manual como informação e saldo RunPod
  somente quando `GET /api/budget` confirma a leitura; falha não vira saldo
  estimado. HTTP 429 da vaga global aparece de modo legível, sem retry
  automático da inferência.
- REQ-008: Se a sessão expirar em qualquer aba, limpar dados privados em
  memória, interromper ações dependentes de sessão e voltar ao login; nenhum
  conteúdo de BI ou bancada deve aparecer após logout. Mensagens de carregamento,
  erro, vazio e sucesso são compreensíveis sem o console.
- REQ-009: A aplicação usa as APIs existentes da `inference_api`, sem cliente
  HTTP diretamente em componentes visuais, e mantém uma única implementação
  ativa de front. Dados da referência HTML permanecem em fixture identificada,
  sem serem promovidos a fonte de verdade operacional.
- REQ-010: `docker compose --env-file BancoModeloUse/.env.local -f inference_api/compose.yaml up --build` inicia
  apenas aplicação e PostgreSQL local após a preparação explícita do volume.
  Em volume vazio, a aplicação informa falta de dados/esquema e não cria nem
  restaura bancos silenciosamente. O front compilado e `/api/*` compartilham a
  mesma origem e a porta publicada pode ser trocada sem alterar o código.
- REQ-011: O modo Docker usa rede privada `app`–`db`, healthcheck do banco,
  volume nomeado persistente, imagem de runtime sem Node, usuário não root
  quando tecnicamente viável, dependências versionadas e contexto de build
  mínimo. Não usar `docker compose down -v` em instrução operacional padrão.
- REQ-012: O script de cópia lógica é idempotente por recusa: verifica que o
  destino é o volume/serviço Docker esperado e está vazio; lê os bancos Windows
  sem alterá-los; restaura exatamente os três nomes permitidos; produz recibo
  local ignorado pelo Git com hashes, contagens e versão. Falha parcial exige
  diagnóstico e não aciona retry ou limpeza automática.
- REQ-013: Segredos dos bancos e da RunPod são recebidos somente em runtime,
  via arquivo local ignorado/variáveis controladas, nunca no Dockerfile,
  camadas da imagem, bundle, `docker compose config` exibido ou logs. O modo
  Docker não presume `INFERENCE_VLLM_URL` configurada e mostra modelos
  indisponíveis sem fazer geração remota.

## Business or domain rules

- BR-001: Ambos os pesquisadores autenticados têm o mesmo acesso às cinco
  abas; autoria de prompt, critério, run e feedback vem da identidade validada
  pelo backend, não de campo livre.
- BR-002: A bancada é exploração de prompts e modelos. Seus checks não provam
  correção numérica, causalidade ou avaliação científica. A comparação visual
  não gera ranking/score de modelos.
- BR-003: O BI é retrato sintético fixado em 06/09/2026. A existência posterior
  do DW local v1 não altera a linhagem desse arquivo e não o torna “live”.
- BR-004: Uma só inferência global simultânea e revisões imutáveis continuam
  impostas pelo backend conforme SPEC-003/004; o front não simula autorização.
- BR-005: O PostgreSQL Docker é uma **cópia local separada** para uso do mini
  sistema. O cluster Windows continua sendo a origem preservada; nenhuma
  sincronização bidirecional é prometida. Novos runs feitos no Docker ficam
  no volume Docker e não aparecem automaticamente no banco Windows.

## Decisions already made

- O usuário escolheu o Observatório fornecido como tela central, login primeiro,
  acesso a tudo após login e Bancada como aba lateral esquerda; as demais abas
  permanecem como estão. Essa decisão guia qualquer regra visual genérica.
- A decisão de arquitetura da conversa foi React/TypeScript para o front e
  Python para API/agentes. A aplicação continua na mesma origem local,
  conforme `docs/arquitetura_inferencia_compartilhada.md`.
- O BI permanece snapshot offline nesta SPEC; a integração com DW e um
  eventual painel BI atualizado exigem contrato próprio. Não mascarar a data
  do retrato nem o status real do DW.
- O usuário pediu execução via Docker. Para manter o PostgreSQL Windows no
  loopback e evitar portas de banco expostas, o Docker local inclui uma cópia
  lógica isolada dos três bancos necessários; o DW não integra essa cópia.
  Docker Compose fica em `inference_api/` porque esta frente, não o repositório
  inteiro, é o sistema compartilhado.

## Constraints

- Aplicar a orientação de `AGENTS.md`: preservar dados e resultados protegidos,
  não executar RunPod/ngrok, não deixar front legado ativo e não misturar DW
  local com harness científico.
- A referência HTML é fixture de design e regressão, não deve ser servida em
  produção. Conferir seu SHA-256 antes da extração; registrar a proveniência
  do JSON exportado e comparar valores e CSV antes de substituir o front.
- Conferir consumidores de `inference_api/web/index.html`, inclusive
  `browser_spec004.cjs`, antes de removê-lo. Manter um só escritor no checkout.
- Não enviar credenciais, token, dados protegidos ou saída de API externa em
  screenshots/testes. Não instalar dependências fora da política do skill de
  frontend; resolver conflitos com as decisões explícitas desta SPEC.
- O comando operacional deve separar `build`, preparação do volume, `up`,
  healthcheck, smoke local e parada. Validar em porta alternativa quando
  `8765` estiver ocupada; não interromper o servidor local existente para
  testar Compose. `down` preserva o volume. Documentar claramente que cópia
  lógica inicial e teste real de RunPod/ngrok são etapas distintas.

## Acceptance criteria

- AC-001: Em navegador limpo, `/` mostra login e nenhuma navegação, métrica,
  prompt ou run; credenciais válidas abrem a Visão integrada e as cinco abas;
  logout, token revogado e 401 voltam ao login sem dados privados renderizados.
- AC-002: Em desktop e 360–390 px, as quatro abas BI preservam a estrutura,
  filtros, tabelas, gráficos, estados vazios e exportação da referência; a
  quinta aba é acessível, ativa e visualmente coerente. A página não tem
  overflow horizontal, e labels/foco/estado ativo são acessíveis.
- AC-003: Para a mesma seleção de aba, anos e grão, métricas-chave, linhas da
  tabela e bytes normalizados do CSV coincidem com a referência. A UI exibe
  data do retrato e corrige o status do DW sem alegar dado atualizado.
- AC-004: `GET /api/bi/snapshot` devolve 401 sem bearer ou após logout e 200
  apenas com sessão válida; bundle/arquivos estáticos não contêm o JSON do BI.
- AC-005: Na Bancada, os fluxos de duas revisões de prompt e critério, dois
  aliases, um run, histórico, feedback e comparação funcionam pelos endpoints
  existentes; conflito 409 e rascunho, 429, modelo offline, falhas e
  `answered_unverified` são legíveis.
- AC-006: Somente um front é servido em `/`; testes e documentação não apontam
  o HTML antigo como caminho de uso. Revisão independente aprova paridade,
  segurança da sessão e separação entre exploração e avaliação formal.
- AC-007: Compose valida e constrói as imagens sem incluir `.env.local`, CSVs,
  pesos, resultados ou dumps; aplicação inicia em porta local alternativa com
  PostgreSQL de teste no mesmo Compose, e login, BI protegido e bancada passam
  por HTTP/browser sem servidor Python instalado no host.
- AC-008: O teste Docker demonstra que `db:5432` é alcançável apenas na rede
  interna, que a porta do banco não está publicada, que a porta HTTP se prende
  a `127.0.0.1`, que `down` preserva o volume e que um volume vazio não recebe
  importação/migração automática. Sem RunPod configurada, modelo aparece
  indisponível e não há chamada externa de geração.
- AC-009: Em bancos descartáveis, a cópia lógica é aceita somente em destino
  vazio, gera recibo de hashes/contagens e confirma readback dos três bancos;
  segunda execução recusa sem alterar o destino. O procedimento com dados reais
  fica pronto e documentado, sem executá-lo como efeito implícito desta SPEC.

## Affected areas

- `inference_api/frontend/` (novo), `inference_api/src/inference_api/server.py`,
  arquivo privado de snapshot BI e testes da `inference_api`.
- `inference_api/web/index.html` e consumidores diretos, a retirar após paridade.
- `inference_api/compose.yaml`, `inference_api/Dockerfile`, `.dockerignore`
  aplicável ao contexto de build, scripts locais de preparo/validação Docker,
  `inference_api/src/inference_api/config.py` e bind do servidor HTTP.
- `inference_api/README.md`, `docs/arquitetura_inferencia_compartilhada.md`,
  `README.md`, `specs/README.md` e eventuais instruções da frente no `AGENTS.md`.
- Sem mudança em `BancoModeloUse/dw/`, `model_evaluation/`, `FineTuning/` ou
  `runpod/`.

## References

- `AGENTS.md` e `README.md`: proteção, fonte de verdade e mapa do checkout.
- `inference_api/README.md` e `docs/arquitetura_inferencia_compartilhada.md`:
  endpoints, topologia, identidade e limites de validação.
- `inference_api/web/index.html`, `inference_api/src/inference_api/server.py` e
  `inference_api/tests/browser_spec004.cjs`: comportamento atual a migrar.
- `inference_api/src/inference_api/config.py`, `inference_api/run.py`,
  `inference_api/requirements.txt`, `runpod/serving/manifest.json` e
  `BancoModeloUse/scripts/local_postgres.py`: contratos de conexão, entrada,
  dependências, catálogo de aliases e isolamento do cluster Windows.
- `specs/active/SPEC-003/SPEC.md` e `specs/active/SPEC-004/SPEC.md`: acesso,
  concorrência e funções exploratórias.
- `BancoModeloUse/dw/README.md` e
  `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`: estado do DW e
  separação do benchmark científico.
- `specs/active/SPEC-008/references/BI_Pesquisa_Offline.reference.html`:
  fonte congelada do design, dados e CSV do Observatório; o texto “DW
  pendente” é histórico, conforme a correção exigida nesta SPEC.
- `specs/active/SPEC-008/baseline.json`: inventário pré-migração.

## Skills

- `karya-frontend-builder` (instalado): arquitetura React, fronteira de API,
  responsividade, validação e segurança de dependências. A paridade com o
  Observatório e a autenticação existente prevalecem sobre defaults visuais
  e mocks do skill.
- `karya-infra-orchestrator` (instalado): aplicar apenas suas referências de
  Docker, Compose, ambiente e validação. Não criar Terraform, Vercel, Render,
  Supabase ou estrutura de monorepo genérica; a topologia local desta SPEC
  prevalece.

## Validation requirements

- VAL-001: `git diff --check` na raiz; verificar que alterações de outras
  SPECs no checkout compartilhado não foram incorporadas inadvertidamente.
- VAL-002: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v`.
- VAL-003: `npm --prefix inference_api/frontend run typecheck`.
- VAL-004: `npm --prefix inference_api/frontend run lint`.
- VAL-005: `npm --prefix inference_api/frontend run test`.
- VAL-006: `npm --prefix inference_api/frontend run build`; conferir o lockfile
  conforme a política do `karya-frontend-builder`.
- VAL-007: Executar teste HTTP local para login, `GET /api/me`, snapshot 401/200,
  logout/revogação e rotas existentes; inspecionar bundle/estáticos por ausência
  do JSON BI e de tokens. Sem chamada real à RunPod.
- VAL-008: Executar Playwright local com API de inferência simulada para login,
  quatro abas BI, filtros/CSV, Bancada (revisões, modelos, run, feedback,
  comparação, conflito, 429 e erros), logout e viewport desktop/360 px.
  Capturar evidência sem segredos e comparar referência/novo front.
- VAL-009: Inspecionar a extração do JSON, agregações e CSV contra a fixture;
  conferir o texto de `snapshot_at`, o status do DW e a ausência de chamadas ao
  DW. Registrar hashes e diferenças intencionais.
- VAL-010: Conferir referências/consumidores do HTML antigo e registrar sua
  remoção, bem como a atualização dos READMEs e arquitetura. A fixture em
  `references/` permanece identificada apenas como contrato histórico de
  regressão, nunca como rota de execução.
- VAL-011: `docker compose --env-file inference_api/.local/docker-test.env -f inference_api/compose.yaml config --quiet` com arquivo local de teste sem
  segredo real; conferir que só HTTP loopback é publicado e que o PostgreSQL
  não possui `ports`.
- VAL-012: `docker compose --env-file inference_api/.local/docker-test.env -f inference_api/compose.yaml build` e inspeção da
  imagem/contexto por ausência de `.env.local`, CSVs, pesos, resultados e dumps.
- VAL-013: Subir Compose com nome de projeto e porta de teste isolados,
  provisionar somente fixture descartável, executar smoke HTTP/browser de
  login, BI e bancada, depois parar sem `-v`. Registrar IDs dos serviços,
  healthchecks, porta e preservação do volume. Não usar credenciais reais.
- VAL-014: Exercitar a cópia lógica apenas entre bancos descartáveis, incluindo
  recusa de segunda aplicação e falha parcial; conferir hashes/readback e que
  o cluster Windows em `127.0.0.1:5544` não foi alterado.

## Review requirements

Revisão **independente Sol/high** após implementação. O revisor deve ler
SPEC, manifest, baseline, diff, testes e evidência; verificar gating real dos
dados por sessão, ausência de bundle BI público, paridade das quatro abas,
integridade da Bancada, remoção do front obsoleto e afirmações científicas.
Conferir isolamento dos dois PostgreSQL, ausência de segredos na imagem,
restauração não destrutiva, portas, volume persistente e recibos Docker.
O resultado local não prova Pod, ngrok ou qualidade dos modelos.

## Execution and runtime

Executar somente por thread de implementação própria, conforme
`SPEC.execution.json`, após conferir o estado compartilhado do checkout.
Esta SPEC não inicia a thread, não implementa o front e não aciona serviço
externo. Uma decisão consequencial ausente deve voltar como `needs_design`.
