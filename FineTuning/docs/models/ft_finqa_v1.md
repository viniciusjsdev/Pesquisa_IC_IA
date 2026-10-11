# Modelo `ft_finqa_v1`

Especialização financeira (FinQA) do protocolo v1. Bateria A: `configs/train/ft_finqa_v1_bateria_a.yaml`; Bateria B (padrão): `configs/train/ft_finqa_v1.yaml`. Dados congelados em `data/processed/finqa_v1/`, rastreados por `data/manifests/finqa_v1.json`.

## Estado dos artefatos locais

- Rodada preliminar de 1024 tokens: `results/experiments/2026-05-31_h100_qwen25_7b_maxlen1024_prelim/runpod_import/ft_finqa_v1_run_v1_seed42/`.
- Rodada H100 de 4096 tokens: `results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/ft_finqa_v1/run_20260601_002803_seed42/`.

Ambas têm manifest local com `status: completed`, adapter e métricas de avaliação. O manifest da rodada 4096 registra `tokenization.max_length: 4096`. Compare `meta/run_manifest.json` e `metrics/*.json` da run exata antes de relatar desempenho; os recálculos posteriores em `results/recomputed_metrics/` são artefatos separados. Este status não representa nova validação do modelo.
