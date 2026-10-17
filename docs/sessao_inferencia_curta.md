# SPEC-005: sessão curta de inferência compartilhada

**Estado em 16/10/2026:** procedimento e verificações locais preparados e
[aprovados em revisão independente](../specs/active/SPEC-005/evidence/review.json).
Nenhuma Pod, geração remota ou URL ngrok foi ativada por esta SPEC. O ensaio
descrito abaixo é exploratório: não usa gold set nem produz métricas do artigo.

Este roteiro pressupõe uma janela inferior a 24 horas, um operador responsável
por acompanhar o custo e autorização explícita para **cada** ativação externa.
O teto manual de US$ 10 exibido no front não é um limite imposto pela RunPod.
Os estados de cada gate são `CONFIRMED` (readback observado), `BLOCKED` (falha
conhecida) e `UNCERTAIN` (efeito ou estado não reconciliado). Um gate bloqueado
interrompe a sequência; nunca recriar Pod, refazer geração ou reenviar um run
automaticamente.

## 1. Pré-voo local, sem rede externa

Na raiz do repositório, com o PostgreSQL isolado já iniciado, faça uma leitura
preliminar dos gates locais:

```powershell
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py status
inference_api/.venv/Scripts/python.exe inference_api/session_checks.py preflight --output inference_api/.local/preflight-YYYYMMDD-HHMMSS.json
```

Antes de existir a Pod, `serving_configuration` ficará `BLOCKED`; use o
relatório para confirmar separadamente os gates locais e **não** declarar a
sessão pronta. Repita o pré-voo completo após obter a origem HTTPS e as
credenciais da sessão. O pré-voo não consulta a URL: verifica que ela é uma
origem HTTPS sem credenciais embutidas. Ele falha
se o Git não estiver limpo, se faltar a DW v1 em `db_pesquisa_dw`, migrações 1/2
ou os dois usuários ativos no banco da aplicação, se faltar qualquer adapter
ou SHA-256, revisão exata da base, URL/token protegido ou a configuração de
uma inferência global sem cotas diárias. As conexões de aplicação e DW usam transações somente leitura em
`127.0.0.1:5544`. A leitura da migração/fingerprint da DW prova apenas
disponibilidade local, não valida novamente a carga ou o harness. O relatório não contém
senhas, token nem resposta de modelo e marca geração remota e ngrok `not_run`.

O Git deve estar limpo após a revisão/commit das alterações locais. Caso haja
mudanças ainda em avaliação, o gate permanece `BLOCKED` e seu estado deve ser
reconciliado antes da sessão. O pré-voo não faz `git add`, commit ou limpeza.

## 2. Ativação paga separada

