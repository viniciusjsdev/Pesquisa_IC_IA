---
id: SPEC-011
title: Diagnostico e correcao demonstravel dos FT-FinQA
status: ready
contract_version: 1
---

# SPEC-011: Diagnóstico e correção demonstrável dos FT-FinQA

## Goal

Isolar por evidência por que `ft-finqa-a` repete até o limite de contexto e
`ft-finqa-b` pode responder com um fragmento numérico na Bancada. Corrigir a
causa que for demonstrada em prompt, protocolo de inferência, parser ou
configuração de serving, e validar base/adapters sob condições comparáveis.
Se a causa exigir novos pesos ou decisão científica, entregar diagnóstico e
plano versionado sem alterar os artefatos históricos.

## Context

- O [teste dos sete aliases](../../../runpod/serving/evidence/2026-10-17-bancada-sete-aliases.md)
  registrou `finish_reason=length` nos FT-FinQA A/B com 500 tokens. O
  [replay sem teto da aplicação](../../../runpod/serving/evidence/2026-10-17-finqa-sem-teto-l4.md)
  viu A repetir até 945 + 3151 = 4096 tokens e B parar após 20 tokens com
  conteúdo insuficiente. O [replay SSE](../../../runpod/serving/evidence/2026-10-17-streaming-bancada-l4.md)
  confirmou que A chega completo ao backend, sem HTTP 524 ou OOM observados.
- A Bancada usou pacote integrado de 945 tokens e temperatura 0,2. O
  protocolo histórico em `FineTuning/configs/eval/` usa geração determinística
  e `max_new_tokens` 24/32. Portanto, os testes anteriores não isolam
  adapter, prompt, parâmetros, base revision ou parser como causa.
- O servidor `runpod/serving/serving.py` fixa `--max-model-len 4096`.
  O backend recusa corretamente `finish_reason=length` como resposta
  completa. A configuração de 24 GB mostrou uso próximo de 21,5 GB de VRAM
  na geração longa; ampliar a janela exige medição, não suposição.
- `FineTuning/AGENTS.md` define a prioridade do protocolo, YAML, manifests e
  resultados. A revisão exata da base do treino histórico não foi fixada;
  a revisão da sessão de serving não prova equivalência aos pesos do treino.

## Scope

- Auditar offline manifests, configs, templates, código de formatação,
  tokenizer, outputs brutos preservados e hashes dos FT-FinQA A/B e da base.
  Distinguir fatos observados, hipóteses e lacunas.
- Preparar uma matriz pequena e versionada de casos diagnósticos com a mesma
  pergunta/evidência e parâmetros explícitos para base, A e B: pelo menos
  formato do protocolo histórico e formato atual da Bancada. Usar limites
  explícitos de saída apenas nos ensaios diagnósticos; não reintroduzir teto
  padrão oculto na Bancada. Comparar conteúdo, parada, repetição, contexto,
  tool calls, duração, uso e identidade do modelo.
- Corrigir código/configuração quando a evidência localizar defeito no
  prompt/template, montagem de mensagens, parâmetros, parser ou serving.
  Versionar qualquer mudança de prompt/protocolo e manter os runs antigos
  legíveis; não chamar truncamento de resposta válida.
- Preparar ensaio remoto curto e reprodutível para os sete aliases, com
  preflight de hashes/revisões, estimativa de custo, limite de tempo e recibos.
  Executar RunPod somente após autorização específica da sessão; parar e
  conferir cobrança residual ao final.
- Registrar conclusão limitada: diferença de comportamento não é acurácia
  científica. Qualquer retraining ou seleção de novos pesos depende de
  contrato/decisão científica explícita depois do diagnóstico.

## Non-scope

- Groq, correções de login, UI de sessão ou integração de provedor externo;
  isso pertence à SPEC-010.
- Alterar splits, dados congelados, pesos, checkpoints, manifests históricos,
  métricas/predições brutas ou texto editorial do artigo.
