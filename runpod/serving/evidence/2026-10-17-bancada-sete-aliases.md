# Validação de infraestrutura dos sete aliases na Bancada — 17/10/2026

Escopo: um teste exploratório de conectividade e persistência por alias na
Bancada autenticada via ngrok, mais um run da base com tool real da DW. Não é
avaliação científica, aferição de acurácia nem teste de carga. O checkout local
continuou no commit `494325797356183897e97149805cb25ead3b3eb9` com
alterações sem commit já existentes. A Pod recebeu cópias locais de
`serving.py`, `gateway.py` e `verify_remote.py`.

## Ambiente e serving

- As Pods `g0y5v9h2x9x6us` e `r0uheznbe2eyn5` não reiniciaram por falta de
  GPU livre no host. A oferta A5000 desapareceu temporariamente do catálogo;
  a RTX 4090 Community também perdeu capacidade antes da criação. Nenhuma
  dessas tentativas criou cobrança adicional.
- A Pod `hyeeqzysb2o84s` foi criada pelo console, sem Terraform, em
  `CA-MTL-1` Secure Cloud: 1× RTX A5000 24.564 MiB, 50 GB RAM, 9 vCPU,
  imagem `runpod/pytorch:1.4.0-cu1281-torch280-ubuntu2404`, 50 GB de disco
  temporário e nenhum volume persistente. Preço exibido: US$ 0,27/h de GPU
  mais US$ 0,007/h de disco, total arredondado US$ 0,28/h.
- Driver NVIDIA `580.178.04`. Ambiente isolado instalado na Pod:
  vLLM `0.11.0`, PyTorch `2.8.0+cu128`, torchvision `0.23.0` e
  transformers `4.57.6`. `serving.py validate` confirmou seis adapters e o
  manifesto SHA-256
  `201ffce772a2275f87bebcd384862a30b3ed3e941aa557d5cce7c42d012a58d1`.
  A base Qwen usou a revisão
  `a09a35458c702b33eeacc393d103063234e8bc28`; sua revisão histórica
  de treino segue desconhecida.
- `verify_remote.py` passou com 7/7 gerações curtas por HTTPS na sessão
  `b9d4683c-ed7b-43a6-987a-aa26c2481bf5`. Recibo ignorado em
  `runpod/serving/.local/verification-platform-20261017.json`, SHA-256
  `379CD1E8A8A0C577C31BA339FEDABBDC15CE36B2E98A57C31D284C9C9380F15B`.
  `GET /v1/models` sem bearer recebeu HTTP 401. Uma leitura pontual após os
  runs mostrou 22.837/24.564 MiB de VRAM; não é pico nem garantia de
  concorrência ou de execução sustentada.

## Plataforma local e ngrok

O frontend autenticado como Vinicius mostrou os sete aliases disponíveis.
Cada alias foi executado uma vez com o mesmo pacote privado
`integrado-produto-2020-01`, SHA-256
`ba57ab3d37a191c6e2be91622e975ae93794117828ad357dee6c8f51cb0f346c`,
temperatura `0,2` e limite de 500 tokens. Os sete snapshots ficaram no
`db_inference_app`. A consulta local de readback gerou o resumo ignorado
`inference_api/.local/platform-runs-20261017.json`, SHA-256
`2906046D0974F55F48752E94034896865E336FA0EAC9A8989D6E0D470D4B2211`.

| Alias | Estado na Bancada | Run ID | Resposta vLLM |
| --- | --- | --- | --- |
| `qwen-base` | `answered_unverified` | `f0c73fd1-9d6d-4273-adfd-fa4447a0b086` | `stop`, 393 tokens |
| `ft-finqa-a` | `response_error` | `d6f32d99-52ea-4118-b6a8-7200375106f5` | `length`, 500 tokens |
| `ft-failure-a` | `answered_unverified` | `b1c39edc-1413-4930-9e7a-6358fae0cc2a` | `stop`, 364 tokens |
| `ft-hibrido-a` | `answered_unverified` | `48112f9b-f435-4037-9f4d-0bf33ca3660d` | `stop`, 452 tokens |
| `ft-finqa-b` | `response_error` | `57626c2f-fc61-4e09-9670-15a2457cdb19` | `length`, 500 tokens |
| `ft-failure-b` | `answered_unverified` | `18ada6da-78bb-44e2-aad8-4a1589d264fd` | `stop`, 398 tokens |
| `ft-hibrido-b` | `answered_unverified` | `152091e6-6863-4dff-bf33-6bee7dec9700` | `stop`, 259 tokens |

Os dois FT-FinQA devolveram corpo textual e a identidade da sessão, mas
atingiram o limite de saída. O cliente classificou essas respostas como
`Invalid chat completion shape`/`response_error`; a causa da geração longa
ou fora do formato ainda não foi isolada. Não houve evidência de OOM nem de
falha HTTP nesses dois runs. Os outros cinco confirmaram o alias servido e a
sessão no snapshot; `answered_unverified` não certifica qualidade da resposta.

Um run adicional da base em `dw_tools`, ID
`4a9cc490-0afe-4117-957f-2e98d733df16`, terminou
`answered_unverified`, com dois turnos e chamada `product` à DW. O pré-voo
local confirmou banco DW, banco da aplicação, seis hashes e uma vaga global;
o agregado foi `BLOCKED` por alterações sem commit e configuração remota
intencionalmente ausente antes da ativação. A suíte local teve 41 testes sem
falhas (7 pulados). O `tunnel-check` confirmou `/` 200, três rotas autenticadas
401 sem sessão e `/v1/models` 404 no ngrok.

## Encerramento e custo

A Pod foi parada após o teste. O console mostrou `Not running` para
computação e disco e US$ 0,00/h para as três Pods listadas. O saldo exibido
passou de US$ 12,20 antes da criação para US$ 12,17 na leitura logo após a
parada: diferença observada US$ 0,03, não fatura discriminada e sujeita à
atualização posterior. Como não havia volume persistente, cache, pesos,
ambiente e token da Pod foram apagados. Recibos e runs locais permanecem.
O backend local foi reiniciado sem URL/token remotos; a interface voltou a
marcar os sete aliases indisponíveis. `terraform plan/apply/destroy` não foi
executado.
