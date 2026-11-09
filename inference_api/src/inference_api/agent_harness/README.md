# Harness da Bancada · SPEC-015

Implementação local do contrato 3 em 08/11/2026. A usa `fixed_evidence_v2`, índice semântico de pacote sem linhas globais e liberação de evidências ao Revisor/Redator somente após análise validada. Domínio suportado ausente encerra com insuficiência, sem consultar banco. B mantém contratos/prompts. O serviço externo finaliza a raiz após persistência; execução direta conserva finalização standalone. O aceite depende de `specs/active/SPEC-015/evidence/v3/` e revisão independente; não há score científico.

`scenarios.run` é a fachada de execução. Ela prepara o estado serializável e invoca um `StateGraph` real, sem checkpoint persistente, store, retry automático ou memória entre runs. `agent_harness.run` reexporta essa mesma fachada. O algoritmo anterior foi arquivado fora do checkout; `engine.py` conserva somente schemas e limites ainda consumidos pelos testes e gates dos adaptadores históricos.

| Pasta | Responsabilidade |
|---|---|
| `graph/` | estado, construção, nós e arestas condicionais explícitos |
| `agents/` | interface comum, runner de uma chamada e sete componentes |
| `context/` | projeções por papel e índices usados na validação semântica |
| `tools/` | DW, contributors, trace, industrial e financeiro |
| `policies/` | pacote fixo A, acesso B, budgets e reparos |
| `contracts/` | contratos efetivos extraídos, inclusive os antes gerados em Python |
| `../data_access/queries/` | implementação SQL e validação de planos; sem LLM |
| `../observability/` | exportação opcional e sanitizada; histórico local oficial |

O fluxo é Analista → Selecionador → projeção → Especialista do domínio → evidência → Revisor → Redator. Lacuna autorizada retorna ao Selecionador; reparos de saída retornam ao mesmo papel, e plano corrigível retorna ao mesmo Especialista. São três módulos de Especialista com o papel externo `especialista_consulta`, sem chamadas extras. Todos os papéis usam o ModelService e o mesmo perfil congelado da run.

A usa pacote imutável, sem consultas nem fingerprints de banco. B usa o mapa aprovado e os serviços de consulta controlada existentes. Fonte proibida, orçamento, cancelamento e falhas de provedor mantêm o protocolo anterior. O framework não faz nova tentativa implícita. Snapshots v7 e históricos continuam legíveis.

`synthetic_demo.py` conserva somente MAPS, QUESTION e fixture_query consumidos pelos testes. Seus antigos comandos pagos, openai_audit e dois verificadores do protocolo retirado foram arquivados. Consulte `specs/active/SPEC-015/evidence/legacy-inventory.json`: os originais têm localização e SHA-256 verificados. Os testes específicos do algoritmo retirado estão no mesmo arquivo externo; verificações independentes de filtros, provedores, catálogo e permissões foram preservadas.

Validação atual: `inference_api/scripts/verify_spec015_local.py`, testes `test_spec015_*.py`, suites da API/model_evaluation e testes/typecheck/lint/build do frontend. A integração cria e encerra PostgreSQL descartável e usa transportes sintéticos. Não execute scripts antigos para regenerar evidências históricas.

A configuração do painel está documentada em `docs/langsmith_bancada.md`. A validação local do SDK não equivale a confirmação visual no serviço hospedado.
