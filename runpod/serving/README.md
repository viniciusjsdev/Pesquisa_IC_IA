# SPEC-002: preparação local do serving

## Diagnóstico FT-FinQA SPEC-011

Em 19/10/2026, o [diagnóstico offline](../../specs/active/SPEC-011/evidence/local-2026-10-19.md)
confirmou por JSON bruto preservado que A repetiu até `length` e B devolveu
fragmento insuficiente já na resposta direta do vLLM. A causa entre formato
do prompt, política de geração, revisão da base e pesos continua `unresolved`.
[`diagnose_finqa.py`](diagnose_finqa.py) prepara uma matriz de 15 gerações
pareadas (base, A e B em cinco condições), sem mudar o limite padrão da Bancada.
Seu modo `plan` é somente leitura e não consulta a Pod.

Para uma futura sessão **especificamente autorizada**, registrar antes:
Pod/GPU/preço e disponibilidade atuais, tempo máximo, teto de custo, revisão
da base, transferência do pedido privado e destino dos recibos. A referência
histórica da L4 em 17/10 foi cerca de US$ 0,60/h com disco temporário;
proposta de ensaio: 45 minutos de Pod e US$ 0,75 no total, com até 30 minutos
para a matriz depois do preflight; recalcular pelo preço
exibido antes da ativação. Esse é um limite operacional manual, não proteção
automática de cobrança. Usar Pod descartável sem volume persistente somente
se a capacidade/preço atuais e a autorização permitirem. Não abrir ngrok para
este roteiro, que usa o gateway HTTPS para preflight e o vLLM em loopback
dentro da Pod para os contrastes chat/completions. Dados de pesquisa privados
não devem ser copiados para a Pod sem autorização explícita da sessão.

Sequência no checkout da Pod, **após** o gate acima e com token apenas na
variável de ambiente `INFERENCE_VLLM_TOKEN`:

```sh
python runpod/serving/serving.py validate
python runpod/serving/verify_remote.py \
  --endpoint "$SERVING_HTTPS_ENDPOINT" \
  --base-revision "$BASE_REVISION" \
  --output runpod/serving/.local/spec011-verify.json
python runpod/serving/diagnose_finqa.py plan \
  --request-file runpod/serving/.local/finqa-unlimited-requests-20261017.json
python runpod/serving/diagnose_finqa.py execute --execute \
  --request-file runpod/serving/.local/finqa-unlimited-requests-20261017.json \
  --base-revision "$BASE_REVISION" \
  --receipt runpod/serving/.local/spec011-verify.json \
  --session-file runpod/serving/.local/session.json \
  --output-dir runpod/serving/.local/spec011-diagnostic-session \
  --max-wall-seconds 1800
```

O verificador precisa confirmar os sete aliases, seis hashes e a sessão antes
do diagnóstico. O script recusa recibo de outra sessão, revisão ou manifesto
e consulta a identidade **viva** do gateway autenticado antes e depois de cada
geração direta. A janela de 4.096 registrada no artefato vem do comando do
checkout; quando `/v1/models` informa `max_model_len`, o valor reportado também
fica registrado. O script grava pedido/resposta brutos e recibo de erro por
tentativa sob `.local`, com `summary.json` atualizado mesmo se uma chamada
falhar, e deixa de iniciar novas chamadas quando seu orçamento de tempo vence;
uma chamada em curso ainda pode excedê-lo. Ele **não** desliga a Pod.
Registrar SHA-256
dos arquivos, motivo de parada, tokens, conteúdo, repetição, tool calls
(esperadas zero), duração e custo efetivo. Um `stop` só atesta transporte
completo; avaliar o conteúdo separadamente. Um `length` permanece resposta
incompleta. Ao terminar ou falhar, copiar os recibos privados, parar a Pod,
conferir no console as cobranças residuais de GPU e armazenamento e guardar o
readback. Se a comparação apontar pesos/treino, abrir decisão científica
posterior; não regravar adapters nem promover o ensaio a benchmark.

