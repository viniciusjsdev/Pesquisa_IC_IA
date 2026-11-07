# M0 · aprovação do contrato semântico para uso local (02/11/2026)

O pesquisador respondeu **“Aprovo o contrato detalhado para uso local”** à
pergunta que apontou para a [ficha completa de revisão](m0-semantic-activation-review-2026-11-02.md)
e identificou os hashes do mapa candidato e do contrato de saída. O
[recibo estruturado](m0-semantic-local-approval-2026-11-02.json) registra a
origem da decisão, o escopo exato e esses hashes.

A decisão cobre as 12 fontes do piloto, seus campos, grãos, cobertura,
filtros, ressalvas e a projeção limitada de `contributors`/`trace`, **somente
para leitura local** e sem join entre bancos. A aprovação anterior do recorte
e da política continua válida. Esta decisão não autoriza transmissão de
detalhe a Groq/OpenAI/RunPod, execução de modelos externos nem pontuação
científica. A identidade humana é documentada pela resposta da conversa; o
hash apenas verifica os bytes dos artefatos.

A ativação no código ainda exige gerar o catálogo local habilitado apenas com
esses bytes, conferir inventário físico e fingerprint da carga, validar a role
`spec013_reader` e executar os testes de leitura/limites. Qualquer alteração do
mapa ou contrato de saída exige nova revisão.
