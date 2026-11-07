# Contrato funcional — SPEC-014 v1

Estado: proposta pronta para implementação, 06/11/2026. Nomes de módulos abaixo são destinos de implementação; nenhum serviço novo está ativo por este documento.

## Fronteiras

`Bancada → API/jobs → harness → serviço de modelos → adaptador → endpoint`.
O resultado volta pelo adaptador, serviço e validador do contrato do papel antes da próxima etapa. Cada papel é uma chamada distinta; loops criam novas chamadas com IDs próprios, usando o mesmo perfil congelado.

No B há uma segunda fronteira independente: `Especialista → plano JSON → validação/orçamento → consulta somente leitura → resultado com origem → Revisor`. O endpoint de inferência nunca recebe credenciais dos bancos. No A essa fronteira não é injetada; validação também rejeita qualquer tentativa de usá-la.

`model_service/` terá contratos tipados, registro de perfis/capacidades, preflight, serviço e adaptadores. Reutilizar os parsers/transporte e recibos existentes, centralizando responsabilidades em vez de duplicar três implementações de orçamento. `models.py` pode manter uma fachada para consumidores enquanto a migração é feita; não manter motores antigos de execução ativos após aceite.

## Pedido da Bancada

Exemplos de novo corpo sem credenciais; demais campos existentes de autenticação, prompt e critérios continuam sob o contrato da API:

```json
{
  "execution_contract_version": 1,
  "scenario": "fixed_evidence",
  "model_profile_id": "candidate-configured",
  "question": "Quais evidências sustentam a comparação dos períodos?",
  "evidence_packet": {"id": "packet-001", "sha256": "hash-verificado-no-servidor"},
  "generation": {"temperature": 0, "output_token_limit": null},
  "limits": {"model_calls": 48, "query_attempts": 0, "investigation_rounds": 3}
}
```

No B, `scenario=data_access`, `evidence_packet=null`, `query_attempts=3` e `catalog_version` aponta para o recorte aprovado. A versão na fronteira JSON é inteiro positivo estrito, igual a `version` do catálogo aprovado; string, booleano e coerção implícita são rejeitados. Limites do cliente podem apenas reduzir o perfil autorizado; nunca ampliar. Limites efetivos, inclusive tempo e corpo da requisição, são congelados no snapshot antes da primeira chamada. Valores de 48/3/3 são o perfil inicial desta migração, não recomendação universal nem aprovação de custo.

O servidor determina `allowed_actions`: A=`analyze_packet`; B=`query_source`. Rejeitar corpo misto/contraditório, IDs desconhecidos, hash divergente e parâmetros não suportados. Não inferir cenário a partir da pergunta. O usuário escolhe o tratamento; os agentes o recebem explicitamente em cada envelope.

## Papéis, contexto e transições

Todos recebem: `contract_version`, `run_id`, `call_id`, `role`, `scenario`, `round`, `model_profile_id`, pergunta literal, política de ações e saldo atualizado. Conteúdo de dados e outputs de agentes é tratado como dado, nunca como instrução para ampliar permissões. Os prompts estáticos e contratos são versionados.

| Papel | A: contexto e responsabilidade | B: contexto e responsabilidade | Saída/transição |
|---|---|---|---|
| Analista da Pergunta | Pergunta + índice do pacote; extrair necessidades | Pergunta + índice dos domínios habilitados | Necessidades/ambiguidade → Selecionador; não tratável → Redator com lacuna |
| Selecionador de Fontes | Índice de evidências do pacote, necessidades e lacunas; selecionar trecho/domínio recebido | Índice aprovado, evidências e tentativas; selecionar primeira/próxima fonte | `packet_source` ou `query_source` → projeção determinística → Especialista correspondente; sem fonte → Redator |
| Especialista do domínio | Dados e metadados da fonte selecionada no pacote; interpretar sem consultar | Contrato completo da fonte selecionada, filtros tipados, necessidade e feedback; montar plano | A: análise com refs → Revisor. B: plano → validação/execução → Revisor |
| Revisor das Evidências | Pergunta inteira, evidências aceitas, achados, lacunas, tentativas e saldo | Mesmo escopo, acrescido dos resultados/erros de consulta e cobertura | Suficiente → Redator; falta evidência → Selecionador se há ação útil e saldo; senão → Redator com ressalvas |
| Redator da Resposta | Evidências recebidas, achados e limites | Evidências consultadas, achados e limites | JSON com resposta, refs e ressalvas → histórico; sem pontuação automática |

