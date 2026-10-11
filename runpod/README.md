# RunPod: fluxo codificado no repositório

Esta pasta contém os scripts de execução remota. O [guia antigo](GUIA_RUNPOD_SETUP.md) foi retirado de uso. Antes de uma nova execução, conferir ambiente, custo, dependências e estado do pod; a presença destes scripts não é prova de prontidão remota.

## Layout esperado pelos scripts

`runpod_setup.sh` clona este repositório em `/workspace/FineTuning`. Assim, o projeto de treino fica em `/workspace/FineTuning/FineTuning`, e o diretório de execução é `/workspace/FineTuning/FineTuning/finetune_qwen_wsl`. Os scripts usam `FineTuning/configs/paths.cloud.yaml`, cache em `/workspace/Qwen` e saídas em `/workspace/FineTuning/FineTuning/results/experiments/<EXPERIMENT_TAG>/`.

| Script | Função |
| --- | --- |
| `runpod_setup.sh` | Clona o repositório e instala dependências no `venv`. |
| `runpod_download_qwen.sh` | Baixa o modelo Qwen para o cache remoto. |
| `runpod_full_training.sh` | Treina FinQA, Failure e Híbrido sob o mesmo `RUN_NAME`. |
| `runpod_full_evaluation.sh` | Avalia base e os três adapters no mesmo grupo de resultados. |
| `runpod_train_then_eval_watch.sh` | Observa o término do treino, verifica os três adapters e inicia a avaliação. |

`EXPERIMENT_TAG` e `RUN_NAME` podem ser definidos no ambiente. O treino grava `/workspace/current_training_run.env`, que a avaliação e o watcher leem para reutilizar a identidade da execução. O watcher procura `runpod_full_evaluation.sh` na sua própria pasta; mantenha os scripts juntos.

O watcher espera a sessão `tmux` de treino terminar, procura `FULL_TRAINING_DONE` no log cumulativo `/workspace/full_training.log` e confere a existência dos três arquivos de adapter no caminho da run selecionada. O marcador do log não é associado ao `RUN_NAME`: se o log contiver uma conclusão anterior e forem reutilizados nomes e adapters, essa checagem não comprova que o treino atual terminou com sucesso. Confira o log e os manifests da run específica antes de interpretar a avaliação como continuação válida do treino.

Os resultados locais foram importados em diretórios com nomes datados, como `FineTuning/results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/`. O manifest dessa rodada registra a saída remota original sob o protocolo `h100_qwen25_7b_maxlen4096`; não suponha que o nome da pasta importada seja o valor de `EXPERIMENT_TAG` para uma nova execução. Consulte [resultados](../FineTuning/results/README.md) e o manifest da run exata.

`FineTuning/configs/paths.local.yaml` é específico da máquina e ignorado pelo Git. Use `paths.cloud.yaml` no ambiente previsto pelos scripts; a existência da configuração local não valida caminhos de outra máquina.
