#!/usr/bin/env bash
set -euo pipefail

WORKDIR=/workspace/FineTuning/FineTuning/finetune_qwen_wsl
PATHS_CONFIG=configs/paths.cloud.yaml
CONTEXT_FILE=${CONTEXT_FILE:-/workspace/current_training_run.env}

if [ -f "$CONTEXT_FILE" ]; then
  # shellcheck disable=SC1090
  source "$CONTEXT_FILE"
fi

EXPERIMENT_TAG=${EXPERIMENT_TAG:-h100_qwen25_7b_maxlen4096}
RUN_NAME=${RUN_NAME:-run_manual_eval_seed42}
RESULTS_ROOT=../results
RUNS_ROOT=${RUNS_ROOT:-${RESULTS_ROOT}/experiments/${EXPERIMENT_TAG}}
LOG_DIR=${RESULTS_ROOT}/logs/${EXPERIMENT_TAG}/${RUN_NAME}

cd "$WORKDIR"
mkdir -p "$LOG_DIR"

exec > >(tee -a "$LOG_DIR/full_evaluation.log" /workspace/full_evaluation.log) 2>&1

source venv/bin/activate

export HF_HOME=/workspace/Qwen
export TRANSFORMERS_CACHE=/workspace/Qwen
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export TOKENIZERS_PARALLELISM=false
export WANDB_DISABLED=true

echo "FULL_EVALUATION_START_$(date -Is)"
echo "EXPERIMENT_TAG=$EXPERIMENT_TAG"
echo "RUN_NAME=$RUN_NAME"
echo "RUNS_ROOT=$RUNS_ROOT"
nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv,noheader

run_eval() {
  local label="$1"
  shift
  echo "EVAL_START_${label}_$(date -Is)"
  python 5_avaliar_batch_wsl.py "$@"
  echo "EVAL_DONE_${label}_$(date -Is)"
  nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv,noheader
}

run_eval base \
  --base-only \
  --eval-config configs/eval/base.yaml \
  --paths-config "$PATHS_CONFIG" \
  --run-dir "$RUNS_ROOT/base_eval/$RUN_NAME"

run_eval ft_finqa \
  --adapter-only \
  --eval-config configs/eval/base.yaml \
  --paths-config "$PATHS_CONFIG" \
  --run-dir "$RUNS_ROOT/ft_finqa_v1/$RUN_NAME"

run_eval ft_failure \
  --adapter-only \
  --eval-config configs/eval/base.yaml \
  --paths-config "$PATHS_CONFIG" \
  --run-dir "$RUNS_ROOT/ft_failure_v1/$RUN_NAME"

run_eval ft_hibrido \
  --adapter-only \
  --eval-config configs/eval/base.yaml \
  --paths-config "$PATHS_CONFIG" \
  --run-dir "$RUNS_ROOT/ft_hibrido_v1/$RUN_NAME"

echo "FULL_EVALUATION_DONE_$(date -Is)"
