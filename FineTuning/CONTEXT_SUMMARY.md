# Contexto do FineTuning

Este diretório compara `Qwen/Qwen2.5-7B-Instruct` (base) com `ft_finqa_v1`, `ft_failure_v1` e `ft_hibrido_v1` em FinQA e FailureSensorIQ.

## Ordem de leitura e fontes de verdade

Leia `AGENTS.md` e siga a prioridade que ele define: `docs/protocol_v1.md`; `configs/train/*.yaml` e `configs/eval/*.yaml`; `data/manifests/*.json`; `results/experiments/<protocol>/<experiment>/<run>/meta/run_manifest.json`; depois `docs/architecture.md` e `docs/experiments/matriz_avaliacao.md`. Este resumo é um mapa, não substitui essas fontes. Para uma métrica, confira também o JSON da run e a versão de cálculo usada.

## Estrutura

- `data/processed/*_v1/`: splits congelados. `data/manifests/*.json`: rastreabilidade dos datasets.
- `configs/`: treino, avaliação e paths. `configs/paths.local.yaml` é pessoal e ignorado pelo Git; `configs/paths.cloud.yaml` está versionado.
- `finetune_qwen_wsl/2_treinar_wsl.py` e `5_avaliar_batch_wsl.py`: treino e avaliação em lote; `common/` contém funções compartilhadas.
- `results/experiments/`: runs importadas ou executadas, com manifests, adapters, métricas e predições; consulte [results/README.md](results/README.md).
- [Catálogo de modelos e adapters](docs/modelos_disponiveis.md): caminhos locais, arquivos de peso, hashes, diferenças entre as baterias 1024/4096 e confronto com o artigo.
- [Escopo de envio do artigo](docs/escopo_envio_artigo.md): conjunto ativo, pesos via Git LFS e material retirado da árvore ativa.
- `data_ft/`: fonte preservada dos splits versionados; `finetune_qwen_wsl/output/` não é destino de novas runs.
- `../runpod/`: scripts remotos que dependem do layout atual.

## Estado observado neste checkout

- A rodada preliminar de 1024 tokens está em `results/experiments/2026-05-31_h100_qwen25_7b_maxlen1024_prelim/runpod_import/`.
- A rodada H100 de 4096 tokens está em `results/experiments/2026-06-01_h100_qwen25_7b_maxlen4096_run_20260601_002803_seed42/`.
- Nas duas rodadas, os manifests locais dos três fine-tunings registram `status: completed`; há adapters, JSONs de métricas e predições locais. Isso confirma a catalogação dos artefatos, não uma nova execução ou validação independente neste checkout.
- `results/recomputed_metrics/2026-09-14_failure_multilabel_v2/` contém o recálculo multirrótulo citado no artigo, separado das métricas originais. Consulte `docs/protocol_v1.md`, a implementação em `finetune_qwen_wsl/common/metrics.py` e a proveniência antes de usar números.

Para nova execução, selecione explicitamente a bateria do artigo com `2_treinar_wsl.py --modelo finqa|failure|hibrido --bateria A|B`; B é o padrão dos scripts RunPod. Consulte `docs/protocol_v1.md` para os YAMLs de treino e inferência. Faça `--dry-run` quando aplicável e use `results/experiments/<protocol>/<experiment>/<run>/`. Não reutilize nomes de run sem verificar colisões. Não edite splits, manifests ou resultados brutos manualmente.
