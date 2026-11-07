# M3 · aprovação humana do conteúdo dos nove casos (01/11/2026)

O pesquisador respondeu **“Tudo aprovado”** à solicitação que enumerava
**I1, I2, I3, F1, F2, F3, X1, X2 e X3**, apontava para o pacote privado de
revisão e pedia aprovação ou correção de cada ID. A resposta completa também
pediu que os pontos de validação humana fossem documentados para futuros
pesquisadores.

O [recibo estruturado](m3-human-case-content-approval-2026-11-01.json)
registra **nove decisões `approved_content`**, uma por ID, todas vinculadas
ao mesmo pacote revisado de SHA-256
`75927ad3cdc81b7aaa59527c51c89809205243263bce08d857d67b1dd18fa27c`.
Os dois arquivos privados de referência mantiveram seus hashes. Não houve
justificativa individual adicional nem correções solicitadas. O arquivo
revisado foi preservado sem edição depois da resposta.

`model_evaluation/verify_human_review_receipt.py` confirmou em leitura local
os nove IDs e os SHA-256 do pacote e das duas referências. O resultado
`human_identity_independently_verified=false` deixa claro o limite dessa
checagem técnica: a autoria humana vem do registro da conversa, não do hash.

**Alcance:** perguntas, números de referência, ressalvas e interpretação do
pacote que o pesquisador leu. A aprovação humana do conteúdo está concluída
para essa versão. A habilitação científica ainda requer manifestos executáveis
com pergunta/filtros/mapa/carga/fórmula/tolerância vinculados aos mesmos
artefatos; cada resposta de modelo exigirá adjudicação posterior de cálculo e
conclusão. Nenhum run foi pontuado por esta aprovação.

O procedimento repetível para outras pessoas está em
[`docs/protocolo_validacao_humana_avaliacao.md`](../../../../docs/protocolo_validacao_humana_avaliacao.md),
com [ficha de revisão](../../../../model_evaluation/templates/revisao_humana_caso_e_run.md).
