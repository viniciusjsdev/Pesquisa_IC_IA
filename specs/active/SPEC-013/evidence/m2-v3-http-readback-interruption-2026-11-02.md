# SPEC-013 · primeiro I1 com contrato v3 interrompido no readback

O job `70ce3518-1379-45ec-859e-cd96a962471c` foi aceito para o diagnóstico
I1 com contrato v3 e espaçamento de 20 segundos entre chamadas Groq. Durante
o acompanhamento, o GET do job recebeu HTTP 503 por erro de conexão local.
O script anterior encerrava imediatamente em qualquer código diferente de 200;
ao encerrar o processo, o worker em thread daemon deixou de existir.

A leitura posterior do cluster isolado `127.0.0.1:5544` funcionou. O processo
PostgreSQL continuava ouvindo na porta e não houve novo evento Windows de
falha de `postgres.exe` nesse intervalo. O log registrou erros WinSock 10053/
10054 do cliente, mas não estabelece sua causa. O job foi encontrado em
`running`, sem `run_id`, e marcado `interrupted` apenas para esse ID. Não há
trace persistido do run; número de chamadas ao provedor e estado das consultas
são desconhecidos. Não houve repetição automática.

O script de ensaio agora preserva um recibo privado de intenção com
`request_key` antes do POST e tolera falhas transitórias **somente nos GETs**
de acompanhamento e readback. Ele não repete o POST nem chamadas Groq. O
primeiro v3 continua fora da matriz e sem score.
