# Auditoria sintética da cadeia de agentes via OpenAI — 01/11/2026

O pesquisador autorizou usar a API da OpenAI para um teste plausível da
engenharia e arquitetura. Esta auditoria executou **somente a pergunta, os
mapas e a fixture inventados** da SPEC-013; não leu PostgreSQL, não enviou
dados reais, não acionou RunPod e não criou um modo OpenAI na Bancada.
O adaptador de diagnóstico usa o cliente Responses já existente com
`gpt-6-luna`, `store: false`, contexto novo por papel, até 16 chamadas e
4.096 tokens de saída por chamada. Erros de provedor não são reenviados.
Os quatro runs preservam trace, entradas e saídas por papel, IDs de resposta
e uso reportado pelo provedor:

| Trace | Chamadas | Consultas sintéticas | Resultado e achado |
| --- | ---: | ---: | --- |
| [1](openai-synthetic-audit-2026-11-01.json) | 6 | 0 | `contract_error`: A3 confundiu IDs do mapa com IDs de resultados em `evidence_refs`. |
| [2](openai-synthetic-audit-corrected-2026-11-01.json) | 2 | 0 | O Analista marcou toda a pergunta como intratável por causa da parte causal; o motor então aceitou uma resposta sem evidência. Esse estado foi corrigido para exigir encaminhamento das medidas e marcar ausência de observação como `insufficient_evidence`. |
| [3](openai-synthetic-audit-measurable-2026-11-01.json) | 12 | 2 | A1–A4 alcançaram a DW e a fonte financeira fictícias. A5 escreveu descrições em vez de IDs exatos; o teto de 12 chamadas impediu feedback final. |
| [4](openai-synthetic-audit-final-2026-11-01.json) | 11 | 2 | `answered_unverified`: sequência completa A1 → A2a DW/financeiro → A2b → A3 → consulta sintética → A4 → aprofundamento financeiro → A5. |

No quarto run, `result_01` continha 45 minutos de parada na linha fictícia L1
em 2020 e `result_02` uma observação de lucro líquido fictício de 1.200 em
31/12/2020. O Revisor julgou o primeiro resultado insuficiente e pediu a
fonte financeira; após o segundo, julgou suficiente para responder com
ressalvas. A resposta final citou exatamente `result_01` e `result_02`,
reportou ambos os valores e afirmou que eles não provam causalidade. Não
generalizou a observação financeira para um total anual.

Após o run, a fixture passou a aplicar filtros tipados e rejeitar filtros
desconhecidos. Um replay **local, sem nova chamada de modelo** dos dois planos
salvos no quarto trace devolveu exatamente os mesmos `rows`, `coverage` e
`units` (`replay_matches 2`). Testes adicionais cobrem ano fora da cobertura,
intervalo financeiro sem observação e filtro não permitido. Um filtro recusado
agora retorna ao Planejador uma vez com erro e dica no trace; esse caminho foi
validado localmente, sem nova chamada à API.

As quatro execuções consumiram, segundo os campos `usage` dos traces,
21.217 tokens de entrada e 9.285 de saída. Pelas [tarifas Standard publicadas
para GPT-6 Luna em 01/11/2026](https://developers.openai.com/api/docs/pricing)
(US$ 0,10/1M entrada; US$ 0,50/1M saída), isso equivale a uma **estimativa**
de US$ 0,0068, não a um recibo de cobrança da conta. Os tokens de raciocínio
estão incluídos nos tokens de saída reportados pela API.

Validação posterior: `unittest discover -s inference_api/tests -q` passou com
90 testes (8 pulados por integração opcional); os 22 testes do núcleo
multiagente passaram. `git diff --check` passou. Os 11 JSONs de evidência da
SPEC-013 foram lidos como JSON válido, e a busca por marcadores de chave ou
bearer nos quatro traces OpenAI não encontrou ocorrências.

O teste confirma a cadeia sintética **direta pelo motor**, não a execução
autenticada por HTTP/jobs/UI, o persistir do snapshot v6 no banco da
aplicação, o acesso seguro aos bancos reais, a qualidade de modelos treinados
ou a validade científica da comparação. Os contratos mudaram entre os runs
de diagnóstico; esses quatro resultados não constituem um experimento
controlado entre modelos. A SPEC permanece em `design`.
