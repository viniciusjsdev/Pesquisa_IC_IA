# Organização da API da Bancada

O pacote `inference_api` reúne a interface HTTP, o ciclo de execução, os agentes, o acesso a dados, os provedores e a persistência. Esta reorganização muda somente a localização dos módulos Python. Os contratos de execução dos cenários A e B continuam os da SPEC-014. A falha real `invalid_review_gap` em A permanece registrada e será tratada separadamente.

| Diretório | Responsabilidade |
|---|---|
| `api/` | rotas HTTP e arquivos estáticos |
| `identity/` | autenticação e principal |
| `executions/` | preparação, jobs, critérios e orçamentos |
| `agent_harness/` | papéis, cenários e contratos JSON |
| `model_service/` | configuração dos modelos, transporte e adaptadores |
| `data_access/` | consultas e catálogo de serving |
| `evidence/` | pacotes de evidência |
| `persistence/` | PostgreSQL e migrações |

As entradas públicas `run.py` e `session_checks.py` permanecem na raiz de `inference_api/`. Os testes, scripts e referências a módulos acompanham a nova localização. Os hashes de código em novas execuções passam a apontar para os novos caminhos; snapshots antigos são imutáveis. O aceite exige testes locais e integração HTTP com PostgreSQL descartável, sem chamada externa ao modelo.

## Verificação local em 07/11/2026

O backend passou 132 testes (8 pulados) e `model_evaluation` passou 21. A integração SPEC-014 percorreu o navegador, login, API, jobs, cenários A/B, adaptadores HTTP simulados e histórico com PostgreSQL descartável: 7 runs, `status=passed`. A execução foi sintética, sem provedor externo ou banco de pesquisa. O relatório anterior de aceite da SPEC-014 permaneceu preservado; o trabalho desta reorganização não resolve o `invalid_review_gap` observado no ensaio real de A.
