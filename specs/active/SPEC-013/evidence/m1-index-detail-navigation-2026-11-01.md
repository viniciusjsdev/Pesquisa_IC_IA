# SPEC-013 · índice, detalhe e trajetória da Bancada (01/11/2026)

Escopo desta mudança: motor M1 **sintético**, contratos JSON e apresentação do
snapshot v6 na Bancada. Não houve consulta aos bancos de pesquisa, execução com
Groq/OpenAI/RunPod, migração de PostgreSQL ou pontuação científica.

## Comportamento implementado

- Cada especialista de domínio faz duas chamadas ao mesmo modelo: seleção de
  `table_ids` em índice compacto, seguida de análise de `domain_detail` apenas
  para os IDs selecionados. Entre elas, o backend valida os IDs e o limite,
  projeta o detalhe e registra `map_projection` no trace. ID desconhecido recebe
  feedback corrigível; nenhuma consulta é disparada por esse erro.
- A trajetória da Bancada mostra a pergunta inicial, os eventos agrupados por
  rodada, o papel e o resumo de cada etapa, um painel de recebido/devolvido/
  próximo evento registrado, os JSONs exatos e a resposta final ao término.
  A navegação apresenta **Preparar execução**, **Trajetória da execução** e
  **Histórico** nessa ordem.
  Chamadas ao modelo aparecem como Assistente; projeção e consulta sintética
  aparecem como Ferramenta do backend. Os dois estágios do especialista contam
  como um papel conceitual da mesma IA.

## Verificação local

- `python -m unittest discover -s inference_api/tests -p test_agent_harness.py`:
  **28 testes passaram**. Cobrem seleção e projeção, rejeição de ID desconhecido,
  aprofundamento entre domínios, limite de contexto por papel e consulta sintética.
- `python -m unittest discover -s inference_api/tests -p test_spec013_http.py`:
  **1 teste passou**. Exercita HTTP autenticado, job idempotente e readback do
  snapshot com transporte e armazenamento em memória; a cadeia passou a ter
  12 chamadas no caso simulado.
- Frontend: `vitest run` **4 testes passaram**; `tsc -b --pretty false`, ESLint
  dos três arquivos de componente/teste afetados e `vite build` passaram.
  Os testes de UI verificam a ordem dos dois estágios, a projeção intermediária,
  o painel da etapa e a resposta final. Um smoke adicional em Chrome local,
  com todas as rotas API mockadas, abriu um snapshot v6 pelo Histórico,
  selecionou `map_projection`, conferiu o painel e a resposta e salvou
  `inference_api/.local/spec009-browser/harness-v6.png`. Nenhum provedor foi chamado.

Uma execução ampla de `unittest discover -s inference_api/tests -v` em 01/11
teve 102 testes, 8 pulados e um erro no teste legado de cookie
`test_spec010.CookieHttpTests.test_refresh_logout_csrf_expiration_and_legacy_bearer`:
`ConnectionAbortedError [WinError 10053]` na conexão HTTP local. Os testes
direcionados da SPEC-013 passaram; a suíte ampla precisa de repetição/diagnóstico
antes de ser usada como gate de conclusão.

O mapa semântico aprovado, o orçamento definitivo, o acesso real a DW/origens
e o protocolo científico seguem decisões abertas na SPEC. O estado permanece
`design`; esta evidência não valida M1 completo nem M2/M3.
