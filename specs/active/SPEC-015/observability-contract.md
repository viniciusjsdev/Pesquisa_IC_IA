> **Contrato 3 — desenho pendente de implementação:** [corrections-v3.md](corrections-v3.md) e [fluxo](corrections-v3.mmd) prevalecem para A, finalização da raiz e reconciliação. Descrições de preservação do defeito A e estado/link somente no snapshot abaixo pertencem ao contrato 2 e foram substituídas.

# LangSmith opcional · contrato 2 da SPEC-015

> Fechamento local em 08/11/2026: implementação autorizada e aprovada em `evidence/review.json`. O desenho abaixo foi preservado como contrato; envio hospedado sintético A/B confirmado posteriormente por readback da API (11/26 spans), com renderização na sessão do usuário não inspecionada. A autorização da sessão permite teste sintético no painel, sem envio de dados reais.

Desenho atualizado em 08/11/2026. Implementar a integração faz parte da SPEC; habilitá-la em produção ou enviar dados reais não faz parte da autorização atual. O chat de implementação permanece aguardando autorização. Este contrato complementa o grafo local antes de qualquer alteração de código.

## Objetivo e fronteira

Visualizar a execução, os agentes acionados, chamadas LLM, tools, entradas/saídas, tokens, duração e erros no LangSmith. O histórico local da Bancada continua sendo o registro oficial de engenharia e de futuras avaliações. LangSmith não decide rotas, não altera contexto, não faz novas chamadas LLM nem atribui score científico.

A integração é obrigatória como entrega de código e testes, mas seu uso é opcional e desligado por padrão. Não incluir Studio/Agent Server hospedado, avaliação automática, replay remoto, gerenciamento de prompts remoto ou dependência do LangSmith para iniciar a Bancada. Não trocar ModelService ou adaptadores por wrappers de provedores.

## Arquivos e interface

Adicionar `inference_api/src/inference_api/observability/` com `config.py`, `contracts.py`, `sanitize.py`, `service.py`, `langsmith_sink.py` e `noop.py`. `service.py` oferece uma interface comum de início/fim de execução e eventos com IDs/pais explícitos; `langsmith_sink.py` converte esses DTOs para o SDK. Injetar sink falso nos testes. Nenhum agente importa o SDK diretamente. Fixar a versão compatível do SDK no lock junto com LangGraph, após resolução isolada e testes; não deixar intervalo aberto no ambiente reproduzível.

O grafo recebe a observabilidade pelo contexto de execução, fora do estado enviado à LLM. O ModelService emite dados normalizados da chamada, nunca Request/headers/cliente/credenciais. Tools emitem plano e resultado sanitizados. A integração poderá usar as APIs de instrumentação explícita do SDK, mas terá apenas um responsável pela emissão de cada evento. Não somar tracing automático do LangGraph com emissão manual dos mesmos spans.

## Hierarquia e correlação

Uma raiz por execução da Bancada. Cada invocação de agente é um span filho; sua chamada de modelo é um filho do tipo LLM. Consulta é span tool ligado à execução e correlacionado ao agente/plano que a originou. Reparos são novas tentativas identificáveis, não substituem a chamada anterior.

DTO mínimo: versão, run_id local, event_id, parent_event_id, tipo, papel/nome legível, rodada, tentativa, status, início/fim/duração e metadados permitidos. IDs enviados ao SDK devem ser UUIDs válidos e estáveis derivados da identidade local por mapeamento determinístico; preservar IDs originais como metadados. Mesmo event_id não cria spans duplicados. Validar isolamento entre jobs e propagação de contexto no worker de execução.

Registrar cenário A/B, perfil/modelo/provedor e hashes de configuração, contratos, dados e runtime disponíveis localmente. Não coletar banco adicional para enriquecer telemetria. A deve continuar sem qualquer consulta ao banco, inclusive quando tracing estiver ligado.

Para LLM: mensagens realmente enviadas (cópia sanitizada), resposta bruta permitida, resultado da validação e consumo normalizado pelo ModelService. Informar `ls_provider`, `ls_model_name` e `usage_metadata` ao SDK. Ausência de consumo permanece desconhecida, não zero; não estimar tokens silenciosamente. Tokens de raciocínio são subtipo e não devem ser somados duas vezes. Custo exibido é estimativa apenas quando houver tarifação conhecida; não inventar preço para modelos próprios/compatíveis.

## Configuração e envio

Configuração exclusiva do backend: `INFERENCE_OBSERVABILITY=off|langsmith` (default `off`), `INFERENCE_OBSERVABILITY_CONTENT=metadata|redacted` (default `metadata`), `INFERENCE_OBSERVABILITY_ENDPOINT`, `INFERENCE_OBSERVABILITY_PROJECT` e segredo `LANGSMITH_API_KEY`. Endpoint e projeto são configuração confiável do operador, nunca campos arbitrários de requisição da Bancada. Credencial e variável global `LANGSMITH_TRACING` sozinhas não habilitam envio.

