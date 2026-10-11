# Modelo `ft_hibrido_v1`

Especialização conjunta em FinQA e FailureSensorIQ do protocolo v1. Bateria A: `configs/train/ft_hibrido_v1_bateria_a.yaml`; Bateria B (padrão): `configs/train/ft_hibrido_v1.yaml`. Dados congelados em `data/processed/hybrid_v1/`, rastreados por `data/manifests/hybrid_v1.json`.

## Estado dos artefatos locais

- Rodada preliminar de 1024 tokens: `results/experiments/2026-05-31_h100_qwen25_7b_maxlen1024_prelim/runpod_import/ft_hibrido_v1_run_v1_seed42/`.
- Rodada H100 de 4096 tokens: `results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/ft_hibrido_v1/run_20260601_002803_seed42/`.

Ambas têm manifest local com `status: completed`, adapter e métricas de avaliação. O manifest da rodada 4096 registra `tokenization.max_length: 4096`. Consulte manifest e JSONs de métricas da run exata antes de citar resultados; este status não representa nova validação do modelo.
