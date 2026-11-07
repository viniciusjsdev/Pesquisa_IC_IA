# Três repetições pela Bancada — OpenAI, 05/11/2026

## Escopo e configuração

O pesquisador autorizou três execuções da mesma pergunta para observar a
estabilidade da engenharia, usando a interface autenticada da Bancada. Após
a queda anterior do PostgreSQL, autorizou expressamente nova tentativa. A
referência do job anterior foi verificada na UI como `interrupted`; o histórico
foi conferido e apenas a referência local foi descartada, preservando o job.

Pergunta: “Em 2021, qual agregado de parada da máquina 2000002 está na DW,
quais paradas geradas da mesma máquina/período aparecem no industrial e quais
observações financeiras existem, sem atribuir relação causal?”

Piloto `openai_harness_pilot`, gpt-6-luna, reasoning medium, temperatura não
aplicada, `store=false`, sem teto de tokens/bytes de saída da aplicação.
Mantidas 48 chamadas de modelo, três tentativas de consulta, uma correção por
papel e limites de entrada/resultado. Não foram usados gabaritos na execução.

## Resultado observado e persistido

| Repetição | Run | Chamadas LLM | Tentativas / consultas aceitas | Resultado | Tempo do job |
|---|---|---:|---:|---|---:|
| 1 | `3e4ad01f-6bbe-4687-9443-268081786255` | 19 | 3 / 2 | Resposta parcial; DW e industrial, financeiro não consultado | 110,44 s |
| 2 | `12f2b3bd-81c3-4737-aad1-e1a64e840a5c` | 21 | 3 / 3 | DW, industrial e financeiro; resposta final | 119,08 s |
| 3 | `0f350763-2f56-423d-a701-34626e66a2a0` | 14 | 2 / 1 | `contract_error`; sem resposta final | 76,20 s |

Os três jobs terminaram `completed`, significando que o resultado técnico foi
persistido. Isso não transforma o terceiro run em sucesso: seu snapshot é
`contract_error`. Os dois primeiros são `answered_unverified`, sem nota.
Readback confirmou zero jobs ativos ao final e os três registros na UI.
Nenhuma quarta execução foi enviada. O PostgreSQL permaneceu acessível nas
verificações desta bateria; isso não estabelece a causa da queda anterior.

Na repetição 1, `tool_01` rejeitou filtros incompletos da consulta machine. A
correção obteve o agregado da DW; correções de domínio do Revisor e referências
do Especialista também foram registradas. A terceira tentativa consultou
industrial e esgotou o teto, deixando a lacuna financeira explícita na resposta.

Na repetição 2, não houve rejeições: `machine` → `paradas_maquinas_geradas` →
`resultados_financeiros`. O Revisor pediu aprofundamento duas vezes e depois
declarou suficiência. As ferramentas devolveram uma linha DW, 13 industriais e
13 financeiras; o Redator referenciou os três resultados e produziu ressalvas
no JSON. A apresentação dessas ressalvas na UI está sob auditoria.

Na repetição 3, `call_14` montou plano industrial com intervalo de 2021, mas
sem `maquina_id`; `tool_02` encerrou com `row_limit_exceeded`. Não houve
reexecução automática dessa consulta nem aceitação silenciosa de dados cortados.

## Comparabilidade e tamanho das saídas

Readback dos snapshots confirmou igualdade de pergunta, prompt, critérios,
parâmetros, identidade da fonte, fingerprint do caso, hashes dos contratos e
mapas, protocolo e limites. Isso não equivale a comprovar imutabilidade física
dos bancos entre leituras nem validação científica.

| Repetição | Tokens de entrada | Tokens de saída reportados | Maior chamada (saída) | Maior JSON UTF-8 |
|---|---:|---:|---:|---:|
| 1 | 30.112 | 9.913 | 1.091 | 1.319 bytes |
| 2 | 39.434 | 11.313 | 1.121 | 1.645 bytes |
| 3 | 16.912 | 7.287 | 1.106 | 1.551 bytes |

Total reportado: 114.971 tokens em 54 chamadas. Nenhuma saída atingiu os antigos
tetos de 4.096 tokens ou 8.192 bytes. O ensaio não demonstrou necessidade de
ampliar esses tetos para esta pergunta, mas também não define um teto universal.
Não houve mudança dos limites durante as três repetições.

## Artefatos privados e auditoria

Snapshots completos, sem credenciais, em `inference_api/.local/`:

- `spec013-openai-ui-r1-20261105.json`: SHA-256 `5a609555e796feaf992aa508dfed9db7c118bef9f194a3d44b3e5246535b70bf`.
- `spec013-openai-ui-r2-20261105.json`: SHA-256 `a4eeec73da0666a957e8e6decdb3c68fe0e8fae95e7e2ef2292b77cab22d73b0`.
- `spec013-openai-ui-r3-20261105.json`: SHA-256 `f155dd03021b84944da64bf0d5e9a55cb22387b943e80543b0ec8c6abc080e56`.
- `spec013-openai-ui-three-runs-20261105-summary.json`: métricas, IDs dos jobs,
  tempos e checks de igualdade de configuração.
- Capturas individuais `spec013-openai-ui-r{1,2,3}-20261105.png` e histórico
  `spec013-openai-ui-three-runs-history-20261105.png`.

Os três snapshots foram encaminhados ao chat Astra de auditoria técnica
`01a1ae0e-a4d7-70b3-8379-e67fb4288ead`, somente leitura. A cadeia real com três
bancos foi demonstrada uma vez; a estabilidade geral e as correções técnicas
permanecem pendentes. Não há aprovação final independente nem conclusão da
SPEC. A avaliação científica continua separada e `not_scored`.

## Parecer independente recebido

O [parecer Astra das três repetições](astra-three-runs-review-2026-11-05.md)
confirmou hashes/configuração e fidelidade mecânica das duas respostas aos
resultados armazenados, sem validar ciência. Identificou a perda dos tipos de
filtros entre mapa e Planejador: `maquina_id` era autorizado, mas `call_14` da
repetição 3 não recebeu seu tipo, embora o Especialista o tivesse recebido.
A omissão do filtro não pode ser atribuída exclusivamente ao modelo.

Também confirmou saldo de consultas desatualizado no feedback de correção,
ressalvas/referências do Redator ausentes na apresentação final da UI e a
necessidade de explicitar cobertura sem truncamento. Os achados anteriores
continuam abertos. Todas as 54 chamadas registraram `finish_reason=stop`;
foram 86.458 tokens de entrada e 28.513 de saída, incluindo 16.193 de raciocínio.
Nenhuma correção de código foi aplicada entre essas execuções.
