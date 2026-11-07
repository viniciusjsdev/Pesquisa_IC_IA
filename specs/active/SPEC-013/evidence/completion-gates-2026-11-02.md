# SPEC-013 · estado para conclusão · 02/11/2026

**Escopo vigente em 05/11/2026:** a [decisão do pesquisador](engineering-scope-2026-11-05.md)
separa conclusão de engenharia e avaliação científica. SPEC-013 contrato 2
exige testes técnicos, cadeia real completa pela Bancada e auditoria Astra.
A matriz científica e a adjudicação humana das respostas ficam posteriores;
sem elas, não há score científico. OpenAI está autorizada para o piloto de
engenharia. Os estados e critérios datados abaixo são históricos quando
contrariarem essa decisão. A SPEC permanece `in_progress`.


## Atualização de 04/11/2026 · gates efetivamente abertos

Um [novo diagnóstico I3 v7](m2-i3-v7-postgres-readback-groq-limit-2026-11-04.md)
concluiu duas consultas reais e persistiu o trace: o PostgreSQL respondeu
durante e depois do ensaio. O Revisor pediu DW após o detalhe industrial e
julgou suficientes as duas evidências. A Groq retornou HTTP 429 na chamada
final do Redator; o run ficou `provider_rate_limited`, sem resposta ou score.
Isso remove a queda do banco como bloqueio observado **nesse ensaio**, mas
não explica sua causa anterior nem fecha o gate de cadeia v7 completa.

As aprovações do recorte, política piloto, contrato semântico, nove contratos
executáveis v4 e transmissão delimitada à Groq/Qwen estão registradas. Não
precisam ser solicitadas novamente. O modo piloto, catálogo, tools, motor,
trace, UI e avaliador conservador existem e passaram nos testes locais. Um
diagnóstico anterior completou uma cadeia HTTP/Groq/DW, mas o protocolo
comparável atual é v7. Os runs v6 são diagnósticos históricos.

Para `done` no contrato atual, faltam exatamente:

1. Resolver ou contornar de modo verificável a instabilidade do PostgreSQL
   isolado e completar pelo menos um run v7 por HTTP/job/Groq/consulta/trace.
   O [diagnóstico de 04/11](m2-i3-v7-postgres-interruption-2026-11-04.md)
   terminou antes da primeira consulta, com snapshot de emergência e job
   `interrupted`; o smoke local de três bancos passou após a recuperação.
2. Congelar e executar a matriz aprovada de I1–I3, F1–F3 e X1–X3, três
   repetições cada, sob os mesmos hashes de casos, mapas, contratos, dados,
   prompts e limites. Registrar toda falha sem repetição silenciosa e explicar
   qualquer exclusão. Dois diagnósticos v7 anteriores foram limitados pela
   Groq; ainda não há uma matriz v7.
3. Entregar os snapshots e referências privadas à pessoa revisora e registrar
   por `run_id`/hash a decisão humana sobre cálculo e conclusão de cada run
   pontuável. Os checks automáticos de rota/citação não substituem essa
   adjudicação. Registrar também a revisão do relatório científico, se houver
   interpretação comparativa; com apenas Qwen neste piloto, não afirmar
   superioridade entre modelos.
4. Completar os gates de validação do manifest e obter a revisão técnica
   independente prevista em `SPEC.execution.json`, incluindo segurança,
   compatibilidade, isolamento do gabarito e comparabilidade. Registrar
   `completion.json` e `review.json` válidos; então atualizar `SPEC.md` e o
   manifest para `done`.

O restante deste documento preserva a sequência histórica de 02/11 e não
substitui a atualização acima.

O estado verificável é `in_progress`. A aprovação humana do recorte, da política,
do conteúdo de I1–I3/F1–F3/X1–X3 e do contrato semântico local está registrada
em recibos separados. A aprovação semântica autorizou **leitura local**, não
transmissão de detalhe industrial/financeiro a Groq, OpenAI ou RunPod.

**Atualização posterior no mesmo dia:** o pesquisador aprovou a [v4 exata dos
nove casos](m3-executable-case-activation-2026-11-02.md) e o
[envio delimitado à Groq/Qwen](m2-groq-real-data-approval.json). Os gates 2 e 3
de autorização/revisão foram satisfeitos. Uma chamada Groq validou o primeiro
papel, mas o [ensaio I1 integrado](m2-groq-i1-http-interruption-2026-11-02.md)
foi interrompido pela queda do PostgreSQL antes da persistência do run. Os
gates 1, 4 e 5 seguem abertos. A v5 privada habilita o avaliador a receber
casos aprovados, mas cada run ainda exige adjudicação humana.

Um segundo I1 [persistiu job e trace](m2-groq-i1-http-rate-limit-2026-11-02.md),
o que comprova parte do gate 1. O `429` no quarto papel encerrou o run antes
de consultar banco (`queries=0`); o caminho positivo completo de dados e
resposta permanece aberto. O avaliador retornou `not_scored`.

## Concluído no escopo local

- Motor de papéis JSON, correção limitada, trace, jobs e visualização com fixture.
- Catálogo piloto de 12 fontes aprovado e lido com `spec013_reader` nos três
  bancos, sem join entre bases nem SQL do modelo.
- [Cadeia local](m2-approved-catalog-local-chain-2026-11-02.json) de 17 chamadas
  com modelo programado, catálogo aprovado e três consultas reais.
- Nove contratos privados de caso derivados de pacote de conteúdo aprovado,
  com referências reexecutadas e [versão v4 ligada aos mapas aprovados](m3-approved-map-binding-2026-11-02.md),
  ainda sem score.
- Exportação candidata do cenário A para DW V2 por `--dw-v2`, com pacote v1
  histórico preservado e escopo de readback V2 explícito.
- Modo piloto no backend e na UI, bloqueado por recibo de transmissão e chave
  local. O POST HTTP sem aprovação retorna 400 antes de criar job.
- Suítes Python: `model_evaluation` 19/19; `inference_api` 115 testes com 8
  opcionais ignorados na execução que passou. Duas execuções anteriores da
  suíte API tiveram interrupção intermitente `WinError 10053` em testes HTTP
  locais diferentes; não há atribuição causal estabelecida.
- Frontend: typecheck, lint, 9 testes e build passaram com Node local; os quatro
  comandos exigidos pelo manifesto foram repetidos via `validate_frontend.py`.

## Gates para `done` da SPEC atual

1. Validar o caminho positivo por HTTP autenticado, job, PostgreSQL e trace do
   modo `agent_harness_pilot`. O caminho negativo passou: sem autorização,
   o POST retorna 400 antes de criar job ou chamar provedor.
2. Testar modelo real no fluxo integrado apenas após revisão e autorização
   específica de destino, classe e payload; o consentimento local atual não
   cobre esse envio. Manter GPT/RunPod sem uso sem autorização própria.
3. Revisar o contrato executável v4 de cada caso; o vínculo técnico aos mapas
   foi gerado, mas o recibo de conteúdo anterior não aprova essa nova versão
   para pontuação.
4. Executar a matriz sob dados/prompts/limites congelados, com as repetições
   aprovadas, e obter adjudicação humana de cálculo e conclusão em cada run.
   Até lá, `not_scored` e nenhuma comparação científica.
5. Obter a revisão técnica independente exigida pelo manifesto após os
   ensaios autorizados e a adjudicação humana dos resultados.

Marcar `done` antes desses gates contrariaria AC-005, AC-007 e AC-008 da
[SPEC](../SPEC.md) e o
[protocolo de validação humana](../../../../docs/protocolo_validacao_humana_avaliacao.md).
