# Parecer Astra sobre as três repetições OpenAI

Fonte: chat `01a1ae0e-a4d7-70b3-8379-e67fb4288ead`, resposta final
`msg_04592f0789ba3694016aed384bd77487d28496910def6fbca6`. Auditoria somente leitura;
sem aprovação final da SPEC. Texto recebido preservado abaixo.

**As três repetições encerram esta observação de engenharia: houve uma resposta parcial, uma resposta com os três domínios e uma interrupção controlada por excesso de linhas.** O run 3 revelou uma lacuna concreta na projeção dos tipos de filtros para o Planejador. Não é possível atribuir essa falha exclusivamente ao candidato.

Os hashes dos três snapshots conferem com os informados. Pergunta, modelo/configuração, prompt, catálogo, contratos, mapas e limites são iguais entre as repetições.

| Repetição | Chamadas | Tentativas / consultas aceitas | Desfecho | Tokens totais |
|---|---:|---:|---|---:|
| 1 | 19 | 3 / 2 | Resposta parcial; lacuna financeira declarada | 40.025 |
| 2 | 21 | 3 / 3 | Resposta com DW, industrial e financeiro | 50.747 |
| 3 | 14 | 2 / 1 | `query_blocked: row_limit_exceeded`; sem resposta | 24.199 |
| **Total** | **54** | **8 / 6** | — | **114.971** |

**[P2] Tipos de filtros presentes no catálogo são omitidos do contexto do Planejador.**

No [run 3](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/.local/spec013-openai-ui-r3-20261105.json), a sequência é inequívoca:

- `call_10` pede eventos industriais da máquina e do período solicitados.
- `call_12` recebe o mapa detalhado, incluindo `field_types.maquina_id = integer`.
- `call_13` escolhe a fonte de eventos gerados e mantém a máquina na justificativa.
- `call_14` recebe `filter_specs = ["parada_id", "maquina_id", "hora_inicio_parada:range"]`, **sem tipos para os filtros de igualdade**. Sua justificativa declara que omitiu `maquina_id` porque o mapa recebido não especificava o tipo.
- `tool_02` executa exatamente esse plano, restrito apenas pelo intervalo anual, e encontra excesso de linhas.

A instrução do Planejador exige usar somente chaves e tipos declarados em `filter_specs`, mas [engine.py:389](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/src/inference_api/agent_harness/engine.py:389) projeta os nomes de `filter_candidates` sem transportar os tipos que [typed_detail.py:80](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/src/inference_api/agent_harness/typed_detail.py:80) exige.

**Classificação:** a omissão foi uma decisão explícita do candidato, apoiada em uma insuficiência real do contexto entregue. `maquina_id` estava permitido; faltava seu contrato tipado. Os runs 1 e 2 conseguiram usar o filtro sob a mesma projeção incompleta, mas isso não elimina o defeito nem prova o comportamento contrafactual do run 3.

**Correção recomendada:** entregar ao Planejador contratos estruturados dos filtros autorizados — chave, operador, tipo JSON, restrições e obrigatoriedade — derivados do catálogo aprovado. O backend deve continuar sem acrescentar filtros semânticos por conta própria.

O bloqueio posterior funcionou conforme a política atual: `row_limit_exceeded` é terminal. Embora restasse uma tentativa, o motor encerrou sem nova chamada, sem resposta fictícia e sem promover as linhas rejeitadas a evidência. **Não houve falha de provedor ou banco nesse run.** A interrupção PostgreSQL anterior às três repetições permanece um incidente separado.

Nas duas respostas produzidas, a conferência mecânica encontrou correspondência entre texto e resultados armazenados: valores DW, IDs/datas industriais e, no run 2, as 13 observações financeiras. A consulta financeira não filtrou por máquina. Isso comprova fidelidade ao snapshot, não validade científica dos dados ou das conclusões.

Continuam relevantes os achados observados nesta rodada:

- **Orçamento desatualizado na correção:** `call_10` do run 1 recebeu três tentativas restantes quando restavam duas; o contador global, entretanto, respeitou o teto.
- **Ressalvas e referências omitidas da apresentação:** `call_21` do run 2 produziu quatro ressalvas e três referências preservadas no JSON, mas a resposta final da UI exibe somente `resposta`, em [HarnessRounds.tsx:166](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/frontend/src/features/bench/HarnessRounds.tsx:166).
- **Cobertura pouco explícita:** os Revisores não recebem uma declaração inequívoca de ausência de truncamento do recorte aceito, embora o executor rejeite excesso.
- Permanecem os achados anteriores sobre contexto do Planejador, tentativa recusada ausente da correção, dependências inexatas do trace, medição incompleta do payload, tentativas do Redator ocultas, comparação sem hashes do harness e adjudicação sem hash do run.

O consumo agregado foi de **86.458 tokens de entrada e 28.513 de saída**, incluindo **16.193 tokens de raciocínio**. Todas as 54 chamadas registram `finish_reason=stop`. A maior saída individual foi de 1.121 tokens e o maior JSON, 1.645 bytes: esta rodada não demonstrou necessidade de ultrapassar os tetos anteriores.

**Conclusão:** a observação demonstrou o caminho positivo pelos três bancos, correções explícitas, persistência de respostas e bloqueio terminal de excesso. Também identificou defeitos de contexto e apresentação que precisam ser corrigidos antes da revisão final. Não aprovo a SPEC nem atribuo score científico. A inspeção permaneceu somente leitura, sem banco, rede, provedor ou novas inferências.
