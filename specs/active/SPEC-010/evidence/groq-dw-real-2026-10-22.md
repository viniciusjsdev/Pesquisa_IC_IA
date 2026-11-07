# Extensão posterior à SPEC-010: Groq com DW real — 22/10/2026

Esta extensão foi autorizada explicitamente pelo pesquisador para enviar os
resultados das consultas fixas da DW à API externa da Groq. Ela fica fora do
escopo sintético originalmente aprovado na SPEC-010 e **não recebeu nova
revisão independente**. Checkout de implementação antes de commit:
`13d7df5c748f79387d34f39cd30b6cf82c96c869` mais diff local.

## Contrato implementado

- `provider=groq` aceita `evidence_mode=dw_tools` com pergunta e prompt livres.
  Os dois modos sintéticos continuam com prompt fixo; `dw_snapshot` e pacotes
  privados continuam rejeitados para Groq.
- O catálogo anuncia as cinco tools fixas. A LLM escolhe uma; o backend valida
  nome e argumentos e consulta `db_pesquisa_dw` em transação somente leitura.
  Não há SQL livre. Limites: cinco chamadas, seis turnos, 200 linhas e 16 KiB
  de resultados cumulativos.
- A primeira requisição externa leva pergunta, prompt e catálogo. Quando uma
  consulta é concluída, o turno seguinte leva o resultado da DW à Groq. O
  snapshot v4 registra modo, fingerprint, tool trace, turnos, destino e uso.

## Validação local

| Verificação | Resultado |
| --- | --- |
| `python -m unittest discover -s inference_api/tests` na venv local | 58 testes, OK; 8 ignorados por condições de ambiente. |
| TypeScript `tsc -b --pretty false`, ESLint e Vite build | Passaram. |
| Teste simulado do serviço | Groq escolheu `product`; somente o resultado validado da DW foi incluído no turno seguinte. Tool `sql` foi recusada sem consulta. |
| Bancada autenticada em `127.0.0.1:8765` | Na sessão de Vinicius foi selecionado o novo modo; a DW informou disponível antes do envio. |

## Um ensaio real sem reenvio

Pergunta limitada ao produto `1000001` e ano `2020`, sobre operações e vendas
observadas. O prompt exploratório padrão foi mantido. O job
`24f89a8c-86a8-4d46-a2f2-31c9af7375b0` recebeu HTTP 202 e gerou o run
`3a53255e-196b-4c9d-bc60-fc0d4f11c96e`, persistido no histórico da Bancada
com autor autenticado `Vinicius` e estado `answered_unverified`.

O modelo servido foi `openai/gpt-oss-120b`. Em dois turnos, a Groq escolheu
`product(year=2020,id=1000001)`; o backend executou uma consulta somente
leitura, retornou uma linha e enviou o resultado de 780 bytes à Groq. O
fingerprint lido no snapshot é
`64493abfdfd0b87535778eafd9d5938fad6039a99d9307f85e4cfc6eec0e89f2`.
O último turno informou `finish_reason=stop` e 1.377 tokens totais. O readback
do run persistido confirmou `provider=groq`, `evidence_mode=dw_tools`, uma
tool concluída, dois turnos, destino
`https://api.groq.com/openai/v1/chat/completions` e identidade verificada.
O readback do job confirmou `completed` e vínculo ao mesmo run; o primeiro
turno terminou em `tool_calls`, e o conteúdo da mensagem `tool` no segundo
turno coincidiu byte a byte com o JSON canônico do resultado salvo.
Não houve RunPod, ngrok, migração ou alteração da carga DW.

O resultado comprova o caminho Bancada → Groq → escolha de tool → DW → Groq →
histórico para **esta pergunta**. O texto do modelo não foi conferido contra
gabarito; checks de verdade numérica, causalidade e IDs citados ficaram
`not_checked`. O status `answered_unverified` é exploratório. A chave e os
corpos completos das mensagens externas não foram copiados para esta evidência;
o snapshot autenticado preserva os turnos e o resultado integral para auditoria.
