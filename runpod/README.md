# RunPod: fluxo codificado no repositório

Esta pasta contém os scripts de execução remota. Antes de uma nova execução, conferir ambiente, custo, dependências e estado do pod; a presença destes scripts não é prova de prontidão remota.

## Serving de modelos preparado localmente

A [SPEC-002](../specs/active/SPEC-002/SPEC.md) preparou em
[`serving/`](serving/README.md) o manifesto dos sete aliases, validação de
hashes, comando vLLM estático, gateway de duas rotas, verificador explícito e
Terraform declarativo. Os testes locais não iniciaram Pod nem comprovaram
compatibilidade ou capacidade remota. A troca entre adapters da mesma base
usa o campo `model` por requisição, sem reiniciar o Pod. O
[catálogo de modelos](../FineTuning/docs/modelos_disponiveis.md) e os manifests
das runs identificam os artefatos científicos; a revisão da base do treino
histórico segue desconhecida. Os scripts abaixo continuam destinados a treino
e avaliação. O [runbook de serving](serving/README.md) documenta a estimativa
de cobrança de GPU e discos, a revisão de `terraform plan` e a confirmação
explícita necessária para um `apply` em outra interação. A conclusão local da
SPEC-002 não indica Pod implantada.

Em 17/10/2026 houve um [teste remoto separado](serving/evidence/2026-10-17-a5000.md)
na RTX A5000 de 24 GB. A Pod foi criada pelo console, não por Terraform, e
parada ao fim sem volume persistente. Sete aliases responderam por HTTPS;
esse primeiro teste não incluiu a Bancada. Uma
[segunda sessão exploratória](serving/evidence/2026-10-17-integracao-bancada.md)
validou os dois modos com a base via ngrok, observou uma falha de resposta do
adapter FT-FinQA A e parou novamente a Pod a US$ 0,00/h. Não houve avaliação
científica; `terraform plan/apply` continua sem execução real.

Uma [validação adicional da infraestrutura](serving/evidence/2026-10-17-validacao-infra.md)
teve de criar outra RTX A5000 pelo console porque o host da Pod anterior
não tinha GPU livre. O novo host aceitou vLLM 0.11.0/CUDA 12.8, confirmou
sete aliases por HTTPS e uma execução da Bancada após correção de
`tool_calls: []` no backend. A Pod nova foi parada sem volume persistente,
com US$ 0,00/h no readback. A versão do driver do host precisa ser conferida
antes de escolher o runtime; a identidade da GPU não garante compatibilidade
com PyTorch/CUDA 13.0.

Um [novo teste de infraestrutura](serving/evidence/2026-10-17-bancada-sete-aliases.md)
executou os sete aliases uma vez cada na Bancada via ngrok, com cinco respostas
registradas e dois FT-FinQA truncados no limite de 500 tokens. A base também
consultou a DW por tool. A Pod A5000 da sessão foi parada sem volume
persistente, com US$ 0,00/h no console. Não houve Terraform nem avaliação
científica.

Um [replay posterior na L4](serving/evidence/2026-10-17-finqa-sem-teto-l4.md)
omitiu `max_tokens` nas requisições FT-FinQA. B respondeu por invocação direta
do serviço backend, sem login HTTP, e foi
salvo como `answered_unverified`, porém só produziu um fragmento numérico.
A alcançou a janela de 4.096 tokens do vLLM em acesso direto ao gateway;
o acesso pelo proxy HTTPS falhou antes com HTTP 524. A Pod L4 foi parada
sem volume persistente e o console confirmou US$ 0,00/h. Essa sessão não
executou React/ngrok, Terraform ou avaliação científica.

O [replay público posterior com streaming e jobs](serving/evidence/2026-10-17-streaming-bancada-l4.md)
usou a L4 de 24 GB por cerca de 23 minutos. Sete aliases passaram no
verificador HTTPS; pela Bancada autenticada via ngrok, a base respondeu e o
FT-FinQA A enviou o fluxo SSE completo sem HTTP 524. Esse adapter repetiu
texto até a janela de 4.096 tokens e ficou `response_error`, sem validação
científica. O job persistiu após refresh e novo login. A Pod foi parada a
US$ 0,00/h, sem volume persistente; API, ngrok e banco local foram encerrados.
Não houve Terraform nem prova de carga sustentada.

## Layout esperado pelos scripts

`runpod_setup.sh` clona este repositório em `/workspace/FineTuning` apenas se a pasta ainda não existir; se existir, reutiliza o checkout sem atualizar o commit. Confira o commit antes de executar. O projeto de treino fica em `/workspace/FineTuning/FineTuning`, e o diretório de execução é `/workspace/FineTuning/FineTuning/finetune_qwen_wsl`. Os scripts usam `FineTuning/configs/paths.cloud.yaml`, cache em `/workspace/Qwen` e saídas em `/workspace/FineTuning/FineTuning/results/experiments/<EXPERIMENT_TAG>/`.

| Script | Função |
| --- | --- |
| `runpod_setup.sh` | Clona se necessário e instala dependências no `venv`. |
| `runpod_download_qwen.sh` | Baixa o modelo Qwen para o cache remoto. |
| `runpod_full_training.sh` | Treina FinQA, Failure e Híbrido sob o mesmo `RUN_NAME`. |
| `runpod_full_evaluation.sh` | Avalia base e os três adapters no mesmo grupo de resultados. |
| `runpod_train_then_eval_watch.sh` | Observa o término do treino, verifica os três adapters e inicia a avaliação. |

`EXPERIMENT_TAG` e `RUN_NAME` podem ser definidos no ambiente. O treino passa o destino derivado de `EXPERIMENT_TAG` ao Python com `--runs-root`, faz um `--dry-run` em uma run separada com sufixo `_preflight` e então inicia a run real. O treino grava `/workspace/current_training_run.env`, que a avaliação e o watcher leem para reutilizar a identidade da execução. O watcher procura `runpod_full_evaluation.sh` na sua própria pasta; mantenha os scripts juntos.

O watcher espera a sessão `tmux` de treino terminar, procura `FULL_TRAINING_DONE` no log cumulativo `/workspace/full_training.log` e confere a existência dos três arquivos de adapter no caminho da run selecionada. O marcador do log não é associado ao `RUN_NAME`: se o log contiver uma conclusão anterior e forem reutilizados nomes e adapters, essa checagem não comprova que o treino atual terminou com sucesso. Confira o log e os manifests da run específica antes de interpretar a avaliação como continuação válida do treino.

Os resultados locais foram importados em diretórios com nomes datados, como `FineTuning/results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/`. O manifest dessa rodada registra a saída remota original sob o protocolo `h100_qwen25_7b_maxlen4096`; não suponha que o nome da pasta importada seja o valor de `EXPERIMENT_TAG` para uma nova execução. Consulte [resultados](../FineTuning/results/README.md) e o manifest da run exata.

`FineTuning/configs/paths.local.yaml` é específico da máquina e ignorado pelo Git. Use `paths.cloud.yaml` no ambiente previsto pelos scripts; a existência da configuração local não valida caminhos de outra máquina.
