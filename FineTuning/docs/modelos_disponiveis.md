# Modelos e pesos disponíveis neste checkout

Inventário local conferido em 11/10/2026. A base é `Qwen/Qwen2.5-7B-Instruct`; os seis diretórios abaixo contêm **adapters PEFT/LoRA**, não modelos completos. Para inferência, carregue a mesma base e aplique um único adapter. O código faz isso em [`common/modeling.py`](../finetune_qwen_wsl/common/modeling.py) com `AutoModelForCausalLM.from_pretrained(base_model, cache_dir=...)` e `PeftModel.from_pretrained(..., adapter_path)`; o tokenizer é carregado da base. A base não foi encontrada dentro de `FineTuning/`. O runtime usa o identificador Hugging Face e o cache definido em `configs/paths.local.yaml` ou [`paths.cloud.yaml`](../configs/paths.cloud.yaml), podendo obtê-la do cache ou baixá-la conforme o ambiente. Nenhum download ou teste de geração foi feito neste inventário.

## Qual usar para próximos testes

Os caminhos abaixo são **relativos à raiz do repositório**. Em cada `adapter/` local existem `adapter_model.safetensors` (80.792.096 bytes), `adapter_config.json` (1.101 bytes), `tokenizer.json` (11.421.991 bytes), `tokenizer_config.json` (694 bytes), `chat_template.jinja` (2.507 bytes) e `README.md` (5.202 bytes). Para o carregador atual, os dois primeiros são os arquivos do adapter; os arquivos de tokenizer/template acompanham a exportação, mas o carregador usa o tokenizer da base. Preserve o template de prompt do protocolo ao comparar inferências.

| Uso | Rodada e modelo | Diretório relativo do adapter | Manifest da run | Estado registrado |
| --- | --- | --- | --- | --- |
| Candidato para novo teste financeiro com contexto integral | 4096, FT-FinQA | `FineTuning/results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/ft_finqa_v1/run_20260601_002803_seed42/adapter/` | [manifest](../results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/ft_finqa_v1/run_20260601_002803_seed42/meta/run_manifest.json) | `completed` |
| Candidato para novo teste industrial com contexto integral | 4096, FT-Failure | `FineTuning/results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/ft_failure_v1/run_20260601_002803_seed42/adapter/` | [manifest](../results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/ft_failure_v1/run_20260601_002803_seed42/meta/run_manifest.json) | `completed` |
| Candidato para novo teste conjunto com contexto integral | 4096, FT-Híbrido | `FineTuning/results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/ft_hibrido_v1/run_20260601_002803_seed42/adapter/` | [manifest](../results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/ft_hibrido_v1/run_20260601_002803_seed42/meta/run_manifest.json) | `completed` |
| Reproduzir Bateria A e seu melhor resultado industrial publicado | 1024 preliminar, FT-Failure | `FineTuning/results/experiments/2026-05-31_h100_qwen25_7b_maxlen1024_prelim/runpod_import/ft_failure_v1_run_v1_seed42/adapter/` | [manifest](../results/experiments/2026-05-31_h100_qwen25_7b_maxlen1024_prelim/runpod_import/ft_failure_v1_run_v1_seed42/meta/run_manifest.json) | `completed` |
| Reproduzir Bateria A financeira | 1024 preliminar, FT-FinQA | `FineTuning/results/experiments/2026-05-31_h100_qwen25_7b_maxlen1024_prelim/runpod_import/ft_finqa_v1_run_v1_seed42/adapter/` | [manifest](../results/experiments/2026-05-31_h100_qwen25_7b_maxlen1024_prelim/runpod_import/ft_finqa_v1_run_v1_seed42/meta/run_manifest.json) | `completed` |
| Reproduzir Bateria A e seu melhor equilíbrio publicado | 1024 preliminar, FT-Híbrido | `FineTuning/results/experiments/2026-05-31_h100_qwen25_7b_maxlen1024_prelim/runpod_import/ft_hibrido_v1_run_v1_seed42/adapter/` | [manifest](../results/experiments/2026-05-31_h100_qwen25_7b_maxlen1024_prelim/runpod_import/ft_hibrido_v1_run_v1_seed42/meta/run_manifest.json) | `completed` |

