# M3 parcial · avaliador pós-run isolado (01/11/2026)

`model_evaluation/harness_score.py` foi acrescentado como função offline.
Recebe o snapshot **após** a resposta, um caso separado e uma adjudicação
separada. Sem caso aprovado por pessoa identificada: `not_scored`. Sem revisão
do run: `awaiting_run_review`, com checks automáticos de rota e integridade de
referências, mas `scores: null`. Cálculo e conclusão só recebem pontuação de
uma adjudicação vinculada ao run e ao hash exato do caso.

O teste `model_evaluation/tests/test_harness_score.py` usa caso e revisão
**fictícios** para controlar: rota equivalente, ausência de linha, referência
inventada, mudança da pergunta, run incompleto e adjudicação com hash antigo.
`python -m unittest discover -s model_evaluation/tests -v` passou: 14 testes
incluindo os 4 novos. A suíte da API passou: 107 testes, 8 ignorados por gates
de integração. No frontend, `tsc -b`, ESLint e Vitest passaram (4 arquivos,
8 testes), assim como o build Vite. O comando `npm` não está no PATH desta
sessão; as ferramentas foram executadas pelo `node.exe` do runtime local.
`git diff --check` passou.

Esta implementação não prova que os checks automáticos capturam validade
semântica. Não há casos científicos selecionados ou gabaritos reais aprovados,
nem consultas de referência reexecutadas, rubrica final, repetições ou revisão
independente. Nenhum provedor foi chamado neste ensaio.
