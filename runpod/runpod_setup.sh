#!/usr/bin/env bash
set -euo pipefail

exec > >(tee -a /workspace/setup.log) 2>&1

echo "SETUP_START_$(date -Is)"
cd /workspace

if [ ! -d FineTuning ]; then
  git clone https://github.com/Vinicius380/Pesquisa_IC_IA.git FineTuning
fi

cd /workspace/FineTuning/FineTuning/finetune_qwen_wsl

python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements_wsl.txt

echo "SETUP_DONE_$(date -Is)"
