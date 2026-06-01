#!/usr/bin/env bash
set -euo pipefail

exec > >(tee -a /workspace/train_then_eval_watch.log) 2>&1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTEXT_FILE=${CONTEXT_FILE:-/workspace/current_training_run.env}
if [ -f "$CONTEXT_FILE" ]; then
  # shellcheck disable=SC1090
  source "$CONTEXT_FILE"
fi

EXPERIMENT_TAG=${EXPERIMENT_TAG:-h100_qwen25_7b_maxlen4096}
RUN_NAME=${RUN_NAME:-run_manual_watch_seed42}
RUNS_ROOT=${RUNS_ROOT:-/workspace/FineTuning/FineTuning/results/experiments/${EXPERIMENT_TAG}}

echo "WATCH_START_$(date -Is)"
echo "EXPERIMENT_TAG=$EXPERIMENT_TAG"
echo "RUN_NAME=$RUN_NAME"
echo "RUNS_ROOT=$RUNS_ROOT"

while tmux has-session -t full_training 2>/dev/null; do
  echo "WATCH_WAIT_TRAINING_$(date -Is)"
  sleep 60
done

if ! grep -q 'FULL_TRAINING_DONE' /workspace/full_training.log 2>/dev/null; then
  echo "WATCH_ABORT_NO_FULL_TRAINING_DONE_$(date -Is)"
  exit 1
fi

for adapter in \
  "$RUNS_ROOT/ft_finqa_v1/$RUN_NAME/adapter" \
  "$RUNS_ROOT/ft_failure_v1/$RUN_NAME/adapter" \
  "$RUNS_ROOT/ft_hibrido_v1/$RUN_NAME/adapter"
do
  if [ ! -s "$adapter/adapter_model.safetensors" ] && [ ! -s "$adapter/adapter_model.bin" ]; then
    echo "WATCH_ABORT_MISSING_ADAPTER_$adapter"
    exit 1
  fi
done

if tmux has-session -t full_evaluation 2>/dev/null; then
  echo "WATCH_EVAL_ALREADY_RUNNING_$(date -Is)"
else
  chmod +x "$SCRIPT_DIR/runpod_full_evaluation.sh"
  tmux new-session -d -s full_evaluation "$SCRIPT_DIR/runpod_full_evaluation.sh"
  echo "WATCH_EVAL_STARTED_$(date -Is)"
fi
