# M1 · HTTP autenticado com PostgreSQL local (01/11/2026)

`inference_api/scripts/verify_spec013_http_postgres.py` executou o modo
`agent_harness` pela API HTTP local, com autenticação substituída por uma
identidade de teste, modelo `ScriptedModel` e armazenamento PostgreSQL real
da Bancada. O resultado foi lido de volta pelo endpoint de run; o job foi
consultado pelo endpoint próprio e o mesmo `request_key` não criou segundo
job. A execução registrou 12 chamadas de papel e duas consultas à fixture.

O [recibo](m1-http-postgres-readback-2026-11-01.json) confirma os gates de
autenticação, idempotência, job, snapshot e remoção verificada dos UUIDs
criados. O teste não chamou Groq/OpenAI/RunPod e não abriu os bancos de
pesquisa. Ele não prova o comportamento do provedor real pela Bancada nem
habilita os mapas de dados reais.