**Estado em 15/10/2026:** manifesto, preflight, comando vLLM, gateway de
inferência, verificador remoto e Terraform foram escritos e testados apenas
localmente. Nenhum Pod foi criado, iniciado ou consultado; pesos não foram
transferidos e nenhuma geração remota foi observada. A revisão da base usada
nos treinos históricos é desconhecida. Uma revisão exata para uma futura sessão
de serving deve ser escolhida e registrada, sem alegar identidade com o treino.
A SPEC-002 teve a **preparação local aprovada em revisão independente** em
15/10/2026. A implantação paga e a prova de inferência real ficam para outra
interação; essa aprovação não atesta funcionamento remoto.

**Teste remoto em 17/10/2026:** uma RTX A5000 de 24 GB foi criada pelo console
RunPod, sem volume persistente, sobre o commit `4943257`. A base Qwen e os seis
adapters carregaram no vLLM 0.31.0; os sete aliases responderam a gerações
curtas pelo gateway em loopback e pela URL HTTPS externa. A Pod
`r0uheznbe2eyn5` foi parada após o teste, com leitura de US$ 0,00/h quando
parada. Consulte o [registro da sessão](evidence/2026-10-17-a5000.md) e os
recibos ignorados em `.local/`. Essa prova não valida a integração da Bancada,
o túnel ngrok, concorrência sustentada nem a avaliação científica. A base
histórica do treino permanece sem revisão identificada. Terraform não criou
nem gerencia a Pod desta sessão.

**Integração exploratória posterior em 17/10/2026:** a mesma Pod foi
reiniciada e o backend local usou seu gateway HTTPS pela Bancada no ngrok.
`qwen-base` completou um run de pacote fixo e outro de tools com chamada real
de `product`; `ft-finqa-a` gerou saída alheia ao pacote até
`finish_reason=length` e seu run foi guardado como `response_error`, sem
reenvio. Duas requisições simultâneas diretas ao gateway, com 3.126 tokens de
entrada cada, passaram na base e em `ft-hibrido-a`. Consulte a
[evidência desta sessão](evidence/2026-10-17-integracao-bancada.md). A Pod foi
parada novamente sem custo residual observado. O cliente Python precisou
enviar `User-Agent: PesquisaICIA/1.0`: o proxy da RunPod devolveu 403 ao
identificador padrão do `urllib` nesta sessão.

**Validação adicional da infraestrutura em 17/10/2026:** a Pod anterior
não pôde reiniciar por falta de GPU livre naquele host. Uma nova RTX A5000
do mesmo preço iniciou com driver CUDA 12.8, incompatível com o PyTorch/CUDA
13.0 trazido pelo vLLM 0.31.0 usado antes. Um ambiente descartável com
vLLM 0.11.0, PyTorch 2.8.0+cu128, torchvision 0.23.0 e transformers 4.57.6
passou no `verify_remote.py` formal: sete aliases e sete gerações mínimas por
HTTPS. A API e a Bancada voltaram a receber uma resposta via ngrok após
o ajuste de `tool_calls: []` em `service.py`. A nova Pod foi parada, sem
volume persistente e com US$ 0,00/h no console. Consulte a
[evidência da sessão](evidence/2026-10-17-validacao-infra.md). Antes de subir
outro host, conferir o driver CUDA real e escolher versões compatíveis de
vLLM, PyTorch, torchvision e transformers; o código Terraform não fixa
essas dependências dentro da imagem.

**Teste dos sete aliases pela Bancada em 17/10/2026:** outra A5000 Secure
Cloud foi criada quando surgiu capacidade. O
[registro da sessão](evidence/2026-10-17-bancada-sete-aliases.md) documenta
7/7 gerações mínimas por HTTPS, sete runs de pacote fixo pela plataforma via
ngrok (cinco `answered_unverified`, dois FT-FinQA truncados) e um run da base
com chamada `product` à DW. A Pod foi parada a US$ 0,00/h, sem volume
persistente. Ainda não há avaliação científica nem prova de carga sustentada.

