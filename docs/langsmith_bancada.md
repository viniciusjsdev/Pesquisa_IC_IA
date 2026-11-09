> **SPEC-015 contrato 3, engenharia local em 08/11/2026:** [correção de A e dois ajustes do LangSmith](../specs/active/SPEC-015/corrections-v3.md). Implementado e aprovado em revisão independente local. A multidomínio corrigido, raiz após persistência e reconciliação manual com receipt durável. [Parecer v3](../specs/active/SPEC-015/evidence/v3/review.json). [Ambiente local ativado e conferido em 08/11/2026](bancada_operacao.md), com A/B real e LangSmith. Sem score científico.

# Visualização da Bancada no LangSmith

## Contrato 3: estado atual e atualização manual

O cenário A usa o protocolo `fixed_evidence_v2`: índice local com domínios industrial/financeiro separados da origem DW, itens disponíveis/examinados e somente evidências analisadas na resposta. `product`/`material` passam por um especialista consolidado. Ausência, contradição ou limite encerram com resposta parcial e `insufficient_evidence`. Bytes, schema e hash do pacote original permanecem intactos. B conserva seus contratos e prompts.

A raiz da execução gerenciada fecha após a persistência local; erro técnico aparece em `error`, enquanto insuficiência é uma conclusão sem erro técnico. O recibo durável fica em `run_observability`, separado de `runs.snapshot`, e liga IDs distintos de harness/run/job/trace. Escritas de progresso são agrupadas num worker limitado por observer; falha do banco de recibos degrada somente o monitoramento.

A preparação do banco da aplicação é explícita e exige backup lógico:

```powershell
inference_api/.venv/Scripts/python.exe inference_api/run.py migrate-observability --pg-dump "C:/Program Files/PostgreSQL/15/bin/pg_dump.exe"
```

O comando gera automaticamente um backup datado em `inference_api/.local/observability-backup-*.dump`. A migração 004 é aditiva e idempotente, depende das versões 1–3 e recusa bancos diferentes de `db_inference_app`. Não foi aplicada ao banco de uso real nesta entrega. O rollback conserva tabelas e recibos; o runtime anterior simplesmente os ignora.

No detalhe/histórico, o proprietário pode clicar **Atualizar monitoramento**. A ação autenticada lê raiz/spans no destino original congelado, sem modelo, consulta de pesquisa ou reenvio de eventos. Limites: 128 spans, três requisições físicas, dez segundos totais, sem retry. A conferência compara IDs, pais e trace; `submitted` indica envio aceito e `remote_verified` indica árvore remota completa. Raiz ainda não indexada fica pendente; erro posterior conserva a última confirmação/link. Não há polling remoto automático.

GET da execução mantém o snapshot original e acrescenta o campo irmão `observability_current`; o POST de reconciliação não aceita configuração de destino no corpo. Histórico sem recibo usa metadata antiga e informa que a atualização está indisponível. Coleta off continua sem novos envios, mas uma consulta manual a recibo existente pode usar a configuração confiável original. Mudança de projeto/região retorna `destination_unavailable`, sem tráfego.

Validação do contrato 3: `inference_api/scripts/verify_spec015_v3_local.py` usa UI real, HTTP local, PostgreSQL descartável e modelos/telemetria falsos. Evidências em `specs/active/SPEC-015/evidence/v3/`; os ensaios hospedados abaixo pertencem ao contrato anterior.

SPEC-015 contrato 2, implementação em 08/11/2026. O histórico da Bancada continua sendo o registro oficial. Após configuração local da chave, o envio hospedado sintético foi confirmado por leitura da API: A com 11 spans e B com 26, raízes, pais e entradas/saídas LLM presentes. Evidências em `specs/active/SPEC-015/evidence/hosted-synthetic-check.json` e `hosted-readback.json`. A renderização visual na sessão autenticada do usuário não foi inspecionada pelo agente. A autorização inicial cobria somente fixtures; o ensaio real posterior abaixo recebeu autorização própria na sessão.

## Ensaio real B pela Bancada em 08/11/2026

Após pedido explícito do usuário para testar B com modelo real e acompanhar os agentes no LangSmith, os quatro bancos foram verificados em leitura e o servidor local foi reiniciado com o código atual. O usuário fez login e submeteu a pergunta pela Bancada. A execução `892016c5-9c2c-4aae-a18c-e254416aad21` terminou `answered_unverified`, com oito chamadas OpenAI `gpt-6-luna`, esforço solicitado `low` e duas consultas: `paradas_maquinas_geradas` pelo especialista industrial e `resultados_financeiros` pelo financeiro. O Revisor pediu aprofundamento após a primeira consulta e declarou suficiência após a segunda.

O readback do LangSmith confirmou 19 spans, uma raiz, oito chamadas LLM e duas tools com pais íntegros, no projeto `pesquisa-ic-ia-real-engineering`. A UI enviou `output_token_limit=null`, sem teto solicitado de saída; isso difere dos 2.048 tokens sugeridos antes do envio manual. Uso registrado: 21.066 tokens de entrada, 2.500 de saída e 712 de raciocínio como subtipo da saída. Nenhum valor monetário foi estimado. Resposta sem adjudicação humana e sem score científico. Evidência sanitizada: [recibo do ensaio](../specs/active/SPEC-015/evidence/real-b-ui-2026-11-08.json); snapshot integral preservado em arquivo local ignorado. A configuração persistente permanece off; a observabilidade foi habilitada no processo local desta sessão autorizada.

