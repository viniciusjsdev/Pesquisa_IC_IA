# RunPod

Scripts e guia operacional para preparar o pod, baixar o Qwen, treinar,
avaliar e monitorar a execucao.

## Arquivos

- `runpod_setup.sh`: clona/prepara o ambiente e instala dependencias.
- `runpod_download_qwen.sh`: baixa `Qwen/Qwen2.5-7B-Instruct` para cache.
- `runpod_full_training.sh`: treina FinQA, FailureSensorIQ e Hibrido.
- `runpod_full_evaluation.sh`: avalia base e adapters do mesmo run.
- `runpod_train_then_eval_watch.sh`: aguarda treino terminar e inicia avaliacao.
- `GUIA_RUNPOD_SETUP.md`: guia operacional detalhado.

## Convencao

Manter estes arquivos juntos. O watcher procura `runpod_full_evaluation.sh` na
mesma pasta em que ele estiver sendo executado.