- Treino/re-treino, escolha de novo checkpoint, mudança silenciosa de
  hiperparâmetros ou afirmação de melhora de acurácia sem benchmark formal.
- Ligar Pod, abrir ngrok ou aplicar Terraform pela mera existência desta SPEC.
- Implementar o harness científico ou promover `answered_unverified` a
  resultado validado.

## Requirements

- REQ-001: Inventário por alias da base, adapter, bateria, hash dos pesos,
  configuração registrada, revisão conhecida/desconhecida da base e formato
  de prompt. Preservar links para a run exata e os recibos de 17/10/2026.
- REQ-002: A matriz diagnóstica isola uma variável por condição: modelo,
  template/prompt ou parâmetros. Nunca atribuir a uma única variável uma
  diferença observada quando outras mudaram. Registrar tokens de entrada,
  limite explícito de saída, janela total, temperatura, top_p, stop e versão
  de serving/cliente.
- REQ-003: Checar se o texto bruto da repetição/fragmento vem do vLLM ou
  resulta da reconstrução SSE, inclusive deltas de tool e `finish_reason`.
  Testes locais com fluxos sintéticos devem cobrir parser e classificação.
- REQ-004: O diagnóstico distingue (a) modelo gerou saída inadequada,
  (b) resposta válida foi truncada por configuração, (c) parser/serviço
  classificou incorretamente, (d) limite de VRAM/infra, ou `unresolved`.
  `finish_reason=length` permanece erro de resposta incompleta.
- REQ-005: Se a correção for de código/configuração, acrescentar teste que
  reproduz o defeito, atualizar READMEs/docs afetados e registrar o efeito
  sobre comparabilidade. Não modificar runs históricos; novos runs ganham
  identidade de condição distinta.
- REQ-006: O ensaio remoto proposto começa por `serving.py validate` e
  `verify_remote.py`, usa os hashes do manifesto e a revisão da base da
  sessão, executa condições pareadas e registra saídas brutas protegidas,
  status, uso e custo. Antes da execução paga, obter autorização explícita
  para Pod, teto de tempo/custo e, se necessário, ngrok. Ao terminar, parar
  Pod e verificar custo residual no console.
- REQ-007: Se a análise apontar peso/treino como hipótese principal,
  documentar critérios para um novo experimento e a decisão científica
  pendente. Não regravar adapter, fazer fine-tuning ou eleger vencedor nesta
  SPEC. Se a causa continuar não isolada, relatar `unresolved` com o próximo
  teste discriminante e sua estimativa de custo.

## Business or domain rules

- BR-001: As Baterias A (1024) e B (4096) e suas métricas históricas são
  condições diferentes. O status `completed` no manifest confirma a run,
  não qualidade da resposta atual na Bancada.
- BR-002: A comparação científica exige mesmo caso, evidência, template,
  política de geração e base conhecida. Ensaios diagnósticos da Bancada não
  viram benchmark oficial por estarem pareados.
- BR-003: Não há geração ilimitada: qualquer servidor tem janela/contexto finito.
  A ausência de `max_tokens` na aplicação não suspende `max-model-len`.

## Decisions already made

- Esta é a segunda fase e usa outro chat. A SPEC-010 estabiliza a plataforma;
  antes de qualquer escrita compartilhada, confirmar que a thread 010
  terminou sua escrita ou isolou o checkout de forma acordada.
- O diagnóstico precede mudança de pesos. Correções de código/configuração
  entram apenas quando a causa for demonstrada. Nova rodada de treino exigirá
  decisão e contrato posteriores.
- RunPod e qualquer gasto exigem autorização específica posterior; o trabalho
  offline e os testes simulados podem avançar sem Pod.

## Constraints

- Ler `FineTuning/AGENTS.md` e suas fontes na ordem declarada. Preservar
  material científico e não editar Google Doc ou exportações do artigo.
- O checkout está modificado desde o replay; registrar HEAD/diff antes de
  trabalhar e não limpar nem sobrescrever mudanças da SPEC-010.
