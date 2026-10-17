# Frentes de inferência e dados

Cada SPEC é uma unidade de implementação. O estado das frentes deve ser lido em
`SPEC.md` e `SPEC.execution.json`; este índice mostra somente a ordem e os
limites. As SPECs 001–006 têm threads dedicadas registradas nos manifests;
retomadas devem usar seus IDs. A SPEC-007 foi implementada localmente em
16/10/2026 e tem thread efetiva registrada no manifest. As
[revisões independentes da SPEC-006](active/SPEC-006/evidence/review.json) e da
[SPEC-007](active/SPEC-007/evidence/review.json) aprovaram o escopo local nessa data.
A SPEC-008 foi revisada em 16/10/2026 (contrato v2) para incluir execução
local via Docker Compose com banco isolado. A implementação local na thread
registrada no manifest foi [aprovada na quinta rodada de revisão independente](active/SPEC-008/evidence/review.json)
em 16/10/2026. O front ativo agora é React, com snapshot BI protegido pela
sessão. Os bancos reais não foram copiados.
A primeira API e os contratos foram incluídos em `622fc0f`; a SPEC-002 foi
registrada em `513114d`. As implementações e revisões locais das SPECs 006–008
em 16/10/2026 têm evidências próprias nos respectivos diretórios.

| Ordem | SPEC | Frente | Dependência de execução |
| --- | --- | --- | --- |
| 1 | [SPEC-001](active/SPEC-001/SPEC.md) | Orquestração de agentes, ferramentas de dados e contrato de evidências | Primeira |
| 2 | [SPEC-002](active/SPEC-002/SPEC.md) | Serving vLLM e proveniência dos modelos na RunPod | Contrato de aliases atual; integração final com SPEC-001 |
| 3 | [SPEC-003](active/SPEC-003/SPEC.md) | Identidade individual, autorização e limites de uso | API atual; revisar interação com SPEC-001 |
| 4 | [SPEC-004](active/SPEC-004/SPEC.md) | Bancada web de prompts, verificações e comparação | SPEC-001 e SPEC-003 |
| 5 | [SPEC-005](active/SPEC-005/SPEC.md) | Validação integrada e procedimento da sessão curta | SPEC-001 a SPEC-004 |
| 6 | [SPEC-006](active/SPEC-006/SPEC.md) | DW local rastreável para análise industrial e financeira | `done` no escopo local; não altera a API das SPECs 001 a 005 |
| 7 | [SPEC-007](active/SPEC-007/SPEC.md) | Exportar pacotes fixos de evidência do DW, sem LLM ou gabarito | `done` no escopo local; gold set e caso científico oficial seguem pendentes |
| 8 | [SPEC-008](active/SPEC-008/SPEC.md) | Observatório unificado com Bancada de testes após login, modo host e Docker local | `done` no escopo local, revisão independente aprovada; cluster Windows preservado |
| 9 | [SPEC-009](active/SPEC-009/SPEC.md) | Alternância explícita na Bancada entre pacote fixo da DW e tools escolhidas pela LLM | `done` no escopo local, [revisão independente aprovada](active/SPEC-009/evidence/review.json); sem execução remota nem cópia real do DW |

A SPEC-001 foi implementada localmente e aprovada em revisão independente em
14/10/2026. A SPEC-002 tem implementação local de manifesto, scripts e
Terraform e um [runbook de custos e aplicação futura](../runpod/serving/README.md).
Sua [revisão independente](active/SPEC-002/evidence/review.json) aprovou o
contrato local em 15/10/2026 sem Pod: geração e validação remota ficam para outra sessão,
e `terraform apply` depende de confirmação explícita. Em 15/10/2026 o usuário
definiu para a SPEC-003 somente Nicoli e Vinicius: ambos podem ficar logados,
mas apenas uma inferência global ocorre por vez, sem limite diário. O painel
mostra teto manual de US$ 10 e saldo RunPod confirmado por leitura quando
disponível. A implementação local e os testes da SPEC-003 constam da
[evidência de 15/10/2026](active/SPEC-003/evidence/local-2026-10-15.md);
a [revisão independente](active/SPEC-003/evidence/review.json) aprovou o
escopo local. O usuário escolheu autenticação somente na aplicação, sem OAuth
ou Basic Auth no ngrok. Antes da exposição futura, as senhas escolhidas no
chat devem ser trocadas em terminal local. A aprovação não cobre ngrok ou
avaliação científica. A revisão independente da SPEC-006 foi concluída
separadamente em 16/10/2026 para a carga local.

Em 15/10/2026, a SPEC-004 foi implementada localmente sobre `1e8cb76` com
revisões declarativas de critérios e comparação visual. A migração 002 passou
em banco descartável e foi aplicada em `db_inference_app` após backup lógico;
a UI passou em navegador com API simulada. A
[revisão independente](active/SPEC-004/evidence/review.json) aprovou o escopo
local em 15/10/2026; esses testes não provam inferência remota.

Em 16/10/2026, a SPEC-005 recebeu pré-voo local, ensaio HTTP opt-in e
[runbook da sessão curta](../docs/sessao_inferencia_curta.md). A validação
local tem recibo e [revisão independente](active/SPEC-005/evidence/review.json)
aprovada. O router não pôde abrir uma thread SDK porque falta
`.codex/references/runtime-policy.json`; a revisão foi feita por subagente
separado, em leitura. O contrato está `done` no escopo local. Geração remota,
ngrok e encerramento real de recursos continuam não executados.

As threads são separadas para manter o contexto de cada frente. Todas usam o
mesmo checkout local; só uma deve escrever nele por vez. A thread seguinte
confere o estado do Git e os contratos concluídos antes de editar. Revisão
independente é exigida onde o manifest indicar. Nenhuma SPEC autoriza iniciar
Pod, abrir ngrok, gastar créditos, publicar ou alterar dados científicos. A
SPEC-006 autorizou uma carga local em `db_pesquisa_dw` após verificar as fontes;
ela não modifica os dois bancos de origem nem o banco da aplicação. A SPEC-007
não autoriza nova carga: sua exportação local usa somente leitura. A SPEC-009
contrata a escolha de tools pela LLM **para runs exploratórios da Bancada** e
o uso dos pacotes candidatos da SPEC-007 no outro modo. Ela não define gold
set, rubrica ou pontuação científica; o harness formal ainda exige contrato
separado, conforme a arquitetura de avaliação.

Fonte de verdade científica: [`BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`](../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md).
Topologia: [`docs/arquitetura_inferencia_compartilhada.md`](../docs/arquitetura_inferencia_compartilhada.md).
