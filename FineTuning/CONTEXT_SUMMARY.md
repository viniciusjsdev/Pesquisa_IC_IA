# CONTEXT_SUMMARY.md

Resumo central do projeto para handoff entre IAs (Codex/Cursor/CLI).

## 1) Objetivo do projeto
Fine-tuning multi-dominio do `mistralai/Mistral-7B-Instruct-v0.3` com protocolo experimental v1 para comparar:
- `Base`
- `FT-Hibrido`
- `FT-FinQA`
- `FT-Failure`

Objetivos experimentais:
- generalizacao cruzada entre dominios
- transferencia de raciocinio numerico
- ganho vs baseline

## 2) Leitura recomendada (ordem)
1. `AGENTS.md`
2. `docs/protocol_v1.md`
3. `docs/architecture.md`
4. `docs/experiments/matriz_avaliacao.md`
5. `configs/train/base.yaml`
6. `configs/train/ft_hibrido_v1.yaml`
7. `configs/train/ft_finqa_v1.yaml`
8. `configs/train/ft_failure_v1.yaml`
9. `configs/eval/base.yaml`
10. `data/manifests/hybrid_v1.json`
11. `data/manifests/finqa_v1.json`
12. `data/manifests/failure_v1.json`
13. `finetune_mistral_wsl/2_treinar_wsl.py`
14. `finetune_mistral_wsl/5_avaliar_batch_wsl.py`
15. `finetune_mistral_wsl/common/config_utils.py`
16. `finetune_mistral_wsl/common/dataset_utils.py`
17. `finetune_mistral_wsl/common/metrics.py`

## 3) Estrutura canonica (usar)
- `configs/` -> protocolo de treino/avaliacao
- `data/processed/*_v1/` -> datasets congelados por experimento
- `data/manifests/*.json` -> rastreabilidade/hashes
- `runs/<experiment>/<run>/` -> artefatos por run
- `docs/` -> protocolo + relatorios por modelo

## 4) Estrutura legado (nao usar para novos experimentos)
- `data_ft/` -> origem historica
- `finetune_mistral_wsl/output/` -> outputs do fluxo antigo
- `runs/ft_hibrido_legacy/` -> catalogo do modelo legado pre-v1

## 5) Comandos principais
### 5.1 Preparar datasets versionados
```bash
python finetune_mistral_wsl/prepare_experiment_datasets.py
```

### 5.2 Treinar (atalho por modelo)
```bash
python finetune_mistral_wsl/2_treinar_wsl.py --modelo finqa --dry-run
python finetune_mistral_wsl/2_treinar_wsl.py --modelo finqa

python finetune_mistral_wsl/2_treinar_wsl.py --modelo failure --dry-run
python finetune_mistral_wsl/2_treinar_wsl.py --modelo failure

python finetune_mistral_wsl/2_treinar_wsl.py --modelo hibrido --dry-run
python finetune_mistral_wsl/2_treinar_wsl.py --modelo hibrido
```

### 5.3 Avaliar em lote (oficial)
```bash
python finetune_mistral_wsl/5_avaliar_batch_wsl.py --run-dir runs/ft_finqa_v1/<run_name> --compare
python finetune_mistral_wsl/5_avaliar_batch_wsl.py --run-dir runs/ft_failure_v1/<run_name> --compare
python finetune_mistral_wsl/5_avaliar_batch_wsl.py --run-dir runs/ft_hibrido_v1/<run_name> --compare
```

## 6) Invariantes obrigatorias
- nao mudar split durante a bateria experimental
- manter mesmo protocolo de inferencia na comparacao
- registrar tudo em `runs/.../meta/run_manifest.json`
- usar `configs/*.yaml` (nao hardcode no codigo)
- executar `--dry-run` antes do treino real

## 7) Saidas esperadas por run
- `adapter/`
- `checkpoints/`
- `logs/`
- `metrics/` (`summary.json`, `finqa.json`, `failure.json`, `cross_domain.json`)
- `predictions/*.jsonl`
- `meta/run_manifest.json`

## 8) Estado atual (resumo)
- Reestruturacao v1 implementada
- Configs de treino/avaliacao criadas
- Datasets versionados e manifests criados
- Run manifests de dry-run existem para os 3 modelos v1
- Catalogo de legado criado em `runs/ft_hibrido_legacy/`

## 9) Arquivos de status por modelo
- `docs/models/ft_finqa_v1.md`
- `docs/models/ft_failure_v1.md`
- `docs/models/ft_hibrido_v1.md`

## 10) Texto curto para handoff para outra IA
"Leia primeiro `CONTEXT_SUMMARY.md`, depois `AGENTS.md` e `docs/protocol_v1.md`. Siga apenas o protocolo v1, trate `data_ft/` e `finetune_mistral_wsl/output/` como legado, e registre qualquer execucao em `runs/<experiment>/<run>/meta/run_manifest.json`."
