# SPEC-013 — proposta de decisões M0 para revisão

**Estado:** proposta, sem aprovação científica ou habilitação de consultas reais.
Foi derivada do [readback canônico](canonical-load-readback-2026-11-01.md),
do [inventário físico reproduzível](m0-physical-schema-2026-11-01.md),
do [contrato da DW](../../../../BancoModeloUse/dw/README.md) e dos requisitos
da [SPEC-013](../SPEC.md). A carga física existente não estabelece sozinha
quais perguntas ou relações são válidas para a pesquisa.

## DEC-001 — mapas por domínio

Um [mapa candidato em JSON](m0-semantic-map-candidate-2026-11-01.json)
detalha o primeiro recorte, marcado integralmente `enabled: false`. Seus
campos de tabelas tipadas e referências a tabelas DW foram comparados ao
inventário físico: `candidate_map_physical_refs_valid`. Isso valida a
existência física, não o significado ou autorização dos campos.
Uma [conferência posterior reproduzível](m0-catalog-review-2026-11-01.md)
ampliou o candidato para 12 fontes, verificou tipos físicos, FKs e outputs das
cinco consultas DW, e confirmou novamente o hash do inventário no cluster.
O recorte permanece desabilitado e DEC-001–005 continuam abertas.

- Manter o **inventário físico versionado** de todas as 35 tabelas DW e 56
  tabelas de origem separado da **allowlist semântica de consulta**. O agente
  especialista recebe primeiro o índice do domínio indicado e, após escolher
  IDs validados, somente o detalhe dessas tabelas, com campos, tipos, chaves,
  grão, cobertura, unidades e vínculos autorizados. Uma tabela existente pode
  estar documentada e ainda indisponível para consulta.
- O inventário físico mede 53.047/37.418/17.202 bytes por domínio, antes das
  descrições semânticas, superando o teto M1 de 16.384 bytes por entrada.
  **Desenho documentado na SPEC-013:** A2a recebe primeiro um índice semântico curto do próprio
  domínio e devolve IDs de tabelas candidatas; o backend valida esses IDs e
  injeta os schemas detalhados em uma segunda chamada A2a do **mesmo modelo**.
  A escolha de relevância permanece com o candidato. Índice, trecho, versões
  e limites entram no trace e são iguais entre modelos. A política de conteúdo
  e os limites continuam sem aprovação em DEC-001/002; o motor M1 sintético já
  executa essas duas chamadas, sem usar este mapa real.
- Primeira allowlist candidata: cinco consultas DW já existentes (`machine`,
  `product`, `financial`, `quality`, `material`), `contributors` e `trace` para
  a linhagem; no industrial, paradas originais, paradas geradas e operações;
  no financeiro, observações de `resultados_financeiros` e vendas. A estrutura
  foi conferida contra a carga V2, mas a interpretação e habilitação de cada
  coluna/filtro ainda exigem revisão.
- Não aprovar join entre resultado financeiro e máquina, produto, ordem ou
  parada por proximidade de data. `resultados_financeiros` tem 72 observações,
  não um total anual completo; 2019 e 2020 não têm observação nessa tabela.
  A fixture sintética de 2020 não descreve a carga real.
- Antes da implementação de M2, reconciliar o código/manifesto canônico do
  worktree separado com este checkout, aceitar V2 conscientemente no verificador
  e exportador, e registrar fingerprint, grão e relações de cada fonte habilitada.

## DEC-002 — orçamento do pipeline

O limite de M1 (16 chamadas, 2 consultas, 1 correção por papel, 16 KiB de entrada
e 8 KiB de resultado) é **apenas da fixture**. Uma pergunta que precise das
três fontes exige pelo menos três consultas, e 16 chamadas podem não deixar
espaço para correção. Candidata para medir no piloto: no máximo 3 consultas,
24 chamadas e uma correção explícita por papel/consulta, com limites de linhas,
bytes e tempo por tool. Esses 24 calls são hipótese de piloto, não orçamento
aprovado. Fixar números finais após medir índices, trechos e resultados de
casos representativos, incluindo as duas chamadas A2a propostas. Qualquer
payload acima do teto deve falhar
com estado explícito; não cortar linhas, IDs, unidades ou proveniência.

## DEC-003 — seleção e revisão dos casos

Criar uma matriz antes de escolher quantidades: domínio industrial, financeiro
e integrado × evidência suficiente, ausente e contraditória × tipo de cálculo
ou interpretação. Cada caso deve registrar a origem da pergunta, campos
necessários, consulta de referência reexecutável, fingerprint, regra de
inclusão/exclusão e limites de conclusão. A quantidade por estrato e as pessoas
responsáveis por preparar e revisar cada gabarito precisam de decisão dos
pesquisadores. Os exemplos existentes não se tornam casos oficiais por padrão.

## DEC-004 — acesso e transmissão

- Em M2, testar primeiro as tools em leitura local, com conta PostgreSQL
  restrita a `SELECT` nas fontes aprovadas, transação `READ ONLY`, timeout,
  allowlist de identificadores, limite de linhas/bytes e fingerprint da carga.
- Manter bloqueado por padrão o envio de qualquer detalhe industrial ou
  financeiro a Groq, OpenAI ou outro provedor. Um ensaio com fonte real exige
  autorização específica que identifique provedor, classes de dados e payload.
  A autorização anterior para a auditoria fictícia não cobre essa transmissão.
- Separar a autorização de consulta local da autorização de transmissão: uma
  leitura local para conferir contrato não habilita automaticamente inferência.

## DEC-005 — rubrica e comparação

Pontuar rota, evidência, cálculo e conclusão separadamente. Checks numéricos
devem usar consultas de referência e tolerâncias definidas por caso; revisão
humana decide interpretações aceitáveis e inferências vedadas. Caminhos
equivalentes com evidência válida podem obter o mesmo resultado. Sem gabarito
aprovado, registrar `not_scored`. Pesos agregados, número de repetições, política
para runs incompletos e critério de comparação entre modelos precisam de
aprovação antes de calcular ranking ou afirmar diferença de qualidade.

## Gate para `ready`

O documento propõe um recorte inicial e uma ordem de trabalho. Ainda faltam:
aprovação das fontes/colunas/relações, orçamento medido e fixado, seleção e
responsáveis dos casos, desenho de credenciais de leitura e autorização de
transmissão quando aplicável, rubrica e repetições. Até isso ocorrer, o
`SPEC.execution.json` permanece `design`.
