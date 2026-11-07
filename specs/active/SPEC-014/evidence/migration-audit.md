# Auditoria de migração — 06/11/2026

Baseline: `implementation-baseline.json`, cópia externa indicada no próprio arquivo. HEAD inicial `13d7df5c748f79387d34f39cd30b6cf82c96c869`; o checkout incluía alterações anteriores não commitadas.

| Caminho | Consumidores e tratamento | Evidência |
|---|---|---|
| `dw_snapshot`, `dw_tools` | `service._validate_input`, POST `/api/runs` e `/api/run-jobs`: criação rejeitada; `RunDetail` mantém leitura e exportação de versões antigas. | `test_spec014`, `local-integration.json` |
| `agent_harness_pilot`, `agent_harness`, `synthetic_*` | criação rejeitada com `legacy_execution_mode_retired`; interface não oferece esses modos; snapshots v6 permanecem em `HarnessRounds`. | `test_spec014`, browser local |
| CLI históricos `probe_spec013_groq.py`, `verify_spec013_pilot_http_groq.py`, `verify_spec013_http_postgres.py`, `run_spec013_pilot_matrix.py` | substituídos por bloqueio imediato sem acesso a banco ou provedor; originais preservados na cópia externa com hashes no baseline. | busca `rg` no checkout; baseline preservado |
| Transportes `groq.py`, `openai_provider.py`, `models.py` | parsers SSE continuam consumidos pelos adaptadores; leitores e testes anteriores conservados. | `model_service/adapters.py`, suites backend |
| Persistência e identidade | `storage.py`, `auth.py`, jobs com chave idempotente, snapshots antigos e export JSON preservados. | regressão, navegador e PostgreSQL fixture |
| Testes de criação antiga | 27 expectativas obsoletas inventariadas em `retired-test-contracts.json`, cópia integral no baseline externo; contratos novos cobertos por `test_spec014.py` e integração. Outros testes de transporte, autenticação, contratos e consultas permanecem. | inventário e logs |
| Componentes executáveis | `runtime_identity.py` inclui `model_service/*.py` e harness; snapshot registra hashes antes e depois. | código e testes de comparação v7 |
| Dados protegidos | SPEC-013, pesos, dados e diagrama preservados. | confronto de 126 hashes pelo revisor independente |

O manifest registra a **política documental legada** gpt-5.6, pois o schema da ferramenta ainda não admite nomes atuais. O lifecycle registra o runtime observado (Astra e depois Terra) e não apresenta esse campo documental como medição do runtime. `full-access` e `deny_all` são nomes de contrato; a sessão real opera com permissões efetivas informadas pelo ambiente. O validator estrutural retornou `valid: true` para o par, sem constituir validação da execução.
