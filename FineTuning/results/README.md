# Resultados de Fine-Tuning

Esta pasta concentra artifacts de treino e avaliacao para evitar mistura com
codigo, datasets e notebooks.

## Convencao

- `experiments/<protocolo>/<experimento>/<run>/`: saidas de treino e avaliacao.
- `experiments/<protocolo>/base_eval/<run>/`: inferencia do modelo base no mesmo
  protocolo.
- `logs/<protocolo>/<run>/`: logs de orquestracao RunPod e contexto do run.
- `legacy/`: resultados locais antigos, preservados apenas como historico.

## Protocolos atuais

- `2026-05-31_h100_qwen25_7b_maxlen1024_prelim`: copia da execucao RunPod
  inicial. Preliminar porque o limite de 1024 tokens truncou 45,86% do FinQA.
- `h100_qwen25_7b_maxlen4096`: protocolo recomendado para o novo treinamento em
  H100, com `tokenization.max_length=4096` e `max_input_length=4096` na avaliacao.

## Versionamento

Checkpoints, adapters, predicoes e logs ficam ignorados no `.gitignore` para
evitar commits pesados. Metricas e manifests pequenos podem ser versionados se
forem selecionados conscientemente.
