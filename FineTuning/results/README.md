# Resultados do FineTuning

`experiments/<protocol>/<experiment>/<run>/` reúne `meta/run_manifest.json`, `adapter/`, `metrics/` e `predictions/` quando produzidos. As duas baterias do artigo estão catalogadas abaixo. Os seis pesos finais em `adapter/` usam Git LFS. Checkpoints intermediários foram retirados da árvore ativa; predições e logs das duas baterias são preservados.

## Rodadas catalogadas

| Diretório local | Leitura |
| --- | --- |
| `experiments/2026-05-31_h100_qwen25_7b_maxlen1024_prelim/runpod_import/` | Importação da rodada preliminar com limite de 1024 tokens. O truncamento documentado limita sua interpretação. |
| `experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/` | Importação da rodada H100 com limite de 4096 tokens; contém base e as três variantes. |

Os manifests locais dos três modelos em cada rodada registram `completed`. Os diretórios dos modelos contêm adapter, métricas e predições. Para status, configuração e identidade exatos, abra o manifest de cada run; para desempenho, leia o JSON de métricas correspondente. A presença desses arquivos não equivale a validação independente.

O nome datado do diretório importado não é necessariamente o `output.root_runs_dir` registrado no manifest remoto. Para nova execução, os configs e scripts RunPod atuais usam `results/experiments/h100_qwen25_7b_maxlen4096/` por padrão, sob o checkout remoto. Consulte [runpod/README.md](../../runpod/README.md).

`recomputed_metrics/2026-09-14_failure_multilabel_v2/` contém o recálculo multirrótulo usado pelo artigo, separado das métricas originais. Compare proveniência, script e versão antes de citar qualquer resultado. Não sobrescreva os JSONs originais para trocar a definição de métrica.
