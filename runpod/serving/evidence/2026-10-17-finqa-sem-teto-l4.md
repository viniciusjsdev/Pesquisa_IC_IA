# Replay FT-FinQA sem teto da aplicação na L4

**Sessão:** 17/10/2026 em São Paulo (18/10/2026 UTC). Esta é uma validação
exploratória de infraestrutura e integração, não uma avaliação científica.

## Pod e escopo

- O usuário autorizou uma Pod por até uma hora. A Pod
  `pesquisa-ic-ia-finqa-sem-teto-20261017` (`mh1haxycv8zky9`) foi criada pelo
  console RunPod aproximadamente às 00:42:25 UTC e parada aproximadamente às
  01:05:50 UTC, dentro da janela autorizada.
- 1× NVIDIA L4 de 24 GB, 50 GB de disco temporário, sem volume persistente.
  O console mostrou US$ 0,60/h durante a execução e, após a parada, **total
  US$ 0,00/h**, compute e container storage `Not running`. O modal de parada
  mostrou custo ocioso US$ 0,000/h. O saldo visível passou de US$ 12,16 antes
  da criação para US$ 11,96 no último readback; essa diferença de US$ 0,20
  não é uma fatura final da sessão.
- Imagem `runpod/pytorch:1.4.0-cu1281-torch280-ubuntu2404`. O host mostrou
  driver 595.91.07/CUDA 13.2 e `nvidia-smi` identificou a L4 com 23.034 MiB
  visíveis. Durante a geração longa, 21.468 MiB estavam ocupados e a GPU
  atingiu 98–99% de utilização; não houve erro de falta de VRAM.
- Checkout remoto no commit `494325797356183897e97149805cb25ead3b3eb9`;
  base Qwen fixada em `a09a35458c702b33eeacc393d103063234e8bc28`;
  vLLM 0.11.0. Os arquivos locais de serving ainda sem commit foram copiados
  para a Pod. Nenhum `terraform apply`, treino ou avaliação científica foi
  executado.

## Evidência de serving

O `serving.py validate` confirmou o manifesto SHA-256
`201ffce772a2275f87bebcd384862a30b3ed3e941aa557d5cce7c42d012a58d1`
e os seis adapters. O `verify_remote.py` foi executado no venv da Pod contra
o endpoint HTTPS, depois da última inicialização, e passou com **7/7 aliases**
na sessão `3af22313-19bc-4b89-8b3a-b0cbc5638f4c`.

Recibo local ignorado pelo Git:
`runpod/serving/.local/verification-finqa-unlimited-20261017.json`, SHA-256
`770302526271c1888ee1f39014354052b13dcac78a66725a4f9ccc9ceb8dfcc1`.
Os prompts curtos do verificador têm `max_tokens: 8` por desenho e não são o
replay de FinQA.

## Replay dos casos históricos

Foram reutilizados o pacote `integrado-produto-2020-01` SHA-256
`ba57ab3d37a191c6e2be91622e975ae93794117828ad357dee6c8f51cb0f346c`,
as mensagens, o prompt, os critérios e a temperatura 0,2 dos runs históricos
`d6f32d99-52ea-4118-b6a8-7200375106f5` (A) e
`57626c2f-fc61-4e09-9670-15a2457cdb19` (B). A única mudança intencional
na requisição de inferência foi **omitir `max_tokens`**. Não foi aberto ngrok,
nem se executou o React nesta sessão. A invocação abaixo entrou diretamente
em `service.execute_run` e persistiu novos snapshots no banco isolado da
aplicação. O objeto `Principal` foi reconstruído de um run anterior de
Vinicius, **sem passar pelo login HTTP**. Por isso o campo interno
`author_verified: true` desses novos snapshots não constitui prova de
autenticação nesta sessão; eles são registros técnicos de replay e não devem
ser usados como runs autenticados de avaliação.