- Quando faltarem arquivos de respostas brutas ignorados do Git, registrar a
  lacuna; não inferir seu conteúdo somente do resumo Markdown.

## Acceptance criteria

- AC-001: Relatório de diagnóstico identifica para A e B o que foi observado,
  o que é hipótese e quais variáveis diferem do protocolo histórico, com
  hashes, manifests e runs verificáveis.
- AC-002: Testes locais demonstram parser SSE, motivo de parada e estados de
  erro corretos; qualquer ajuste aplicado tem reprodução antes/depois e
  documentação sincronizada.
- AC-003: Matriz pareada e script/roteiro remoto estão prontos, com preflight,
  teto de gasto proposto, recibos esperados e parada. Sem autorização de
  custo, o relatório marca validação real pendente; não declara os modelos
  corrigidos.
- AC-004: Após execução remota especificamente autorizada, os novos runs
  mostram se a correção resolveu repetição/fragmento sob as condições
  declaradas, sem mascarar `length` ou inventar acurácia. Se não resolver,
  registrar `unresolved` ou necessidade de novo experimento.
- AC-005: Revisão independente confere proveniência científica, preservação
  dos artefatos, separação de hipóteses e provas e custo autorizado.

## Affected areas

- `FineTuning/` para leitura de protocolo, YAML, manifests e resultados;
  mudanças somente em código/docs de inferência se a causa for demonstrada.
- `inference_api/src/inference_api/` e `runpod/serving/` para parser/serving,
  testes, evidências e READMEs; `specs/README.md` e arquitetura se o fluxo
  mudar. `BancoModeloUse/` é referência de evidência, não alvo de carga.

## References

- `AGENTS.md`, `README.md`, `FineTuning/AGENTS.md`,
  `FineTuning/CONTEXT_SUMMARY.md` e `FineTuning/docs/protocol_v1.md`:
  limites de pesquisa e prioridade das fontes.
- `FineTuning/configs/eval/base.yaml`, `base_bateria_a.yaml`,
  `FineTuning/docs/modelos_disponiveis.md` e manifests das runs:
  condições e identidade de A/B.
- `runpod/README.md`, `runpod/serving/README.md`, `manifest.json`,
  `serving.py`, `verify_remote.py` e os três registros de 17/10/2026:
  serving e observações reais.
- `inference_api/README.md`, `docs/arquitetura_inferencia_compartilhada.md`,
  `models.py`, `service.py` e `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`:
  contrato da Bancada e fronteira científica.

## Skills

Nenhuma skill especializada é obrigatória para implementar correção de
inferência. Se houver mudança de protocolo experimental, seguir
`FineTuning/AGENTS.md`; revisão científica independente é obrigatória.

## Validation requirements

- VAL-001: `git diff --check`.
- VAL-002: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v`.
- VAL-003: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -p test_serving.py -v`.
- VAL-004: Checar SHA-256 dos seis adapters contra
  `FineTuning/docs/modelos_disponiveis.md` e `runpod/serving/manifest.json`,
  sem editar os pesos.
- VAL-005: Testar localmente matriz de parser/stop/uso com respostas sintéticas
  e comparar configurações versionadas. Toda execução real exige gate
  separado de custo e credencial.
- VAL-006: Inspecionar diff, documentação, manifests, dados/resultados
  protegidos e recibos antes da revisão independente.

## Review requirements

Revisão independente crítica. Conferir que causa de adapter não foi inferida
somente de truncamento, que condições comparadas são declaradas e que nenhuma
mudança científica ou execução paga ocorreu sem gate próprio.

## Execution and runtime

Ver `SPEC.execution.json`. O segundo chat começa por inventário e diagnóstico
somente leitura enquanto a SPEC-010 escreve no checkout. Implementação e
testes que escrevam esperam a reconciliação da primeira fase. A ausência de
autorização para Pod limita a conclusão ao estágio local/diagnóstico.
