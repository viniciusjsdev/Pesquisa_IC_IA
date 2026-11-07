# SPEC-012: ensaio real OpenAI + pacote DW pela Bancada — 26/10/2026

Base do checkout: `13d7df5c748f79387d34f39cd30b6cf82c96c869`, com alterações locais não commitadas. O pesquisador aprovou em 26/10/2026 a retenção local vigente (snapshot integral sem TTL ou remoção automática, acessível a Vinicius e Nicoli). O revisor independente aprovou tecnicamente os modos OpenAI + DW antes deste ensaio; o parecer está em [review_dw.json](review_dw.json). Esta execução externa tem recibo próprio e não substitui a revisão.

## Execução pela Bancada

- [Billing overview](https://platform.openai.com/settings/organization/billing/overview) mostrava US$ 4,67 de crédito e recarga automática desligada antes da chamada. Esse valor arredondado não prova cobrança exata.
- Pela Bancada autenticada como Vinicius, foram escolhidos `openai · gpt-6-luna`, modo `Pacote fixo da DW`, e o candidato `integrado-produto-2020-01` com SHA-256 do corpo `ba57ab3d37a191c6e2be91622e975ae93794117828ad357dee6c8f51cb0f346c`. O fingerprint declarado da DW coincide com a carga local: `64493abfdfd0b87535778eafd9d5938fad6039a99d9307f85e4cfc6eec0e89f2`.
- Pergunta do pacote: “Como se comparam operacoes e vendas deste produto em 2020, e ha observacoes de resultado financeiro no ano?” O prompt da Bancada foi “Responda somente com base nas evidências fornecidas. Cite os IDs usados e explicite limites.” O backend acrescentou sua orientação fixa de evidência.
- Uma única ação “Executar uma vez” criou o job `e1f88b86-9adb-4c58-b7a1-fcab0dfb2ceb`. O destino configurado foi `https://api.openai.com/v1/responses`. Foram enviados a pergunta, o prompt e os **2.762 bytes exatos** do pacote candidato selecionado; não houve chamada de tool nem nova consulta à DW durante esse run. Nenhum CSV bruto, banco completo, gabarito, peso ou segredo foi enviado.

## Readback

| Campo | Observado |
| --- | --- |
| Job / run | `e1f88b86-9adb-4c58-b7a1-fcab0dfb2ceb` `completed` → `f7beaf30-1ff4-4ae3-a849-a38792f21c7b`, criado em `2026-10-26 04:16:01 UTC` |
| Estado | `answered_unverified`, sem erro, um turno Responses, modelo solicitado e servido `gpt-6-luna`, `store:false` |
| Resposta | Produto `1000001` em 2020: 6.168 linhas de operação, 611.785 unidades reportadas, uma linha de venda, valor observado 53.161,6 unidades monetárias; nenhuma observação financeira no ano. A resposta ressalvou que ausência de observação não é zero e não inferiu receita ou lucro anual. |
| Pacote | SHA-256 do corpo acima; SHA-256 dos bytes do arquivo `5f23f344cb45f5601beba7b40994117c6711bc3289da589c6c110d9ebe61be0b`; 2.762 bytes; dois itens de evidência |
| Uso informado | 826 tokens de entrada, 358 de saída (132 de raciocínio), 1.184 no total; 0 tokens de entrada em cache |
| IDs do provedor | `req_e6cb82dc7787475e8484b6075c8447d7` / `resp_0e282fc1057c6b42016aded3fb053887d29a85802e14d7be22` |

O readback ligou o job concluído ao run persistido. Os bytes do pacote guardados no snapshot, após decodificação, são **idênticos** aos do arquivo candidato conferido por ID/hash. O snapshot registra autor, pergunta, prompt, pacote, fingerprint, destino, modelo servido, uso, IDs e resposta. Os valores citados acima estão no pacote; isso é uma conferência pontual de fidelidade, não um gold set ou validação científica. O estado `answered_unverified` permanece apropriado.

Um adendo independente, somente de leitura, confirmou o mesmo job/run no banco da aplicação, os hashes e bytes do pacote, o uso, os IDs e a ausência de tools ou marcadores de segredo; não executou nova inferência nem nova consulta à DW. Após a decisão de retenção e a revisão DW, `INFERENCE_OPENAI_DW_ENABLED=1` foi gravado em `BancoModeloUse/.env.local`, ignorado pelo Git. Um backend iniciado de novo exibiu o Luna e os dois modos DW na Bancada autenticada; o histórico reabriu este run. O padrão do código permanece desligado para outros ambientes.

Pelo [preço Standard publicado para o Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) em 25/10/2026, o custo estimado desse uso é **US$ 0,0002616** (`826 × 0,10 / 1.000.000 + 358 × 0,50 / 1.000.000`). Não é um débito confirmado pela conta. Não houve repetição automática.
