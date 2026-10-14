# Frentes de inferência e dados

Cada SPEC é uma unidade de implementação. O estado das frentes deve ser lido em
`SPEC.md` e `SPEC.execution.json`; este índice mostra somente a ordem e os
limites. As SPECs 001–006 têm threads dedicadas registradas nos manifests;
retomadas devem usar seus IDs. A SPEC-007 foi preparada como contrato futuro,
com `thread_id: null`; nenhuma nova thread ou execução foi iniciada. As mudanças
locais em `inference_api/` anteriores a estas SPECs ainda estão sem commit e são
a base de trabalho compartilhada.

| Ordem | SPEC | Frente | Dependência de execução |
| --- | --- | --- | --- |
| 1 | [SPEC-001](active/SPEC-001/SPEC.md) | Orquestração de agentes, ferramentas de dados e contrato de evidências | Primeira |
| 2 | [SPEC-002](active/SPEC-002/SPEC.md) | Serving vLLM e proveniência dos modelos na RunPod | Contrato de aliases atual; integração final com SPEC-001 |
| 3 | [SPEC-003](active/SPEC-003/SPEC.md) | Identidade individual, autorização e limites de uso | API atual; revisar interação com SPEC-001 |
| 4 | [SPEC-004](active/SPEC-004/SPEC.md) | Bancada web de prompts, verificações e comparação | SPEC-001 e SPEC-003 |
| 5 | [SPEC-005](active/SPEC-005/SPEC.md) | Validação integrada e procedimento da sessão curta | SPEC-001 a SPEC-004 |
| 6 | [SPEC-006](active/SPEC-006/SPEC.md) | DW local rastreável para análise industrial e financeira | Frente separada; não altera a API das SPECs 001 a 005 |
| 7 | [SPEC-007](active/SPEC-007/SPEC.md) | Exportar pacotes fixos de evidência do DW, sem LLM ou gabarito | Implementação local futura; revisão da SPEC-006 antes de uso como caso científico oficial |

A SPEC-001 foi implementada localmente e aprovada em revisão independente em
14/10/2026. Sua conclusão não cobre serving remoto, ngrok ou avaliação
científica. A revisão independente da SPEC-006 permanece separada.

As threads são separadas para manter o contexto de cada frente. Todas usam o
mesmo checkout local; só uma deve escrever nele por vez. A thread seguinte
confere o estado do Git e os contratos concluídos antes de editar. Revisão
independente é exigida onde o manifest indicar. Nenhuma SPEC autoriza iniciar
Pod, abrir ngrok, gastar créditos, publicar ou alterar dados científicos. A
SPEC-006 autorizou uma carga local em `db_pesquisa_dw` após verificar as fontes;
ela não modifica os dois bancos de origem nem o banco da aplicação. A SPEC-007
não autoriza nova carga: sua futura exportação será somente leitura. O cenário
de escolha de tools pela LLM e a pontuação científica formal ainda precisam de
contratos próprios, conforme a arquitetura de avaliação.

Fonte de verdade científica: [`BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`](../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md).
Topologia: [`docs/arquitetura_inferencia_compartilhada.md`](../docs/arquitetura_inferencia_compartilhada.md).
