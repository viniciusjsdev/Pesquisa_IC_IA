# Validação de engenharia · SPEC-015 contrato 2

## Verificação hospedada posterior

Em 08/11/2026, após o usuário salvar a chave local, o teste hospedado expôs e corrigiu conflito de argumentos no construtor real do SDK e encerramento precoce do verificador com fila pendente. As tentativas anteriores foram preservadas e reconciliadas antes de novo envio. O par final foi aceito e lido de volta: A com 11 spans e B com 26, raízes únicas, pais íntegros e entradas/saídas LLM. Não houve inferência paga nem acesso a banco de pesquisa. Backend permanece off. Ver `hosted-readback.json` e aprovação independente `hosted-fix-review.json`.

A suite final tem 114 testes de backend (8 opt-in pulados), 18 métodos focados (78 casos diferenciais), 12 de observabilidade; integração UI/PostgreSQL descartável passou novamente em 7 runs. O flush normal continua limitado a 2 segundos, sem retry. Apenas o verificador dedicado mantém seu processo vivo por até 20 segundos adicionais para entregar a fila. A renderização na sessão autenticada do usuário não foi inspecionada. O relatório inicial abaixo preserva o estado anterior à configuração da chave.

Data: 08/11/2026. Baseline Git: `e93b816ef6df667992f3bfd0f632aaf7875f78e2`. Sem commit/push desta implementação. O checkout já continha cinco documentos modificados e a SPEC não rastreada; esse material foi preservado e atualizado para refletir a execução autorizada nesta sessão. O modelo executor efetivamente exposto à sessão não informa identificador exato; nenhum alias legado foi invocado nem outro chat de implementação criado.

## Resultado observado

A fachada ativa executa um StateGraph real do LangGraph 1.2.20, com nós de agentes, projeção, tools e guardas. Reparos de saída e de plano são arestas explícitas. Há um módulo por componente e três especialistas sob o mesmo papel externo. O estado é serializável e isolado; clientes, cancelamento e observabilidade ficam no contexto de execução. O ModelService e os adaptadores foram preservados, acrescentando emissão opcional de eventos normalizados.

Os contratos A/B efetivos foram extraídos para JSON, incluindo as alterações antes produzidas em Python. Foram capturados 78 casos sintéticos do commit de referência em uma árvore temporária, antes de editar o motor. O teste diferencial confronta todos os resultados, planos e corpos HTTP exatos. Normaliza somente latência, identidade do código/framework e metadados novos de observabilidade; usa o mesmo UUID para conservar bytes de envelopes. Não ignora ordem, prompts, filtros, erros ou contadores.

As funções/classes dos serviços de consulta realocados têm ASTs idênticas às do baseline; somente imports e caminhos mudaram. A consulta SQL continua nos serviços de dados. Os wrappers antigos são aliases para o mesmo módulo, preservando consumidores e monkeypatches. O algoritmo anterior foi retirado, mantendo no engine somente os schemas/limites consumidos pelos adaptadores históricos. `agent_harness.run` aponta para `scenarios.run`.

LangSmith 0.14.17 foi resolvido em ambiente isolado e fixado no lock com hashes. A instalação limpa e os testes específicos passaram em `inference_api/.local/spec015-clean`. A instalação pelo mesmo lock foi aplicada ao ambiente local da API. Docker passou a instalar o lock; não foi construída nem executada infraestrutura Docker/remota nesta mudança.

## Critérios

