# M1 · persistência local da fixture no PostgreSQL (01/11/2026)

`inference_api/scripts/verify_spec013_storage_local.py` executou a cadeia
sintética com transporte de modelo substituído por `ScriptedModel`. O serviço
gravou um snapshot v6 no `db_inference_app`; o teste leu esse run de volta,
criou um job com chave de envio, confirmou idempotência, passou por
`accepted → running → completed` e leu o job de volta. A cadeia registrou
12 chamadas e duas consultas **somente à fixture**.

O [recibo JSON](m1-postgres-storage-readback-2026-11-01.json) confirma todos
os readbacks e a limpeza verificada dos UUIDs criados por este ensaio.
O teste não chamou Groq/OpenAI/RunPod nem consultou os bancos de pesquisa;
não exercitou autenticação HTTP real nem browser com esse run persistido.
O smoke de navegador com snapshot v6 mockado está em
[outra evidência](m1-index-detail-navigation-2026-11-01.md).
