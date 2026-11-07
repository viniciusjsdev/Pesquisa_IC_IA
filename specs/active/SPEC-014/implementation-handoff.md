# Handoff — implementar SPEC-014 em outra thread

Esta entrega contém desenho e documentação; implementação não iniciada. O usuário pediu que outra thread aplique a SPEC. Não criar thread nem executar automaticamente a partir deste arquivo.

**Acionamento explícito em 06/11/2026:** após a correção visual, o usuário pediu “Invoca a outra Thread passando o contexto pra ela”. Isso autoriza o despacho manual para implementação desta SPEC. `automatic_handoff=false` continua correto: a criação decorre desse pedido, não de automação. A thread de origem encerra suas edições antes do despacho; a implementadora passa a ser a única escritora desta frente. Ver [conferência de alinhamento](evidence/diagram-spec-alignment-2026-11-06.md).

## Prompt de partida

> Implemente `specs/active/SPEC-014/SPEC.md` e seu `SPEC.execution.json`, lendo primeiro AGENTS.md, README.md, inference_api/README.md e docs/arquitetura_inferencia_compartilhada.md. A arquitetura já está resolvida em architecture-contract.md e no diagrama da página rC3Onoxkcgc0oOyFh0Ck. Preserve o checkout compartilhado, a SPEC-013 done e evidências históricas. Faça os dois cenários com agentes e o serviço comum de modelos; retire caminhos antigos de novas execuções sem perder leitura histórica. Execute testes locais e auditoria independente; não envie dados a provedores ou provisione infraestrutura fora da autorização vigente. Retorne evidência por AC, limitações e diff; não atribua nota científica.

## Sequência de implementação

1. **M1 — baseline e contratos:** registrar HEAD/status/hash dos arquivos tocados antes de editar; comparar com a baseline desta SPEC. Inspecionar service/models/jobs, engine, adapters existentes e consumidores da UI/CLI. Criar schemas discriminados A/B e contratos do serviço. Versionar entrada/saída/snapshot/runtime conforme seu formato vigente; não reutilizar versão antiga com semântica nova.
2. **M2 — serviço de modelos:** extrair/adaptar transportes atuais para `model_service/`; registry/config, preflight, request/response/errors, capacidades, identidade e recibos. Conformidade com transporte fake antes de qualquer integração externa. Migrar consumidores de `models.py` sem perder streaming, proveniência, sessão e orçamento do body completo.
3. **M3 — motor A/B:** políticas explícitas, contexto por papel, Especialista analisando pacote ou montando consulta, loops e erros. Preservar B validado pela SPEC-013; bloquear acesso de pesquisa no A inclusive metadados/fingerprint. Remover bifurcação por provedor de `engine` e papéis. Adaptar avaliação/exportação para reconhecer cenários novos sem pontuar.
4. **M4 — Bancada e migração:** duas opções, perfil independente, configuração por capacidade, trajetórias A/B, erros, histórico legado. API/jobs rejeitam criação em modo antigo. Inventariar referências e consumidores antes de retirar caminhos comprovadamente sem uso; preservar replay histórico somente leitura e materiais protegidos. Atualizar documentação e diagrama se detalhes executáveis exigirem correção antes do código correspondente.
5. **M5 — validação e revisão:** matriz 2×3 com transportes fake; integração local pela UI com autenticação/jobs/histórico e DB isolado fixture; testes de erros e regressão. Revisor independente verifica diff, baseline e resultados. Registrar completion/review/lifecycle nos schemas do projeto. `done` só com todos os AC atendidos e parecer aprovado; validação científica posterior continua fora deste aceite.

## Comandos de validação

Rodar a partir da raiz, usando interpretador disponível confirmado. Não instalar infraestrutura ou abrir provedores para fazer os testes offline.

```powershell
# VAL-001 — contrato de planejamento (esta entrega)
inference_api/.venv/Scripts/python.exe C:/Users/vinic/.codex/skills/project-spec-architect/scripts/validate_spec.py specs/active/SPEC-014/SPEC.md specs/active/SPEC-014/SPEC.execution.json --project-root . --require-ready

# VAL-002 e VAL-006 — regressão e testes novos incorporados às suites
$env:PYTHONPATH = 'inference_api/src;.'
inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -p 'test_*.py'
inference_api/.venv/Scripts/python.exe -m unittest discover -s model_evaluation/tests -p 'test_*.py'

# VAL-003/007/008/009 — na pasta inference_api/frontend, Node/npm do projeto
npm run test -- --run
npm run typecheck
npm run lint
npm run build
```

Para VAL-001 depois de iniciar implementação, retirar `--require-ready` ao validar estados posteriores. Se npm não estiver no PATH, usar a instalação local já configurada e registrar o executável exato; não trocar versões de dependências inadvertidamente. Reconciliar skips: testes necessários ao aceite A/B não podem ser omitidos alegando que a regressão passou.

**VAL-004:** criar teste de integração repetível nos testes da frente e relatório `evidence/local-matrix.md`: A/B × OpenAI/Groq/compatível com servidor fake local, corpo serializado verificado e respostas declaradas sintéticas. Mais teste navegador das duas opções, acompanhamento, reabertura e erro. B faz três leituras em DB isolado fixture; registrar identidade/estado dessa fixture, sem tocar cluster original. Teste A falha deliberadamente se qualquer função de pesquisa/manifest de fontes for chamada.

**VAL-005:** `evidence/migration-audit.md` enumera cada antigo caminho, consumidores pesquisados, ação tomada e teste que conserva o comportamento exigido. Preservar funções de autenticação, orçamento, jobs/idempotência, export e comparação. Atualizar inventário do runtime e verificar que novos módulos/schemas entram no hash. Sem alterações em dados/pesos/gabaritos/recibos antigos.

## Matriz mínima adicional

| Área | Evidência obrigatória |
|---|---|
| API | A sem pacote rejeitado; B com pacote contraditório rejeitado; modo antigo rejeitado; URL arbitrária não aceita; perfil indisponível/capacidade inválida sem chamada |
| Contexto | JSON por papel; ausência de gold; referência inventada rejeitada; pergunta original preservada; dados tratados como dados; overflow sem truncamento silencioso |
| Agentes A | Pacote suficiente, insuficiente, fonte ausente, repetição sem progresso, tentativa de query rejeitada |
| Agentes B | DW/industrial/financeiro; plano recusado/correção; teto contando recusas; insuficiência/encerramento com lacuna |
| Adaptadores | Sucesso, strict/prompt-validated, usage ausente, término truncado, recusa, 429, timeout, stream interrompido; zero fallback e zero retry de transporte |
| Recibos | Body exato após serialização, destino/identidade/parâmetros/hash; erro antes e depois do envio distinguíveis; segredo redigido |
| Persistência | Reabertura, export legado e novo, job idempotente, critérios humanos ligados ao hash exato, condição científica indeterminada quando falta proveniência |
| UI | Somente A/B; label sem siglas confusas; sem piloto separado; cenário A sem eventos de query; campos dirigidos por capacidade |

## Evidência e limites

Não reutilizar saída da SPEC-013 como prova de execução da SPEC-014. Baseline e regressão anterior ajudam a detectar perda, não substituem novos testes. Não marcar perfil remoto como validado apenas porque transporte fake passou. Descrever explicitamente evidência offline/local/remota por adaptador e condições ainda não verificadas.

A mudança resolve engenharia e normalização; ela não promete respostas iguais entre provedores. Modelo, quantização, template, schema nativo e parâmetros podem alterar qualidade e precisam aparecer no snapshot. O revisor técnico não aprova gabaritos nem respostas de pesquisa.
