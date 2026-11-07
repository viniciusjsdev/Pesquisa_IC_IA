# Diagnóstico I3 v7 em 04/11: queda do PostgreSQL isolado

O diagnóstico `i3-diagnostico-v7-20261104` começou com o protocolo v7,
Groq/Qwen autorizado e o banco local `127.0.0.1:5544` acessível. O job
`7f59d598-f3c4-45ad-9b5c-4cd73745b173` foi aceito uma única vez. Houve
nove chamadas de modelo. Antes da primeira consulta, o PostgreSQL isolado
deixou de aceitar conexões. A tool registrou `OperationalError`; o motor
terminou `contract_error`/`query_error`, com zero consultas concluídas.

A persistência normal do run também falhou. O mecanismo de emergência guardou
o snapshot privado em
`inference_api/.local/spec013_failed_persistence/dcc3d694-213b-4cf2-9683-aeec0d6fc64b.json`
com SHA-256
`f0bff864e189ee4b010cee0600f3ac02e8213fd21359c448489c06ffa7cef217`.
O `run_id` interno do harness é `dcc3d694-213b-4cf2-9683-aeec0d6fc64b`;
não há `run_id` de armazenamento associado ao job. O banco foi recuperado
localmente e o job exato foi reconciliado de `running` para `interrupted`.
O script de verificação foi encerrado depois dessa reconciliação. A pergunta
não foi reenviada, e o run permanece `not_scored`.

O log do PostgreSQL registra recuperação automática e prontidão às 13:30:56
de 04/11. O Event Viewer contém falhas de `postgres.exe` às 13:25:15 e
13:25:20 (`ucrtbase.dll`, exceção `0xc0000409`). Isso comprova falha do
processo, sem demonstrar sua causa. Como o diagnóstico parou antes do Revisor,
ele ainda não verifica se a nova projeção de contexto corrige a decisão de I3.

O verificador HTTP passa a reconhecer `interrupted` como estado terminal do
job, para permitir readback e encerramento após reconciliação manual, sem
repetir POST ou chamada de modelo. A matriz v7 ainda não começou.

Após a recuperação, um smoke local com catálogo aprovado, modelo programado
e role restrita passou por DW, industrial e financeiro: 17 chamadas, três
consultas, nenhuma chamada de provedor. Isso confirma leitura local naquele
momento; não explica a falha anterior nem demonstra estabilidade sustentada
do processo PostgreSQL. `py_compile` do verificador, esquema do manifest da
SPEC e `git diff --check` passaram.