**Replay FT-FinQA sem teto da aplicação na L4 em 17/10/2026:** o
[registro da sessão](evidence/2026-10-17-finqa-sem-teto-l4.md) documenta
sete aliases confirmados por HTTPS, um run B `answered_unverified` por
invocação direta do backend sem login HTTP e a geração direta dos dois
FT-FinQA sem `max_tokens`. A chegou aos 4.096
tokens totais de contexto (`finish_reason=length`) e B parou com 20 tokens
de saída, porém sem resposta útil. A requisição longa pelo proxy HTTPS
devolveu 524. Naquele teste, o backend esperava até 600 s e o gateway até
610 s, mas o gateway enviava o corpo somente após a geração.
A Pod foi parada sem volume persistente a US$ 0,00/h; não houve avaliação
científica, React/ngrok ou Terraform nesta sessão.

**Correção local posterior, sem Pod nova:** o gateway encaminha SSE do vLLM
em chunks e mantém os cabeçalhos de identidade. O cliente da API reconstrói
resposta e tool calls e guarda os bytes recebidos. A Bancada recebe um job
HTTP 202 e consulta o estado em chamadas curtas. O [teste local](evidence/2026-10-17-transporte-assincrono-local.md)
confirmou encaminhamento do primeiro evento antes de a geração simulada
terminar, parser de tools e fluxo de navegador simulado. Naquele momento,
faltava provar a combinação no proxy HTTPS real, com ngrok e banco migrado.
As Pods anteriores, temporárias e sem volume persistente, não continham a
mudança; o replay posterior abaixo recebeu esta versão de `gateway.py`.

**Replay público posterior em 17/10/2026:** a
[evidência da L4 com streaming](evidence/2026-10-17-streaming-bancada-l4.md)
confirma 7/7 aliases no verificador HTTPS e jobs da Bancada autenticada via
ngrok com `qwen-base` e `ft-finqa-a`. O caso longo chegou como SSE completo,
sem o HTTP 524 anterior; FT-FinQA A terminou `length` nos 4.096 tokens de
contexto e foi recusado como resposta válida. O refresh exigiu novo login,
mas o mesmo job e run foram recuperados sem reenvio. A L4 foi parada com
readback de US$ 0,00/h e sem volume persistente. O teste valida um job por
vez nesse caminho, não a qualidade do modelo ou carga sustentada.

A [SPEC-005](../../docs/sessao_inferencia_curta.md) acrescenta pré-voo local,
ensaio histórico de três rotas/dois aliases, prova HTTP de túnel e encerramento com
readback. A SPEC-009 retirou o ensaio das rotas anteriores do comando ativo;
o ensaio exploratório dos dois modos ocorreu na sessão de integração citada
acima. O `verify_remote.py` abaixo continua sendo o smoke test explícito de
sete aliases; a SPEC-005 não o executou contra uma Pod. A verificação HTTPS
desta sessão usou um cliente PowerShell e produziu recibo local separado.

A SPEC-009 acrescentou ao comando vLLM `--enable-auto-tool-choice` e
`--tool-call-parser hermes` para Qwen2.5. O backend solicita
`tool_choice: auto` e valida a identidade de sessão em cada turno. Testes
locais com servidor simulado não provam que os adapters reais farão chamadas
válidas. A base fez uma chamada `product` válida em 17/10/2026; tool calling
de cada adapter ainda precisa de ensaio próprio.

## Peças e limites

- [`manifest.json`](manifest.json) lista `qwen-base` e os seis adapters A/B,
  seus caminhos, runs e SHA-256. `base_revision: null` é deliberado: o campo
  operacional exige um commit de 40 caracteres na sessão. O hash do manifesto
  é calculado sobre JSON canônico para não depender de LF/CRLF.
