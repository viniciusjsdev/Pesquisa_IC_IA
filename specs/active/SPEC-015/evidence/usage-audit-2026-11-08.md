# Auditoria de prontidão para uso · SPEC-015

Data: 08/11/2026. Auditoria solicitada após implementação e execução real pela Bancada. Inspeção independente do código atual, testes locais e leitura do trace hospedado; nenhuma implementação/correção, inferência nova, escrita remota, alteração de banco de pesquisa ou commit/push foi realizada por esta auditoria. Este relatório não substitui retroativamente os pareceres de migração anteriores nem marca a SPEC como concluída novamente.

## Parecer

O cenário B funciona para uso supervisionado no recorte piloto de 12 fontes aprovadas. A execução real observada passou por industrial e financeiro; não prova todas as perguntas, todas as fontes, outros provedores reais ou produção sob carga. Não aprovo monitoramento integral como confiável sem corrigir os dois achados P2 abaixo. A continua com defeito funcional conhecido, explicitamente fora do escopo da migração. Validação científica permanece separada e sem score.

## Achados reproduzidos

### AUD-01 · P2 · Erro da execução não é enviado no campo de erro da raiz

`inference_api/src/inference_api/observability/service.py:102–106` encerra a raiz com `status=result['status']`, mas sem o argumento `error`. Em `observability/langsmith_sink.py:19–25`, status é enviado em `extra.metadata`, enquanto o campo próprio `error` recebe null. Metadata não substitui o campo de erro do span no contrato LangSmith.

Reprodução local sem rede: executar o grafo A com transporte de modelo que lança TimeoutError e sink em memória. Resultado local: `contract_error`, `final_state.error=provider_timeout`; filho LLM registra `provider_timeout`, raiz registra `error=null`. A falha está presente nos filhos/metadados, mas ausente do campo padronizado da raiz, prejudicando filtros, alertas e interpretação agregada. Não foi criada uma execução remota com erro para demonstrar sua aparência visual.

Correção proposta: mapear erro técnico final para `error` sanitizado da raiz; distinguir insuficiência de evidência de falha técnica. Também explicitar a fronteira da raiz: hoje ela encerra dentro do grafo antes das verificações/persistência em `executions/service.py`, portanto não deve afirmar sucesso da operação completa da Bancada antes de sua conclusão. Testar timeout, contrato inválido, cancelamento e falha de consulta, preservando erros em filhos e sem novo dispatch.

