# Núcleo de agentes da SPEC-013

**SPEC-014 · implementada em engenharia local em 06/11/2026:** [Evolução planejada: mesmos cinco papéis nos dois cenários, Especialista analisa pacote no A ou monta plano no B, serviço comum para todas as chamadas de modelo.](../../../../specs/active/SPEC-014/architecture-contract.md) O ensaio real posterior mostrou `invalid_review_gap` no cenário A; a correção desse cenário segue pendente e separada da reorganização de pastas.

**Contrato vigente em 06/11/2026:** [consulta pelo Especialista](../../../../specs/active/SPEC-013/specialist-query-contract.md).
São cinco papéis, na ordem Analista → Selecionador → Especialista → Revisor
→ Redator. Entre Especialista e Revisor, o backend valida e executa a leitura.
O Selecionador recebe índice estático; o Especialista recebe o contrato completo
somente da fonte escolhida, com tipos e JSON Schema dos filtros. Não há
Planejador separado nem descoberta LLM em duas chamadas. Aprofundamento volta
ao Selecionador; correção de plano volta ao Especialista com tentativa recusada,
erro, evento e orçamento atualizado. Contratos: saída v8, entrada v7.

`synthetic_demo.py` usa `fixture-2`, tipos e `filter_contracts` explícitos,
com intervalo financeiro `from`/`to`, inclusivo/exclusivo. O mesmo schema
valida a execução da fixture. Mapas reais são compilados do catálogo aprovado
por `catalog_runtime.py`; não se alteram os bytes do catálogo ou seus recibos.
Runs antigos permanecem legíveis, mas não são evidência da nova arquitetura.
As observações datadas abaixo são históricas quando divergirem desta seção.

**Observação de saída em 05/11/2026:** no piloto OpenAI de engenharia,
`openai_pilot.PILOT_LIMITS` usa `output_bytes=None` e o adaptador omite
`max_output_tokens`. A política é registrada no snapshot; tokens de uso e
bytes de saída ficam disponíveis para dimensionar os tetos após o ensaio.
Groq e demais modos preservam seus limites. Saídas inválidas continuam rejeitadas.

**Estado vigente em 05/11/2026:** o piloto real também dispõe de adaptador
OpenAI em `openai_pilot.py`, autorizado para engenharia no contrato 2 da
SPEC-013. A ativação exige recibo específico e
`INFERENCE_SPEC013_OPENAI_REAL_DATA=1`; Groq conserva seu gate separado.
O motor registra `queries` (resultados aceitos), `query_attempts` (todas as
invocações do adaptador) e limites efetivos. Até três tentativas são permitidas
no piloto. A UI foi preparada, mas o envio real aguarda comando do usuário.
Há achados técnicos P2 abertos na auditoria Astra; não há aprovação final.
As descrições datadas abaixo preservam estados históricos.

`engine.py` executa os cinco papéis com o mesmo candidato. `map_projection`
registra o hash do mapa e do contrato completo entregue a `especialista_consulta`.
A projeção é código local, não consulta o banco nem escolhe fontes por conta própria.
`contracts.json` contém
as tarefas e os JSON Schemas de saída; `input_contracts.json` versiona as
projeções de entrada e o feedback de correção. Ambos têm SHA-256 no trace;
uma entrada fora do contrato encerra antes da chamada ao modelo. O transporte do modelo e a consulta
sintética são injetados pelo chamador. Cada chamada recebe um envelope JSON
com papel, rodada, referências e entrada específica; o backend valida a saída,
fixa a identidade do modelo e registra o evento. O trace integral não é
repassado aos papéis. Uma saída malformada pode receber uma correção explícita;
falha do provedor ou troca de modelo encerra sem repetição.

O núcleo distingue os protocolos sintético e piloto local e não importa
cliente de banco. `synthetic_demo.py` contém uma pergunta e fontes inventadas
da DW, industrial e financeiro. Testes cobrem início direto no financeiro,
DW seguida de detalhe industrial e ordem canônica de especialistas.
Para executar o ensaio Groq, configure a chave local já usada pela API. O
modelo padrão deste modo é `qwen/qwen3.8-27b`; opcionalmente defina outro
modelo Groq **não GPT** em `GROQ_HARNESS_MODEL`:

