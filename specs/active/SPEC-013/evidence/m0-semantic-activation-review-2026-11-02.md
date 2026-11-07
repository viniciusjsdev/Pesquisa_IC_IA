# SPEC-013 · contrato semântico para habilitar o piloto local

**Estado:** preparado para revisão humana; não é aprovação nem autorização de
envio a provedor. O [recorte de 12 fontes](m0-pilot-scope-approval-2026-11-01.md)
e a [política piloto](m0-pilot-policy-approval-2026-11-01.md) já foram aprovados.
Esta ficha registra **o significado e a saída exata** que ainda precisam de
validação antes de disponibilizar o mapa real aos agentes.

O [mapa candidato](m0-semantic-map-candidate-2026-11-01.json) permanece
`candidate_not_enabled`, SHA-256
`d2a4a30815f97a7065b9df46fcf36c9e70966cbe3e8c9f0cdd410ba7c8b0f1fb`.
O [contrato de saídas do backend](../../../../inference_api/src/inference_api/agent_harness/data_contracts.json)
tem SHA-256
`1ef705c9a42702b451f2ea18d137626d2ec11f25422400e2d1bd9390ca4e6b3b`.
Ambos estão fixados no código local. Uma alteração de bytes exige nova revisão.

## DW e linhagem

| Fonte | Grão e filtros | Campos entregues | Interpretação que precisa ser aceita |
| --- | --- | --- | --- |
| `machine` | máquina/ano; `year`, `id` | ID da máquina, contagem e quantidade reportada de operações, contagem e minutos de paradas | Minutos são duração de fatos iniciados no ano. Operações não se ligam individualmente às paradas; 90 eventos gerados entram na carga V2. |
| `product` | produto/ano; `year`, `id` | ID, operações, quantidade reportada, vendas e valor observado | Valor de vendas observadas não é receita contábil. Quantidades podem repetir etapas. |
| `financial` | observação/data; `year` | ID, data, receita e lucro reportados | São linhas datadas, com cobertura esparsa; não se deve somá-las como total anual. 2019/2020 não têm observação nessa tabela. |
| `quality` | produto/ano; `year`, `id` | ID, inspeções, unidades aprovadas/rejeitadas, excedentes | Inspeções podem repetir lote; soma de unidades não é produção única. |
| `material` | material/ano; `year`, `id` | ID, consumos, quantidade, observações e faixa de preço | Preços observados não são custo realizado; não há regra de preço por consumo. |
| `contributors` | agregado/fato; `kind`, `year`, `id`, `fact`, `after`; página de até 20 IDs | `fact`, `total`, `ids`, `next_after` | Lista IDs de fatos DW que contribuem para um agregado; `next_after` exige paginação. Não constitui vínculo causal. |
| `trace` | fato/linha de origem; `fact`, `id`; uma linha | `mapped_id`, `original_id`, `period_index`, banco/tabela/CSV/hash de origem | Mostra proveniência de um fato DW; **não** entrega `raw_record` ou `typed_record` ao agente. Para valores, usar a tool de detalhe aprovada. |

As cinco consultas são fixas e têm o código SHA-256
`f295a6ad1ec35455f3cfd297106748d86ef0faccd2fb2b46753ad7f2f054ddde`.
O fingerprint da carga DW V2 é
`66f8808cf83902ff6c7fd277937bf8e0671482058f540f3ea9c1ec8c5a182800`.

## Fontes tipadas

| Fonte | Campos autorizados | Filtros e grão | Limite de interpretação |
| --- | --- | --- | --- |
| `paradas_maquinas` | `parada_id`, `maquina_id`, início/fim, motivo, registro | ID, máquina ou intervalo de início; evento/período | 1.200 eventos originais; duração depende dos horários e regras de projeção. |
| `paradas_maquinas_geradas` | mesmos campos e `origem` | ID, máquina ou intervalo de início; evento/período | 90 eventos gerados; `maquina_id` não tem FK física aqui. |
| `registros_operacao` | ID, ordem, máquina, início/fim, setup, quantidade, energia, registro | ID, máquina, ordem ou intervalo de início; registro/período | Registros podem repetir etapas; a soma não é produção única. |
| `resultados_financeiros` | ID, data, receita total, lucro líquido | ID ou intervalo de data; observação/período | 72 linhas de cobertura esparsa; não atribuir lucro/receita a máquina ou produto. |
| `vendas` | ID, produto, quantidade, preço unitário, data, cliente | ID, produto ou intervalo de data; venda/período | Quantidade × preço é valor observado de venda; não é receita contábil. `produto_id` não tem FK física nesta tabela. |

`physical_relations` no JSON informa FKs existentes, mas **não autoriza joins**
nas tools. O piloto não executa join entre bancos; mesmo período não prova
relação entre registros. Toda fonte é limitada a 20 linhas, 32 KiB e 10 s por
consulta; um payload excedente falha explicitamente.

## Evidência técnica local

- O [serviço de consultas em leitura](m2-local-query-adapter-readback-2026-11-02-v2.json)
  testou `machine`, `financial`, `contributors`, `trace`,
  `paradas_maquinas_geradas` e `vendas` com a role `spec013_reader`, sem provedor.
- A [cadeia de três bancos](m2-local-chain-readback-2026-11-02-v2.json)
  executou 17 chamadas de papel e três consultas com modelo programado de
  teste; o maior envelope de entrada mediu 22.110 bytes, abaixo de 32 KiB.
  Isso verifica a orquestração local, não a qualidade das decisões de um LLM.
- O catálogo **em disco continua desabilitado**. Os testes usaram cópia
  habilitada apenas em memória; nenhuma fonte real foi enviada a provedor.

## Decisão humana necessária

A pessoa revisora precisa conferir se **cada linha desta ficha e cada campo do
JSON candidato** expressa corretamente grão, unidade, cobertura, filtros,
relação e ressalva para as perguntas piloto. A decisão deve citar os hashes do
mapa e do contrato de saída acima, registrar correções ou aprovação integral
e identificar a pessoa revisora/data. Aprovação desse contrato autoriza apenas
a **habilitação local** após o verificador físico; transmissão a Groq/OpenAI e
pontuação científica têm gates separados.
