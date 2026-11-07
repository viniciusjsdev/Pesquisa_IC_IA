# SPEC-012: primeiro ensaio real sintético na OpenAI — 25/10/2026

Base do checkout: `13d7df5c748f79387d34f39cd30b6cf82c96c869`, com alterações locais não commitadas. Este recibo é posterior à [revisão independente do código sintético](review.json); não amplia o escopo daquela revisão.

## Pré-voo e envio

- A página [Billing overview](https://platform.openai.com/settings/organization/billing/overview) da organização Personal exibiu **US$ 4,67** de crédito e **Auto-reload is OFF** antes da chamada. Após recarregar a página depois da chamada, continuou exibindo US$ 4,67; a tela arredonda para centavos e não comprova cobrança exata.
- O backend reconheceu `OPENAI_API_KEY` sem exibir seu valor. `INFERENCE_OPENAI_DW_ENABLED` estava `false`. O PostgreSQL isolado `127.0.0.1:5544` foi iniciado sem carga, migração ou consulta à DW; o banco da aplicação tinha dois pesquisadores ativos e a tabela `runs`.
- Foi feita **uma execução** de `service.execute_run` para `provider=openai`, `model_alias=openai`, `evidence_mode=synthetic_snapshot`, limite solicitado de 2.048 tokens de saída. O caminho direto do serviço usou a identidade local existente do pesquisador Vinicius e persistiu o run; este ensaio não passou pelo login HTTP, fila de jobs ou interface visual.
- Destino: `https://api.openai.com/v1/responses`; modelo solicitado e servido: `gpt-6-luna`; `store:false`; esforço de raciocínio `medium`. Foram enviados somente a pergunta fixa “Qual foi o valor fictício em 2020?”, o prompt sintético aprovado com orientação de evidência e o JSON da fixture inventada `synthetic-v1`. O JSON de evidência tinha **237 bytes**. Não houve envio da DW, de CSV, gabarito, pesos ou resultados de treino.

## Resultado e readback

| Campo | Observado |
| --- | --- |
| Run persistido | `28815758-32c9-4751-8be7-8261bc769ed7`, criado em `2026-10-25 22:51:30 UTC` |
| Estado | `answered_unverified`, sem erro, um turno de modelo |
| Resposta | “Em 2020, o valor fictício observado foi **42 unidades fictícias**. Os dados são sintéticos; a cobertura é observada para este registro.” |
| Uso informado pela API | 160 tokens de entrada, 102 de saída (63 de raciocínio), 262 no total; 0 tokens de entrada em cache |
| IDs para reconciliação | resposta `resp_09c32352af8ef70b016ade87f010fc87d2b2020bf01885e375`; requisição `req_71df4da2b23a4dcd8ae4c346ad5c4281` |
| Readback do banco | mesmo run, `provider=openai`, `data_class=synthetic_fixture`, destino Responses, 237 bytes de evidência, um turno, resposta e uso acima |

O [preço Standard publicado para o Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) em 25/10/2026 era US$ 0,10 por milhão de tokens de entrada e US$ 0,50 por milhão de tokens de saída. Aplicado ao uso informado, o custo **estimado** desta requisição é **US$ 0,000067** (`160 × 0,10 / 1.000.000 + 102 × 0,50 / 1.000.000`). Não é um recibo de cobrança da conta; o saldo arredondado não permite apurar o débito.

O estado `answered_unverified` só confirma resposta exploratória à fixture. A chamada prova acesso da chave a esse modelo e parsing/persistência do turno real pelo serviço. Não comprova login, jobs, recuperação de UI, escolha de tool pela LLM no provedor real, modos DW ou comparação científica. Nenhuma repetição automática foi feita. A decisão de retenção local e a revisão específica dos modos DW da OpenAI continuam pendentes.