```powershell
$env:PYTHONPATH='inference_api/src'
$env:GROQ_HARNESS_MODEL='qwen/qwen3.8-27b'
inference_api/.venv/Scripts/python.exe -m inference_api.agent_harness.synthetic_demo
```

O script e o modo `agent_harness` da Bancada não mudam o `GROQ_MODEL` dos
modos existentes. O ensaio é limitado à
fixture, depende da cota do provedor e não gera score científico. A integração
com jobs/UI foi implementada e validada com transporte simulado; mapas reais,
validação física e consultas DW/industrial/financeiro pertencem ao modo
piloto separado, com gates específicos.

Com autorização específica, `openai_audit.py` executa a **mesma pergunta,
mapas, fixture e prompt de papel** usando o cliente Responses já presente na
API. Ele cria uma conversa nova por papel, limita a 16 chamadas e 4.096 tokens
de saída por chamada, exige um arquivo para o trace e não cria modo de Bancada:

```powershell
$env:PYTHONPATH='inference_api/src'
inference_api/.venv/Scripts/python.exe -m inference_api.agent_harness.openai_audit --output specs/active/SPEC-013/evidence/openai-synthetic-audit.json
```

O [ensaio de 01/11/2026](../../../../specs/active/SPEC-013/evidence/openai-synthetic-architecture-audit-2026-11-01.md)
completou a cadeia sintética direta após correções de contrato. Uma
[validação posterior](../../../../specs/active/SPEC-013/evidence/m1-http-input-contracts-2026-11-01.md)
passou pelo HTTP autenticado, job idempotente e leitura de snapshot v6 com
transporte e armazenamento em memória. Não testou persistência PostgreSQL,
interação visual, provedor real pela Bancada nem bancos de pesquisa.
Um [ensaio posterior](../../../../specs/active/SPEC-013/evidence/m1-postgres-storage-2026-11-01.md)
verificou a persistência do run/job da fixture por chamada direta do serviço,
com transporte simulado e limpeza dos registros criados.
Um [ensaio integrado adicional](../../../../specs/active/SPEC-013/evidence/m1-http-postgres-2026-11-01.md)
passou por HTTP autenticado, job idempotente e PostgreSQL real da Bancada com
modelo simulado, sem consultar bancos de pesquisa ou chamar provedor.

## Serviço local de consultas (02/11/2026)

`local_queries.py` recebe apenas **planos tipados** do Especialista.
Ele exige catálogo habilitado para leitura local, fingerprint da DW, fontes e
campos autorizados, conta `spec013_reader`, transação `READ ONLY`, limites de
linhas/bytes/tempo e proveniência. Fontes fixas DW, linhagem e detalhe tipado
têm contratos distintos; nenhuma aceita SQL livre ou relação entre bancos.
`data_contracts.json` fixa os campos de saída da DW/linhagem, o hash do mapa
candidato e o hash do código de consulta. `catalog_runtime.py` injeta apenas
fontes habilitadas em uma cópia aprovada do mapa. O motor registra plano
recusado e feedback JSON para o mesmo papel, sem executar a consulta.
Resultados reais não entram no modo `agent_harness` da
Bancada nem são enviados a Groq/OpenAI enquanto o catálogo semântico e o gate
de transmissão não estiverem aprovados. O
[ensaio local](../../../../specs/active/SPEC-013/evidence/m2-local-chain-readback-2026-11-02-v2.json)
usou transporte de modelo programado e a conta de leitura restrita: 17
chamadas, 3 consultas em DW/industrial/financeiro e 22.110 bytes no maior
input. O [recorte semântico detalhado](../../../../specs/active/SPEC-013/evidence/m0-semantic-activation-review-2026-11-02.md)
foi aprovado para uso local. `approved_catalog.py` confere o recibo e ativa
uma cópia exata das 12 fontes. `real_pilot.py` compõe esse catálogo com o
motor e a leitura local, mas `agent_harness_pilot` só chega à Groq se houver
recibo específico que corresponda ao
[contrato de transmissão](../../../../specs/active/SPEC-013/evidence/m2-groq-real-data-transmission-review-2026-11-02.md)
e `INFERENCE_SPEC013_GROQ_REAL_DATA=1`. O padrão está fechado; os testes
de despacho usam mocks e não transmitem dados reais.
