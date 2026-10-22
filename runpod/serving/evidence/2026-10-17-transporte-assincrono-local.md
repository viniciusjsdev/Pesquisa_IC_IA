# Correção local do transporte e dos jobs da Bancada — 17/10/2026

## Escopo e proveniência

Checkout em `4943257` com alterações locais **sem commit**. Esta evidência
registra implementação e testes locais, sem revisão independente desta mudança.
Nenhuma Pod, inferência paga, ngrok,
`terraform apply` ou avaliação científica foi executada nesta mudança.
O replay anterior que motivou a correção está em
[`2026-10-17-finqa-sem-teto-l4.md`](2026-10-17-finqa-sem-teto-l4.md).

## Mudança

- `runpod/serving/gateway.py` encaminha SSE do vLLM em chunks, com token e
  allowlist preservados e cabeçalhos de identidade da sessão. A resposta não
  espera a geração inteira para começar a sair do gateway.
- `inference_api/src/inference_api/models.py` pede streaming, reconstrói
  conteúdo, tool calls, uso e `finish_reason` e registra os bytes SSE. Um
  fluxo incompleto ou `finish_reason=length` continua em `response_error`.
- `inference_api/src/inference_api/jobs.py` e a migração 003 guardam jobs
  vinculados ao pesquisador, com chave UUID idempotente, uma vaga global e
  resultado associado ao run imutável. Reinício da API marca jobs inacabados
  `interrupted`, sem reenvio automático.
- O React usa `POST /api/run-jobs` e consultas curtas ao job. Perda da resposta
  inicial é reconciliada pela chave antes de permitir novo envio; recarregar
  a página conserva o ID do job na sessão do navegador.

## Validação observada

| Verificação | Resultado |
| --- | --- |
| `python -m unittest discover -s inference_api/tests -v` | 45 testes, OK; 8 testes de banco condicionais pulados nessa execução. |
| `INFERENCE_IDENTITY_DB_TEST=1` em `test_streaming_jobs.py` | 4 testes, OK, incluindo migração e HTTP assíncrono em banco descartável. |
| Gateway SSE simulado | O primeiro evento chegou ao cliente antes da liberação do término do modelo simulado. |
| Parser SSE | Tool call fragmentada reconstruída; fluxo sem `[DONE]` recusado; `length` preservado no registro de erro. |
| TypeScript e Vite | `tsc -b --pretty false` e build Vite passaram com Node 24.19.0. |
| Navegador simulado | `browser_spec009.cjs` passou em Chromium contra o React compilado e API mockada, nos dois modos, histórico e comparação. |
| API host local | `GET /health` 200, `/` 200, `/api/me` sem sessão 401; serviço encerrado após a checagem. |

O ESLint não devolveu resultado dentro de 60 s nesta máquina e foi interrompido;
isso não é um passe de lint. O Docker Desktop Linux Engine estava indisponível,
logo a imagem/Compose desta versão não foi reconstruída nem executada.

## Migração do banco local

Antes da mudança, `db_inference_app` retornou versões `[1, 2]` e não tinha
`run_jobs`. A migração 003 foi aplicada ao **banco local isolado**
`127.0.0.1:5544`, depois de `pg_dump` custom. Readback: versões
`[1, 2, 3]`, tabela `run_jobs`, zero jobs no momento da leitura.

- Backup ignorado pelo Git:
  `inference_api/.local/run-jobs-backup-20261017-225012.dump`
- Tamanho: 65.881 bytes.
- SHA-256: `8EA1424BE222F238A6D0F2337948D39F844A99ED75AD04B85F3B5F301B1C8924`.
- `pg_restore -l` leu o arquivo e listou 47 linhas de inventário, sem erro.
- A API e o PostgreSQL local foram parados após o readback; portas 8765 e
  5544 sem serviço no check final.

O banco da cópia Docker não recebeu a migração 003. Os testes em banco
descartável e host não comprovam o comportamento da imagem Docker.

## Prova remota necessária

Após autorização de custo para uma nova Pod de 24 GB, sem volume persistente,
e conferência da oferta no console, instalar **esta versão** de `gateway.py` e do backend, confirmar
vLLM compatível com o driver do host, autenticação e `verify_remote.py` 7/7.
Na plataforma via ngrok, submeter uma pergunta curta da base e um caso longo
FT-FinQA A sem `max_tokens`; exigir HTTP 202 rápido, progressão
`accepted/running/completed`, run salvo, SSE com identidade e bytes/uso,
ausência de 524 e nenhum reenvio ao atualizar a página. O FT-FinQA A pode
continuar terminando `length` e repetindo texto: isso mede comportamento do
modelo dentro da janela de 4.096 tokens, separado do transporte. Testar B
como caso separado e julgar a utilidade da resposta por critério humano.
Parar a Pod ao final e ler o custo residual. Sem esse replay, a correção está
validada **localmente**, não no caminho público completo.
