# SPEC-013 · vínculo dos nove casos aos mapas locais · 02/11/2026

`model_evaluation/.local/spec013-pilot-case-contracts-2026-11-02-v4.json`
foi criado sem substituir v1–v3. SHA-256 dos bytes do arquivo:
`27214d0acc5424f11bf9c27e3f4c5ee0be1d977dc169524fceb3a8900fa2018a`.

O gerador conferiu o pacote de conteúdo revisado, as duas referências privadas,
o catálogo candidato, a aprovação semântica local e a transformação exata para
o catálogo habilitado. Para cada passo, verificou fonte única habilitada,
campos, filtros e grão no mapa aprovado. O manifesto privado contém os hashes
dos mapas `dw`, `industrial` e `financeiro`, as fontes exigidas e os estados de
evidência de I1–I3, F1–F3 e X1–X3.

O comando usado foi:

```powershell
BancoModeloUse/.venv/Scripts/python.exe -m model_evaluation.materialize_spec013_pilot_cases --approved-local-catalog --output model_evaluation/.local/spec013-pilot-case-contracts-2026-11-02-v4.json
```

`harness_score.evaluate` devolveu `not_scored` para o contrato v4, como
esperado. O estado é `approved_map_bound_pending_case_review`: o usuário
aprovou o **conteúdo** do pacote anterior, enquanto esta nova vinculação
técnica e as futuras respostas de modelo precisam de revisão humana própria.
Nenhum gabarito foi enviado a agente ou provedor; nenhum banco foi escrito.
