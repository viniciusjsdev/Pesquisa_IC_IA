# DataMind: alertas de IA com rastreabilidade

**Estado: conceito de produto, fora da base analítica atual.** A área IA do
[painel de referência](https://kkh7ikcyoxgn.manus.space/) está em modo offline.
Seus valores visíveis não demonstram previsões executadas nem resultados
medidos. Os nove CSVs simulados recebidos no commit foram retirados do checkout
e arquivados fora do projeto com inventário e SHA-256. O histórico do Git
também preserva sua versão original. Eles não integram o conjunto canônico
de ingestão atual.

Na máquina onde esta revisão foi feita, o arquivo histórico está em
`D:\Projetos\Github_ViniciusJ\_arquivo_Pesquisa_IC_IA\historico\Pesquisa_IC_IA_legacy_archive_20261011\BancoModeloUse\future_ia_csv_20261029`.
O caminho não é portátil; `inventory.json` nessa pasta lista os nove CSVs,
linhas e hashes conferidos após a cópia.

## Ideia

Mostrar alertas ou sugestões produzidos por modelos de aprendizado de máquina
e permitir seguir cada caso até uma decisão humana e um resultado mensurado.
O produto deve distinguir previsão, recomendação, ação e efeito; exibir a
origem dos dados e o grau de evidência de cada afirmação.

## Contrato de dados para uma futura implementação

| Registro | Campos mínimos | Para que serve |
| --- | --- | --- |
| Versão do modelo | `modelo_versao_id`, `modelo_id`, versão, treino, vigência e fonte | Identificar o modelo efetivamente disponível no instante do alerta. |
| Insight/alerta | `insight_id`, `modelo_versao_id`, instante, alvo, tipo, confiança e evidência | Rastrear o que foi previsto ou recomendado. |
| Ação | `acao_id`, `insight_id`, instante, responsável, estado e evidência de execução | Separar recomendação de ação realizada. |
| Resultado | `resultado_id`, `acao_id`, período, linha de base, valor observado, unidade e método | Medir efeito sem equiparar economia estimada a economia realizada. |

Uma ligação por proximidade de data, máquina ou mês é apenas hipótese; não vira
chave causal. Um insight sem ação comprovada pode ser exibido como pendente.
Uma ação sem resultado medido não recebe economia realizada. Versões de modelo
sem histórico temporal não devem ser atribuídas retroativamente a insights.

## Critério para voltar ao escopo da base

Definir a fonte e o significado de cada campo, obter registros com IDs e
datas coerentes, validar chaves e cobertura, e aprovar separadamente a
ingestão e as métricas. Até lá, não criar tabelas de IA na DW corrente nem
alimentar indicadores da seção IA com os números demonstrativos do painel.