| Caminho | Alias | Resultado observado |
| --- | --- | --- |
| Backend → HTTPS, espera de 120 s | A | Run `b1a7770c-491c-4b65-95e1-a89db5f501e0`: `model_error`, `TimeoutError` de leitura, `max_tokens: null`. |
| Backend → HTTPS, esperas ampliadas | A | Run `add318bd-f841-4893-9020-5016ce37d260`: `model_error`, HTTP 524 vindo do caminho de proxy; `max_tokens: null`. O segundo run planejado nessa tentativa foi interrompido, sem snapshot novo. |
| Gateway local da Pod, sem proxy | A | HTTP 200, 195 s, `finish_reason=length`, 945 tokens de prompt + 3.151 de saída = 4.096 tokens da janela do vLLM. A saída de 13.068 caracteres repete instruções e não conclui a resposta. |
| Gateway local da Pod, sem proxy | B | HTTP 200, 1,5 s, `finish_reason=stop`, 945 tokens de prompt + 20 de saída. O texto de 22 caracteres é um fragmento numérico sem explicação. |
| Backend → HTTPS | B | Run `1e57ef9a-ab03-46e8-8c53-55a39c7bdc32`: `answered_unverified`, `finish_reason=stop`, 20 tokens de saída, `max_tokens: null`; o corpo HTTP registrado **não contém** `max_tokens`, e a sessão/proveniência foi confirmada. |

As respostas diretas estão preservadas localmente, fora do Git, em
`runpod/serving/.local/direct-finqa-ft-finqa-a.json` (SHA-256
`7e220f6dfcc438d0084e2071bafc75d3a82fa2673b145e2180c282bf7a2e7aa8`)
e `runpod/serving/.local/direct-finqa-ft-finqa-b.json` (SHA-256
`2fb46f6af16a97bcb0267040830eaf7ca0c41026214287e97240ede1a76d6a9b`).
O resumo direto está em `.local/direct-finqa-summary.json` (SHA-256
`37fded108fad4887912a3c00947a753bc67e323dea70d86ac32a529ea470738e`).

No run B persistido, presença de evidência e período passaram, mas IDs citados,
verdade numérica e causalidade ficaram `not_checked`. Portanto
`answered_unverified` significa somente que houve resposta e persistência;
o fragmento numérico observado não satisfaz a pergunta da pesquisa.

## Limite identificado

O código da aplicação já omite `max_tokens` quando o pesquisador não informa
esse parâmetro. Nesta sessão, o primeiro limite adicional foi a espera de
120 s no backend. Ela foi ampliada para 600 s, e a espera do gateway para
610 s. Mesmo assim, o gateway atual só devolve a resposta depois de ler o
corpo inteiro do vLLM; para o FT-FinQA A, a origem levou 195 s e o endpoint
HTTPS devolveu HTTP 524 antes da conclusão. O [significado de HTTP 524 na
Cloudflare](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/)
é conexão estabelecida com a origem, mas sem resposta dentro do prazo do
proxy. Esta é a interpretação mais compatível com o erro e com o código do
gateway; não foi medida uma configuração interna específica da RunPod.

Após o ajuste das esperas, passaram localmente os 8 testes de
`test_serving.py` e os 11 de `test_contract.py`; `py_compile` dos arquivos
alterados e `git diff --check` não apontaram erro de sintaxe ou whitespace.
Esses testes não simulam o prazo do proxy HTTPS.

O teste direto prova que a L4 e o vLLM conseguem gerar sem teto explícito da
aplicação. Também mostra que o adapter A continua até o limite de contexto
de 4.096 tokens, enquanto B para cedo com conteúdo fraco. Para respostas
longas passarem pela plataforma pública, o transporte precisará transmitir
progresso/streaming ou usar execução assíncrona com consulta de resultado.
Isso permanece pendente. Esta sessão não comprova acurácia, comparação entre
modelos nem aptidão científica dos FT-FinQA.

Ao encerrar, o PostgreSQL isolado iniciado para o replay voltou a ficar
parado (`127.0.0.1:5544` sem listener); a API local também não escutava em
`127.0.0.1:8765`. Todos os arquivos de resposta e recibos citados acima
foram copiados antes de parar a Pod descartável.
