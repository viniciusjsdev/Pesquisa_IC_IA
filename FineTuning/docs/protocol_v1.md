# Protocolo Experimental v1

## Objetivo
Padronizar treinamento, avaliação e documentação para comparação entre `Base`, `FT-Híbrido`, `FT-FinQA` e `FT-Failure`.

## Perfis do artigo

O [artigo](https://docs.google.com/document/d/1LExZ17IkPXIKYGCHLEJ3mEZSsCU2It1X/edit), Tabela 1, descreve duas baterias. Os YAMLs `configs/train/ft_*_v1_bateria_a.yaml` selecionam a Bateria A; os três `configs/train/ft_*_v1.yaml` selecionam a Bateria B e são o padrão de `--modelo`. Em `2_treinar_wsl.py`, use `--modelo finqa|failure|hibrido --bateria A|B` (padrão B). Para avaliação em lote, use `configs/eval/base_bateria_a.yaml` na A e `configs/eval/base.yaml` na B. A configuração A usa limite de entrada 1024, `max_new_tokens: 24` e lote de geração 16, conforme os quatro JSONs históricos; B usa 4096, 32 e 8. O script RunPod existente continua selecionando B por padrão.

| Perfil | Treino e inferência | Microbatch × acumulação | Taxa FinQA | Taxa Failure/Híbrido |
| --- | ---: | ---: | ---: | ---: |
| A | 1024 | 4 × 8 | `2e-4` | `2e-4` |
| B (padrão) | 4096 | 2 × 16 | `2e-4` | `5e-5` |

Os valores acima coincidem com os seis `resolved_config_snapshot` dos manifests locais. Os perfis A usam diretório de saída novo em `results/experiments/h100_qwen25_7b_maxlen1024`, pois o caminho `runs` dos manifests importados era específico da execução remota histórica. Os pesos já treinados permanecem inalterados; a seleção do perfil só afeta novas execuções.

## Configs canônicas
- Base model: `Qwen/Qwen2.5-7B-Instruct`
- QLoRA NF4 4-bit
- LoRA: `r=8`, `alpha=16`, `dropout=0.1`
- Target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`
- `max_length=1024` (A) ou `4096` (B)
- `batch_size`/`gradient_accumulation_steps` conforme `configs/train/*.yaml`
- `seed=42`
- `warmup_ratio=0.05`
- `evaluation_strategy=epoch`, `save_strategy=epoch`
- `num_train_epochs=3`

## Comparabilidade
- Comparar modelos dentro da mesma bateria e declarar a taxa de aprendizado por modelo; na Bateria B, FinQA usa `2e-4` e Failure/Híbrido usam `5e-5`.
- Reportar explicitamente `global_steps`, `steps_por_epoca` e `tokens_aproximados_processados`.
- Comparações do artigo usam apenas os manifests das Baterias A e B em `results/experiments/`.

## Métricas
### FinQA
- Exact Match normalizado
- Numeric Accuracy (tolerância absoluta/relativa)
- MAE e MRE em amostras numéricas parseáveis
- Breakdown por operação (`meta.program`)

### FailureSensorIQ
- Accuracy por correspondência exata do conjunto de alternativas corretas (subset accuracy)
- Precisão, recall e F1 macro e micro multirrótulo sobre as alternativas A-E
- Jaccard médio por amostra
- Exact Match (normalizado)
- Falhas de parsing e confusões mais frequentes entre conjuntos de alternativas

As respostas do FailureSensorIQ podem conter mais de uma alternativa correta. A
avaliação não deve reduzir o gabarito ou a predição à primeira letra encontrada.

As listas `evaluation.metrics` dos YAMLs de avaliação descrevem as métricas principais; `5_avaliar_batch_wsl.py` não as usa como filtro. O avaliador calcula o payload completo definido em `common/metrics.py`, incluindo `accuracy` como alias de `subset_accuracy` e diagnósticos como `legacy_first_label_accuracy`, `confusion_top` e médias de rótulos. Confira a definição e o JSON da run antes de comparar resultados antigos com recálculos posteriores.

## Outputs padronizados
- Treino: `results/experiments/<protocol>/<experiment>/<run>/meta/run_manifest.json`.
- Novas avaliações em lote: `meta/evaluation_manifest.json`, `metrics/{finqa,failure,cross_domain,summary}_{base,adapter}.json` conforme os domínios/modelos executados e `predictions/{base,adapter}_predictions.jsonl` sob o diretório de run selecionado. O avaliador recusa diretórios que já tenham métricas ou predições; não cria cópias de nomes antigos sem sufixo.
- Avaliações históricas importadas: `metrics/*.json` e `predictions/*.jsonl`, sem manifest de avaliação. Confira os JSONs e a proveniência da run treinada, quando aplicável; não infira uma configuração completa a partir do manifest de treino.

O `--dry-run` do treino cria uma run de preflight e seu manifest; use um nome distinto da run real. O `--dry-run` da avaliação valida entradas e colisões sem criar arquivos.

## Proveniência
`data_ft/` é a fonte local dos splits versionados; `data/processed/` e `data/manifests/` são os dados congelados das duas baterias. Runs anteriores às Baterias A e B não integram o pacote ativo do artigo.