Agentes não têm memória implícita entre chamadas. O harness monta contexto por projeção explícita de campos/referências, entrega dados selecionados integralmente dentro dos limites e registra os hashes/IDs do material usado. Não substitui evidências por resumo gerado pelo código. Se o contexto não couber, emitir erro de orçamento com recibo; não truncar silenciosamente. Especialista só recebe o domínio escolhido; Revisor e Redator recebem a evidência acumulada necessária à pergunta. Não pedir cadeia de pensamento privada: registrar decisões, justificativas curtas, achados e referências verificáveis.

Exemplo de payload do Especialista A, dentro do envelope comum:

```json
{
  "input": {
    "need": "comparar totais de dois períodos",
    "source": {"id":"packet:001:dw", "domain":"dw", "grain":"period"},
    "evidence": [{"id":"packet:001:e1", "period":"P1", "total":100}],
    "feedback": null
  },
  "output_schema_id": "specialist.fixed_evidence.v1"
}
```

Saída esperada:

```json
{"action":"analyze_packet","evidence_refs":["packet:001:e1"],"findings":["O pacote contém o total de P1."],"gaps":["O total de P2 não foi fornecido."]}
```

No B, preservar o plano tipado vigente da SPEC-013 e acrescentar o discriminador `action=query_source` na versão nova do envelope/contrato; não renomear campos do plano só para adaptar o provedor. O input contém o contrato completo da fonte selecionada, evidências e `feedback={rejected_plan,error_code,details,event_id,remaining_budget}` quando aplicável. Os JSONs existentes de Analista, Revisor e Redator recebem o cenário/política no envelope; o Selecionador distingue `selection_kind=packet_source|query_source`. O motor valida que as referências produzidas existem e pertencem ao run.

A revisão pode repetir uma análise de trecho do pacote, mas não repetir indefinidamente a mesma decisão sem progresso. Registrar chave `(role, source_id, need, evidence_hashes, feedback_hash)`; se repetida sem nova informação, fechar com lacuna. Limites de três rodadas investigativas e 48 chamadas incluem reparos. Em B, todas as tentativas de consulta, inclusive recusadas, contam no teto três. Reservar capacidade para Redator; se não houver, terminar como erro de orçamento, sem inventar resposta final.

## Serviço de modelos e capacidades

Perfil imutável por execução:

```json
{
  "id":"candidate-configured",
  "version":1,
  "provider_id":"deployment-local",
  "adapter_id":"chat_completions",
  "deployment_id":"endpoint-configured",
  "requested_model":"configured-model",
  "capabilities": {
    "json_schema":"prompt_validated",
    "streaming":true,
    "temperature":true,
    "reasoning_effort":false,
    "seed":false,
    "omit_output_limit":true
  }
}
```

Exemplo de forma, não afirmação das capacidades de um modelo existente. Perfis reais são derivados da configuração auditada e do adaptador, com hash, data e origem da declaração. Não aceitar capacidades arbitrárias vindas do navegador. `json_schema` admite `native_strict`, `json_object`, `prompt_validated`; nenhum deles dispensa validação local. Registrá-lo como condição experimental, porque pode mudar o comportamento. Não habilitar tool-calling nativo como requisito: os agentes retornam contratos JSON e o harness encaminha ações. APIs nativas de tool-calling futuras exigem equivalência documentada.

Interface interna conceitual: `generate(ModelRequest) -> ModelResult`.

Request: versão, IDs de run/call/papel, perfil resolvido, mensagens/contexto, schema e sua versão, parâmetros pedidos, política de timeout/saída/body, referência da autorização e destino aprovado. Nunca carregar gabaritos.

Result: `status=completed|error`, conteúdo textual original permitido, JSON parseado somente se válido, motivo bruto/normalizado de término, erro tipado, uso `input/output/reasoning/total` com `null` quando ausente, latência, requested/applied parameters, identidade efetiva, provider request ID quando disponível, recibo de bytes/hash do body efetivamente enviado. Não inventar zero tokens nem estimativa como consumo medido. Conteúdo sensível segue armazenamento local protegido existente; logs públicos sanitizados.

O serviço aplica preflight e monta a requisição com o adaptador; o orçamento de corpo é checado **depois da serialização completa e antes do transporte**, inclusive schema, prompts e framing. O snapshot inclui a versão/hash do adaptador, perfil/capacidades, modelo solicitado e resolvido quando verificável, endpoint lógico sem segredo, serving manifest/revisão de pesos/adaptador quando existente. Sem identidade verificável, resultado pode ser exploratório; não declarar equivalência científica.

