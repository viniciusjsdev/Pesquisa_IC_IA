# Replay da Bancada com streaming e jobs na L4 — 17/10/2026

## Escopo e ambiente

Sessão exploratória autorizada pelo usuário, sobre o checkout `4943257` mais
alterações locais sem commit. Não houve `terraform apply`, volume persistente,
recarga da DW nem avaliação científica. O objetivo foi validar o transporte
e o job assíncrono da Bancada até o serving real na RunPod.

A A5000 antiga `hyeeqzysb2o84s` não reiniciou porque o host perdeu a GPU;
a migração automática falhou. Uma nova A5000 esgotou antes da criação. Com
autorização específica, foi reiniciada a Pod L4 Secure de 24 GB
`mh1haxycv8zky9` em 18/10/2026 às 02:23:07 UTC (17/10 em São Paulo).
O console mostrou US$ 0,59/h de GPU e cerca de US$ 0,007/h de disco temporário,
arredondado a US$ 0,60/h, com 50 GB temporários e nenhum volume persistente.
O limite autorizado foi uma hora e US$ 0,60. A chave pública SSH local foi
acrescentada somente à Pod temporária com autorização separada; a chave privada
não foi enviada.

No checkout remoto público `494325797356183897e97149805cb25ead3b3eb9`,
os seis pesos LFS foram materializados. `serving.py validate` confirmou o
manifesto SHA-256 `201ffce772a2275f87bebcd384862a30b3ed3e941aa557d5cce7c42d012a58d1`.
O runtime usou vLLM 0.11.0, PyTorch 2.8.0+cu128, torchvision 0.23.0+cu128 e
transformers 4.57.6, compatíveis com o driver 595.91.07. O gateway com SSE
e o verificador desta versão local foram copiados e seus SHA-256 conferidos.
O vLLM escutou somente em loopback; o gateway autenticado ficou na porta 8000.

O `verify_remote.py` passou 7/7 aliases e gerações mínimas por HTTPS externo
às 02:33:11 UTC. Sessão de serving
`981e2288-976c-436a-9a0b-630342e57c63`, revisão exata da base
`a09a35458c702b33eeacc393d103063234e8bc28`. A chamada anônima a
`/v1/models` recebeu 401. O recibo completo, sem token, está no arquivo
ignorado `runpod/serving/.local/verification-20261018.json`, SHA-256
`560A183ACE4666E36E15D28CC557000382B5D32E7A02D0A9530B3A4227B685B1`.
O log remoto e o manifesto de sessão foram copiados para `.local/` antes da
parada; o log copiado não contém o bearer.

## Banco, API e Bancada

O PostgreSQL host isolado iniciou em `127.0.0.1:5544`; a migração explícita
003 dos jobs já estava aplicada com backup lógico em sessão local anterior.
O pré-voo desta sessão leu DW v1, versões `[1,2,3]` da aplicação, duas
identidades ativas, seis adapters e o limite global de uma inferência. O
resultado agregado permaneceu `BLOCKED` pelo checkout Git alterado e pela
origem de serving ausente antes de a Pod estar pronta. Corrigiu-se a expectativa
obsoleta `[1,2]` do próprio pré-voo para `[1,2,3]`; quatro testes direcionados
passaram. Isso não transforma o gate agregado em aprovação.

A API local em modo host apontou para o gateway HTTPS e usou o recibo da
sessão. Vinicius fez login diretamente no Chrome. Pelo `localhost`, a Bancada
listou os sete aliases e submeteu o pacote imutável
`integrado-produto-2020-01` (SHA-256 `ba57ab3d37a1...`) com temperatura 0,2
e `max_tokens: null`:

| Caminho | Job | Run | Resultado e transporte |
| --- | --- | --- | --- |
| localhost, `qwen-base` | `a0298473-af4a-4058-96e0-6a05d3a780bb` | `631dac8e-d02c-4263-8fc5-558944b793e8` | `answered_unverified`; SSE gravado; `finish_reason=stop`; 945 tokens de entrada + 296 de saída. |
| localhost, `ft-finqa-a` | `843afe13-8ef7-4ae3-9ac2-6081f8838198` | `da56f5cf-da75-4691-ba26-b91ad6fa6ad9` | `response_error`; SSE completo gravado; 945 + 3.151 = 4.096 tokens; `finish_reason=length`. A saída repetiu texto e não foi aceita como resposta. |

