# Contrato 3 — execução real pela Bancada em 06/11/2026

Uma execução autorizada pelo pesquisador, iniciada pelo Chrome após seu login,
completou o fluxo sem Planejador separado. Base do checkout: `13d7df5`, com
alterações compartilhadas preservadas e sem commit novo. Este registro sucede
os [testes locais da implementação](specialist-query-implementation-2026-11-06.md).

## Configuração e recibo

- Provedor/modelo: OpenAI `gpt-6-luna`, raciocínio médio, temperatura omitida.
- Sem teto de tokens ou bytes de saída imposto pela aplicação nesta rodada;
  limites nativos do provedor continuam aplicáveis. `store=false`.
- Até 48 chamadas, 3 tentativas de consulta, 20 linhas por consulta,
  entrada/resultado de até 32.768 bytes e uma correção por papel.
- API `127.0.0.1:8765`; PostgreSQL isolado `127.0.0.1:5544`.
- Job `a17437ad-680a-4c68-9280-5cc45efcd8b6`.
- Run `769ecfc1-62a0-42a1-9fdf-95bbe9f2ea36`.
- Início 13:17:45 e fim 13:18:52, horário de São Paulo; duração 67,2 s.
- Job `completed`; resposta `answered_unverified`, sem pontuação científica.

Pergunta enviada:

> Em 2021, qual agregado de parada da máquina 2000002 está na DW, quais paradas geradas da mesma máquina/período aparecem no industrial e quais observações financeiras existem, sem atribuir relação causal?

## Resultado observado

| Rodada | Fonte consultada | Retorno |
| --- | --- | --- |
| 1 | DW, `machine` | Uma linha agregada: 38 paradas e 3.421 minutos |
| 2 | Industrial, `paradas_maquinas_geradas` | 13 eventos gerados da máquina e período |
| 3 | Financeiro, `resultados_financeiros` | 13 observações datadas, sem vínculo de máquina |

O Analista identificou os três domínios. Selecionador e Especialista trabalharam
em cada rodada; o Revisor pediu aprofundamento após DW e industrial, e considerou
a evidência suficiente após financeiro. O Redator usou `result_01`, `result_02`
e `result_03`. Houve 12 chamadas de modelo e três consultas/tentativas no backend.
Nenhum papel Planejador aparece no trace. Todas as chamadas terminaram com `stop`.
Uso reportado: 45.379 tokens de entrada, 5.655 de saída, total 51.034. Tokens de
saída incluem raciocínio contabilizado pelo provedor; não são apenas o JSON visível.
Maior saída JSON registrada: 1.824 bytes. Uma rodada não define o limite ideal.

## Recusa e recuperação

`call_09`, Especialista financeiro, recebeu o contrato correto, mas devolveu
`grao=id/data_registro/source_period`. O contrato exige o identificador literal
`id/observation_date/source_period`; campos, filtros, fonte e limite eram válidos.
O validador recusou com `plan_outside_selected_map` antes de chamar a ferramenta.

`call_10` recebeu o contrato completo, a saída recusada, o erro e o saldo atualizado
(uma consulta restante, 39 chamadas restantes). Corrigiu o grão e foi validada;
`tool_03` executou a leitura financeira. A tentativa de correção consumiu uma chamada
de modelo; não houve consulta ao banco para o plano recusado. Isso demonstra o ciclo
de recuperação desta execução, sem prometer ausência de erros futuros do modelo.

Não houve falha de banco/provedor durante a execução. A API estava parada no
preflight e foi reiniciada; a causa da parada anterior não foi estabelecida.

## Persistência, interface e limites

Conferidos job e snapshot persistidos, trajetória na UI e entrada do histórico
de 06/11/2026 às 13:18:52. O registro foi reaberto pelo histórico. A interface
mostra a recusa e a tentativa 2, com entrada e saída consultáveis.

Artefatos privados, fora do material científico versionado:

- `inference_api/.local/spec013-contract3-openai-ui-20261106.json`:
  SHA-256 `8ae24c1cd61e9b2e2ebf60ce3c9542d79f71145d2a8cc22fca2dffc4d25fe356`.
- Resumo no mesmo diretório: `spec013-contract3-openai-ui-20261106-summary.json`.
- Capturas: `spec013-contract3-preflight-20261106.png`,
  `spec013-contract3-history-20261106.png` e
  `spec013-contract3-correction-20261106.png`; resumo visual em
  `spec013-contract3-completed-20261106.png`.

O JSON final preserva ressalvas sobre dados sintéticos, cobertura e ausência de
causalidade. O bloco principal da resposta na UI ainda não apresenta as ressalvas
separadas; este é um achado de apresentação já aberto, não aprovação dessa tela.
Não houve ingestão nem escrita nos bancos de pesquisa. Houve envio autorizado à
OpenAI e gravação do job/run no banco da aplicação. Nenhum gabarito foi enviado.

Esta evidência confirma uma cadeia real completa do contrato 3. Não elimina
pendências de engenharia anteriores, não demonstra superioridade estatística e
não conclui a SPEC, que permanece `in_progress`. A revisão científica das respostas
permanece na fase posterior, separada da auditoria técnica desta execução.

## Auditoria independente desta execução

Astra, chat `01a1ae0e-a4d7-70b3-8379-e67fb4288ead`, turno
`01a1b1aa-e679-7860-b3da-2b3de1dbfd8f`, somente leitura, sem acesso a banco
ou provedor. Parecer concluído em 06/11/2026: cadeia real confirmada e nenhuma
nova falha de execução encontrada neste run. Conferiu hash do export, contratos
atuais, projeções do catálogo, propagação das evidências e correspondência
mecânica dos números/datas/IDs da resposta com os resultados persistidos.

Reconfirmou dois P2 anteriores: `source_event_ids` ainda representa uma janela
de três eventos, sem todas as dependências reais (por exemplo, o Redator recebe
três evidências, mas referencia apenas `call_10`, `tool_03`, `call_11`); a seção
final da UI renderiza apenas `resposta`, omitindo as ressalvas e referências
que estão salvas. A auditoria não aprovou a SPEC inteira nem atribuiu nota.

Após a conferência, API e PostgreSQL continuavam escutando nas portas acima,
com zero jobs `accepted/running`. Não foi iniciada uma segunda rodada.