| Critério | Evidência de engenharia |
|---|---|
| AC-001 | Grafo com agentes, ferramentas e arestas restritas; teste estrutural; nenhum loop de produção anterior |
| AC-002 | A sem banco/fingerprints com tracing ligado/desligado; B e tools de DW/linhagem/industrial/financeiro; suites de catálogo e consultas preservadas |
| AC-003 | Projeções exatas confrontadas com baseline; instâncias de modelo por run, contextvars e duas runs concorrentes sem IDs/contexto compartilhados |
| AC-004 | 78 casos diferenciais: A/B × três adaptadores × sucesso, JSON inválido, ausência de fonte, aprofundamento/no progress, defeito A, fonte/ação proibida, orçamento, cancelamento, timeout, reparo e erro terminal de consulta, referências inválidas |
| AC-005 | Reparos e recusas contabilizados; orçamento válido com mais transições que o limite default; erro de recursão artificial preserva chamadas já executadas; nenhum retry de provedor |
| AC-006 | Histórico/exportação/jobs existentes e integration v3/v7; identidade recursiva muda com módulo profundo; metadados opcionais/aditivos |
| AC-007 | Matriz A/B × OpenAI Responses/Groq Chat/Chat Completions com transporte falso |
| AC-008 | Sete runs via navegador → autenticação → jobs → grafo → PostgreSQL descartável → resposta/erro → histórico; cluster encerrado |
| AC-009 | Lock com hashes/instalação limpa, consumidores reconciliados, arquivo verificável, 155 arquivos protegidos conferidos e funções de consultas preservadas |
| AC-010 | Revisão independente inicial pediu correções; reavaliação final registrada separadamente. Não presumir aprovação pelo resultado deste relatório |
| AC-011 | Spans correlacionados, hierarquia, IDs sem duplicação, tokens conhecidos/ausentes, reasoning como subtipo; serialização real do SDK em sessão local falsa |
| AC-012 | Global flag não habilita envio; modos metadata/redacted; segredos aninhados, tokens opacos, JSON truncado, erros e objetos desconhecidos; teto por evento, fila/flush limitados, indisponibilidade sem nova inferência |
| AC-013 | Metadados aditivos na Bancada, URLs privadas validadas, estados de falha/parcial, runs antigas, paridade off/on; integração de falha do sink sem perder resposta |

## Validações e arquivo

`validation-results.json` contém os comandos canônicos, códigos de saída, duração e arquivos de log. Os gates automatizados VAL-001–008 e VAL-010 passaram. VAL-009 é a reconciliação deste relatório, `structural-validation.json`, `legacy-inventory.json`, instalação limpa e comparação com baseline. Os testes de banco dependentes de opt-in continuam pulados na suite geral; a integração específica usa cluster novo descartável e cobre autenticação, jobs, histórico e leitura de fixtures.

Trinta e seis métodos de testes do protocolo retirado foram arquivados, sem alterar suas expectativas antigas. Foram mantidos os testes independentes de filtros, catálogo, gates e transporte. O novo recorte adiciona 16 métodos específicos, incluindo o teste diferencial com 78 casos; a redução da contagem geral não representa testes aprovados automaticamente. Originais de 12 arquivos estão fora do checkout com SHA-256 verificado. A SPEC-013/014 e suas evidências não foram regeneradas.

Uma primeira inspeção independente apontou redaction de tokens opacos/JSON truncado, configuração inválida, hashes metadata e consumidores do motor antigo. Foram corrigidos e adicionados testes; as evidências de revisão conservam esse histórico. A revisão final precisa avaliar o estado corrigido e seus gates antes de marcar done.

## Painel e limites

O usuário autorizou usar o painel, mas não há login nem chave LangSmith disponíveis nesta sessão. A aba do serviço abriu na tela de login. A verificação hospedada não foi executada. `verify_spec015_langsmith.py --send-synthetic` prepara duas execuções inventadas A/B com modelos e dados simulados; exige configuração local explícita, grava recibo próprio e não toca bancos reais. Esse comando não integra os gates automáticos.

`observability-validation.json` contém medição local de overhead com modelo falso e sink em memória; não mede latência da rede hospedada nem qualidade de modelos. Exportação permanece off por padrão. Não houve chamada paga de modelo, envio de dados reais, RunPod, ngrok, migração de schema SQL, mudança em dados, gabaritos ou score científico. A falha conhecida de A permanece caracterizada e sem correção funcional nesta refatoração.
