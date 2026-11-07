# Consulta construída pelo Especialista — 06/11/2026

Base do checkout: `13d7df5`, com alterações anteriores compartilhadas preservadas.
Sem commit novo. Escopo autorizado: diagramas primeiro, documentação depois,
seguida da retirada do Planejador separado. SPEC contrato 3, ainda `in_progress`.

## Entrega

1. Atualizada a página `rC3Onoxkcgc0oOyFh0Ck` no arquivo diagrams.net
   `G1RbtLePrWCTs8GjCAmAegFv7XBcAtzN8E`: fluxo geral, gatilhos/retornos,
   fichas com JSON dentro dos quadros e exemplo horizontal dos três bancos.
   A página do DER não foi editada. O editor informou alteração salva; leitura
   posterior do XML confirmou os 132 elementos e seus atributos/rótulos.
   [Snapshot editável](specialist-owned-query-flow-2026-11-06.drawio) e
   [captura da página](specialist-query-diagram-2026-11-06.png).
2. Documentado o [contrato 3](../specialist-query-contract.md), reconciliados
   SPEC.md, manifest, READMEs e arquitetura. Só depois foi alterado o motor.
3. Motor usa Analista, Selecionador, Especialista do domínio, Revisor e Redator.
   Contrato de saída v8 e entrada v7. Selector recebe índice estático; Especialista
   recebe pergunta literal, fonte completa, tipos/filtros, evidências e lacuna.
   Feedback traz output/plano recusado, evento e saldo atualizado. Backend
   permanece responsável pela validação e leitura. Não há SQL livre.
4. `filter_contracts` é derivado do executor, sem alterar o catálogo aprovado.
   Fixture sintética v2 usa o mesmo formato e intervalos `from`/`to`.
   Interface apresenta o Especialista montando consulta e mantém leitura dos
   papéis antigos somente para snapshots históricos.

## Verificação executada

| Verificação | Resultado |
| --- | --- |
| `python -m unittest discover -s inference_api/tests -q` | 132 testes, zero falhas, 8 pulados |
| `python -m unittest discover -s model_evaluation/tests -q` | 19 testes aprovados |
| Frontend `validate_frontend.py test` | 10 testes aprovados |
| Frontend typecheck, lint e build | Aprovados |
| SPEC.execution.json contra schema local v2 | Válido, contrato 3 |
| `git diff --check` | Sem erro; avisos de LF/CRLF em arquivos já modificados |
| Fixture com catálogo real e leituras simuladas dos três domínios | 11 chamadas e três consultas; sem papéis removidos |
| Recuperação | Plano recusado e saldo de 3 para 2 entregues ao mesmo Especialista |
| Bancada recarregada | Sessão restaurada; catálogo, revisões e histórico carregados |

A primeira passagem da suíte completa teve `WinError 10053` no HTTP local;
a suíte específica passou e a repetição completa terminou sem erro. Não se
atribuiu causa sem evidência. O erro esperado de CLI `rehearsal` nos logs faz
parte de um teste de argumento inválido, não é falha da suíte.

Antes do reinício havia zero jobs `accepted/running`. Serviço relançado em
`127.0.0.1:8765`, PID observado 50872, frontend recompilado. A interface foi
aberta no Chrome com a sessão do usuário. Nenhuma pergunta foi enviada e
nenhuma chamada nova foi feita à Groq/OpenAI/RunPod. Não houve nova ingestão,
alteração dos bancos de pesquisa, casos, gabaritos ou recibos aprovados.

## Revisão independente e limites

Auditor Astra no chat `01a1ae0e-a4d7-70b3-8379-e67fb4288ead`, somente leitura.
Primeiro parecer identificou dois P2: falta de tipos/filtros no consumidor
sintético e gates/documentação ainda descrevendo a arquitetura anterior.
Ambos foram corrigidos. Reconferência no turno
`01a1af34-081e-7813-990a-24cbd4830fb2`:
“As duas pendências desta alteração estão resolvidas. Não encontrei novos
defeitos no escopo reconferido.” O auditor executou nove testes direcionados,
sem acesso a bancos, credenciais ou provedores.

Este parecer é limitado à alteração. Achados anteriores de dependências do
trace, medição do payload completo, apresentação de ressalvas/tentativas do
Redator, comparação de runs e vínculo da adjudicação continuam separados.
O ensaio real de 05/11 pertence ao contrato anterior; não comprova este fluxo.
A matriz científica continua vinculada aos hashes anteriores e não foi
atualizada silenciosamente. Não há aprovação global da SPEC nem nota científica.
