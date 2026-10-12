# AGENTS.md - Regras para IAs no projeto FineTuning

## 0) Entrada recomendada
Antes de qualquer acao, leia `CONTEXT_SUMMARY.md` para contexto unificado e ordem de leitura.

## 1) Escopo e objetivo
Este repositorio implementa fine-tuning multi-dominio do `Qwen/Qwen2.5-7B-Instruct` com protocolo experimental v1.
Modelos-alvo:
- `ft_hibrido_v1`
- `ft_finqa_v1`
- `ft_failure_v1`

Objetivo operacional de IA neste repo:
- manter comparabilidade cientifica entre modelos
- preservar reprodutibilidade
- evitar regressao para paths hardcoded e saidas misturadas

## 2) Fontes de verdade (ordem de prioridade)
Para o **texto, autoria e versão editorial do artigo**, a única fonte canônica é o [documento no Google Docs](https://docs.google.com/document/d/1LExZ17IkPXIKYGCHLEJ3mEZSsCU2It1X/edit). `artigo_canonico/` guarda exportações datadas, não uma segunda versão autoritativa. A ordem abaixo rege o protocolo técnico, os dados e as execuções; não substitui o documento editorial.

1. `docs/protocol_v1.md`
2. `configs/train/*.yaml` e `configs/eval/*.yaml`
3. `data/manifests/*.json`
4. `results/experiments/<protocol>/<experiment>/<run>/meta/run_manifest.json`
5. `docs/architecture.md` e `docs/experiments/matriz_avaliacao.md`

Se houver conflito entre scripts, protocolo e artefatos, confira código, configs, manifests e resultados da run exata antes de decidir o ajuste. Registre a divergência e sua evidência; não altere dados congelados ou resultados brutos para forçar concordância documental.

## 3) Estrutura canonica (nao legado)
- `configs/`: configuracao de treino e avaliacao
- `data/processed/*_v1/`: datasets congelados por experimento
- `data/manifests/*.json`: rastreabilidade e hashes
- `results/experiments/<protocol>/<experiment>/<run>/`: artefatos por execucao
- `finetune_qwen_wsl/common/`: utilitarios compartilhados
- `docs/`: protocolo, arquitetura e documentacao de modelos

## 4) Fonte dos splits e material historico
- `data_ft/` contem os tres splits que alimentam `prepare_experiment_datasets.py`; deve ser preservado para regenerar os conjuntos congelados.
- Runs anteriores as Baterias A e B foram retiradas do checkout ativo. Novos treinos e avaliacoes devem usar `data/processed`, `configs/*` e `results/experiments/*`.

## 5) Contratos de dados
Formato esperado de amostra JSONL:
- `prompt` (str)
- `resposta` (str)
- `meta` (obj)

Campos importantes em `meta`:
- `dataset`: `FinQA` ou `FailureSensorIQ`
- `program` (FinQA, quando existir)
- `id` (quando existir)

Regras:
- nao editar manualmente `data/processed/*_v1/*.jsonl`
- para regenerar datasets versionados, usar:
  - `python finetune_qwen_wsl/prepare_experiment_datasets.py`
- preservar splits `train/val/test`
- preservar `meta.dataset` para filtros de dominio

## 6) Contratos de treino
Script oficial: `finetune_qwen_wsl/2_treinar_wsl.py`

Atalhos suportados:
- `--modelo hibrido`
- `--modelo finqa`
- `--modelo failure`

Regras:
- preferir `--modelo` (nao hardcode de config no script)
- executar `--dry-run` antes de treino real
- o `--dry-run` do treino grava uma run de preflight; use nome separado da run real. O `--dry-run` da avaliação apenas verifica entradas e não grava resultados.
- usar apenas configs de `configs/train/`
- nao alterar hiperparametros no codigo; alterar YAML
- salvar tudo em `results/experiments/<protocol>/<experiment>/<run>/...`

Exemplos:
- `python finetune_qwen_wsl/2_treinar_wsl.py --modelo finqa --dry-run`
- `python finetune_qwen_wsl/2_treinar_wsl.py --modelo finqa`

## 7) Contratos de avaliacao
Script oficial de benchmark: `finetune_qwen_wsl/5_avaliar_batch_wsl.py`

Modos:
- `--base-only`
- `--adapter-only`
- `--compare`

Regras:
- avaliacao oficial deve usar `configs/eval/*.yaml`
- manter protocolo deterministico de inferencia para comparabilidade
- salvar em `results/experiments/<protocol>/<experiment>/<run>/metrics` e `predictions`
- `3_testar_wsl.py` e `4_inferencia_wsl.py` sao apoio/demo, nao benchmark oficial

## 8) Invariantes de comparabilidade cientifica
- mesmo `base_model`
- mesma familia de configuracao LoRA/QLoRA (salvo experimento explicito)
- `seed` controlada
- mesma politica de tokenizacao (`max_length`, truncation/padding)
- mesmo template de prompt Instruct
- mesmo protocolo de inferencia para comparacao entre modelos
- reportar steps/tokens no `run_manifest.json`

## 9) Reprodutibilidade e auditoria
O treino atual grava `meta/run_manifest.json`. Novas avaliações em lote gravam `meta/evaluation_manifest.json`, `metrics/*.json` e `predictions/*.jsonl`; recusam um diretório que já tenha métricas ou predições. As avaliações históricas das Baterias A e B não têm esse manifest de avaliação. Para citá-las, confira o JSON, a config inferível dos artefatos e a proveniência da run treinada, quando houver adapter.

Para runs de treino, atualize o status (`dry_run_ok`, `completed`, `failed`) e registre falhas no manifest. Não sobrescreva runs existentes sem intenção explícita. Preserve manifests, métricas e predições brutas das duas baterias do artigo.

## 10) Regras de alteracao de codigo
- evitar hardcode de caminhos absolutos
- usar `configs/paths.local.yaml` para ambiente local
- manter compatibilidade com WSL (preferencial para treino)
- mudancas de metrica devem ocorrer em `common/metrics.py` e ser refletidas em `docs/protocol_v1.md`
- mudanças de schema de output devem atualizar `docs/protocol_v1.md`, a documentação dos resultados e os consumidores/testes afetados

## 11) Regras de documentacao
Ao criar/alterar experimento, atualizar:
- `docs/models/<model_id>.md`
- `docs/experiments/matriz_avaliacao.md` (se mudar desenho experimental)
- `docs/protocol_v1.md` (se mudar protocolo)

Ao mudar script, YAML, métrica ou estrutura de resultados, confira os comandos e caminhos documentados contra o código e atualize as páginas afetadas na mesma mudança. Identifique afirmações sobre runs existentes pela run, evidência e data/commit da conferência; diferencie status registrado, validação local e reprodução independente. Retire código, configuração e instruções obsoletos do checkout depois de conferir referências; preserve o histórico necessário em arquivo externo com inventário.

## 12) Anti-padroes proibidos
- comparar modelos com configs de inferencia diferentes sem declarar
- alterar split depois de iniciar bateria de comparacao
- misturar artefatos de runs diferentes no mesmo diretorio
- editar manualmente manifests para "forcar" consistencia

## 13) Checklist rapido para IA antes de executar
1. Confirmar `configs/paths.local.yaml` no ambiente local ou `configs/paths.cloud.yaml` no RunPod
2. Confirmar dataset manifest do experimento
3. Rodar `--dry-run`
4. Rodar treino
5. Rodar avaliacao em lote
6. Verificar `run_manifest.json` do treino e `evaluation_manifest.json`/`metrics`/`predictions` da nova avaliação; para as avaliações históricas, conferir os JSONs originais sem inventar um manifest
7. Atualizar docs de modelo