Fonte primária: [formato de spans LangSmith](https://docs.langchain.com/langsmith/run-data-format), campos `error`, `status` e `extra` separados.

### AUD-02 · P2 · Estado/link do LangSmith pode ficar desatualizado no histórico

`observability/service.py:102–110` espera até dois segundos e devolve uma cópia do snapshot. `executions/service.py:191` persiste essa cópia. O worker continua enviando depois; não há reconciliação em `persistence/storage.py:330–343`, que apenas lê o JSON salvo. A URL é buscada uma única vez, imediatamente após enviar a raiz (`observability/langsmith_sink.py:27–36`); leitura sem resultado/timeout é ignorada e não há reconciliação posterior no produto.

Reprodução com sink atrasado: snapshot entregue à persistência permanece `pending`, zero enviados e sem URL; depois o mesmo Observer mostra `submitted`, dois eventos enviados e URL. O dicionário previamente entregue não muda. Aumentar o flush não resolve o caso geral nem substitui reconciliação.

Confirmação adicional no snapshot da execução real `892016c5-9c2c-4aae-a18c-e254416aad21`: estado `submitted`, 19 eventos, mas sem `url`/`trusted_origin`. O recibo posterior tem URL obtida manualmente por leitura. Assim, visualizar o trace no LangSmith não comprova que o botão de acesso ficará disponível no histórico da Bancada.

Correção proposta: persistir identificação remota/destino e estado de exportação separadamente do snapshot científico imutável; reconciliar estado e URL por leitura autorizada, sob demanda ou via worker, com limites. Nunca reenviar modelo ou consulta para recuperar observabilidade. Testar entrega após o flush, raiz ainda não indexada, reinício, erro definitivo e histórico antigo.

## Limitação funcional já conhecida

`agent_harness/policies/fixed_evidence.py:8–12` atribui domínio `dw` a todos os itens de A. `agents/evidence_reviewer.py` rejeita aprofundamento para domínio fora desse conjunto. A fixture diferencial `review_gap` mantém `invalid_review_gap`. Isso não é regressão introduzida pelo LangGraph, mas impede afirmar prontidão geral de A para perguntas com múltiplos domínios. Corrigir em contrato próprio e repetir a validação dos dois cenários antes da comparação científica.

## Verificações feitas nesta auditoria

- Backend: 114 testes executados, zero falhas/erros, oito skips opt-in. Logs em `inference_api/.local/spec015-usage-audit-20261108/backend-tests.log`; rede externa bloqueada no processo de testes e telemetria desligada. A suite inclui os 78 casos diferenciais congelados.
- Avaliação: 21 testes locais, zero falhas/erros/skips; rede bloqueada. Isso valida software, não resultados científicos.
- Frontend: seis arquivos, 21 testes aprovados; typecheck aprovado. Não foi feita nova execução interativa nem rebuild/deploy.
- `pip check`: nenhuma dependência quebrada. Não foi repetida instalação limpa nem build Docker nesta auditoria.
- Reprodução sintética dos dois achados: `inference_api/.local/spec015-usage-audit-20261108/probes.json`.
- Código do runtime inventariado no snapshot real coincide com os arquivos atuais comparados; nenhuma diferença encontrada nesse conjunto. O checkout ainda tem a implementação sem commit, sobre `e93b816ef6df667992f3bfd0f632aaf7875f78e2`.
- Inspecionados StateGraph, módulos de agentes/tools, projeções de contexto, guardas, contratos, saneamento, configuração, SDK instalado, persistência e UI. A fila limitada e a separação de falhas de envio preservam a inferência nos casos testados.
- Catálogo aprovado: sete fontes DW/linhagem, três industriais e duas financeiras. Isso não é acesso irrestrito a todo schema.
- Evidência anterior de integração UI/PostgreSQL descartável foi inspecionada, não repetida nem sobrescrita. O ensaio real B e seu snapshot foram inspecionados; adjudicação da resposta não foi realizada.

## Readback independente hospedado

Leitura sem escrita do trace `1ed70461-5966-5b99-9ea5-b889c3fb5193`, correspondente à execução real registrada: raiz `success`, 19 spans únicos, oito LLM, duas tools, pais íntegros; 21.066 tokens de entrada, 2.500 de saída e 23.566 totais. Contagens coincidem com recibo/snapshot local. Modelo registrado: `gpt-6-luna`, esforço solicitado baixo. Fontes consultadas: `paradas_maquinas_geradas` e `resultados_financeiros`.

Primeira leitura com timeout de dois segundos expirou. Uma segunda leitura, somente consulta e com timeout de dez segundos, confirmou os dados. Nenhum evento foi reenviado. Evidência sanitizada em `inference_api/.local/spec015-usage-audit-20261108/remote-readback.json`. Renderização do painel autenticado não foi inspecionada por esta auditoria; o usuário relatou ter visto a execução.

## Próximo aceite

Corrigir AUD-01 e AUD-02, acrescentar regressões que falhem no código atual e passem no corrigido, repetir testes pertinentes e verificar raiz com erro e exportação atrasada sem reenvio de inferência. Manter A explicitamente limitado até sua correção própria. Para uso com novas fontes/modelos/dados, verificar os contratos e autorizações correspondentes; o ensaio de um modelo no piloto não garante capacidade de todos os provedores. Não usar aprovação de engenharia como score científico.
