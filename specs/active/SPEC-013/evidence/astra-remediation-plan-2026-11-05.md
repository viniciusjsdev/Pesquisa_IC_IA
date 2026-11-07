# Correções da auditoria de engenharia

A auditoria inicial Astra identificou oito lacunas (parecer no arquivo
astra-initial-engineering-review-2026-11-05.md). Não é revisão final aprovada.

Antes de novo ensaio real, o teto de três consultas passa a contar todas as
invocações do adaptador, inclusive rejeitadas, de modo conservador. O contador
de resultados aceitos permanece separado. Estouro de linhas ou bytes encerra
o caminho real sem correção/reexecução. Os limites efetivos e ambas as contagens
ficam no snapshot, preservando snapshots anteriores.

As demais correções técnicas a reconciliar antes do done são: contexto do
Planejador com evidências e lacunas; tentativa recusada no feedback; dependências
reais no trace; tamanho completo das mensagens; todas as tentativas do Redator
na UI; comparabilidade de contratos/mapas/limites; hash do run na adjudicação.
Cada alteração terá teste de regressão; nenhuma exige adjudicar modelos reais.

Após as [três repetições OpenAI](openai-ui-three-runs-2026-11-05.md), o
[parecer complementar](astra-three-runs-review-2026-11-05.md) acrescenta:
tipos/operadores/restrições/obrigatoriedade dos filtros no contexto do
Planejador; saldo atualizado nas correções; ressalvas e referências na resposta
visível; cobertura explícita de resultados aceitos sem truncamento. Não houve
implementação dessas correções durante a bateria, para preservar a configuração.
