# Protocolo Experimental v1

## Objetivo
Padronizar treinamento, avaliação e documentação para comparação entre `Base`, `FT-Híbrido`, `FT-FinQA` e `FT-Failure`.

## Configs canônicas
- Base model: `mistralai/Mistral-7B-Instruct-v0.3`
- QLoRA NF4 4-bit
- LoRA: `r=8`, `alpha=16`, `dropout=0.1`
- Target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`
- `max_length=1024`
- `batch_size=1`, `gradient_accumulation_steps=32`
- `seed=42`
- `warmup_ratio=0.05`
- `evaluation_strategy=epoch`, `save_strategy=epoch`
- `num_train_epochs=3`

## Comparabilidade
- Mesmas configs centrais para os 3 fine-tunings.
- Reportar explicitamente `global_steps`, `steps_por_epoca` e `tokens_aproximados_processados`.
- Resultados legados (pré-v1) devem ser marcados como `legacy_pre_protocol_v1`.

## Métricas
### FinQA
- Exact Match normalizado
- Numeric Accuracy (tolerância absoluta/relativa)
- MAE e MRE em amostras numéricas parseáveis
- Breakdown por operação (`meta.program`)

### FailureSensorIQ
- Accuracy
- F1 macro
- Exact Match (normalizado)
- Confusões mais frequentes (top pares)

## Outputs padronizados
- `runs/<experiment>/<run>/meta/run_manifest.json`
- `runs/<experiment>/<run>/metrics/*.json`
- `runs/<experiment>/<run>/predictions/*.jsonl`

## Legado
O modelo híbrido atual deve ser catalogado em `runs/ft_hibrido_legacy/` com inconsistências de configuração documentadas.