Os três pesos preliminares têm também 80.792.096 bytes cada. Para escolher um **modelo principal**, defina primeiro domínio, janela de entrada e métrica; o artigo não sustenta eleger toda a rodada 4096. `completed` é o status do treino no manifest, não prova de validade do benchmark ou de geração reproduzida aqui.

## Configurações registradas

Todos os manifests indicam semente 42, três épocas, QLoRA 4-bit NF4 com dupla quantização e cálculo FP16; LoRA `r=8`, `alpha=16`, `dropout=0,1`, módulos `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`. Tokenização: truncamento ativo e sem padding no treino. A métrica para escolher o melhor checkpoint é `eval_loss`, que não equivale à acurácia do benchmark. Dados e hashes dos splits: [FinQA](../data/manifests/finqa_v1.json), [FailureSensorIQ](../data/manifests/failure_v1.json), [híbrido](../data/manifests/hybrid_v1.json).

Os três manifests de **dataset** ainda têm `max_length_policy.max_length: 1024`, registro da preparação dos dados; isso não substitui o `resolved_config_snapshot.tokenization.max_length: 4096` e o `runtime.max_length: 4096` dos manifests de treino da Bateria B. A versão exata dos pesos da base não foi fixada por hash neste catálogo.

| Rodada | Limite de treino no manifest | Microbatch × acumulação | Taxa de aprendizado no manifest | Steps FT-FinQA / FT-Failure / FT-Híbrido | Configuração para nova execução |
| --- | ---: | ---: | --- | --- | --- |
| 1024, Bateria A preliminar | 1024 | 4 × 8 | `2e-4` nos três | 462 / 624 / 1086 | `configs/train/ft_{finqa,failure,hibrido}_v1_bateria_a.yaml`; inferência [`base_bateria_a.yaml`](../configs/eval/base_bateria_a.yaml). |
| 4096, Bateria B | 4096 | 2 × 16 | FT-FinQA `2e-4`; FT-Failure e FT-Híbrido `5e-5` | 462 / 624 / 1086 | [`ft_finqa_v1.yaml`](../configs/train/ft_finqa_v1.yaml), [`ft_failure_v1.yaml`](../configs/train/ft_failure_v1.yaml), [`ft_hibrido_v1.yaml`](../configs/train/ft_hibrido_v1.yaml); inferência [`base.yaml`](../configs/eval/base.yaml). É o padrão de `--modelo` e do script RunPod. |

Para avaliação, [`base_bateria_a.yaml`](../configs/eval/base_bateria_a.yaml) declara `max_input_length: 1024`, `max_new_tokens: 24` e lote 16, como os quatro JSONs históricos da A; [`base.yaml`](../configs/eval/base.yaml) declara 4096, 32 e 8 para B. Os manifests de treino não comprovam sozinhos a configuração de inferência da avaliação já publicada.

**Correção do YAML FinQA:** o manifest do FT-FinQA aponta para `configs/train/ft_finqa_v1.yaml` no commit `27c947d`, onde `learning_rate` era `0.0002`. O commit posterior `e4c8805` alterou esse arquivo para `0.00005` enquanto a execução já estava em andamento. O `meta/resolved_train_config.json` da run e o `trainer_state.json` do checkpoint final registram a configuração original; o histórico do treinador chega a aproximadamente `0.000198`. O YAML atual foi realinhado para `0.0002`, conforme artigo e snapshot. Isso não altera o adapter já treinado.

## Identidade SHA-256 dos arquivos finais

Cada linha se refere aos arquivos dentro do `adapter/` da respectiva bateria, não a checkpoints intermediários. Cada peso tem 80.792.096 bytes.