- [`serving.py`](serving.py) confere catálogo científico, paths, manifests de
  treino, configuração PEFT, peso e hash. `command` imprime um vetor de
  argumentos; `start` executa o vetor diretamente, sem shell, somente após
  preflight. vLLM escuta em `127.0.0.1:8002`, com base e seis LoRAs estáticas.
- [`gateway.py`](gateway.py) escuta na porta 8000, exige bearer token e
  encaminha somente `GET /v1/models` e `POST /v1/chat/completions` para os
  sete aliases declarados. O endpoint
  administrativo de LoRA, `/invocations` e demais rotas são recusados. O
  token fica apenas em `INFERENCE_VLLM_TOKEN`, nunca no manifesto, Terraform,
  snapshot ou URL. A conexão pública deve usar HTTPS pela camada de proxy da
  RunPod; o vLLM isolado não deve ter porta pública.
- [`verify_remote.py`](verify_remote.py) exige a URL HTTPS explícita, refaz
  preflight no checkout do Pod, consulta modelos e pede uma geração de até oito
  tokens por alias. A saída inclui versão local do vLLM, revisão da base,
  aliases, hashes e resultado por alias, sem gravar a resposta textual. O
  cliente envia um `User-Agent` específico para evitar a recusa observada no
  proxy da RunPod ao identificador padrão do `urllib`.
- [`terraform/`](terraform/) declara um Pod com somente a porta HTTP 8000
  exposta. Tipo de GPU, data center, imagem, quantidade de GPUs, disco e tipo
  de nuvem são entradas obrigatórias. Nenhum `plan` ou `apply` foi executado.

O gateway devolve identidade de sessão, revisão e SHA-256 do manifesto em
headers. O backend preenche a proveniência do snapshot **apenas** quando esses
headers coincidem com o manifesto local. `available` depende de
`/v1/models`; `generation_confirmed` exige adicionalmente um recibo
`passed` da mesma URL e sessão. Esses campos registram a sessão observada;
não provam que a revisão servida era a usada no treinamento nem constituem
benchmark científico.

## Validação estática, sem Pod

Na raiz do repositório, com um Python local:

```powershell
inference_api/.venv/Scripts/python.exe runpod/serving/serving.py validate
inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v
git diff --check
```

`command --base-revision <commit-HF-de-40-hex>` também valida e imprime o
argv que será usado, mas **não inicia** o vLLM. Ele só aceita revisão exata;
`latest`, branch e tag são recusados. Não use um hash fictício como revisão
operacional. Os seis pesos finais são Git LFS; após cópia/clone, conferir se
foram materializados antes do preflight.

## Terraform: preparar sem criar recurso

