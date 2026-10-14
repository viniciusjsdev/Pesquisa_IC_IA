---
id: SPEC-001
title: Orquestracao deterministica de agentes e evidencias para LLMs
status: done
contract_version: 1
---

# SPEC-001: Orquestracao deterministica de agentes e evidencias para LLMs

## Goal

Construir a primeira cadeia de agentes da inferência exploratória para perguntas
financeiras, industriais e integradas. Ela deve consultar fontes permitidas,
entregar um pacote de evidências versionado à LLM selecionada por requisição e
registrar a resposta e seus limites, sem usar o gold set científico.

## Context

`inference_api/` já possui duas consultas anuais e chama um alias vLLM, mas a
rota é escolhida manualmente por query ID e o snapshot ainda não descreve uma
cadeia de agentes. `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`
define orquestrador, serviços financeiro/industrial, montador de contexto,
modelo em teste e verificador. O usuário confirmou em 13/10/2026 que a primeira
versão seguirá esse desenho determinístico; não haverá uma LLM autônoma por
domínio. O harness formal permanece separado.

## Scope

- Criar contratos tipados e versionados para `QuestionRequest`, `RoutePlan`,
  `EvidenceItem`, `EvidenceBundle`, `ModelOutput`, `CheckResult` e `RunSnapshot`.
- Criar o **Orquestrador**: valida escopo explícito (`financeiro`, `industrial`
  ou `integrado`), período e opções; seleciona ferramentas da allowlist e
  registra a origem da escolha. Na primeira versão, o escopo é declarado pelo
  pesquisador ou por caso de teste, não inferido por LLM; o snapshot não o
  descreve como acerto de roteamento automático.
- Criar **Agente de Dados Financeiros** e **Agente de Dados Industriais** como
  serviços determinísticos: SQL parametrizado e somente leitura, timeout,
  limites de linhas, cálculos explícitos e proveniência. Reaproveitar as duas
  consultas anuais existentes; não abrir SQL livre nem fazer join sem vínculo.
- Criar **Montador de Evidências**: atribui IDs estáveis a itens, registra
  banco/tabela/campo, filtros, período, unidade, granularidade, valor, fórmula,
  qualidade e ressalva. A rota integrada pode reunir itens dos dois domínios
  no mesmo ano para investigar associação, sem atribuição causal.
- Criar **Agente de Resposta**: recebe somente pergunta, prompt versionado,
  bundle de evidências e alias selecionado; chama o cliente LLM uma vez. Não
  recebe conexão de banco, ferramenta SQL ou gold set. Preserva texto bruto,
  referências a IDs de evidência e informação efetivamente retornada pelo
  servidor de modelos.
- Criar **Verificador Exploratório** determinístico: confere schema, presença
  das evidências exigidas, IDs citados existentes e estado de chamada. Ele
  declara `not_checked` para verdade numérica/causalidade que não puder provar;
  nunca marca uma resposta como cientificamente validada.
- Persistir snapshot final imutável e erros por etapa, com estado distinto para
  falha de rota, consulta, evidência, modelo, resposta e verificação.

## Non-scope

- Criar agentes LLM especializados por domínio, classificador Jev, juiz LLM,
  ferramentas autônomas, geração de SQL pela LLM ou prompt com acesso ao banco.
- Construir novo DW, gold set, harness formal ou métricas do artigo.
- Alterar dados/splits/pesos/manifests/resultados de `FineTuning/`.
- Iniciar RunPod ou ngrok; SPEC-002 e SPEC-003 cuidam dessas fronteiras.

## Requirements

- REQ-001: Cada agente tem entrada, saída, falhas e responsabilidade explícitas;
  somente agentes de dados podem abrir conexões às fontes, e somente o agente
  de resposta pode chamar a LLM.
- REQ-002: A allowlist de ferramentas é definida no backend. `scope=integrado`
  executa as duas rotas permitidas com mesmo período; qualquer ferramenta ou
  parâmetro desconhecido falha antes de consultar dados.
- REQ-003: Os agentes de dados não consultam por conta própria outros bancos,
  não escrevem e não inferem vínculo causal entre registros de domínios.
- REQ-004: O bundle de evidências tem `schema_version`, IDs, unidade,
  granularidade, período, fonte, consulta parametrizada, resultado, limites e
  qualidade/ausência. O agente de resposta recebe exatamente o bundle gravado.
- REQ-005: Se dados obrigatórios faltarem ou a consulta falhar, o orquestrador
  registra `insufficient_evidence` ou erro específico sem chamar a LLM;
  resposta vazia ou inválida é preservada como falha, não fabricada.