| Bateria/modelo | `adapter_model.safetensors` | `adapter_config.json` |
| --- | --- | --- |
| A / FT-FinQA | `6d94dc0e5f6df1e119c9a1e23c1f39262b9dec2153c8dce151c0e7219b74ce5c` | `1fc046f2aa4bd222c7a15709adf0a6fb42bd95aa129a0647655e86531171a2f1` |
| A / FT-Failure | `19629c837269113c383a043079cbd9410fa6117d951020c9529c05eeb112f9a1` | `ee0a5f9589c1a7a5db7fdf0e7b00290a89dfef49841c311117f0586500d2d0bd` |
| A / FT-Híbrido | `bada36090f4ea5e5375d49c403262b1af878e864b154503d6d1dab4c6111fce0` | `0a2be5ebf10c53265e2659176cb7a96716b13c5234ad7b975499d0655e84d0b8` |
| B / FT-FinQA | `34397e6c6df395dcc1e8889d63a69451b02bb20306d27f0b2f13dd200d2d8f80` | `780d0c72a060aa4151c2f5289967bbe4d274c3109d8faa4e521f40e382dfe1af` |
| B / FT-Failure | `037e8459a10076abba0a73d6ccfe23f88ca069b514920f1c1bf655eb62861e2a` | `fb866c989479b48eedb86b9d5454358a961b4dd40bcf8a4c778cee4a76653a02` |
| B / FT-Híbrido | `1f4be66064376173f1d62064db74d475c44ab6efb37bf94f0aef6f0b95ec6bd5` | `e714e25d77ed33fd5ee6b0d89ee16c0b327ce9efdb2b466a617478d6d4865139` |

Os três diretórios finais 4096 têm arquivos auxiliares idênticos entre si: `tokenizer.json` SHA-256 `21e2b58ce119ac9c0d306b7a35d538fe02f55e7f2af95cb0a2d563e892790684`; `tokenizer_config.json` `04b1682c59acbd057f4c9072297faa73d56fc9de053094c659cdb4c464f58f86`; `chat_template.jinja` `cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`; `README.md` `3191b465069be139a907db620ecaaee6188deeae1f5e14f8ec7281f71bba535d2`. Os manifests preservam caminhos absolutos do ambiente remoto; use os caminhos relativos desta página para localizar a importação neste checkout.

## Correspondência com o artigo

O [artigo Google Docs](https://docs.google.com/document/d/1LExZ17IkPXIKYGCHLEJ3mEZSsCU2It1X/edit), única versão editorial canônica, foi conferido novamente por exportação DOCX e PDF em 11/10/2026. Ele apresenta Bateria A (1024) e B (4096). Sua Tabela 1 confirma os limites, semente, LoRA, microbatch e a taxa **específica** do FT-FinQA de `2e-4` nas duas baterias, de acordo com os manifests e com o YAML corrigido de 4096. A Tabela 2 relata FT-FinQA 4096 com 15,42% no FinQA; FT-Failure 1024 com 96,63% de correspondência exata e F1 macro 0,989 no FailureSensorIQ; FT-Híbrido 1024 com maior média harmônica da Bateria A (18,75%). Os 32 valores da tabela conferiram com os JSONs locais dentro do arredondamento exibido; isso não constitui reprodução independente. O artigo observa que a diferença entre baterias não pode ser atribuída apenas à janela de contexto, pois outros hiperparâmetros variaram. Para conferir números, use os JSONs da run exata e examine separadamente [`results/recomputed_metrics/`](../results/recomputed_metrics/), cuja definição multirrótulo é posterior; veja o [protocolo](protocol_v1.md).

## Disponibilidade no Git

Os seis pesos finais são incluídos no Git via Git LFS, com regra limitada a `results/experiments/**/adapter/adapter_model.safetensors`. Os checkpoints intermediários não integram o commit. Após clonar, execute `git lfs pull`, confira os SHA-256 acima e obtenha a base Qwen separadamente. A versão exata da base ainda não está fixada por hash neste repositório.
