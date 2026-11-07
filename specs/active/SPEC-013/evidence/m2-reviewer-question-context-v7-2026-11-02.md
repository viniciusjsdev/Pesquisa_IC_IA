# SPEC-013: pergunta e domínios na chamada do Revisor

Na primeira leva v6, I1-r1 concluiu com rota e referência automáticas válidas.
I2-r1 terminou em `insufficient_evidence`, com rota e referência 0. I3-r1
respondeu depois de consultar somente `paradas_maquinas_geradas`, embora o
caso aprovado exija também o agregado `machine` da DW. Os três snapshots
privados e recibos públicos foram preservados; nenhum recebeu revisão humana
ou score científico.

O trace I3 mostra uma perda objetiva de contexto entre papéis. A pergunta
literal pede o total que a **DW** registra e as paradas geradas no
**industrial**. A1 identificou ambos os domínios e a necessidade de total e
lista. O Revisor recebeu a necessidade resumida e uma única evidência
industrial, mas não recebeu a pergunta literal nem os domínios identificados
por A1. Concluiu `suficiente` por interpretar a contagem industrial como o
total da pergunta. A decisão é do modelo, mas o contrato lhe omitiu a
distinção de origem que ele deveria julgar.

O próximo contrato do Revisor inclui `question` literal e
`domains_identified` de A1, além da necessidade, do resultado atual e das
evidências anteriores. A tarefa do papel pede conferir cada parte da pergunta
contra fonte, grão e cobertura, sem presumir que uma contagem industrial
substitui o agregado pedido à DW. O backend continua validando formato,
referências e limites; não escolhe a fonte nem decide suficiência pelo modelo.
Essa revisão altera os bytes dos contratos e exige um protocolo v7 separado.
Os runs v6 permanecem diagnósticos; não há repetição automática nem
reclassificação retroativa.

| Run v6 | `run_id` | Estado | Chamadas / consultas | SHA-256 do snapshot privado |
| --- | --- | --- | --- | --- |
| I1-r1 | `9916f37b-05ec-4c99-8d68-03f5ed5446db` | `answered_unverified` | 10 / 1 | `1d871186525f7a87f87d24d19d61d139b95a068be08636d62c3891f02d139065` |
| I2-r1 | `633b10fd-d9b8-40c8-a15a-62ba4c49fdfe` | `insufficient_evidence` | 14 / 2 | `c84bb9a406145009a81237635a8d6e27c7b8a82274e780ec2ab0e671c61fd37b` |
| I3-r1 | `c251a9fe-2dc2-40b1-a1f9-ed40c4ffefeb` | `answered_unverified` | 11 / 1 | `cffd793234fd03a8aea61a55b1c7b7a42e3904c19ca7518a88a3027987361ed7` |

Os testes locais do motor passaram (32 casos) e a cadeia programada com
três bancos passou (17 chamadas, 3 consultas, maior input 15.068 bytes).
O protocolo v7 fixa `contracts.json` SHA-256
`f3387fa41fce155ad6767862bd167ae899897fce92ff9515831d09a6f0c1eb95`
e `input_contracts.json` SHA-256
`b5498e5c2d093e07b11bdd6d66cd7ad526073202ff1777b77756f95d54b29ba1`.

O diagnóstico real `i3-diagnostico-v7` não alcançou o Revisor: o Selecionador
recebeu HTTP `429` com `Retry-After: 207`, após oito chamadas de modelo e
antes de qualquer consulta. Job `1ed00a5b-7894-4d01-978f-ebc31bcfc223`,
run `bbae3151-8cd9-4a59-a014-69f918ffd291`, snapshot privado SHA-256
`a0ba13db7755ea657639c2f0569027c299950997482bec3e753b5c23439f8956`.
Estado `provider_rate_limited`, `not_scored`; não houve repetição automática.
O teste local comprova a passagem do contexto, mas o resultado real não
comprova ainda a nova decisão do Revisor.

Após ultrapassar aquele prazo, um novo diagnóstico com rótulo próprio,
`i3-diagnostico-v7-pos429`, teve uma primeira chamada válida e recebeu outro
HTTP `429` na segunda, com `Retry-After: 363`. Job
`ba79f515-73b0-4c96-b3c4-726567444fd0`, run
`53bfd64f-1a18-490b-9bf3-31e0f68e5d1a`, duas chamadas, zero consultas,
snapshot privado SHA-256
`e2d477d8b58e29c6c8f44c72b4a02a26f7aa08399d7622a3371e23036ba26386`.
As chamadas externas foram interrompidas. O limite observado não permite
concluir a matriz v7 neste momento; nenhum ensaio falho será contado como
resposta revisada ou repetido automaticamente.
