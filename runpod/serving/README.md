# SPEC-002: preparação local do serving

**Estado em 15/10/2026:** manifesto, preflight, comando vLLM, gateway de
inferência, verificador remoto e Terraform foram escritos e testados apenas
localmente. Nenhum Pod foi criado, iniciado ou consultado; pesos não foram
transferidos e nenhuma geração remota foi observada. A revisão da base usada
nos treinos históricos é desconhecida. Uma revisão exata para uma futura sessão
de serving deve ser escolhida e registrada, sem alegar identidade com o treino.
A SPEC-002 teve a **preparação local aprovada em revisão independente** em
15/10/2026. A implantação paga e a prova de inferência real ficam para outra
interação; essa aprovação não atesta funcionamento remoto.

A [SPEC-005](../../docs/sessao_inferencia_curta.md) acrescenta pré-voo local,
ensaio histórico de três rotas/dois aliases, prova HTTP de túnel e encerramento com
readback. A SPEC-009 retirou o ensaio das rotas anteriores do comando ativo;
um novo ensaio dos dois modos ainda precisa ser contratado. O `verify_remote.py` abaixo continua sendo o smoke test explícito
de sete aliases; a SPEC-005 não o executou contra uma Pod.

A SPEC-009 acrescentou ao comando vLLM `--enable-auto-tool-choice` e
`--tool-call-parser hermes` para Qwen2.5. O backend solicita
`tool_choice: auto` e valida a identidade de sessão em cada turno. Testes
locais com servidor simulado não provam que os adapters reais farão chamadas
válidas; esse ensaio depende de uma sessão RunPod futura e explícita.

## Peças e limites

- [`manifest.json`](manifest.json) lista `qwen-base` e os seis adapters A/B,
  seus caminhos, runs e SHA-256. `base_revision: null` é deliberado: o campo
  operacional exige um commit de 40 caracteres na sessão. O hash do manifesto
  é calculado sobre JSON canônico para não depender de LF/CRLF.
- [`serving.py`](serving.py) confere catálogo científico, paths, manifests de
  treino, configuração PEFT, peso e hash. `command` imprime um vetor de
  argumentos; `start` executa o vetor diretamente, sem shell, somente após
  preflight. vLLM escuta em `127.0.0.1:8001`, com base e seis LoRAs estáticas.
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
  aliases, hashes e resultado por alias, sem gravar a resposta textual.
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
sem GPU, preço, imagem ou capacidade aprovados.

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
| Volume persistente da Pod | `volume_in_gb` × US$ 0,10/GB/mês, proporcional ao tempo em execução | Continua a US$ 0,20/GB/mês até a Pod ser removida. |
| Volume de rede, se criado separadamente | Tarifa atual da opção escolhida × capacidade × tempo | Continua mesmo sem Pod, até ser removido. Não é criado por este Terraform. |

As tarifas de disco acima constavam da documentação oficial consultada em
15/10/2026; reconferir na sessão paga. Com os **tamanhos ilustrativos** de
`session.auto.tfvars.example` (100 GB persistentes e 40 GB de contêiner),
o armazenamento em execução seria aproximadamente **US$ 0,0194/h**, usando
30 dias por mês para converter a tarifa; somar a GPU da oferta escolhida.
Se a Pod fosse parada e mantida, só o volume persistente custaria
aproximadamente **US$ 0,0278/h** sob a mesma convenção. Esses números são
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

Este runbook não foi executado na RunPod. Capacidade para base mais seis LoRAs,
compatibilidade do vLLM, URL HTTPS concreta e parada/remoção precisam de teste
na sessão autorizada. O cenário de avaliação científica continua em
[`BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`](../../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md).
