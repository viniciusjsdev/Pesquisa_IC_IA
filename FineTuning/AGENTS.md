# AGENTS.md - Regras para IAs no projeto FineTuning

## 0) Entrada recomendada
Antes de qualquer acao, leia `CONTEXT_SUMMARY.md` para contexto unificado e ordem de leitura.

## 1) Escopo e objetivo
Este repositorio implementa fine-tuning multi-dominio do `mistralai/Mistral-7B-Instruct-v0.3` com protocolo experimental v1.
Modelos-alvo:
- `ft_hibrido_v1`
- `ft_finqa_v1`
- `ft_failure_v1`

Objetivo operacional de IA neste repo:
- manter comparabilidade cientifica entre modelos
- preservar reprodutibilidade
- evitar regressao para paths hardcoded e saidas misturadas

## 2) Fontes de verdade (ordem de prioridade)
1. `docs/protocol_v1.md`
2. `configs/train/*.yaml` e `configs/eval/*.yaml`
3. `data/manifests/*.json`
4. `runs/<experiment>/<run>/meta/run_manifest.json`
5. `docs/architecture.md` e `docs/experiments/matriz_avaliacao.md`

Se houver conflito entre scripts e docs, a IA deve alinhar para o protocolo v1 e registrar ajuste.

## 3) Estrutura canonica (nao legado)
- `configs/`: configuracao de treino e avaliacao
- `data/processed/*_v1/`: datasets congelados por experimento
- `data/manifests/*.json`: rastreabilidade e hashes
- `runs/<experiment>/<run>/`: artefatos por execucao
- `finetune_mistral_wsl/common/`: utilitarios compartilhados
- `docs/`: protocolo, arquitetura e documentacao de modelos

## 4) O que e legado
- `data_ft/`: origem historica dos dados preparados
- `finetune_mistral_wsl/output/`: artefatos do fluxo antigo
- `runs/ft_hibrido_legacy/`: catalogacao do modelo legado

Regra: legado e somente referencia historica. Novos treinos e avaliacoes devem usar `data/processed`, `configs/*` e `runs/*`.

## 5) Contratos de dados
Formato esperado de amostra JSONL:
- `prompt` (str)
- `resposta` (str)
- `meta` (obj)

Campos importantes em `meta`:
- `dataset`: `FinQA` ou `FailureSensorIQ`
- `program` (FinQA, quando existir)
- `id` (quando existir)

Regras:
- nao editar manualmente `data/processed/*_v1/*.jsonl`
- para regenerar datasets versionados, usar:
  - `python finetune_mistral_wsl/prepare_experiment_datasets.py`
- preservar splits `train/val/test`
- preservar `meta.dataset` para filtros de dominio

## 6) Contratos de treino
Script oficial: `finetune_mistral_wsl/2_treinar_wsl.py`

Atalhos suportados:
- `--modelo hibrido`
- `--modelo finqa`
- `--modelo failure`

Regras:
- preferir `--modelo` (nao hardcode de config no script)
- executar `--dry-run` antes de treino real
- usar apenas configs de `configs/train/`
- nao alterar hiperparametros no codigo; alterar YAML
- salvar tudo em `runs/<experiment>/<run>/...`

Exemplos:
- `python finetune_mistral_wsl/2_treinar_wsl.py --modelo finqa --dry-run`
- `python finetune_mistral_wsl/2_treinar_wsl.py --modelo finqa`

## 7) Contratos de avaliacao
Script oficial de benchmark: `finetune_mistral_wsl/5_avaliar_batch_wsl.py`

Modos:
- `--base-only`
- `--adapter-only`
- `--compare`

Regras:
- avaliacao oficial deve usar `configs/eval/*.yaml`
- manter protocolo deterministico de inferencia para comparabilidade
- salvar em `runs/<experiment>/<run>/metrics` e `predictions`
- `3_testar_wsl.py` e `4_inferencia_wsl.py` sao apoio/demo, nao benchmark oficial

## 8) Invariantes de comparabilidade cientifica
- mesmo `base_model`
- mesma familia de configuracao LoRA/QLoRA (salvo experimento explicito)
- `seed` controlada
- mesma politica de tokenizacao (`max_length`, truncation/padding)
- mesmo template de prompt Instruct
- mesmo protocolo de inferencia para comparacao entre modelos
- reportar steps/tokens no `run_manifest.json`

## 9) Reprodutibilidade e auditoria
Cada run deve ter, no minimo:
- `meta/run_manifest.json`
- `metrics/*.json` (quando houver avaliacao)
- `predictions/*.jsonl` (quando houver avaliacao)

A IA deve:
- atualizar status da run (`dry_run_ok`, `completed`, `failed`)
- registrar erro em manifest em caso de falha
- nao sobrescrever run existente sem intencao explicita
- nao apagar artefatos legados

## 10) Regras de alteracao de codigo
- evitar hardcode de caminhos absolutos
- usar `configs/paths.local.yaml` para ambiente local
- manter compatibilidade com WSL (preferencial para treino)
- mudancas de metrica devem ocorrer em `common/metrics.py` e ser refletidas em `docs/protocol_v1.md`
- mudancas de schema de output devem atualizar templates em `docs/templates/`

## 11) Regras de documentacao
Ao criar/alterar experimento, atualizar:
- `docs/models/<model_id>.md`
- `docs/experiments/matriz_avaliacao.md` (se mudar desenho experimental)
- `docs/protocol_v1.md` (se mudar protocolo)

## 12) Anti-padroes proibidos
- treinar usando `finetune_mistral_wsl/output/` como destino novo
- comparar modelos com configs de inferencia diferentes sem declarar
- alterar split depois de iniciar bateria de comparacao
- misturar artefatos de runs diferentes no mesmo diretorio
- editar manualmente manifests para "forcar" consistencia

## 13) Checklist rapido para IA antes de executar
1. Confirmar `configs/paths.local.yaml` valido
2. Confirmar dataset manifest do experimento
3. Rodar `--dry-run`
4. Rodar treino
5. Rodar avaliacao em lote
6. Verificar `run_manifest.json`, `metrics`, `predictions`
7. Atualizar docs de modelo
