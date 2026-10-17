# Pesquisa IC IA

Mapa do checkout para a pesquisa com Qwen, dados industriais e financeiros. As frentes abaixo compartilham o repositório, mas têm contratos e estados próprios.

| Frente | Onde começar | Conteúdo |
| --- | --- | --- |
| Fine-tuning e avaliação | [FineTuning/CONTEXT_SUMMARY.md](FineTuning/CONTEXT_SUMMARY.md) e [FineTuning/AGENTS.md](FineTuning/AGENTS.md) | Protocolo, configurações, dados congelados, código de treino, adapters e métricas. |
| Execução remota | [runpod/README.md](runpod/README.md) | Scripts históricos de treino/avaliação e [preparação local de serving com custos e aplicação futura](runpod/serving/README.md), sem Pod criado. |
| Bases para nova avaliação | [BancoModeloUse/README.md](BancoModeloUse/README.md) | 75 CSVs, importador local verificável, [DW local v1](BancoModeloUse/dw/README.md), [pacotes fixos locais](model_evaluation/README.md) e [desenho dos dois cenários de comparação](BancoModeloUse/docs/arquitetura_avaliacao_modelos.md); harness formal pendente. |
| Inferência compartilhada | [inference_api/README.md](inference_api/README.md) e [arquitetura](docs/arquitetura_inferencia_compartilhada.md) | O README da API descreve o caminho atual de cada pergunta na Bancada: pacote fixo da DW ou tools escolhidas pela LLM, registro do run e localização das perguntas. A SPEC-005 mantém o runbook da sessão curta. RunPod, ngrok e avaliação científica não foram executados. |
| Contratos de implementação | [specs/README.md](specs/README.md) | SPECs 001–009 concluídas no escopo local; a [SPEC-009](specs/active/SPEC-009/SPEC.md) implementou a alternância exploratória na Bancada e teve [revisão independente aprovada](specs/active/SPEC-009/evidence/review.json) em 16/10/2026. O harness científico formal continua pendente. |
| Saídas locais anteriores | `artifacts/`, `tmp/` | Arquivadas fora deste checkout em 11/10/2026; não integram o fluxo ativo. |

## Caminhos do FineTuning

- Fontes de verdade: [protocolo](FineTuning/docs/protocol_v1.md), `FineTuning/configs/train/`, `FineTuning/configs/eval/`, `FineTuning/data/manifests/` e `FineTuning/results/experiments/*/*/*/meta/run_manifest.json`, na ordem definida em `FineTuning/AGENTS.md`.
- Dados de treino e teste congelados: `FineTuning/data/processed/*_v1/`. Não editar splits manualmente.
- Código de treino e avaliação: `FineTuning/finetune_qwen_wsl/`; a configuração fica em `FineTuning/configs/`.
- Adapters, métricas, predições e manifests de cada execução: `FineTuning/results/experiments/`. Veja o [índice de resultados](FineTuning/results/README.md). Os seis pesos finais usam Git LFS; a base Qwen é obtida separadamente.
- Para localizar os pesos locais, conferir SHA-256, configurações registradas e escolher a bateria para próximos testes, veja o [catálogo de modelos e adapters](FineTuning/docs/modelos_disponiveis.md).
- Fonte local dos splits: `FineTuning/data_ft/`. A [versão editorial canônica do artigo](https://docs.google.com/document/d/1LExZ17IkPXIKYGCHLEJ3mEZSsCU2It1X/edit) está no Google Docs; [DOCX e PDF locais](FineTuning/artigo_canonico/README.md) são snapshots exportados. O [escopo do artigo](FineTuning/docs/escopo_envio_artigo.md) registra o material histórico retirado da árvore ativa.

O [DW local v1](BancoModeloUse/dw/README.md) foi implementado e carregado em um banco novo, separado dos dois bancos de origem e do banco da aplicação. O [desenho da avaliação](BancoModeloUse/docs/arquitetura_avaliacao_modelos.md) separa raciocínio com evidência fixa de pesquisa com tools. O [exportador local da SPEC-007](model_evaluation/README.md) já prepara pacotes candidatos, sem LLM ou gabarito; o harness científico formal permanece planejado. A [Bancada exploratória](inference_api/README.md) agora usa pacotes fixos ou tools escolhidas pela LLM em novos runs; snapshots antigos continuam legíveis. O [serving vLLM](runpod/serving/README.md) foi preparado em código local e a SPEC-002 foi encerrada após revisão independente, sem criar a Pod. Custos, `plan` e `apply` estão documentados para a próxima interação; pesos remotos, geração e exposição compartilhada ainda faltam. Nenhuma pasta de treino ou de RunPod foi movida: scripts, configurações, manifests e referências de artigo ainda dependem dos caminhos atuais. Qualquer mudança física futura exige inventário de referências, migração explícita e validação dos consumidores.

Código e documentação fora de uso não ficam como orientação ativa. As antigas árvores `agentes/`, `crawler-relacao-investidor/` e `BancoModeloUse/references/bi/` foram preservadas fora do checkout em 11/10/2026. O rascunho de “Gold Set” incompatível com a DW v1 foi arquivado em 16/10/2026 fora do checkout com hash e inventário próprios. Na máquina de origem, o arquivo externo é `D:\Projetos\Github_ViniciusJ\Pesquisa_IC_IA_legacy_archive_20261011`; esse caminho não é portátil para outros clones.
