# Validação da infraestrutura de inferência em 17/10/2026

Escopo: disponibilidade e integração da plataforma local com RunPod. Não houve
avaliação de qualidade, comparação científica, teste de carga sustentada nem
nova avaliação dos adapters na Bancada. Checkout local e remoto no commit
`494325797356183897e97149805cb25ead3b3eb9`, mais os arquivos de serving e
API alterados localmente, ainda sem commit. A execução foi pelo console da
RunPod, sem `terraform plan/apply`.

## Pod e ambiente

- A tentativa de reiniciar a Pod anterior `r0uheznbe2eyn5` falhou com a
  mensagem do console `There are not enough free GPUs on the host machine`.
  Ela continuou parada a US$ 0,00/h.
- Foi criada a Pod descartável `g0y5v9h2x9x6us`, Secure Cloud `EU-SE-1`,
  1× RTX A5000 com 24.564 MiB de VRAM, 50 GB de RAM, 9 vCPU, imagem
  `runpod/pytorch:1.4.0-cu1281-torch280-ubuntu2404`, disco temporário de
  50 GB e nenhum volume persistente. Console: US$ 0,27/h de GPU mais
  US$ 0,007/h de disco, total exibido US$ 0,28/h.
- Git LFS materializou os seis adapters; `serving.py validate` confirmou os
  hashes e o manifesto SHA-256
  `201ffce772a2275f87bebcd384862a30b3ed3e941aa557d5cce7c42d012a58d1`.
  A base Qwen foi fixada na revisão
  `a09a35458c702b33eeacc393d103063234e8bc28`. Sua revisão no treino
  histórico ainda é desconhecida.
- O vLLM 0.31.0 instalado inicialmente trouxe PyTorch 2.13/CUDA 13.0 e
  falhou antes de carregar o modelo: o driver deste host reportou suporte a
  CUDA 12.8 e o PyTorch o recusou como antigo. Um ambiente isolado com vLLM
  0.11.0, PyTorch 2.8.0+cu128, torchvision 0.23.0 e transformers 4.57.6
  iniciou o mesmo comando de serving. O pin de transformers foi necessário:
  a versão 5.20.1 instalada pelo resolvedor não tinha
  `all_special_tokens_extended`, exigido pelo vLLM 0.11.0. A
  [documentação de instalação do vLLM 0.11.0](https://docs.vllm.ai/en/v0.11.0/getting_started/installation/gpu.html)
  descreve a distribuição CUDA 12.8. Esses ajustes ficaram apenas na Pod
  temporária.
- O vLLM reportou 14,2865 GiB na carga dos pesos e 5,47 GiB de cache KV
  disponível. Uma leitura pontual após o smoke indicou 23.009/24.564 MiB
  de VRAM usados; não é medida de pico nem garantia de concorrência.

## Conectividade e plataforma

- O verificador formal `verify_remote.py` passou com 7/7 aliases por HTTPS,
  uma geração de até oito tokens por alias, sessão
  `ba12522d-3df2-4f8c-9903-4c84183053a9`. O gateway devolveu HTTP 401
  sem bearer. Recibo sem token:
  `runpod/serving/.local/verification-infra-20261017.json`, SHA-256
  `EC72BC65942530A1D2DAF5A91BF60370B377C173DA45B3DB10BAC44E57650A4B`.
- Com o backend apontando para essa sessão, a Bancada autenticada via ngrok
  mostrou os sete aliases disponíveis. O primeiro smoke com `qwen-base` e
  pacote fixo foi persistido como `tool_protocol_error`, ID
  `e3507b58-2828-40f0-ae2d-26fea91fd4dd`. O turno bruto mostrou
  `finish_reason=stop`, resposta textual não vazia e `tool_calls: []`, sem
  tools na requisição. `service.py` interpretava qualquer `tool_calls` não
  nulo como chamada. A condição foi corrigida para tratar apenas a lista
  vazia como ausência de chamada e preservar rejeição de formatos inválidos.
- Os testes locais `test_contract.py` (11) e `test_spec009_http.py` (1)
  passaram após a correção. Um segundo smoke pela Bancada, ID
  `3446e8c6-fee6-4572-8ea6-a4751a89c25a`, foi salvo como
  `answered_unverified`, com a mesma identidade de serving. Isso confirma
  requisição e resposta ponta a ponta; o texto não foi pontuado
  cientificamente.
- O `tunnel-check` final confirmou `/` 200, as três rotas de API testadas
  401 sem autenticação e `/v1/models` 404 no ngrok. A inspeção local do
  ngrok mostrou um túnel HTTP para `127.0.0.1:8765`.

## Encerramento e limites

A Pod foi parada, com readback de computação e disco `Not running`, total
US$ 0,00/h; o saldo exibido passou de US$ 12,28 antes da criação para
US$ 12,20 após a parada. A diferença observada de US$ 0,08 não é fatura
discriminada. O disco temporário e seus ambientes foram apagados. O backend
local foi reiniciado sem endpoint/token remoto; os modelos voltaram a
`indisponível` na interface e o ngrok/bancos continuaram ativos.

O pré-voo local final confirmou DW, banco da aplicação, hashes dos adapters
e configuração de uma vaga global. O resultado agregado permaneceu
`BLOCKED` por alterações sem commit e pela ausência intencional da
configuração de serving com a Pod parada. Não houve `terraform apply`,
benchmark científico, validação de qualidade dos modelos, teste sustentado
de carga nem demonstração de dois pesquisadores simultâneos.
