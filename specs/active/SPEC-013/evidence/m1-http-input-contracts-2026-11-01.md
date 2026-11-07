# SPEC-013 — validação local de contratos e HTTP (01/11/2026)

**Escopo:** alterações de código e testes locais. Modelo e armazenamento de
jobs/runs foram simulados; nenhuma chamada Groq, OpenAI, RunPod ou PostgreSQL
ocorreu neste ensaio. Nenhum dado real foi transmitido.

## Mudanças

- `input_contracts.json` versiona os campos de entrada por papel e o feedback
  de correção. O motor valida a projeção antes de chamar o modelo, inclui seu
  SHA-256 no fingerprint do caso, em cada evento cognitivo e no resultado. O
  template mostra os schemas de entrada e saída ao modelo.
  Isso alterou o prompt e o fingerprint **depois** da auditoria OpenAI do
  mesmo dia. O run OpenAI anterior permanece evidência histórica do contrato
  usado naquele momento; o contrato atual não teve novo ensaio com provedor real.
- A fixture ganhou uma fonte industrial inventada. Testes separados exercitam
  DW seguida de detalhe industrial e início direto na fonte financeira, ambos
  por decisão estruturada do modelo simulado. Especialistas pedidos juntos
  são chamados em ordem canônica e recebem somente o mapa do próprio domínio.
- O teste HTTP percorre `/api/run-jobs` com autenticação simulada, recusa acesso
  anônimo, verifica idempotência da mesma chave, isolamento do recibo por
  pesquisador, conclusão do job e recuperação do snapshot v6 por `/api/runs`.
  O transporte devolve saídas de papéis roteirizadas; `storage` usa memória,
  portanto esse teste **não prova persistência no PostgreSQL**.

## Validação executada

- `python -m unittest test_agent_harness test_spec013_http -q` com
  `PYTHONPATH=inference_api/tests`: **27 testes passaram**.
- Frontend: `pnpm --dir inference_api/frontend run typecheck`, `lint`,
  `test -- --run` (2 arquivos, 3 testes) e `build`: passaram.
- `git diff --check`: passou com avisos de conversão CRLF em arquivos já
  modificados no checkout.
- `unittest discover -s inference_api/tests -q`: **95 testes, 8 pulados,
  1 erro**. O teste antigo de sessão HTTP `test_spec010.CookieHttpTests` recebeu
  `ConnectionAbortedError: [WinError 10053]` durante uma chamada local de
  logout em três execuções da suíte. O mesmo teste passou isolado. A repetição
  do módulo no mesmo processo também produziu a falha, indicando interação
  com a execução conjunta/loopback Windows; a causa ainda não foi isolada.
  Não contar a suíte completa como aprovada.

## Limites restantes

M1 ainda exige teste com armazenamento PostgreSQL do aplicativo, ensaio da
cadeia pelo job com provedor real ou transporte de fidelidade equivalente e
mais cenários de erro/replay. M0 ainda tem DEC-001–005 abertas; M2 e M3 não
foram implementados. Este ensaio não mede qualidade científica.
