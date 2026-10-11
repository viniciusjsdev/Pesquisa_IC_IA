# Escopo do FineTuning para o artigo

O [Google Doc](https://docs.google.com/document/d/1LExZ17IkPXIKYGCHLEJ3mEZSsCU2It1X/edit) é a única versão editorial canônica do artigo. Ele compara `Qwen/Qwen2.5-7B-Instruct` (Base) com FT-FinQA, FT-Failure e FT-Híbrido em duas baterias: A (1024 tokens) e B (4096 tokens). A base é obtida separadamente; os seis adapters finais são preservados em `results/experiments/` com `adapter_config.json` e `adapter_model.safetensors`. O arquivo de pesos de cada adapter usa Git LFS. Verifique os seis SHA-256 em [modelos_disponiveis.md](modelos_disponiveis.md) após o clone e o download LFS.

## Reproduzir o protocolo

- Treino: `configs/train/ft_*_v1_bateria_a.yaml` para A e `configs/train/ft_*_v1.yaml` para B. `2_treinar_wsl.py --modelo <nome> --bateria A|B` seleciona o perfil; B é o padrão dos scripts RunPod.
- Avaliação: `configs/eval/base_bateria_a.yaml` para A e `configs/eval/base.yaml` para B; confira a configuração por domínio e o manifest da run antes de interpretar métricas.
- Dados: `data_ft/` é a fonte local de `prepare_experiment_datasets.py`; `data/processed/*_v1/` e `data/manifests/` preservam os splits congelados e seus hashes.
- Evidências: `results/experiments/` preserva manifests, configurações resolvidas, métricas originais, predições e logs das duas baterias. `results/recomputed_metrics/2026-09-14_failure_multilabel_v2/` preserva o recálculo multirrótulo usado no artigo; não substitui os JSONs originais.
- Texto editorial: [artigo_canonico/](../artigo_canonico/README.md) contém DOCX e PDF exportados do Google Doc em 11/10/2026. São snapshots para uso local; atualizações devem partir do documento online, não de um gerador local.

## Material retirado da árvore ativa

Cópias dos repositórios FinQA e FailureSensorIQ, cópias adicionais dos datasets originais, exploração em notebooks, relatórios anteriores, configs duplicadas ou não usadas no artigo, runs legadas, renders editoriais temporários, recálculo multirrótulo v1 e checkpoints intermediários foram movidos para `D:\Projetos\Github_ViniciusJ\Pesquisa_IC_IA_FineTuning_archive_20261011`, fora do repositório. O arquivo `move_inventory.json` registra os caminhos e tamanhos. Os dados congelados, manifests, resultados brutos e seis adapters finais permaneceram nos caminhos de origem. A ausência dos checkpoints intermediários não altera a identidade dos seis adapters publicados.

O pacote editorial local divergente (`artigo_novo_2026-09-14/`), incluindo DOCX, PDF, gerador, figura e template, foi movido para `Pesquisa_IC_IA_FineTuning_archive_20261011/artigo_local_divergente_substituido_20261011/`. O `archive_manifest.json` nessa pasta registra seis arquivos e seus SHA-256. O pacote não deve ser usado como fonte do artigo atual.

## Limites de verificação

`status: completed` no manifest registra a conclusão reportada pela execução remota; não prova nova reprodução neste checkout. O commit não inclui o modelo base completo nem fixa seu hash. Uma reprodução independente precisa obter a versão compatível da base, conferir o protocolo de prompt/inferência e executar a avaliação com as dependências de `requirements.txt`/`requirements_wsl.txt`.

O pacote local anterior tinha título, ordem de autores, texto e referências diferentes do Google Doc, embora compartilhasse resultados principais. Antes da substituição, seu gerador havia sido corrigido para retirar a afirmação de uso de gradient checkpointing; esse histórico permanece no arquivo externo, sem autoridade editorial. Na exportação de 11/10/2026, os 32 valores da Tabela 2 do Google Doc conferiram com os JSONs locais de FinQA e com o recálculo multirrótulo v2 de FailureSensorIQ, dentro do arredondamento exibido. Essa conferência não é reprodução independente do treino nem valida todas as afirmações do artigo.
