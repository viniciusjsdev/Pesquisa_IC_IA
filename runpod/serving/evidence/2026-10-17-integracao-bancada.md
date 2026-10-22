# Validação exploratória da Bancada com RunPod em 17/10/2026

Checkout base: `494325797356183897e97149805cb25ead3b3eb9`, mais alterações
locais ainda sem commit. A Pod `r0uheznbe2eyn5` (RTX A5000, 24.564 MiB de
VRAM, 50 GB de disco temporário, sem volume persistente) foi reiniciada pelo
console para esta sessão, sem Terraform. O console mostrou US$ 0,27/h de
computação mais US$ 0,007/h de disco, total arredondado a US$ 0,28/h. O saldo
exibido caiu de US$ 12,34 para US$ 12,29 durante a sessão; US$ 0,05 é apenas
a diferença observada no saldo, não uma fatura discriminada. A leitura final
confirmou Pod parada, computação e disco `Not running`, total US$ 0,00/h.

## Preparação e serving

- O checkout remoto confirmou o commit acima e validou os hashes dos seis
  adapters. As alterações locais de porta foram copiadas separadamente: o
  vLLM escutou em `127.0.0.1:8002` e o gateway na porta pública 8000.
- Ambiente isolado: vLLM `0.31.0`, PyTorch `2.13.0+cu130` e torchvision
  `0.28.0+cu130`. A base `Qwen/Qwen2.5-7B-Instruct` usou a revisão
  `a09a35458c702b33eeacc393d103063234e8bc28`. A revisão usada no treino
  histórico permanece desconhecida. Sessão de serving:
  `3ed4600e-1b49-425f-beba-90488b11e3fc`.
- Um cliente HTTPS local confirmou `/v1/models` e uma geração curta para cada
  um dos sete aliases. Recibo sem bearer:
  `runpod/serving/.local/verification-https-integration-20261017.json`, SHA-256
  `D2BA1AD855B85F6BFF621E4E94C765D73CED013D7BED83E2114C6DCB7B314EE5`.
  Foi um verificador PowerShell específico da sessão; o
  `verify_remote.py` formal não foi executado nesta sessão.
- Um ensaio direto e simultâneo de `qwen-base` e `ft-hibrido-a`, com 3.126
  tokens de entrada por requisição, recebeu HTTP 200, `finish_reason=stop` e
  a mesma identidade de sessão em 1,28 s e 1,52 s, respectivamente. Recibo:
  `runpod/serving/.local/concurrency-20261017.json`, SHA-256
  `5FBCA2D80EC19CE4DF67235BA4F4735EA9A50C3737A8713D01EDDA30A5D1238A`.
  Isso mede somente duas requisições curtas simultâneas, não carga sustentada.
  A leitura pontual após o ensaio foi de 21.965/24.564 MiB de VRAM, não pico.

## Aplicação local e runs

O host já servia a aplicação em `127.0.0.1:8765` com um único ngrok HTTPS
apontando para essa porta. O `tunnel-check` observou `/` 200,
`/api/me`, `/api/runs` e `/api/models` 401 sem login, e `/v1/models` 404.
O banco `db_inference_app` tinha migrações 1/2 e os usuários ativos Nicoli e
Vinicius; `db_pesquisa_dw` tinha a migração v1 e fingerprint
`64493abfdfd0b87535778eafd9d5938fad6039a99d9307f85e4cfc6eec0e89f2`.
O arquivo privado `BancoModeloUse/.env.local` apontava `DW_DB_NAME` para
`db_datamind_dw`; somente esse nome foi corrigido para `db_pesquisa_dw`,
sem alterar as demais entradas. O checkout com alterações sem commit manteve
o gate `git` do pré-voo em `BLOCKED`. Durante a sessão o backend recebeu
temporariamente a URL HTTPS, o bearer e o caminho do recibo da sessão.

O primeiro `GET /api/models` via backend falhou com HTTP 503: o proxy da
RunPod respondeu 403 (`error code: 1010`) ao `User-Agent` padrão
`Python-urllib/3.12`. A mesma chamada com `PesquisaICIA/1.0` respondeu 200.
O cliente HTTP da API e `verify_remote.py` passaram a enviar esse identificador;
os testes de serving e de contrato local passaram (8 e 10 testes). O recibo
PowerShell inicial tinha BOM UTF-8, que o leitor JSON da API recusou; os
mesmos bytes JSON foram preservados sem BOM, sem repetir gerações. Depois
disso, os sete aliases apareceram disponíveis na Bancada via ngrok.

Os runs abaixo foram executados uma vez cada no navegador autenticado como
Vinicius e relidos em `db_inference_app`. Todos são snapshots v3 exploratórios:

| ID | Modo e alias | Resultado observado |
| --- | --- | --- |
| `cb5e304a-67da-4f22-8429-c066344432fe` | `dw_snapshot`, `qwen-base` | `answered_unverified`; pacote `integrado-produto-2020-01` SHA-256 `ba57ab3d37a191c6e2be91622e975ae93794117828ad357dee6c8f51cb0f346c`; sessão do serving registrada. A resposta incluiu uma afirmação de cobertura completa que não foi validada. |
| `f2cf4be7-abf0-4bcf-9ab6-a1a30a9ffe93` | `dw_tools`, `qwen-base` | `answered_unverified`; a LLM chamou `product(year=2020,id=1000001)` e a consulta fixa retornou dados da DW; a resposta e a trilha ficaram no snapshot. |
| `7dd58948-91cf-4054-a311-b6e2c7efb956` | `dw_snapshot`, `ft-finqa-a` | `response_error`; o vLLM respondeu, mas o adapter produziu texto alheio ao pacote até `finish_reason=length` com 500 tokens. O backend rejeitou a resposta incompleta e guardou o turno bruto. Não houve reenvio. |

Resumo local dos três registros, sem texto gerado nem credenciais:
`inference_api/.local/run-summary-20261017.json`, SHA-256
`B37F5E8EB120CC338A3D566ADB9DD2D2816239C11F1A5AFF377497103B0539EE`.
O banco local mantém os snapshots completos; os recibos `.local/` são
ignorados pelo Git.

Após a parada da Pod, o backend foi reiniciado sem URL e bearer remotos. O
catálogo voltou a mostrar modelos indisponíveis e a execução foi desabilitada;
o ngrok e os bancos locais permaneceram ativos. O pré-voo final confirmou DW,
banco da aplicação, adapters e limite global, mas ficou `BLOCKED` pelo Git
com alterações sob revisão e pela ausência intencional da configuração de
serving com a Pod parada. Não houve avaliação científica, comparação formal
entre modelos, ensaio de duas pessoas simultâneas na API nem validação de
concorrência sustentada. O disco temporário da Pod foi apagado ao parar.
