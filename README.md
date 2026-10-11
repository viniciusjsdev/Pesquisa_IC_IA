# Pesquisa IC IA

Mapa do checkout para a pesquisa com Qwen, dados industriais e financeiros. As frentes abaixo compartilham o repositório, mas têm contratos e estados próprios.

| Frente | Onde começar | Conteúdo |
| --- | --- | --- |
| Fine-tuning e avaliação | [FineTuning/CONTEXT_SUMMARY.md](FineTuning/CONTEXT_SUMMARY.md) e [FineTuning/AGENTS.md](FineTuning/AGENTS.md) | Protocolo, configurações, dados congelados, código de treino, adapters e métricas. |
| Execução remota | [runpod/README.md](runpod/README.md) | Scripts RunPod para preparação, treino, avaliação e watcher. |
| Bases para nova avaliação | [BancoModeloUse/README.md](BancoModeloUse/README.md) | 75 CSVs, importador local verificável e plano do novo DW/harness. |
| Exploração anterior | `crawler-relacao-investidor/`, `agentes/` | Crawler e experiências com agentes; não constituem o novo harness. |
| Saídas locais anteriores | `artifacts/`, `tmp/` | Arquivadas fora deste checkout em 11/10/2026; não integram o fluxo ativo. |

## Caminhos do FineTuning

- Fontes de verdade: [protocolo](FineTuning/docs/protocol_v1.md), `FineTuning/configs/train/`, `FineTuning/configs/eval/`, `FineTuning/data/manifests/` e `FineTuning/results/experiments/*/*/*/meta/run_manifest.json`, na ordem definida em `FineTuning/AGENTS.md`.
- Dados de treino e teste congelados: `FineTuning/data/processed/*_v1/`. Não editar splits manualmente.
- Código de treino e avaliação: `FineTuning/finetune_qwen_wsl/`; a configuração fica em `FineTuning/configs/`.
- Adapters, métricas, predições e manifests de cada execução: `FineTuning/results/experiments/`. Veja o [índice de resultados](FineTuning/results/README.md). Os seis pesos finais usam Git LFS; a base Qwen é obtida separadamente.
- Para localizar os pesos locais, conferir SHA-256, configurações registradas e escolher a bateria para próximos testes, veja o [catálogo de modelos e adapters](FineTuning/docs/modelos_disponiveis.md).
- Fonte local dos splits: `FineTuning/data_ft/`. A [versão editorial canônica do artigo](https://docs.google.com/document/d/1LExZ17IkPXIKYGCHLEJ3mEZSsCU2It1X/edit) está no Google Docs; [DOCX e PDF locais](FineTuning/artigo_canonico/README.md) são snapshots exportados. O [escopo do artigo](FineTuning/docs/escopo_envio_artigo.md) registra o material histórico retirado da árvore ativa.

O novo harness de avaliação por API e o novo DW estão [planejados](BancoModeloUse/docs/arquitetura_avaliacao_modelos.md), ainda não implementados. Nenhuma pasta de treino ou de RunPod foi movida: scripts, configurações, manifests e referências de artigo ainda dependem dos caminhos atuais. Qualquer mudança física futura exige inventário de referências, migração explícita e validação dos consumidores.
