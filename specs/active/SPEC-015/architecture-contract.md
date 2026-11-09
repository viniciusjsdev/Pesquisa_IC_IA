> **Contrato 3 — desenho pendente de implementação:** [corrections-v3.md](corrections-v3.md) e [fluxo](corrections-v3.mmd) prevalecem para A, finalização da raiz e reconciliação. Descrições de preservação do defeito A e estado/link somente no snapshot abaixo pertencem ao contrato 2 e foram substituídas.

# Arquitetura proposta · SPEC-015

> Fechamento local em 08/11/2026: implementação autorizada e aprovada em `evidence/review.json`. O desenho abaixo foi preservado como contrato; envio hospedado sintético A/B confirmado posteriormente por readback da API (11/26 spans), com renderização na sessão do usuário não inspecionada. A autorização da sessão permite teste sintético no painel, sem envio de dados reais.

Estado em 08/11/2026: desenho para implementação, não descrição de código já migrado.
O [diagrama técnico](architecture.mmd) foi registrado antes deste contrato. A [página funcional do diagrams.net](https://app.diagrams.net/#G1RbtLePrWCTs8GjCAmAegFv7XBcAtzN8E#%7B%22pageId%22%3A%22rC3Onoxkcgc0oOyFh0Ck%22%7D) permanece referência visual; não foi editada nesta entrega. Este contrato detalha a organização interna sem adicionar papéis LLM ao fluxo.

Contrato 2: [observabilidade LangSmith](observability-contract.md) integra esta arquitetura como exportador opcional. A árvore abaixo ganha observability/ e a Bancada um link/estado opcionais; histórico local continua oficial.

## Escolha e fronteiras

Usar `langgraph==1.2.20`, versão publicada no [PyPI](https://pypi.org/project/langgraph/1.2.20/), com `StateGraph`, nós e arestas condicionais explícitos. Validar compatibilidade com o Python do projeto em ambiente isolado antes de alterar o ambiente ativo. Gerar lock transitivo reprodutível com hashes. Se houver incompatibilidade real, registrar `needs_design`; não trocar versão/framework silenciosamente.

O [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) permite nós Python; cada nó LLM chamará nosso `ModelService`. Não é necessário trocar os adaptadores por clientes LangChain. Dependências transitivas do LangGraph são aceitáveis; o pacote de agentes de alto nível do LangChain não é requisito.

O framework controla a passagem entre etapas; nosso código define contratos, permissões, contexto, validação, ferramentas e orçamento. Não encapsular todo o `scenarios.run` antigo em um único nó. Não manter um segundo loop externo tomando as mesmas decisões do grafo.

Nesta migração, compilar sem checkpointer/store persistente e sem serviço hospedado. [Persistência do LangGraph](https://docs.langchain.com/oss/python/langgraph/persistence) é uma capacidade opcional, diferente dos jobs e snapshots já existentes. Retomada automática após interrupção, memória entre runs, paralelismo dos especialistas, cache e retries do framework ficam fora do escopo. A migração não promete execução externa exatamente uma vez.

## Estrutura alvo

```text
inference_api/src/inference_api/
├── api/                         # contratos HTTP preservados
├── executions/                  # jobs, autorização, limites e snapshots
├── observability/               # config, contratos, sanitização, serviço, LangSmith e noop
├── model_service/               # interface e adaptadores existentes
├── data_access/                 # SQL, conexões e catálogo, sem LLM
│   └── queries/                 # local_queries e typed_detail realocados
├── agent_harness/
│   ├── scenarios.py             # fachada compatível: escolhe política e invoca grafo
│   ├── graph/
│   │   ├── builder.py           # StateGraph e suas arestas
│   │   ├── state.py             # estado tipado, isolado por execução
│   │   ├── nodes.py             # adaptação dos componentes para patches de estado
│   │   └── routing.py           # decisões já validadas → aresta permitida
│   ├── agents/
│   │   ├── base.py              # interface comum
│   │   ├── runner.py            # uma chamada ao ModelService + validação + receipt
│   │   ├── registry.py          # IDs estáveis → implementações
│   │   ├── question_analyst.py
│   │   ├── source_selector.py
│   │   ├── consolidated_specialist.py
│   │   ├── industrial_specialist.py
│   │   ├── financial_specialist.py
│   │   ├── evidence_reviewer.py
│   │   └── answer_writer.py
│   ├── context/
│   │   ├── views.py             # DTOs de contexto por papel
│   │   └── projections.py       # seleção determinística dos campos autorizados
│   ├── tools/
│   │   ├── base.py              # interface, request e resultado
│   │   ├── registry.py
│   │   ├── dw_query.py
│   │   ├── contributors.py
│   │   ├── trace.py
│   │   ├── industrial_query.py
│   │   └── financial_query.py
│   ├── policies/
│   │   ├── fixed_evidence.py    # A: pacote, zero consultas
│   │   ├── tool_access.py       # B: mapa e leitura controlada
│   │   ├── budgets.py
│   │   └── repairs.py
│   ├── contracts/              # JSON de entrada/saída por papel + comuns
│   │   ├── loader.py
│   │   └── *.json
│   ├── catalog_runtime.py      # mapas aprovados, sem alteração semântica
│   └── runtime_identity.py     # inventário recursivo + versões do runtime
└── persistence/                # armazenamento existente, sem migração de dados
```

A árvore lista responsabilidades e arquivos centrais; não exige arquivos vazios. Módulos auxiliares existentes permanecem apenas com consumidores identificados. Pilotos/CLIs passam pela mesma fachada; uma fachada legada pode reexportar símbolos, mas não conservar outro algoritmo de orquestração. Antes de retirar `engine.py`, identificar todos os consumidores, extrair constantes/helpers e migrar testes e entradas ativas. Preservar evidências históricas, não regenerá-las com o novo runtime.

## Interfaces e responsabilidade de cada agente

`Agent` é um Protocol comum: `role_id`, `build_input(view, policy) -> dict`, `output_contract(policy) -> dict`, `validate_semantics(output, view) -> None`. O runner recebe `Agent`, view, contexto da chamada e a interface `ModelService`; devolve saída validada, receipt e erro estruturado, sem escolher próximo agente. Não captura credenciais. Projeções e contratos de entrada são validados antes de enviar a requisição.

| Módulo | Contexto recebido | Trabalho e saída |
|---|---|---|
| Analista | pergunta original, índice permitido dos domínios, protocolo | necessidade estruturada, período, granularidade e lacunas |
| Selecionador | análise, fontes permitidas, evidências, lacuna e tentativas | selecionar fonte permitida ou declarar ausência |
| Especialista consolidado | necessidade, mapa da fonte DW/linhagem ou trecho do pacote, evidências e erro de reparo | B: plano tipado; A: análise e referências do pacote |
| Especialista industrial | mesmo contrato, projeção industrial autorizada em B | plano/análise correspondente à fonte industrial |
| Especialista financeiro | mesmo contrato, projeção financeira autorizada em B | plano/análise correspondente à fonte financeira |
| Revisor | pergunta, evidências acumuladas, análise atual, tentativas e limites | suficiência ou lacuna para nova rodada |
| Redator | pergunta, evidências válidas, lacunas e revisão | resposta com referências e limitações |

Os três especialistas são implementações do mesmo papel externo `especialista_consulta`. Registro escolhe a implementação pelo domínio da fonte, sem uma chamada extra. Preservar IDs externos e nomes legíveis na UI. Não reintroduzir Planejador. Nenhum agente executa SQL diretamente.

Os conteúdos efetivos de prompts, esquemas e envelopes vêm de `scenarios.contracts`, `scenarios.input_schema` e seus consumidores no baseline, inclusive contratos gerados em Python; copiar apenas os JSON antigos é insuficiente. A extração para arquivos preserva os bytes das requisições normalizados segundo o protocolo de equivalência.

## Contexto e estado do grafo

`RunState` contém somente dados serializáveis: identidade da run, cenário, pergunta, perfil/configuração congelados, análise, seleção, projeção, plano, evidências, revisão/lacuna, resposta, contadores, tentativa de reparo, trace, erro e status. Conexões, clientes, segredos, relógio, cancelamento e dependências ficam no contexto de execução injetado, fora do estado persistível. ModelService é único por run; nunca global mutável entre usuários.

Nós retornam patches explícitos; listas de eventos têm um único escritor lógico por transição e IDs únicos. Nenhuma reducer pode duplicar eventos. ContextView entrega apenas os campos já autorizados para o papel; o estado inteiro não entra no prompt. O contexto estático é congelado por run. Não há sumarização LLM implícita, RAG novo, memória compartilhada entre runs nem gabarito acessível aos agentes. Mudança no conteúdo efetivo do prompt exige decisão separada, não se mascara como refatoração.

## Fluxo, validação e ferramentas

1. `executions.service` prepara/autentica como hoje; `scenarios.run` mantém assinatura e formato de retorno e chama o grafo compilado.
2. Analista → Selecionador → projeção do contexto → Especialista apropriado. Sem fonte, segue para redação com lacuna quando permitido pelo protocolo vigente.
3. A valida e registra análise do pacote, sem criar/injetar executor de banco. B entrega plano tipado ao registro de tools. Cada tool possui ID, esquema de entrada/saída e `execute(request, context) -> ToolResult`; chama serviço de dados, jamais a LLM.
4. Backend valida fonte, filtros, relações, modo de leitura e limites; registra tentativa mesmo quando recusada. Reparo de plano permitido retorna ao mesmo Especialista com erro estruturado e consome orçamento. Fonte proibida ou erro terminal não vira tentativa de contornar autorização.
5. Revisor avalia evidências. Lacuna válida e orçamento levam ao Selecionador. Suficiência ou encerramento permitido por orçamento levam ao Redator. Reservar chamada final conforme o código atual; não criar chamada quando orçamento já impedir sua execução.
6. Validar toda saída LLM como JSON + schema + semântica antes da próxima etapa. Reparo de contrato é uma transição explícita para o mesmo papel, limitada como no baseline. Falha de provedor, cancelamento e esgotamento sem caminho permitido encerram com erro rastreável; sem retry automático.
7. Persistência e exportação recebem o mesmo resultado público. Evento de framework não é evento LLM: não duplicar contagem nem inventar chamadas na UI.

Preservar tabelas de códigos corrigíveis/terminais e seus limites exatos a partir do baseline; documentar matriz em evidência antes de migrar. Configurar limite de recursão do grafo com margem demonstrada por testes para todas as transições permitidas pelo orçamento; nunca deixar o default interromper uma execução ainda válida. Converter eventual GraphRecursionError em erro interno explícito, sem falso sucesso.

## Cenários e limites científicos

A e B compartilham os mesmos papéis e grafo, com políticas distintas. A continua escolhendo e analisando trechos do pacote fixo; B continua construindo consultas no especialista. A ausência de ferramentas deve ser testada na fronteira de acesso a dados, incluindo leitura para fingerprints. Três módulos de especialistas não obrigam três chamadas nem consultas aos três bancos.

A limitação real de A (`invalid_review_gap` e domínio atribuído aos itens do pacote) é **defeito conhecido preservado neste recorte**, coberto por teste de caracterização. Não declarar que a migração o corrigiu. Redesenhar A e seus controles experimentais será outra mudança documentada. A migração torna o fluxo auditável, mas não produz equivalência científica entre A e B nem atesta qualidade das respostas.

Controle científico depende de versões, prompts, dados, ferramentas, configuração, orçamento e evidências congelados; usar framework não o elimina. Comparações antes/depois têm identidades de runtime diferentes. Registrar versão do LangGraph, dependências instaladas/lock, hash do grafo/políticas/contratos e inventário recursivo. Não misturar runs antigas e novas como se o harness fosse idêntico.

## Protocolo de equivalência

Capturar fixtures determinísticas da revisão Git do baseline antes de editar a orquestração, em checkout isolado ou subprocesso; não chamar APIs pagas. Comparar a nova execução com o baseline usando os mesmos retornos gravados de modelo e tool. Comparar número/ordem de chamadas, papel, prompt, schema, envelope, plano, tentativas, reparos, evidências, resposta, erro e status.

Lista fechada de normalização: timestamps/durações, run_id/call_id/event_id e referências correspondentes por bijeção, caminhos temporários e novos campos de identidade do código/framework. Hash derivado de conteúdo só pode ser normalizado após comparar o conteúdo original correspondente. Ordem de evidências, texto de prompt, filtros, contadores e códigos de erro nunca são ignorados. Qualquer outra diferença exige explicar e aprovar mudança de contrato antes de seguir.

Histórico v7 permanece legível; metadados novos são opcionais/aditivos. Se isso não for possível, retornar `needs_design` com proposta de versionamento em vez de quebrar consumidores. `runtime_identity.py` passa a inventariar recursivamente arquivos ativos `.py`/`.json` e lock, excluindo caches/segredos; teste altera temporariamente uma cópia de módulo profundo para provar mudança do hash.

## Sequência de implementação

1. Ler baseline, inventariar consumidores e capturar fixtures; resolver/registrar dependências em ambiente isolado.
2. Extrair contratos, contexto, agents/tools/interfaces mantendo testes; extrair serviços de dados sem mudar SQL/mapas/permissões.
3. Implementar StateGraph real, guardas e retornos; delegar fachada ao grafo e atualizar consumidores ativos. Nenhum motor alternativo de produção.
4. Atualizar inventário, snapshots e representação da trajetória mantendo compatibilidade.
5. Rodar equivalência, testes negativos, matriz A/B × adaptadores com transporte falso e integração pela UI com PostgreSQL descartável.
6. Implementar observabilidade opcional conforme contrato próprio; validar off/on, SDK com transporte falso, sanitização, isolamento de falhas e UI. Não ativar exportação hospedada.
7. Remover código sem consumidores comprovados, atualizar documentação/diagrama técnico e emitir relatório por critério. Revisão independente decide aceite de engenharia. Não executar pilotos reais para cumprir esta SPEC sem nova instrução da sessão.
