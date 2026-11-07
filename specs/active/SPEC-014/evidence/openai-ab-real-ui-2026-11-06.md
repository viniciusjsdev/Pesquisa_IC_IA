# Ensaio real A/B pela Bancada — 06/11/2026

Autorização desta sessão: após apresentação de modelo, destino e limites, o pesquisador respondeu “Roda e me diz como ficou”. Uma execução por cenário, sem repetição automática. Finalidade: engenharia; `not_scored`.

## Configuração

OpenAI `gpt-6-luna`, perfil `openai`, raciocínio `medium`, `output_token_limit=null`, sem temperatura/seed enviados. Limites: 48 chamadas, três rodadas, 600 segundos por chamada e 32.768 bytes para entrada, saída e resultado. A: zero consultas durante o run. B: até três tentativas.

Pergunta idêntica nos dois cenários:

> Para o produto 1000001 em 2020, como se comparam os registros de operações e vendas, e quais observações de resultado financeiro existem no ano? Indique fontes, cobertura e limitações, sem atribuir causalidade.

O pacote A foi preparado antes do run por duas leituras somente leitura da DW V2 (`product`, ano 2020, ID 1000001; `financial`, ano 2020). Pacote anterior preservado. Caso `spec014-produto-2020-20261106T225722Z`; SHA-256 do corpo `abfb4cd2399babaccd153eba3f9ddcbe8b3d3ba6561dc3783e4452c245cc6483`. Há uma linha agregada do produto e zero observações financeiras. B recebeu o catálogo aprovado de 12 fontes.

## Resultado

| Cenário | Run persistido | Chamadas | Consultas | Rodadas | Resultado |
|---|---|---:|---:|---:|---|
| A | `054c8969-dbc1-4753-9372-7bb71f922b6c` | 5 | 0 | 1 | `contract_error`: `invalid_review_gap`; sem resposta final |
| B | `588697a1-e773-42e3-a6ec-9763ea003a84` | 8 | 2 | 2 | `answered_unverified`; resposta final registrada |

A atravessou Analista, Selecionador e Especialista. O Revisor pediu aprofundamento no domínio `financeiro`, mas o índice do pacote e `domains_identified` expõem apenas `dw`. A validação recusou a primeira saída e a tentativa de reparo pelo mesmo papel. O segundo item do pacote, que documenta ausência de observação financeira, não chegou a ser selecionado; o Redator não foi chamado. Esse resultado evidencia uma limitação do contexto/contrato no caminho A, sem comprovar funcionamento completo desse cenário com modelo real. As cinco chamadas OpenAI tiveram saída e recibo.

B escolheu `resultados_financeiros`, no banco financeiro, e consultou `[2020-01-01, 2021-01-01)`: zero linhas, `no_observation`. O Revisor pediu aprofundamento e o Selecionador escolheu `product` na DW. O retorno contém 6.168 operações, quantidade reportada 611.785, uma venda e valor observado 53.161,6. O Redator apresentou esses valores, fontes e ressalvas, sem tratar ausência como zero nem afirmar causalidade. Os números foram conferidos contra os retornos persistidos; isso não substitui adjudicação científica. Não houve consulta direta ao banco industrial. Os manifestos industrial/financeiro antes e depois de B coincidem.

Uso reportado: A = 6.609 tokens de entrada + 3.111 de saída (9.720 total); B = 14.130 + 4.142 (18.272 total). Tokens de raciocínio estão incluídos na saída e não devem ser somados novamente. Custo monetário não calculado.

## PostgreSQL e recuperação

Após aceite do job A (`0a1a463b-aa8b-4f98-b01a-866a197c7c11`), o PostgreSQL isolado em `127.0.0.1:5544` deixou de responder. A API preservou o snapshot em `inference_api/.local/spec013_failed_persistence/b522e62a-a068-4075-831b-7c10e3e032ae.json`. O cluster existente foi reiniciado sem recriação de bancos/credenciais. A causa da interrupção não foi determinada.

O snapshot foi reconciliado transacionalmente com o job original, verificando pergunta, identidade e inexistência de run duplicado. Seu conteúdo foi preservado e nenhuma chamada de modelo foi repetida. Job `completed` significa resultado recuperado e vinculado; o resultado do modelo continua `contract_error`. A UI confirmou o erro e a ausência de resposta final.

B foi submetido após a recuperação: job `2f84a634-330c-4d56-ae3c-2e24b6de4a56`, concluído normalmente em aproximadamente 52 segundos. A UI confirmou trajetória e resposta.

## Artefatos e fronteira do aceite

Artefatos privados: `inference_api/.local/spec014-ab-20261106T225722Z/` — manifesto, preparo, recibos específicos A/B, payloads, snapshots completos, recuperação de A, jobs e resumos. Recibos por cenário preservados; autorização ativa encerrada após os dois runs, impedindo reenvio sem nova instrução.

SHA-256 dos objetos completos de run, serializados canonicamente:

- A: `e4b7ac8474dfb8d1326155e2c27aacee994b2fcbbbd73469877b40698132fb4a`.
- B: `c2be02920d5b3b0ab7e61464d5e2a870e65caf30ad93e9c08b7d8fb2ea05bac1`.

Este ensaio complementa o aceite anterior com fixtures. Há uma falha real no caminho A e uma interrupção de infraestrutura sem causa estabelecida. Não atribuir score nem inferir superioridade de modelo. Próxima investigação: alinhar domínio, itens disponíveis e feedback do Revisor em A, com replay desta falha antes de novo envio pago. Nenhum código de execução foi alterado durante a rodada.
