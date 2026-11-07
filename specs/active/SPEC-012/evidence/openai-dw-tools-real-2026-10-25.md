# SPEC-012: ensaio real OpenAI + DW pela Bancada — 25/10/2026

Base do checkout: `13d7df5c748f79387d34f39cd30b6cf82c96c869`, com alterações locais não commitadas. Este é um ensaio exploratório posterior à [revisão independente do fluxo sintético](review.json), que **não** aprovou os modos DW. O pesquisador pediu nesta sessão uma execução pela plataforma com pergunta que exigisse a DW. A habilitação `INFERENCE_OPENAI_DW_ENABLED=1` existiu somente no processo local deste ensaio; depois o servidor foi reiniciado com `0`. Não houve mudança permanente de código ou configuração para liberar DW.

## Envio pela interface

- Bancada em `http://127.0.0.1:8765/`, sessão autenticada como Vinicius; seleção visível `openai · gpt-6-luna` e modo `LLM consulta a DW por tools`. Uma única ação “Executar uma vez” criou o job `ec7b569c-dd4d-4a3e-9bb5-8ed0242de1d6`. Não houve reenvio.
- Pergunta exata: “Quais são as observações financeiras disponíveis na DW em 2021? Consulte a DW antes de responder. Liste os valores, unidades, IDs e datas observados; indique os meses cobertos e as ressalvas. Não invente dados nem calcule um total anual.”
- Prompt da interface: “Responda somente com base nas evidências fornecidas. Cite os IDs usados e explicite limites.” O backend acrescentou sua orientação fixa de evidência. A primeira requisição à OpenAI incluiu a pergunta, esse prompt e a allowlist de cinco tools; não incluiu linhas da DW. O modelo escolheu `financial` com `{"year":2021}`. A consulta fixa leu somente `db_pesquisa_dw` em transação de leitura, e seu resultado de 2.069 bytes foi enviado à OpenAI no segundo turno.
- [Billing overview](https://platform.openai.com/settings/organization/billing/overview) exibiu US$ 4,67 de crédito e recarga automática desligada antes e depois. O saldo arredondado não é recibo de cobrança.

## Readback e limites da prova

| Campo | Observado |
| --- | --- |
| Job / run | `ec7b569c-dd4d-4a3e-9bb5-8ed0242de1d6` `completed` → `a11e5065-eb7b-42f6-8722-55c666a60e59`, criado em 25/10/2026 23:01:53 UTC |
| Resultado | `answered_unverified`, sem erro; modelo solicitado e servido `gpt-6-luna`, Responses API, `store:false` |
| Tool | Uma chamada `financial({"year":2021})`, validada e concluída; 13 linhas, 11 meses observados, 01/01 a 27/12/2021; fevereiro sem linha observada |
| Origem | `db_pesquisa_dw`, fingerprint `64493abfdfd0b87535778eafd9d5938fad6039a99d9307f85e4cfc6eec0e89f2`, contrato de consulta v1, hash `0ec1face22ebad66773b33e3961fb38252426a2caaab0ce827ce6f1fb75714b2` |
| Uso da API | Turno da tool: 533 tokens de entrada, 19 de saída; turno da resposta: 1.186 de entrada, 660 de saída; total 1.719 de entrada e 679 de saída, sem cache informado |
| IDs do provedor | Primeiro turno: `req_6d19ed0d251d4d3f9d87a3e19ebd01f0` / `resp_086d94e699bf78b4016ade8a57ca1c87d2ad712ab97a88b461`; segundo: `req_000d318df8504951867b56be4ce5b6be` / `resp_086d94e699bf78b4016ade8a5a03b487d2af13a349919773b2` |

A interface exibiu o run, a tool, o resultado e os detalhes técnicos. O readback de `run_jobs` ligou o job concluído ao run persistido. O snapshot registra pergunta, prompt, catálogo anunciado, argumentos brutos e validados, resultado da tool, fingerprint, destino, IDs, uso e resposta. Uma nova leitura fixa da DW, com o mesmo fingerprint, retornou **exatamente o mesmo resultado** guardado no trace. Uma conferência local das 13 linhas da tabela da resposta verificou correspondência de IDs, datas, lucro líquido e receita com o resultado da tool. A resposta identificou 11 meses observados, ausência de linha em fevereiro e não calculou total anual.

Pelos [preços Standard publicados para o Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) em 25/10/2026, o uso informado corresponde a **US$ 0,0005114 estimados** (`1719 × 0,10 / 1.000.000 + 679 × 0,50 / 1.000.000`), não a uma cobrança confirmada. O resultado continua exploratório: o check automático de IDs e a conferência científica de números constam `not_checked`; a conferência de tabela acima é uma verificação pontual deste run. O snapshot local guarda as linhas da DW sem expiração automática. Este ensaio não aprova a liberação geral dos modos DW, nem o harness de comparação científica.