O [runbook de serving](../runpod/serving/README.md#próxima-interação-plano-aprovação-e-aplicação)
define a escolha real de GPU/imagem/discos, o preço consultado naquele momento,
o `terraform plan` salvo e a apresentação do custo estimado. A confirmação
explícita do usuário é o último gate antes de `terraform apply`; este
documento não a substitui. Registrar ID da Pod, instante de início, tarifa de
GPU, tamanhos dos discos, saldo observado e responsável pela parada.

No checkout da Pod, após a ativação autorizada, validar os adapters com
`python runpod/serving/serving.py validate`, iniciar o gateway/vLLM pelo
comando documentado na SPEC-002 e conferir que só a porta HTTP 8000 do gateway
está exposta. O vLLM escuta no loopback da Pod. Uma falha de criação ou um
resultado ambíguo exige leitura do estado real da Pod e do Terraform antes de
qualquer nova tentativa.

## 3. Modelo: uma verificação remota explícita

No checkout Linux da Pod, com `INFERENCE_VLLM_TOKEN`,
`INFERENCE_VLLM_URL` e `INFERENCE_BASE_REVISION` somente no ambiente e a
origem HTTPS já confirmada:

```bash
python runpod/serving/verify_remote.py --endpoint "$INFERENCE_VLLM_URL" --base-revision "$INFERENCE_BASE_REVISION" --output runpod/serving/.local/verification.json
```

Este comando é **opt-in** e faz exatamente um `GET /v1/models` e uma geração
curta por cada um dos sete aliases; pode consumir GPU. Ele não cria/inicia Pod.
O recibo registra horário, alias, resultado, sessão, versão vLLM, revisão da
base e hashes dos adapters, sem texto gerado nem bearer. A validação falha se
headers, manifesto, revisão, versão ou lista de modelos divergirem. Copiar o
recibo para um caminho local ignorado pelo Git e definir
`INFERENCE_SERVING_VERIFICATION` no ambiente do backend. O recibo comprova
gerações naquela sessão; não comprova identidade com a revisão histórica do
treino nem acurácia científica.

No notebook, preencher as três variáveis da sessão sem digitar o segredo no
histórico e repetir o pré-voo. Os valores entre `<...>` precisam ser lidos da
sessão real, não inventados:

```powershell
$env:INFERENCE_BASE_REVISION = '<commit-HF-exato-de-40-hex>'
$env:INFERENCE_VLLM_URL = 'https://<origem-HTTPS-do-gateway>'
$secureToken = Read-Host 'Gateway token' -AsSecureString
$env:INFERENCE_VLLM_TOKEN = [System.Net.NetworkCredential]::new('', $secureToken).Password
Remove-Variable secureToken
$env:INFERENCE_SERVING_VERIFICATION = 'inference_api/.local/verification.json'
inference_api/.venv/Scripts/python.exe inference_api/session_checks.py preflight --output inference_api/.local/preflight-final-YYYYMMDD-HHMMSS.json
```

## 4. Aplicação e ngrok, somente na sessão autorizada

Antes da primeira exposição, trocar **ambas** as senhas em terminal local com
`inference_api/run.py set-password --username Nicoli` e `--username Vinicius`.
As escolhas anteriores passaram pelo chat. O comando pede senha sem eco e
revoga sessões anteriores. Confirmar os dois logins com
`inference_api/verify_local_users.py`; esse verificador não cria runs.

Iniciar a aplicação em um terminal local com
`inference_api/.venv/Scripts/python.exe inference_api/run.py serve`. Em outro
terminal, **somente após autorização de exposição**, iniciar `ngrok http 8765`.
Conferir no terminal/painel do ngrok que existe um único encaminhamento HTTPS
para o HTTP da aplicação em `127.0.0.1:8765`, sem endpoint TCP e sem destino
`5544`, `8000` ou `8001`. A autenticação escolhida é a da própria aplicação,
sem OAuth/Basic Auth adicional na borda.

```powershell
$ngrokOrigin = 'https://<origem-HTTPS-mostrada-pelo-ngrok>'
inference_api/.venv/Scripts/python.exe inference_api/session_checks.py tunnel-check --execute --app-origin $ngrokOrigin --output inference_api/.local/tunnel-YYYYMMDD-HHMMSS.json
```

O teste remoto espera `/` 200, `/api/me`, `/api/runs` e `/api/models` 401 sem
sessão, e `/v1/models` 404. Ele não envia credenciais. Isso confirma o
comportamento HTTP observado **por esta URL**; a inspeção do encaminhamento e
de outros túneis continua obrigatória para afirmar que PostgreSQL e vLLM
interno não estão expostos por engano. Registrar URL, horário, processo e
destino vistos, sem publicar a URL em documentação versionada.

## 5. Ensaio ponta a ponta pendente de novo contrato

A SPEC-009 substituiu `scope` por `dw_snapshot` e `dw_tools` para novos runs.
O comando antigo `session_checks.py rehearsal` foi retirado do fluxo ativo
porque fazia seis runs das rotas anteriores e interpretava sua escolha de
consulta como se pudesse representar a pesquisa por tools. Não executá-lo nem
adaptar seus resultados para os modos novos. O pré-voo local e `tunnel-check`
continuam disponíveis.

Antes de uma sessão paga, definir e revisar um ensaio com pacotes candidatos
identificados por ID/hash, perguntas livres para tools, recibo do serving real
Qwen2.5, limites por turno, autores e readback dos snapshots v3. Essa preparação
não cria gold set nem benchmark científico. Cada geração externa continua
exigindo acionamento explícito da sessão; em resposta perdida, reconciliar o
histórico por identidade exata antes de tentar novamente.

## 6. Exportação, custo e encerramento

Durante a sessão, anotar horário inicial, tempo decorrido, preço da GPU e
discos, saldo real e gasto por hora lidos no console da RunPod ou, quando
confirmado, em `/api/budget`. Se a leitura falhar, registrar `UNCERTAIN` e
usar o console para reconciliar; o teto manual de US$ 10 não interrompe a
cobrança. Quando houver um novo relatório de ensaio aprovado, guardar seu SHA-256:

```powershell
Get-FileHash -Algorithm SHA256 inference_api/.local/session-YYYYMMDD-HHMMSS.json
```

O banco `db_inference_app` mantém revisões e snapshots. Para uma cópia lógica
adicional, depois de conferir o destino local protegido, usar `pg_dump` no
banco **da aplicação**, sem tocar os bancos de origem:

```powershell
$dump = 'inference_api/.local/session-app.dump'
if (Test-Path -LiteralPath $dump) { throw 'O dump de destino já existe.' }
$env:PGPASSWORD = ((Get-Content BancoModeloUse/.env.local | Where-Object { $_ -like 'FINANCEIRO_DB_PASSWORD=*' } | Select-Object -First 1) -split '=', 2)[1]
try {
  & 'C:/Program Files/PostgreSQL/15/bin/pg_dump.exe' --format=custom --file $dump --host 127.0.0.1 --port 5544 --username pesquisa_local --dbname db_inference_app
  if ($LASTEXITCODE -ne 0) { throw 'pg_dump falhou; exportação não confirmada.' }
} finally { Remove-Item Env:PGPASSWORD }
& 'C:/Program Files/PostgreSQL/15/bin/pg_restore.exe' --list $dump | Select-Object -First 10
Get-FileHash -Algorithm SHA256 $dump
```

Esse dump inclui dados de autenticação e deve ficar em armazenamento local
protegido, fora do Git. Não sobrescrever um dump existente. Confirmar os IDs
dos runs no banco/arquivo e o hash antes de retirar recursos.

Encerrar o ngrok com Ctrl+C e verificar que a URL deixou de encaminhar.
Encerrar gateway/vLLM com Ctrl+C; conferir o processo e a sessão reais. Parar
a Pod na RunPod para interromper computação e obter readback do estado e da
cobrança. Volume persistente pode continuar custando após a parada; revisar
dados preservados, plano e state antes de pedir autorização para removê-lo.
`terraform destroy` e remoção de Pod/volume exigem acionamento explícito,
pois podem apagar o armazenamento remoto. Se qualquer readback faltar, marcar
`UNCERTAIN` e reconciliar antes de repetir uma ação.

| Gate | Prova para `CONFIRMED` | Limite |
| --- | --- | --- |
| DW local | Pré-voo com migração/fingerprint e `transaction_read_only` | Leitura da carga existente, não recarga ou validação científica |
| Pesos locais | Manifesto, caminhos e SHA-256 dos seis adapters | Não prova base ou pesos servidos |
| Modelo remoto | Recibo de `/v1/models` e sete gerações da mesma sessão | Não é benchmark |
| Aplicação | Futuro ensaio dos dois modos com readback dos snapshots v3 | Não executado; checks exploratórios sem verdade numérica/causal validada |
| Túnel | HTTP externo observado e encaminhamento único para `8765` conferido | Não prova ausência de outros túneis sem inspeção |
| Desligamento | Estado do túnel, processo, Pod e cobrança/armazenamento lidos novamente | Parada de GPU não remove custo do volume persistente |

Falha conhecida é `BLOCKED`; sem readback suficiente, `UNCERTAIN`. A avaliação
científica formal permanece `not_run` até outro contrato e outra execução.
