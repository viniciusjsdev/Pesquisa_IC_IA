# SPEC-013 · despacho backend do piloto real fechado · 02/11/2026

`service.py` aceita o contrato `agent_harness_pilot` com pergunta do usuário,
`provider=groq`, alias `groq_harness`, prompt fixo e parâmetros de geração
fixos. Quando autorizado, `real_pilot.py` entrega ao motor os mapas da cópia
aprovada e `local_queries.execute` para planos tipados; o snapshot v6 distingue
classe de dados, destino, fingerprint, trace, resposta e estado
`answered_unverified`.

O modo está **fechado por padrão**. Antes de abrir job/modelo, o backend exige
simultaneamente `INFERENCE_SPEC013_GROQ_REAL_DATA=1` e recibo específico de
aprovação que vincule o SHA-256 do
[contrato de transmissão](m2-groq-real-data-transmission-review-2026-11-02.md),
destino Groq e classe DW/industrial/financeiro. Este recibo não existe nesta
etapa. A aprovação anterior do catálogo local não satisfaz esse gate.

Os testes exercitaram recusa sem a chave, recusa com chave e recibo ausente,
restrição de provedor/prompt e despacho do modo com transporte, consulta e
persistência simulados. Um POST HTTP autenticado para `/api/run-jobs` devolveu
400 antes da criação de job, com modelo e storage bloqueados por mocks. A UI
mostra a opção piloto com modelo indisponível até a aprovação; typecheck,
lint, 9 testes e build passaram usando o Node local. Nenhuma chamada à Groq,
OpenAI ou RunPod foi feita e nenhum dado industrial/financeiro saiu da máquina.
Esse ensaio HTTP prova o bloqueio; o caminho positivo com modelo real e job
persistido ainda exige autorização e teste próprios.

Após a integração visual, a suíte Python `inference_api` passou com 115 testes
(8 opcionais ignorados); `model_evaluation`, 19/19. `git diff --check` passou.
