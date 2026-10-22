---
id: SPEC-010
title: Bancada com Groq gratuito e fluxo de teste confiavel
status: done
contract_version: 1
---

# SPEC-010: Bancada com Groq gratuito e fluxo de teste confiável

## Goal

Permitir testar a Bancada autenticada com um modelo hospedado no plano gratuito
da Groq, sem iniciar RunPod, e corrigir as falhas de sessão e apresentação de
erros observadas no replay de 17/10/2026. Um run da Groq deve ser identificável
como tal; não representa uma geração dos adapters Qwen nem avaliação científica.

## Context

- Em `bf238ec` mais alterações locais sem commit, a Bancada tem jobs
  persistidos e streaming SSE. O [replay na L4](../../../runpod/serving/evidence/2026-10-17-streaming-bancada-l4.md)
  confirmou transporte e retomada do mesmo job após novo login, mas o refresh
  perdeu a sessão do navegador e o run com erro exibiu identidade incompleta.
- `inference_api/src/inference_api/serving_catalog.py` deriva os sete aliases
  do manifesto RunPod. `models.py` exige cabeçalhos de sessão e recibo
  próprios desse gateway; trocar apenas URL e chave não integra a Groq.
- A [API Groq](https://console.groq.com/docs/openai) usa Chat Completions com
  compatibilidade parcial com OpenAI. [Tool calling local](https://console.groq.com/docs/tool-use/local-tool-calling)
  deixa a execução das consultas autorizadas na aplicação. O
  [plano gratuito](https://console.groq.com/docs/rate-limits) impõe limites por
  conta e devolve 429 quando excedidos. Modelo e limites devem ser conferidos
  na conta no momento do ensaio; não são garantia permanente.
- [LoRA na Groq](https://console.groq.com/docs/lora) é Enterprise e não serve
  os seis adapters Qwen2.5 deste repositório no plano gratuito.

## Scope

- Acrescentar um provedor Groq explícito à Bancada, sem remover ou degradar o
  caminho RunPod. Configurar no servidor uma chave `GROQ_API_KEY` e um ID
  `GROQ_MODEL` disponível no plano gratuito da conta. O navegador não recebe
  a chave nem escolhe livremente endpoint ou modelo não configurado.
- Adaptar catálogo, chamada de chat, SSE, uso de tokens, tool calling local,
  jobs e snapshots para esse provedor. Preservar os contratos de tools da
  SPEC-009: a LLM escolhe uma consulta da allowlist; o backend a valida e a
  executa, sem escolher rota em nome da LLM.
- Recuperar a sessão autenticada após refresh na mesma origem, preservando
  revogação no logout, expiração e o uso de bearer por clientes não navegador.
  O transporte de credencial do navegador deve ser protegido contra acesso
  por JavaScript e requisições entre origens; a revisão independente examina
  especialmente cookie, CSRF, proxy HTTPS e localhost.
- Mostrar identidade/proveniência conhecida mesmo quando a geração termina
  em erro. Distinguir falha de provedor, limite 429, resposta incompleta,
  falha de tool e falta de evidência. Nunca converter saída truncada ou
  inválida em `answered_unverified` para esconder um erro.
- Executar a validação real da Groq apenas com pergunta, pacote e/ou DW de
  fixture sintéticos, depois de a chave ser configurada localmente pelo
  usuário. Registrar recibo sanitizado do ensaio e limites observados.

## Non-scope

- RunPod, ngrok, Terraform, volume, GPU ou mudança em pesos/adapters.
- Enviar à Groq DW real, pacotes privados reais, segredos, resultados brutos
  ou dados de pesquisa sem autorização específica futura. Não abrir plano
  pago nem habilitar faturamento para concluir esta SPEC.
- Corrigir a repetição do FT-FinQA, equiparar o modelo Groq ao Qwen2.5 ou
  atribuir pontuação científica a runs exploratórios.
- Alterar o protocolo oficial de treino/avaliação de `FineTuning/`.

## Requirements

- REQ-001: O seletor e a API distinguem provedor `groq` e modelo configurado
  dos sete aliases `runpod`. Sem chave/modelo configurado, Groq aparece
  indisponível com motivo claro; os aliases RunPod continuam indisponíveis
  quando não há sessão atestada. Nenhum fallback silencioso entre provedores.
- REQ-002: A chave fica somente no processo backend, nunca em bundle,
  snapshot, resposta HTTP, log ou Git. URL de produção fixa na origem oficial
  HTTPS da Groq; endpoint de teste injetável somente no harness local.
- REQ-003: O cliente Groq preserva streaming ou entrega a resposta ao job
  persistido sem timeout do navegador, reconstrói conteúdo/tool calls/uso e
  exige motivo de término válido. Suporta tool calling local com os limites
  atuais da SPEC-009; não habilita tools remotas ou SQL livre.
- REQ-004: Erros HTTP 400/401/429/5xx, timeout, stream incompleto, limite de
  contexto e tool inválida têm estados/mensagens distintos e guardam somente
  os metadados seguros necessários. `Retry-After` de 429 é mostrado quando
  existir; não há reenvio automático de uma geração com resultado incerto.
- REQ-005: Novos snapshots usam versão de schema explícita, `provider`, ID
  efetivo do modelo, parâmetros, origem da evidência, tokens/uso quando
  retornados e status. Campos de revisão Qwen, hash de adapter e recibo
  RunPod ficam ausentes/nulos para Groq; não se inventa proveniência.
  Snapshots v1-v3 continuam legíveis sem reescrita.
- REQ-006: Refresh conserva a sessão do mesmo pesquisador na mesma origem;
  logout revoga a sessão no servidor e impede recuperação posterior. Sessão
  expirada exige novo login. Proteções de cookie/CSRF não quebram o cliente
  bearer existente nem o teste via proxy HTTPS.
- REQ-007: O job conserva chave de idempotência e run após refresh. Uma
  resposta HTTP perdida exige reconciliação antes de outro POST. A UI mostra
  provedor, modelo e erro no histórico inclusive para `response_error`.
- REQ-008: O ensaio local usa fixture sintética e cobre pacote fixo e tools;
  o ensaio real Groq, quando houver chave gratuita, repete esses fluxos sem
  enviar a DW real. Atualizar `inference_api/README.md`, arquitetura e índice
  de SPECs na mesma mudança de código.

## Business or domain rules

- BR-001: Groq é provedor de teste funcional da plataforma, não um dos sete
  modelos treinados. Runs de provedores distintos não são agregados como
  mesma condição científica.
- BR-002: `answered_unverified` significa somente resposta exploratória
  concluída. Limite/erro de provedor ou resposta incompleta continuam falhas.
- BR-003: Uma tool executada só conta como escolha da LLM quando seu pedido
  apareceu no retorno do provedor e passou pela validação da allowlist.

## Decisions already made

- O usuário escolheu duas fases em chats separados: esta usa apenas a Groq
  gratuita para o fluxo da plataforma; a SPEC-011 trata dos modelos Qwen.
- Manter os sete aliases e recibos RunPod separados; `GROQ_MODEL` é uma
  configuração obrigatória para uso real, pois catálogo e cotas variam.
- Para o navegador, usar credencial inacessível a JavaScript e proteger
  operações mutáveis contra CSRF, mantendo o bearer de clientes existentes.
- Validar com dados sintéticos; liberação de dados reais é decisão externa.

## Constraints

- Checkout compartilhado e já modificado: inventariar diff antes de editar,
  preservar mudanças existentes e deixar a SPEC-011 sem escrita simultânea.
- Nunca imprimir a chave. A ativação de uma conta/plano Free e sua chave é
  externa ao repositório; a thread executora orienta configuração local sem
  pedir segredo no chat.
- Não executar RunPod, ngrok nem qualquer serviço faturável nesta fase.

## Acceptance criteria

- AC-001: No navegador, login, refresh, acompanhamento do mesmo job e logout
  funcionam; após logout/expiração a sessão não é recuperada. Testes incluem
  tentativa de requisição mutável de outra origem e bearer de cliente legado.
- AC-002: Com provedor Groq simulado, pacote sintético e tool sintética
  escolhida pela LLM produzem runs distintos, com modelo/uso/evidência
  corretos; nenhum pedido chega à RunPod ou à DW real.
- AC-003: 429 com `Retry-After`, resposta truncada e falha parcial de SSE
  aparecem como falhas específicas, sem reenvio ou sucesso falso; histórico
  e detalhe mostram a identidade conhecida em runs falhos.
- AC-004: Após configuração local de chave de conta Free, um ensaio real
  sanitizado confirma modelo, dois modos e job pelo navegador local. Se a
  chave não estiver disponível, registrar `blocked_external_key` e não
  declarar a integração real concluída; implementação/testes locais podem
  ser relatados separadamente.
- AC-005: Revisão independente confirma isolamento de segredos e dados,
  autenticação/CSRF, proveniência por provedor e compatibilidade histórica.

## Affected areas

- `inference_api/src/inference_api/` (auth, config, catálogo, cliente,
  service, jobs, server), frontend de sessão/Bancada, testes e README.
- `docs/arquitetura_inferencia_compartilhada.md`, `README.md` e
  `specs/README.md` para estado e fluxo. `runpod/serving/` é apenas referência.

## References

- `AGENTS.md`, `README.md`, `specs/README.md` e SPECs 003/008/009:
  proteções, identidade, Bancada e tools.
- `inference_api/README.md`, `docs/arquitetura_inferencia_compartilhada.md`,
  código de auth/sessão, catálogo, models, service e jobs: contrato atual.
- `runpod/serving/evidence/2026-10-17-streaming-bancada-l4.md`:
  erro de refresh e proveniência observados.
- Documentação oficial Groq: [compatibilidade](https://console.groq.com/docs/openai),
  [rate limits](https://console.groq.com/docs/rate-limits),
  [tool calling local](https://console.groq.com/docs/tool-use/local-tool-calling)
  e [LoRA](https://console.groq.com/docs/lora).

## Skills

Nenhuma skill especializada de implementação é obrigatória. A revisão
independente é obrigatória por envolver autenticação e provedor externo.

## Validation requirements

- VAL-001: `git diff --check`.
- VAL-002: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v`.
- VAL-003: `npm --prefix inference_api/frontend run typecheck`.
- VAL-004: `npm --prefix inference_api/frontend run lint`.
- VAL-005: `npm --prefix inference_api/frontend run test -- --run`.
- VAL-006: `npm --prefix inference_api/frontend run build`.
- VAL-007: Ensaio HTTP/browser local com Groq simulado, fixture sintética,
  refresh/logout/CSRF, idempotência, 429 e erro de SSE, sem RunPod/ngrok.
- VAL-008: Com chave Free configurada localmente, ensaio real Groq apenas
  com fixture sintética; registrar ID/modelo, horário, quota observada e
  recibo sanitizado sem chave nem payload sensível.
- VAL-009: Conferir diff, documentação, dados preservados e ausência da
  chave em código, logs, bundle, snapshots e evidências.

## Review requirements

Revisão independente crítica após implementação. Verificar sessão após refresh,
CSRF, isolamento de chave/dados, tool choice real, estados de falha,
proveniência sem identidade Qwen falsa e leitura de snapshots históricos.

## Execution and runtime

Ver `SPEC.execution.json`. A thread desta fase implementa somente este
contrato e registra conclusão local e ensaio Groq real separadamente. A fase
dos modelos permanece em outra thread, sem escrita concorrente.
