#!/usr/bin/env bash
set -euo pipefail

exec > >(tee -a /workspace/qwen_download.log) 2>&1

echo "QWEN_DOWNLOAD_START_$(date -Is)"
cd /workspace/FineTuning/FineTuning/finetune_qwen_wsl
source venv/bin/activate

export HF_HOME=/workspace/Qwen
export TRANSFORMERS_CACHE=/workspace/Qwen

python - <<'PY'
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Qwen/Qwen2.5-7B-Instruct",
    cache_dir="/workspace/Qwen",
    resume_download=True,
)
print("Download concluido")
PY

echo "QWEN_DOWNLOAD_DONE_$(date -Is)"