Aplicar a política do backend também ao tracing automático do LangGraph/SDK; teste com `LANGSMITH_TRACING=true` no ambiente deve provar zero tráfego quando configuração do projeto está off. Não instanciar um exportador ativo no modo off. Configuração inválida desativa somente observabilidade e produz diagnóstico sanitizado local.

Modo `metadata`: somente identidade, status, tempos, contadores e hashes permitidos. Modo `redacted`: inclui cópias sanitizadas de prompts, JSON de entrada/saída, planos, resultados e feedback de validação. Esses conteúdos podem conter dados de negócio; máscara de segredo não os torna automaticamente públicos. Até autorização posterior, toda validação usa dados sintéticos e sink/servidor local falso. Nenhum acesso à conta LangSmith ou envio hospedado é necessário para fechar a engenharia desta SPEC; verificação no painel real fica explicitamente pendente de habilitação, não pode ser alegada como realizada.

## Conteúdo e falhas

Projeção por allowlist antes de serializar/enfileirar: nunca exportar headers, chaves API, cookies, JWT, DSN, senhas, variáveis de ambiente, clientes ou gabaritos. Sanitizar entradas, saídas, exceções e metadados; usar fixtures com segredos em campos aninhados e mensagens de erro. Um objeto não reconhecido é omitido, não convertido por repr. Política atua em cópia e não modifica prompt, resposta, hash nem dados científicos locais.

Limitar evento exportado a 64 KiB UTF-8, indicando `content_omitted` e razão quando exceder; não cortar JSON produzindo conteúdo inválido. Essa limitação só afeta a cópia remota. Não remover conteúdo da trajetória local para caber na telemetria.

Fila em memória limitada a 1.000 eventos por processo; envio em worker separado, timeout de rede de 2 segundos, sem retry automático de telemetria nesta versão. Fila cheia, erro de sanitização ou serviço indisponível descartam somente a cópia remota e registram contagem/estado local. Encerramento admite flush de no máximo 2 segundos; desligamento abrupto pode perder telemetria, preservando os mecanismos locais existentes. Medir overhead; não afirmar latência idêntica ou entrega garantida.

Estado local de observabilidade: `disabled`, `pending`, `submitted`, `partial` ou `failed`. `submitted` significa aceite de envio, não revisão científica ou confirmação visual. Não converter erro de telemetria em provider_error/contract_error, não repetir inferência/consulta nem reabrir job. Manter esse estado em metadados aditivos do run/job, sem alterar digest dos prompts nem inventar eventos de agente.

## Bancada e compatibilidade

Exibir link opcional “Abrir no LangSmith” quando houver URL válida e exportação correspondente. A URL deve pertencer ao destino confiável configurado, nunca ser um link fornecido pela LLM; não publicar trace nem gerar link público. Exibir estado parcial/falha sem esconder resposta ou erro original. Runs antigas sem metadados não exibem ação quebrada. Metadados de observabilidade não entram nos envelopes enviados aos agentes.

Para comparação de engenharia, fixtures com tracing off/on devem conservar chamadas, dados, resposta, erros e budgets, normalizando somente novos metadados de observabilidade e medidas de tempo. Registrar modo/versão da instrumentação nas evidências de desempenho; custos e latência observados com tracing não são presumidos equivalentes aos sem tracing.

## Aceite e testes

`test_spec015_observability*.py` deve cobrir hierarquia/IDs e ausência de duplicação, reparos/erros, três adaptadores, tokens ausentes e reasoning sem duplicação, proteção de conteúdo, modo off com ambiente global ligado, duas runs concorrentes, fila cheia, timeout/serviço indisponível, flush limitado, zero reenvio de inferência, A sem banco e paridade off/on. Exercitar serialização real do SDK contra transporte local falso, não apenas um mock da própria interface. Documentar explicitamente o que não foi validado no painel hospedado.

Verificador local SPEC-015 deve incluir pelo menos uma run A e uma B com sink falso, mais uma falha de exportação que não impeça resposta/histórico. Testes frontend cobrem link e estados, incluindo runs antigas. Evidência em `evidence/observability-validation.json`, sem segredos, e relatório por critérios AC-011 a AC-013.

## Fontes técnicas

- [Instrumentação customizada](https://docs.langchain.com/langsmith/annotate-code): spans, contexto e controle de ativação. RunTree postado pode enviar independentemente do flag global; por isso a política deve ser aplicada antes do exportador.
- [Registro de LLM customizada](https://docs.langchain.com/langsmith/log-llm-trace): formato, provedor/modelo e contagem de tokens.
- [Controle de conteúdo](https://docs.langchain.com/langsmith/mask-inputs-outputs): esconder e transformar cópias antes do envio.
