# SPEC-013 · ativação técnica dos nove casos · 02/11/2026

O pesquisador aprovou a versão privada v4 dos casos I1–I3, F1–F3 e X1–X3
com SHA-256 `27214d0acc5424f11bf9c27e3f4c5ee0be1d977dc169524fceb3a8900fa2018a`.
O [recibo](m3-executable-case-approval-2026-11-02.json) registra a resposta
literal e a decisão por ID. A v4 permaneceu imutável.

`python -m model_evaluation.activate_spec013_pilot_cases` reexecutou o preparo
da v4, comparou os bytes aos do pacote aprovado, verificou o recibo e escreveu
uma v5 privada com SHA-256
`dc8b691165da7c0be071623cf5bfc195284a676c872c93b1b05a8a505b9364c3`.
Cada caso da v5 está `approved` para o avaliador, com pessoa revisora, data e
hash do recibo. O estado do pacote é `approved_for_scoring_pending_run_review`.
Esse estado apenas permite checks automáticos e revisão posterior: nenhuma
resposta de modelo foi aprovada, nenhum score foi atribuído por esta decisão.

Pacotes v4/v5 e valores de referência ficam em `model_evaluation/.local/`, fora
dos payloads dos papéis e fora do Git. A reprodução exige os bytes privados.