OpenAI mantém protocolo e extração já existentes; Groq mantém seu transporte; compatível cobre o contrato do endpoint atual. Usar apenas os campos suportados; nunca descartar silenciosamente `temperature`, `seed`, `reasoning_effort` ou trocar nomes sem registrar a tradução. Mudança de host compatível exige configuração/autorizações e testes de conformidade, sem branch no engine. Protocolo distinto exige adaptador. RunPod aparece na configuração de implantação, não em enum de cenário ou decisões de agentes.

URL/credenciais são configuração confiável do backend. Usuário da Bancada seleciona perfil aprovado, não URL arbitrária. Preservar autenticação/TLS, bloqueio de redirects indevidos e verificação de sessão/proveniência do serving. Não fazer fallback para endpoint público quando self-hosted falhar. Poll de `/api/models` não dispara inferência paga. Expor `configured`, `capability_compatible`, `available|unavailable|unknown` separadamente, com motivo sanitizado.

## Erros e recuperação

| Evento | Responsável e retorno | Continuação |
|---|---|---|
| JSON estrutural inválido | Harness: erro com schema/path, tentativa e saldo | Até uma chamada de reparo pelo mesmo papel e modelo por saída inicial, contada no total; se repetir, terminal |
| Plano inválido corrigível | Backend: plano recusado + erro tipado + saldo | Mesmo Especialista; consome teto de tentativas; sem saldo → lacuna/encerramento registrado |
| Evidência insuficiente | Revisor: gaps + refs + sugestão de fonte/trecho | Selecionador dentro da política A/B e saldo |
| Fonte sem acesso ou ação proibida | Backend: autorização/política negada | Nunca reparar para contornar controle; erro explícito e sem nova consulta |
| Timeout, 429, conexão, recusa do provedor, stream interrompido | Adaptador normaliza erro e recibo | Terminal, sem retry automático e sem trocar modelo |
| Saída truncada, contexto ou corpo excessivo | Serviço: erro explícito, parâmetros e consumo conhecido | Não aceitar resposta parcial como JSON válido; terminal |
| Falha do banco | Serviço de consultas: origem sanitizada e erro | Registrar falha; não reenviar automaticamente; resposta parcial só se motor ainda tem evidência/saldo e não confundir com ausência de dados |

`retryable` do provedor é apenas diagnóstico, não autorização para retry. Reparação de JSON/plano é nova decisão registrada do harness, não repetição opaca da chamada HTTP. Cancellation dos jobs respeita o suporte do transporte; nunca prometer interrupção de cobrança já iniciada. Usuário vê estado final real e pode iniciar novo run com outro ID.

## Migração, histórico e comparação

Congelar e versionar o contrato novo; export não pode usar conversão que altere bytes ou hashes antigos. `dw_snapshot`, `dw_tools`, `agent_harness_pilot` são aceitos apenas por leitores de histórico. Novas submissões devolvem `legacy_execution_mode_retired` e instruem selecionar A/B; não mapear automaticamente. Scripts antigos de pesquisa/replay devem ser classificados por consumidor e preservados como históricos ou migrados explicitamente; nenhum replay pode iniciar consulta legada por acidente.

Registro de perfil identifica o modelo; políticas de A/B não ficam no perfil. UI recebe capacidades e modos disponíveis pelo backend e explica incompatibilidade. A mostra pacote/hash/cobertura e zero consultas; B mostra catálogo/escopo/fontes permitidas e limite de tentativas. Ambos mostram temperatura, política de saída e demais parâmetros apenas quando suportados, com valores aplicados no recibo. Retirar botão separado de piloto; metadado `purpose=engineering|research` não é cenário nem bypass de gates.

Comparação possui eixos separados: tratamento (A/B), protocolo/versões, condição de dados (pacote ou manifest de fontes anterior/posterior), candidato (provedor/modelo/pesos/adaptadores), parâmetros/capacidades e resultados. Não colocar IDs de run e contagens de outcome na chave de condição. Ausência de metadados → indeterminado; fontes alteradas durante B → não comparável. A usa hash do pacote validado sem abrir os bancos. Autorizações de transmissão, aprovações de catálogo e adjudicações humanas continuam específicas a conteúdo/destino/hashes e não migram por conveniência.

## Conclusão de engenharia

Uma matriz offline de 2 cenários × 3 adaptadores, mais integração navegador/API/jobs/persistência com transportes falsos explicitamente identificados, demonstra a engenharia local. Integração B deve usar banco isolado de teste com fixture identificada; A comprova ausência de acesso de pesquisa. Ensaios remotos autorizados complementam a evidência, mas não são substituídos por mocks nem exigidos para afirmar disponibilidade real universal. O aceite declara exatamente o que foi testado. Revisão humana de acerto científico acontece depois, por resposta e hash, antes de notas ou conclusões de pesquisa.