A hierarquia exportada contém uma raiz por run, spans dos agentes, chamadas LLM filhas e ferramentas ligadas ao especialista que produziu o plano. Cada reparo é outra tentativa. Os IDs do SDK são UUIDs derivados da identidade local. O framework automático está desabilitado para evitar duplicação e envio por variáveis globais.

## Configuração local

Instale o ambiente reproduzível na raiz do checkout:

```powershell
inference_api/.venv/Scripts/python.exe -m pip install --require-hashes -r inference_api/requirements.lock
Copy-Item inference_api/observability.env.example inference_api/.local/observability.env
```

Edite o arquivo local, que é ignorado pelo Git. Preencha `LANGSMITH_API_KEY` no computador, sem colar a chave em chats, documentos ou evidências. Defina um projeto privado e a região correta. Para o primeiro teste sintético, mantenha `INFERENCE_OBSERVABILITY=off`: o comando dedicado abaixo habilita envio e modo `redacted` somente no próprio processo. A configuração para ativar o backend, quando o conteúdo das execuções estiver autorizado, é:

```dotenv
INFERENCE_OBSERVABILITY=langsmith
INFERENCE_OBSERVABILITY_CONTENT=redacted
INFERENCE_OBSERVABILITY_ENDPOINT=https://api.smith.langchain.com
INFERENCE_OBSERVABILITY_PROJECT=pesquisa-ic-ia-synthetic
```

`metadata` envia identidade, estados, tempos, contadores e hashes, sem conteúdo. `redacted` também envia cópias sanitizadas de mensagens, JSON, planos e resultados. Para enxergar entradas e saídas no painel, use `redacted` somente para o conjunto autorizado. Sanitização de segredos não torna dados empresariais públicos. O template começa em `off`, e `LANGSMITH_TRACING=true` ou uma chave isolada não ativam exportação. Configuração inválida desliga somente a telemetria e registra diagnóstico sanitizado.

O backend carrega `inference_api/.local/observability.env` sem sobrescrever variáveis já definidas. Reinicie o processo após mudar a configuração. No Compose, as mesmas variáveis devem estar disponíveis ao comando; não foram criados ou modificados recursos remotos.

## Verificação sintética no painel

Depois de configurar o acesso, este comando opta explicitamente pelo envio hospedado de duas fixtures inventadas, A e B. O modelo e as consultas continuam simulados e nenhum banco de pesquisa é aberto:

```powershell
inference_api/.venv/Scripts/python.exe inference_api/scripts/verify_spec015_langsmith.py --send-synthetic
```

O script grava um recibo próprio e recusa nova execução quando já existir recibo; inspecione a execução anterior antes de qualquer novo envio. Envio aceito não equivale a confirmação visual: abra o projeto privado e confira a hierarquia e as entradas/saídas. Não são criados compartilhamentos públicos. A Bancada exibe “Abrir no LangSmith” quando o SDK resolve a URL privada e ela passa pela validação do destino; sem URL confirmada, não inventa link.

O verificador dedicado mantém seu processo vivo por até 20 segundos adicionais para a entrega assíncrona terminar. Isso não repete eventos nem amplia o flush normal de 2 segundos de cada run. A consulta imediata da URL pode ainda não enxergar a raiz recém-gravada; o recibo final também admite reconciliação por leitura posterior do mesmo ID remoto.

Na primeira tentativa, uma chamada inválida ao construtor impediu qualquer exportação. Foi corrigida e recebeu teste usando o construtor real do SDK com transporte falso. Na segunda, A chegou completa e B parcial por encerramento do verificador; os registros foram preservados e lidos antes do novo par, que chegou completo. Os recibos das tentativas permanecem no diretório de evidências.

## Estados e limites

Os estados opcionais são `disabled`, `pending`, `submitted`, `partial` e `failed`. A resposta e o histórico permanecem disponíveis mesmo com falha de exportação. Runs antigas sem esses campos continuam legíveis. `submitted` indica aceite do envio, sem score científico nem garantia de visualização.

A fila de exportação tem no máximo 1.000 eventos por processo. Eventos são projetados e sanitizados antes de enfileirar, com teto de 64 KiB; excesso omite o conteúdo remoto sem alterar o registro local. Rede tem timeout de 2 segundos, sem retry; o flush espera no máximo 2 segundos. A cópia remota pode ficar incompleta. Tokens ausentes ficam desconhecidos; tokens de raciocínio são subtipo, sem soma duplicada. Não é estimado custo para modelos sem tarifação conhecida.

Fontes: [instrumentação explícita do SDK](https://docs.langchain.com/langsmith/annotate-code), [formato de traces LLM](https://docs.langchain.com/langsmith/log-llm-trace) e o [contrato local de observabilidade](../specs/active/SPEC-015/observability-contract.md).
