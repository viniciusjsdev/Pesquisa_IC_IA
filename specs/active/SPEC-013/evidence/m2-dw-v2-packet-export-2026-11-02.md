# SPEC-013 · pacote candidato DW V2 local · 02/11/2026

Comando executado em leitura local:

```powershell
BancoModeloUse/.venv/Scripts/python.exe model_evaluation/export.py model_evaluation/examples/cases_2020.json --dw-v2 --output-dir model_evaluation/.local/packets-dw-v2-spec013-2026-11-02
```

- Pacote: `integrado-produto-2020-01`, corpo SHA-256
  `e31f3e8abbd230647bb0c99c005e99f97f5e765d895625ed4a5904998be7b772`;
  arquivo SHA-256
  `bd2eb54bbc1362c16930b7aa971e1da8f1b2a24e8fb41873856617cbb14cb129`.
- Snapshot: schema V2, fingerprint
  `66f8808cf83902ff6c7fd277937bf8e0671482058f540f3ea9c1ec8c5a182800`,
  167 partições. O readback exigiu 1.200 paradas originais e 90 geradas
  ligadas a `dw.source_file`.
- Resultados: `product` 1 linha `observed`; `financial` 0 linhas
  `no_observation`. Nenhum valor de linha ou gabarito foi publicado aqui.
- `quality_summary.scope = local_dw_v2_readback`, com flags vazias. Essa
  verificação não compara novamente os 166 CSVs com os três bancos.
- `model_evaluation`: 19 testes passaram; o teste V2 também reconfirma leitura
  do pacote V1 e recusa fingerprint/partições alterados. O JSON Schema vincula
  versão V2 ao fingerprint conhecido, 167 partições e escopo de readback;
  uma segunda exportação reutilizou os bytes sem regravar o pacote.
- `inference_api`: 112 testes passaram na terceira execução (8 opcionais
  ignorados); as duas primeiras execuções tiveram `WinError 10053` intermitente
  em testes HTTP locais distintos. Esses testes passaram em execução posterior;
  não foi isolada causa no novo exportador.
- Sem chamada de LLM/provedor, sem score e sem alteração da carga.
