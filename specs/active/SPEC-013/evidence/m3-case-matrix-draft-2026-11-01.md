# M3 · matriz candidata de nove perguntas para revisão

**Estado:** rascunho de seleção, sem gabaritos ou pontuação. O
[perfil de contagens v3](m3-candidate-profile-2026-11-01-v3.json) foi produzido por
`model_evaluation/spec013_candidate_profile.py` em transação `READ ONLY` na
DW local. Ele registra apenas anos, IDs de máquina e contagens. Em 2021 há
13 paradas geradas da máquina `2000002` e 13 observações financeiras. Em
2019 e 2020 não há observações em `fact_financial_observation`. A máquina `1`
não tem fatos de operação ou parada em 2026, enquanto a máquina `1000002`
tem 28 fatos de parada em 2020.

| ID | Família / estado buscado | Pergunta candidata entre aspas | Fontes iniciais possíveis | Revisão necessária |
| --- | --- | --- | --- | --- |
| I1 | Industrial / suficiente | “Quantos minutos de parada a DW registra para a máquina 2000002 em 2021, e qual é a unidade desse total?” | `machine` | Conferir valor, filtro e interpretação do agregado. |
| I2 | Industrial / ausência | “Há registro de operação ou parada da máquina 1 em 2026 na carga consultada?” | `machine` | Conferir `no_observation`; não transformar ausência de linha em zero produzido. |
| I3 | Industrial / aprofundamento | “Qual total de paradas da máquina 2000002 a DW registra em 2021 e quais paradas geradas da mesma máquina/período aparecem no banco industrial, com origem?” | `machine`, `paradas_maquinas_geradas` | Comparar escopos sem afirmar vínculo individual por mera coocorrência. |
| F1 | Financeiro / suficiente | “Quantas observações financeiras datadas há em 2021 e qual período elas cobrem?” | `financial` | Contar observações e meses cobertos; não inferir total anual. |
| F2 | Financeiro / ausência | “Qual foi o lucro líquido reportado em 2019 na tabela de observações financeiras?” | `financial` | Confirmar `no_observation`; ausência não equivale a lucro zero. |
| F3 | Financeiro / aprofundamento | “Em 2021, o valor de vendas observadas é a mesma medida que a receita reportada nas observações financeiras?” | `financial`, `vendas` | Delimitar venda/observação por IDs e datas sem join por coincidência temporal. |
| X1 | Integrado / suficiente | “Em 2021, quais totais de parada da máquina 2000002 e quais observações de lucro líquido existem, lado a lado, sem atribuir causalidade?” | `machine`, `financial` | Conferir unidades, cobertura e proibição de atribuir lucro à máquina. |
| X2 | Integrado / ausência | “Em 2020, as paradas da máquina 1000002 e as observações financeiras disponíveis permitem comparar a evolução do lucro?” | `machine`, `financial` | A DW tem 28 paradas da máquina; a falta financeira deve impedir a conclusão. |
| X3 | Integrado / aprofundamento | “Em 2021, qual agregado de parada da máquina 2000002 está na DW, quais paradas geradas da mesma máquina/período aparecem no industrial e quais observações financeiras existem, sem atribuir relação causal?” | `machine`, `paradas_maquinas_geradas`, `financial` | Verificar filtro de período e limite de linhas; resultado lado a lado, sem join ou inferência causal. |

I3 e X3 foram redigidos para caber em até três consultas sem exigir linhagem
completa de cada evento. A checagem offline de IDs gerados na DW é evidência
do preparador, invisível ao modelo. Estas perguntas ainda não satisfazem o contrato de caso oficial: faltam filtros
fechados, consulta de referência reexecutável, fingerprint do snapshot, números,
fórmulas/tolerâncias, exclusões e revisão humana individual. I3, F3 e X3
podem exigir substituição após conferir cobertura e cardinalidade. Os perfis
v1 e v2 foram preservados como leituras intermediárias; v3 é a referência
atual desta matriz. O
pesquisador aprovou a política da matriz e assumiu a revisão futura dos
gabaritos, não aprovou estas perguntas nem qualquer resposta numérica.

Atualização posterior: o pesquisador
[aprovou o conteúdo dos nove casos](m3-human-case-content-approval-2026-11-01.md)
no pacote privado que inclui as perguntas e os valores de referência. Esta
matriz foi preservada como rascunho histórico; o vínculo executável e a
revisão de respostas de modelo continuam pendentes.
