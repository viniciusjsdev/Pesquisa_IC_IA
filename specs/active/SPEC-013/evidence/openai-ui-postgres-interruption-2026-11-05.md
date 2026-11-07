# Primeira tentativa OpenAI pela Bancada: interrupção antes do modelo

Em 05/11/2026, o pesquisador autorizou executar a pergunta integrada X3 pela
interface, com três repetições previstas se a primeira terminasse corretamente.
A configuração preparada omite o teto de tokens e bytes de saída do piloto.

## Evidência observada

- Chrome autenticado como Vinicius; piloto `openai_harness_pilot`, gpt-6-luna.
- Pergunta: “Em 2021, qual agregado de parada da máquina 2000002 está na DW,
  quais paradas geradas da mesma máquina/período aparecem no industrial e
  quais observações financeiras existem, sem atribuir relação causal?”
- Um único clique em Executar: POST `/api/run-jobs` retornou 202 às 22:53:28
  locais, job `387e8fe6-a5b9-426b-86c6-8de7c139b90f`.
- O worker falhou em `storage.update_job(accepted, running)`, antes da chamada
  a `service.execute_run`. Portanto não houve chamada OpenAI, consulta de
  evidência pelos agentes ou resposta final nesta tentativa.
- Windows Application Error 1000 às 22:53:28 e 22:53:33: `postgres.exe`
  15.0.19.26223, `ucrtbase.dll` 10.0.26100.9711, exceção `0xc0000409`.
  O código da exceção e o módulo não estabelecem a causa raiz.
- A tentativa de persistir a falha também encontrou o banco em recuperação;
  a UI recebeu 503 ao consultar o andamento e informou que não reenviaria.
- A captura está em `inference_api/.local/spec013-openai-ui-attempt1-20261105.png`;
  log local em `inference_api/.local/spec013-bancada-restart-20261105.err.log`.

## Recuperação

O cluster isolado 5544 foi iniciado pelo script existente, com stdin fechado
e stdout/stderr em arquivos persistentes, em processo sem janela. Isso é
recuperação operacional, não prova de correção da causa raiz. Não houve novo
clique, repetição de POST ou substituição silenciosa da tentativa.

O PostgreSQL voltou a aceitar conexões às 22:54:53. O readback encontrou o job
em `accepted`, com `run_id=null`. Após confirmar a falha do worker antes do
modelo, foi reconciliado individualmente para `interrupted`; o readback
confirmou zero jobs ativos. Recibo privado:
`inference_api/.local/spec013-openai-ui-attempt1-reconciliation-20261105.json`,
SHA-256 `52e5819f4ef00fedcfca0750fdf5df320943d99a4a9385ff15271cfa9d50a075`.

A primeira tentativa não atende ao gate de cadeia completa. As repetições
seguintes e a auditoria final seguem pendentes. SPEC continua `in_progress`,
sem pontuação científica.