Na segunda geração a L4 chegou a cerca de 21,5 GB usados de 23.034 MiB, sem
erro de VRAM observado. O erro veio após a resposta em streaming chegar ao
backend, de modo que não reproduziu o HTTP 524 do transporte antigo. A
janela de contexto do serving continua em 4.096 tokens somados para entrada
e saída, embora a Bancada não envie teto de saída.

Com a confirmação do usuário de que as duas senhas haviam sido trocadas,
abriu-se um único túnel ngrok HTTPS para `localhost:8765`. O
`session_checks.py tunnel-check --execute` confirmou `/` 200,
`/api/me`, `/api/runs` e `/api/models` 401 sem login e `/v1/models` 404;
o inventário local do ngrok mostrou apenas esse túnel. A origem temporária
não é publicada aqui. Vinicius fez login diretamente na aba pública.

Pela Bancada pública, `qwen-base` recebeu job
`fd769375-3422-4cea-b963-320d9009d46a` com HTTP 202 no ngrok e concluiu
no run `dce989a0-9dda-4458-a267-bd6f3aa1fa66` às 02:41:39 UTC, estado
`answered_unverified`, SSE gravado, `finish_reason=stop`, 945 + 347 tokens.
O refresh durante o job voltou à tela de login; após novo login, a Bancada
recuperou automaticamente o **mesmo** job/run pelo histórico, sem reenviar.
Assim, a credencial de login da UI não sobrevive ao refresh, mas o job e o
resultado persistem no banco. O ngrok registrou dois `POST /api/run-jobs`
com HTTP 202; o segundo foi o teste FT-FinQA A abaixo.

## Caso longo via ngrok

O job `41ad25e8-1c75-42ba-8528-4c296be01b83` de `ft-finqa-a` foi
aceito pela Bancada pública às 02:42:11 UTC e entrou em `running`. Terminou
às 02:45:26 UTC no run `75a1077b-6046-4699-aee3-b838eb4d9a6f` com
`response_error`. O snapshot contém o fluxo SSE recebido (992.180 caracteres
em base64), uso de 945 + 3.151 = 4.096 tokens e `finish_reason=length`.
Não houve HTTP 524, timeout do ngrok nem erro de VRAM nessa chamada. O
`ModelResponseError: Invalid chat completion shape` é a recusa deliberada do
backend a uma resposta truncada. A UI exibiu `ft-finqa-a · ? · ?` na linha de
sessão do run com erro, embora o registro bruto tenha o SSE e o catálogo da
requisição estivesse atestado; esse detalhe de apresentação/proveniência do
erro ainda merece correção separada.

O resumo sanitizado do inspetor local do ngrok, salvo em
`inference_api/.local/ngrok-jobs-20261017.json`, registrou **dois**
`POST /api/run-jobs` com HTTP 202 e 97 consultas `GET` com HTTP 200, sem
outros status para essas rotas. O refresh do primeiro job não causou terceiro
POST. Esses números são de requisições observadas no túnel, não teste de
carga ou benchmark.

## Encerramento e limites da conclusão

O log final da Pod foi copiado para
`runpod/serving/.local/serving-log-20261018.txt`; o token não aparece nesse
arquivo. A Pod foi parada por volta de 02:46 UTC, cerca de 23 minutos após
o reinício, dentro do limite de uma hora. O modal confirmou ausência de volume
e custo ocioso de US$ 0,000/h. O readback no console mostrou a L4 e as demais
Pods a **US$ 0,00/h**, com computação e armazenamento temporário `Not running`.
Uma captura desse readback está no arquivo ignorado
`runpod/serving/.local/pod-stopped-20261017.png`.
O saldo visível passou de US$ 11,93 antes da ativação para US$ 11,70 no
readback posterior; essa diferença de US$ 0,23 é apenas um instantâneo do
saldo, não uma fatura final reconciliada. A tarifa exibida durante a execução foi
US$ 0,60/h. O túnel ngrok, a API host e o PostgreSQL local foram encerrados;
as portas 4040, 8765 e 5544 ficaram sem listeners.

**Conclusão limitada:** a infraestrutura atual foi validada para um job por
vez no caminho Bancada autenticada → ngrok HTTPS → API host → gateway RunPod
→ vLLM L4 → snapshot PostgreSQL, incluindo geração de cerca de três minutos,
streaming SSE, persistência e retomada após novo login. Os sete aliases
passaram no smoke remoto; apenas a base e FT-FinQA A foram executados pela
Bancada nesta sessão. A interface ainda perde o login no refresh, embora
recupere o job após novo login. A qualidade das respostas FT-FinQA, a
comparação científica, a carga sustentada e a imagem Docker desta versão não
foram validadas. `answered_unverified` continua exploratório.
