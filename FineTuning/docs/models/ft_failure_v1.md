# Modelo `ft_failure_v1`

Especialização industrial (FailureSensorIQ) do protocolo v1. Bateria A: `configs/train/ft_failure_v1_bateria_a.yaml`; Bateria B (padrão): `configs/train/ft_failure_v1.yaml`. Dados congelados em `data/processed/failure_v1/`, rastreados por `data/manifests/failure_v1.json`.

## Estado dos artefatos locais

- Rodada preliminar de 1024 tokens: `results/experiments/2026-05-31_h100_qwen25_7b_maxlen1024_prelim/runpod_import/ft_failure_v1_run_v1_seed42/`.
- Rodada H100 de 4096 tokens: `results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/ft_failure_v1/run_20260601_002803_seed42/`.

Ambas têm manifest local com `status: completed`, adapter e métricas de avaliação. O manifest da rodada 4096 registra `tokenization.max_length: 4096`. A definição multirrótulo de FailureSensorIQ está documentada em `docs/protocol_v1.md`; há recálculos locais separados em `results/recomputed_metrics/`. Confira a proveniência antes de usar métricas antigas ou recalculadas. Este status não representa nova validação do modelo.
