# Dependências reais e resposta completa — 06/11/2026

Escopo autorizado: corrigir os dois P2 confirmados no ensaio
`769ecfc1-62a0-42a1-9fdf-95bbe9f2ea36` e validar. Checkout base `13d7df5`,
com alterações compartilhadas preservadas; sem commit novo.

## Alterações

Contrato documentado antes do código em
[specialist-query-contract.md](../specialist-query-contract.md). A mudança
cumpre o desenho existente, sem trocar agentes, decisões ou modelagem dos bancos.

- `engine.py`: substituída a janela dos últimos três eventos por dependências
  diretas da entrada. Registra produtores da análise, rota, projeção, lacuna,
  evidências e feedback. Projeções e tools também apontam para seus produtores,
  sem alterar o plano recebido pelo executor. IDs são deduplicados e ordenados
  pelo trace; IDs inexistentes/futuros são recusados como erro interno.
- Resultado novo identifica `dependency_policy=direct_input_events_v1`.
  Snapshots históricos não foram reescritos e mantêm sua rastreabilidade original.
- `HarnessRounds.tsx`: a seção final exibe ressalvas, cálculos e referências
  com fonte/grão registrados. Todas as tentativas do Redator são selecionáveis,
  incluindo rejeição, saída bruta e recuperação. Campos ausentes em snapshots
  antigos não são inventados. Referências sem detalhe são identificadas.

## Verificação

| Verificação | Resultado |
| --- | --- |
| Backend completo, `unittest discover -s inference_api/tests -q` | 135 testes, zero falhas, oito pulados |
| Regressões de contrato, `test_specialist_query_contract.py` | 11 aprovadas |
| Avaliador, `unittest discover -s model_evaluation/tests -q` | 19 aprovados |
| Frontend, `validate_frontend.py test` | 12 aprovados |
| Frontend typecheck, lint e build | Aprovados |
| Replay offline da execução real salva | 12 chamadas reproduzidas, três resultados, mesma resposta e evidências |
| Bancada no Chrome, após recompilar/reiniciar | Histórico autenticado aberto; três ressalvas e três referências visíveis |

O replay usa as saídas brutas salvas como transporte determinístico e os resultados
salvos como retorno das tools, sem banco ou provedor. Verifica que as entradas dos
papéis permanecem idênticas, os hashes dos mapas coincidem e somente os vínculos
do envelope mudam. O Redator passa a referenciar `tool_01`, `tool_02`, `tool_03`
e `call_11`; a correção `call_10` inclui a tentativa recusada `call_09`.

Artefatos privados:

- `inference_api/.local/verify_dependency_replay_20261106.py`: procedimento de replay.
- `inference_api/.local/spec013-dependency-replay-20261106.json`:
  SHA-256 `faf21fb3dccf1e03a36aa61000c34360e9149d15c619b0af7e3efc29c11b4aac`.
- Snapshot original continua com SHA-256
  `8ae24c1cd61e9b2e2ebf60ce3c9542d79f71145d2a8cc22fca2dffc4d25fe356`.
- `inference_api/.local/spec013-answer-caveats-fixed-20261106.png`:
  captura da resposta histórica na interface recompilada, incluindo ressalvas/fontes.

A API foi reiniciada após conferir zero jobs ativos. A sessão do usuário continuou
válida. Não foi iniciada nova inferência externa nem regravado o run histórico.
O replay não foi inserido no histórico como se fosse nova inferência.
Os oito testes pulados não são contados como integração aprovada nesta validação.

## Limites de conclusão

Revisão independente Astra concluída no chat
`01a1ae0e-a4d7-70b3-8379-e67fb4288ead`, turno
`01a1b1ec-906a-71b0-a4a3-55a0ddfee0cb`: os dois P2 estão corrigidos no escopo
revisado, sem achados bloqueadores. O auditor executou 11 testes backend,
mais dois cenários adicionais e verificação interativa do componente em jsdom.
Conferiu descoberta adicional, rejeição de consulta/rota, encerramento sem
fonte e tentativas do Redator. Inspeção somente leitura, sem banco ou provedor.

Hashes do código conferido:

- `engine.py`: `b4dfe5914343c4d6ac00823dcb452ba70ec8914b47c8599506e4154c64511b5b`.
- `HarnessRounds.tsx`: `6bdf862d2f0a4e81226f5d76da45676b70e9e57f33fbf3b52885ae44f1ca0bad`.

Os ajustes aqui tratados não encerram automaticamente a SPEC. Permanecem fora
desta correção os apontamentos anteriores de medição do payload completo,
comparabilidade por hashes e vínculo da adjudicação. Revisão científica de
respostas continua posterior e não é bloqueio para a conclusão de engenharia.
Nenhuma pontuação científica foi atribuída.