- REQ-006: O modelo é escolhido por requisição e não altera estado global;
  snapshot registra alias, endpoint, base/revisão, adapter/run/hash quando
  disponíveis, parâmetros, prompt exato, rota, evidências, resposta e checks.
- REQ-007: O verificador não recebe gold set. IDs de evidência citados pela
  resposta devem existir no bundle; check parcial não recebe rótulo de validação
  científica. Feedback humano permanece registro separado.

## Business or domain rules

- BR-001: Soma das vendas disponíveis não é automaticamente receita contábil.
- BR-002: Soma de registros de operação pode duplicar etapas de produção.
- BR-003: Coincidência temporal entre produção/paradas e resultado financeiro
  permite investigar associação, não afirmar causalidade ou atribuir receita a
  máquina sem vínculo comprovado.
- BR-004: Casos exploratórios e benchmark formal têm estados e armazenamento de
  resultado distintos. Gabarito jamais entra no contexto da LLM.

## Decisions already made

- A topologia e a separação entre inferência exploratória e avaliação formal
  constam dos dois documentos de arquitetura nas referências.
- A cadeia determinística de dados e uma LLM redatora por execução foi
  confirmada pelo usuário; Jev e juiz LLM ficam opcionais para outra SPEC.
- `db_inference_app` registra estado da aplicação; bancos de origem são fontes
  de leitura, sem fallback para `localhost:5432`.

## Constraints

- Compatibilizar ou migrar explicitamente o contrato atual de `/api/runs`;
  snapshots existentes não podem ser reescritos silenciosamente.
- Usar o cliente/model catalog atual como fronteira de inferência, alinhando
  proveniência com SPEC-002 depois. Autoria declarada será substituída pela
  identidade verificada da SPEC-003; não duplicar implementação de auth aqui.
- Não copiar código da árvore legada de agentes retirada do checkout.
- Atualizar README e arquitetura na mesma mudança de código.

## Acceptance criteria

- AC-001: Testes mostram as três rotas (`financeiro`, `industrial`,
  `integrado`), rejeição de ferramenta/ano inválido e ausência de SQL livre.
- AC-002: Um caso integrado gera dois itens com proveniência distinta,
  mesmo período e aviso explícito de associação sem causalidade.
- AC-003: A LLM recebe só pergunta, prompt e bundle final; spy de teste prova
  que não recebeu senha, conexão, SQL executável pelo usuário ou gold set.
- AC-004: Erro de banco/ausência de evidência não chama LLM e grava estado
  explicável. Erro de modelo guarda evidência e resposta nula.
- AC-005: Dois runs simultâneos com aliases distintos mantêm seus próprios
  modelos e snapshots. IDs citados inexistentes produzem check falho sem
  reescrever a resposta.
- AC-006: Checks exploratórios aparecem como parciais/não verificados; nenhum
  teste ou UI os rotula como acurácia científica.

## Affected areas

- `inference_api/src/inference_api/` (orquestração, evidência, cliente, serviço,
  persistência), `inference_api/tests/`, `inference_api/README.md`, contratos HTTP
  e `docs/arquitetura_inferencia_compartilhada.md`.

## References

- `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`: papéis, regra de
  associação, gold set e limites do harness.
- `docs/arquitetura_inferencia_compartilhada.md`: topologia, snapshots e
  separação das frentes.
- `inference_api/README.md`: contrato HTTP e limites atuais.
- `inference_api/src/inference_api/evidence.py`: consultas iniciais.
- `inference_api/src/inference_api/service.py`: execução e snapshot atuais.
- `BancoModeloUse/README.md`: fontes e limitações da carga existente.

## Skills

- Nenhum skill de implementação específico; executar a SPEC como contrato
  próprio e seguir `AGENTS.md` da raiz.

## Validation requirements

- VAL-001: `git diff --check` na raiz do projeto.
- VAL-002: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v`
  com casos para limites, rotas, erros e concorrência.
- VAL-003: Teste de integração local somente leitura nos dois bancos já
  carregados; registrar que é leitura de carga existente, não nova importação.
- VAL-004: Inspeção dos payloads enviados à LLM para ausência de gold set,
  segredo, conexão e SQL escolhido pelo navegador.

## Review requirements

Revisão independente Sol/high da fronteira entre dados, LLM e avaliação,
incluindo ausência de causalidade inventada e de vazamento do gold set.

## Execution and runtime

Executar conforme `SPEC.execution.json`. A thread desta frente é a primeira
autorizada a escrever no checkout compartilhado; as demais aguardam a
reconciliação do seu resultado antes de editar.
