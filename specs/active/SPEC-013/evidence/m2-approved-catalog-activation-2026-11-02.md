# M2 · catálogo piloto aprovado para leitura local (02/11/2026)

Após a [aprovação humana do contrato semântico](m0-semantic-local-approval-2026-11-02.md),
foi criada a [cópia habilitada do catálogo](../catalog/pilot_local_v1.json),
SHA-256 `952f33f8def07e4ac7bf3ffdc941e10a2145709e05a1bc09584e52dcbc423fdc`.
Ela difere do [candidato revisado](m0-semantic-map-candidate-2026-11-01.json)
apenas em `status: approved_for_local_query` e `enabled: true` nas 12 fontes.
O loader recusa divergência de qualquer outro campo, da resposta humana ou
dos hashes do mapa/contrato de saída. O candidato original permanece intacto
e desabilitado.

O inventário físico foi reexportado em transações de leitura em 02/11 para
`BancoModeloUse/.local/spec013-physical-schema-readback-2026-11-02.json`.
Seu hash lógico continua
`ca7f44f371fe5403b203d11bbc82a0d01553b5d4783d34cc6f9ebdd750343b62`:
39 objetos industriais, 19 financeiros e 35 da DW. A migração DW V2 mantém
fingerprint `66f8808cf83902ff6c7fd277937bf8e0671482058f540f3ea9c1ec8c5a182800`.

O [readback das 12 fontes](m2-approved-catalog-12-sources-readback-2026-11-02.json)
usou a role `spec013_reader`, planos tipados, `READ ONLY`, timeout e limites,
sem alteração de banco ou chamada a modelo/provedor. Cinco consultas DW,
duas de linhagem e cinco tabelas tipadas responderam com cobertura e
proveniência. Os resultados ficaram entre 615 e 1.889 bytes por plano de
smoke. Esses tamanhos são das seleções pequenas de teste; não provam que todo
plano possível cabe no limite de 32 KiB.

O [smoke de encadeamento](m2-local-chain-readback-2026-11-02-v3.json) continua
com catálogo habilitado apenas em memória e modelo programado. A versão
aprovada pode ser usada pelo serviço **local** após o loader; ela não está
exposta ao modo `agent_harness` da Bancada nem a Groq/OpenAI/RunPod. Não houve
execução científica nem adjudicação humana de resposta de modelo.
