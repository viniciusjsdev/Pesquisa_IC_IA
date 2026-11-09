> **SPEC-015 contrato 3, engenharia local em 08/11/2026:** [correção de A e dois ajustes do LangSmith](../specs/active/SPEC-015/corrections-v3.md). Implementado e aprovado em revisão independente local. A multidomínio corrigido, raiz após persistência e reconciliação manual com receipt durável. [Parecer v3](../specs/active/SPEC-015/evidence/v3/review.json). [Ambiente local ativado e conferido em 08/11/2026](bancada_operacao.md), com A/B real e LangSmith. Sem score científico.

> **LangGraph e painel:** [configuração do LangSmith e limites de validação](langsmith_bancada.md). A execução ativa usa `agent_harness/scenarios.py` → `graph/`; os comandos históricos abaixo não substituem esse caminho.

> **Proposta de migração em 08/11/2026:** [SPEC-015 — LangGraph, agentes, ferramentas e LangSmith opcional](../specs/active/SPEC-015/SPEC.md). Implementação do contrato 2 autorizada em 08/11/2026: grafo real e LangSmith opcional implementados, engenharia local aprovada em revisão independente. Exportação desligada por padrão; envio hospedado sintético A/B confirmado por leitura da API (11/26 spans); renderização na sessão do usuário não inspecionada. Preserva ModelService e A/B; a correção funcional de A permanece separada.

# Organização da API da Bancada

O pacote `inference_api` reúne a interface HTTP, o ciclo de execução, os agentes, o acesso a dados, os provedores e a persistência. A reorganização inicial mudou a localização dos módulos Python; a SPEC-015 passou a orquestração ativa para LangGraph. No contrato 3, A usa projeção semântica local `fixed_evidence_v2`, sem acesso aos bancos de pesquisa; B preserva seus contratos. `observability/receipts.py` guarda o estado atual no banco da aplicação e `observability/reconciliation.py` consulta o destino remoto original somente por ação autenticada. A falha real antiga de A permanece como evidência histórica, sem reinterpretar o snapshot.

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
