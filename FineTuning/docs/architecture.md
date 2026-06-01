# Arquitetura do Projeto (Multi-Fine-Tuning v1)

## Objetivo
Evoluir o projeto para suportar múltiplos fine-tunings (`FT-Híbrido`, `FT-FinQA`, `FT-Failure`) com configuração centralizada, artefatos isolados por run e documentação rastreável.

## Fluxo
1. EDA/Análise (notebooks existentes)
2. Preparação e padronização (notebooks existentes)
3. Snapshot de datasets por experimento (`data/processed/*`)
4. Treinamento parametrizado (`finetune_qwen_wsl/2_treinar_wsl.py`)
5. Avaliação em lote (`finetune_qwen_wsl/5_avaliar_batch_wsl.py`)
6. Demo qualitativo (`finetune_qwen_wsl/3_testar_wsl.py`) e inferência (`4_inferencia_wsl.py`)
7. Documentação de modelos e resultados (`docs/`)

## Estruturas principais
- `configs/`: configurações de treino e avaliação
- `data/processed/`: datasets versionados por experimento
- `data/manifests/`: manifests e hashes dos datasets
- `results/experiments/`: artefatos por experimento/run
- `finetune_qwen_wsl/common/`: utilitários reutilizáveis
- `docs/`: protocolo, arquitetura, matriz de avaliação, docs por modelo