O provider [`decentralized-infrastructure/runpod`](https://registry.terraform.io/providers/decentralized-infrastructure/runpod/1.0.1/docs)
oferece `runpod_pod`; esta configuração fixa a versão `1.0.1` e seu lock
file. Em 14/10/2026, um Terraform CLI 1.13.4 temporário verificou o SHA-256
da distribuição, executou `fmt -check`, `init -backend=false` e
`validate` com sucesso, sem chave RunPod. O provider oficial
[`runpod/runpod` 1.0.9](https://registry.terraform.io/providers/runpod/runpod/latest/docs)
foi testado primeiro, mas `validate` falhou ao carregar o schema do próprio
plugin (`runpod_endpoint_workers.workers` sem Required/Optional/Computed);
por isso ele não é a dependência deste arquivo. A alternativa escolhida passou
na validação local; **não houve teste de criação**. Conferir novamente provider
e oferta antes de uma sessão paga. O exemplo contém valores ilustrativos,
sem GPU, preço, imagem ou capacidade aprovados. `volume_in_gb = 0` omite o
volume da Pod para um teste descartável. Nesse caso, os 50 GB de disco do
contêiner são apagados ao parar a Pod: código, cache do modelo, adapters e
resultados precisam ser copiados antes da parada. Um volume de rede precisa
ser anexado durante a criação de uma nova Pod; não pode ser acrescentado à
Pod existente depois.

```powershell
Copy-Item runpod/serving/terraform/session.auto.tfvars.example runpod/serving/terraform/session.auto.tfvars
# Editar gpu_type_ids, data_center_ids, imagem imutável, cloud_type e tamanhos após conferir oferta/custo.
# Disponibilizar RUNPOD_API_KEY no ambiente a partir de um gerenciador de segredos; não escrever a chave em arquivo versionado ou no histórico.
terraform -chdir=runpod/serving/terraform init
terraform -chdir=runpod/serving/terraform fmt -check
terraform -chdir=runpod/serving/terraform validate
New-Item -ItemType Directory -Force runpod/serving/terraform/.local | Out-Null
terraform -chdir=runpod/serving/terraform plan -out=.local/session.tfplan
```

`session.auto.tfvars`, `.terraform/`, `.local/` e state ficam fora do Git; o
lock file gerado foi preservado para revisão. Trate o plano salvo e o state
como sensíveis. `plan` mostra as mudanças pretendidas, mas **não calcula a
fatura da RunPod**, não garante GPU disponível e não testa a criação real com
este provider. A estimativa deve ser feita separadamente antes de pedir a
confirmação. Nenhum `plan` foi executado nesta SPEC por falta de uma configuração
e credencial reais. **Somente uma confirmação explícita do usuário autoriza
`terraform apply`.**

## Custos a revisar antes da próxima sessão

A [tabela oficial de preços de Pods](https://docs.runpod.io/pods/pricing)
informa cobrança de computação e armazenamento por tempo de uso. O preço da
GPU depende da oferta selecionada e deve ser conferido no console da RunPod
imediatamente antes da criação; não há GPU ou tarifa aprovada nesta SPEC. A
Pod em execução consome créditos inclusive enquanto imagem e pesos estão
sendo preparados. `init`, `fmt`, `validate` e `plan` não criam a Pod.

| Item | Como estimar nesta configuração | Depois de parar a Pod |
| --- | --- | --- |
| GPU | Tarifa atual da GPU no console × número de GPUs × horas de Pod em execução | Computação da GPU deixa de ser cobrada. |
| Disco do contêiner | `container_disk_in_gb` × US$ 0,10/GB/mês, proporcional ao tempo em execução | Não é cobrado; o conteúdo temporário é apagado. |
| Volume persistente da Pod, se `volume_in_gb > 0` | `volume_in_gb` × US$ 0,10/GB/mês, proporcional ao tempo em execução | Continua a US$ 0,20/GB/mês até a Pod ser removida. |
| Volume de rede, se criado separadamente | Tarifa atual da opção escolhida × capacidade × tempo | Continua mesmo sem Pod, até ser removido. Não é criado por este Terraform. |

As tarifas de disco acima constavam da documentação oficial consultada em
17/10/2026; reconferir na sessão paga. Com o exemplo atual de 50 GB temporários
e nenhum volume persistente, o armazenamento em execução seria aproximadamente
**US$ 0,0069/h**, usando 30 dias por mês para converter a tarifa; após a parada,
não há custo residual de armazenamento e os dados são apagados. Um volume de
rede standard opcional de 30 GB custaria aproximadamente **US$ 2,10/mês**,
inclusive sem Pod, e preservaria os dados entre Pods. Esses números são
estimativas de armazenamento, não uma cotação total nem valores aprovados.
Para a sessão, registrar tarifa de GPU, tamanhos reais, duração máxima e
estimativa `GPU + discos`, além de saldo/créditos, antes do `apply`. Este
Terraform não impõe um limite de gastos nem desliga a Pod automaticamente;
definir um responsável por acompanhar o tempo e encerrar a sessão.

## Próxima interação: plano, aprovação e aplicação

1. Reabrir este checkout e conferir revisão independente, arquivos, provider,
   imagem compatível, revisão exata da base e disponibilidade/preço da GPU.
   Definir duração e custo máximo da sessão. Uma imagem ou revisão ainda não
   escolhida não deve ser substituída por um valor fictício.
2. Preencher `session.auto.tfvars` com a oferta real; fornecer a chave RunPod
   somente pelo ambiente. Executar `init`, `fmt -check`, `validate` e
   `plan -out=.local/session.tfplan` como acima. Examinar o plano, inclusive
   número de GPUs, discos, porta 8000 e eventuais substituições de recursos.
3. Apresentar ao usuário o plano concreto, tarifa atual, estimativa para a
   janela prevista e custo de armazenamento se a Pod ficar parada. Aguardar
   sua **confirmação explícita** antes de executar:

   ```powershell
   terraform -chdir=runpod/serving/terraform apply .local/session.tfplan
   ```

4. Após a aplicação autorizada, ler o ID e estado reais no Terraform e na
   RunPod. Se a criação falhar ou o estado for incerto, reconciliar o recurso
   antes de qualquer nova tentativa. Registrar início e custo observado.
5. Seguir a validação remota abaixo. Ao término, conferir o estado e remover
   a Pod quando os artefatos necessários estiverem preservados; confirmar no
   console que a cobrança do volume persistente cessou. `terraform destroy`
   apaga o volume da Pod e exige revisão do estado e dos dados antes de rodar.

## Sessão remota futura, dependente de autorização

1. Cumprir o procedimento de custo, plano e aplicação acima. Guardar ID,
   custo observado e estado do Pod.
2. Disponibilizar no Pod somente o código e os seis diretórios `adapter/`
   listados no manifesto, seus `meta/run_manifest.json`, o catálogo
   `FineTuning/docs/modelos_disponiveis.md` e a base Qwen fixada. Um clone
   completo do repositório é uma alternativa operacional, mas transfere mais
   dados; preserve o layout relativo. Não mover `runpod/*.sh`.
3. No checkout do Pod, executar `python runpod/serving/serving.py validate`.
   Definir `INFERENCE_VLLM_TOKEN` no ambiente do processo, com pelo menos
   32 caracteres. Em seguida, executar
   `python runpod/serving/serving.py start --base-revision <commit-HF-exato>`.
   O comando registra uma sessão sem segredo em
   `runpod/serving/.local/session.json`; Ctrl+C encerra gateway e vLLM.
4. Somente após confirmar proteção HTTPS e autorização da sessão, executar
   `python runpod/serving/verify_remote.py --endpoint https://<origem-do-pod> --base-revision <commit-HF-exato> --output runpod/serving/.local/verification.json`.
   O endpoint é obrigatório e não é inferido do Terraform. O processo consulta
   `/v1/models` e faz sete gerações curtas; isso consome tempo de GPU.
5. Transferir o recibo sem segredo para a máquina da API e definir
   `INFERENCE_SERVING_VERIFICATION` para seu caminho, além de
   `INFERENCE_VLLM_URL` e `INFERENCE_VLLM_TOKEN` no **backend**. Conferir
   `GET /api/models`: candidato, disponível e geração confirmada são estados
   diferentes. Uma sessão ou URL diferente invalida o recibo.
6. Ao fim, inspecionar estado e custo, parar o processo e seguir o plano de
   encerramento da sessão. Parar a Pod evita novo custo de GPU, mas o volume
   persistente continua cobrando até a remoção. Conferir o estado final na
   RunPod e na cobrança após a remoção.

O fluxo de `terraform plan/apply` deste runbook ainda não foi executado. O
teste pelo console de 17/10/2026 confirmou carga e sete gerações curtas na
RTX A5000; a segunda sessão validou exploratoriamente a integração da base
com a aplicação e ambos os modos da Bancada. A Pod foi parada sem custo
residual observado. Uma futura sessão precisa recriar o ambiente temporário
para novos ensaios. O cenário de avaliação científica continua em
[`BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`](../../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md).
