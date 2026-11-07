# SPEC-013 · ensaio I1 integrado interrompido · 02/11/2026

O [recibo de transmissão](m2-groq-real-data-approval.json) vincula a aprovação
do usuário ao SHA-256 exato do
[contrato de transmissão](m2-groq-real-data-transmission-review-2026-11-02.md).
A chave local foi habilitada somente nos processos de ensaio. Nenhum GPT ou
RunPod foi chamado.

1. [Sonda de uma chamada](m2-groq-i1-one-call-probe-2026-11-02.json): Groq/Qwen
   validou a saída JSON do primeiro papel, `analista_pergunta`. Orçamento de uma
   chamada e zero consultas; resultado final `contract_error` esperado por
   limite. O trace completo está privado, com hash no recibo.
2. Ensaio I1 pela rota HTTP local criou o job
   `e4a461ee-030a-4177-829b-a14a473b9180`. A execução chegou a
   `storage.create_run`, depois de `agent_harness.run`. O PostgreSQL isolado em
   `127.0.0.1:5544` fechou conexões e entrou em recuperação; o GET do job
   respondeu 503. Eventos Windows Application Error 1000 e WER 1001, em
   02/11/2026 16:51:35–16:51:44 -03, identificam falhas de `postgres.exe`
   (`ucrtbase.dll`, exceção `0xc0000409`). Isso não identifica a causa raiz.
3. O cluster isolado foi reiniciado com
   `BancoModeloUse/scripts/local_postgres.py start`. O log confirmou recuperação
   automática e serviço pronto em 16:53:04 -03. Leitura posterior encontrou o
   job `running`, sem `run_id` e sem novo run piloto persistido. Esse job foi
   marcado `interrupted`, com motivo e sem repetição automática.

O trace integral do ensaio integrado não foi gravado: a falha ocorreu antes de
`storage.create_run` concluir. Não há prova do número de chamadas Groq, nem
de quais consultas de dados foram concluídas; o ensaio **não** prova o caminho
positivo HTTP → PostgreSQL → trace. O código agora salva uma cópia privada de
emergência se a persistência falhar **em execuções futuras**. Essa correção não
recupera o trace perdido deste ensaio.

Próximo gate: diagnosticar a estabilidade do cluster e executar um novo run
deliberado, com novo ID, capturando trace privado e readback persistido. A
matriz de 9 casos × 3 repetições e a adjudicação humana posterior permanecem
pendentes; nenhum score científico resulta desta sonda.

Um [novo ensaio deliberado](m2-groq-i1-http-rate-limit-2026-11-02.md) foi
executado depois da recuperação e de um smoke local aprovado. Ele persistiu
job/trace, mas terminou em limite `429` antes de consultar dados. Esta seção
preserva a conclusão do primeiro ensaio e não deve ser lida como estado final
do segundo.
