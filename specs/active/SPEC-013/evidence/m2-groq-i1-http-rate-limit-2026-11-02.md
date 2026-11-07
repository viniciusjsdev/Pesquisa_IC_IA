# SPEC-013 · I1 integrado com trace persistido · 02/11/2026

Após recuperar o PostgreSQL isolado e passar novamente a cadeia local de três
bancos com modelo programado, foi iniciado **um novo job I1**, com ID novo e
sem repetir automaticamente o job anterior. O
[recibo JSON](m2-groq-i1-http-run-2026-11-02.json) identifica o job
`b4a4b86d-1d9a-4c32-83f7-f08e68ce5b87` e o run
`4d286acf-2f33-4d3f-9b65-7396f39db8d4`. O GET HTTP leu o snapshot v6
persistido no PostgreSQL. O trace privado completo tem SHA-256
`0e13304be09c02c41ac8bec43a2adfb3d4f4ae66883133350334e778c4949be4`.

Foram registradas quatro chamadas ao Qwen da Groq. O Analista e o Especialista
do Índice devolveram saídas válidas. O Especialista dos Dados citou referência
fora do mapa e foi rejeitado pelo contrato. A chamada de correção recebeu
`provider_rate_limited` (HTTP 429, `Retry-After: 3`); não houve outra tentativa.
O job terminou `completed` como tarefa de execução, mas o run terminou
`provider_rate_limited` e o motor marcou `contract_error`. **Nenhuma consulta
de dados ocorreu**. O avaliador devolveu `not_scored` para esse run.

Esse ensaio prova HTTP local, criação e leitura do job, chamada real ao
provedor, validação/rejeição de papéis e persistência do trace. Não prova a
cadeia com dados reais, a resposta I1, as 27 execuções previstas ou qualidade
científica. A autenticação HTTP do ensaio usou bearer de teste mapeado a um
pesquisador existente; não valida a credencial de produção. GPT/OpenAI e RunPod
não foram chamados.

Após a correção de recuperação e vínculo ao hash exato da autorização, 4 testes específicos do gate/persistência do
piloto passaram. Após essas adições, a suíte API completa passou: 118 testes,
8 opcionais ignorados; a primeira execução encontrou o `WinError 10053`
intermitente em um teste HTTP local, e o teste isolado passou em seguida.
Os 19 testes de `model_evaluation` passaram. O manifest da SPEC validou contra
o JSON Schema. Esses testes não substituem o ensaio real interrompido nem a
revisão humana dos resultados.
