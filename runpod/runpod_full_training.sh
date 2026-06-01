#!/usr/bin/env bash
set -euo pipefail

WORKDIR=/workspace/FineTuning/FineTuning/finetune_qwen_wsl
PATHS_CONFIG=configs/paths.cloud.yaml
EXPERIMENT_TAG=${EXPERIMENT_TAG:-h100_qwen25_7b_maxlen4096}
RUN_NAME=${RUN_NAME:-run_$(date -u +%Y%m%d_%H%M%S)_seed42}
RESULTS_ROOT=../results
RUNS_ROOT=${RESULTS_ROOT}/experiments/${EXPERIMENT_TAG}
RUNS_ROOT_ABS=/workspace/FineTuning/FineTuning/results/experiments/${EXPERIMENT_TAG}
LOG_DIR=${RESULTS_ROOT}/logs/${EXPERIMENT_TAG}/${RUN_NAME}

cd "$WORKDIR"
mkdir -p "$LOG_DIR"
cat > "$LOG_DIR/run_context.env" <<EOF
EXPERIMENT_TAG=$EXPERIMENT_TAG
RUN_NAME=$RUN_NAME
RUNS_ROOT=$RUNS_ROOT_ABS
EOF
cp "$LOG_DIR/run_context.env" /workspace/current_training_run.env

exec > >(tee -a "$LOG_DIR/full_training.log" /workspace/full_training.log) 2>&1

source venv/bin/activate

export HF_HOME=/workspace/Qwen
export TRANSFORMERS_CACHE=/workspace/Qwen
export TOKENIZERS_PARALLELISM=false
export WANDB_DISABLED=true

echo "FULL_TRAINING_START_$(date -Is)"
echo "EXPERIMENT_TAG=$EXPERIMENT_TAG"
echo "RUN_NAME=$RUN_NAME"
echo "RUNS_ROOT=$RUNS_ROOT_ABS"
python - <<'PY'
import torch
print("cuda_available", torch.cuda.is_available())
print("gpu", torch.cuda.get_device_name(0))
print("vram_gb", round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1))
PY

run_train() {
  local model="$1"
  echo "TRAIN_START_${model}_$(date -Is)"
  nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv,noheader
  python 2_treinar_wsl.py \
    --modelo "$model" \
    --paths-config "$PATHS_CONFIG" \
    --run-name "$RUN_NAME"
  echo "TRAIN_DONE_${model}_$(date -Is)"
  nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv,noheader
}

run_train finqa
run_train failure
run_train hibrido

echo "FULL_TRAINING_DONE_$(date -Is)"
