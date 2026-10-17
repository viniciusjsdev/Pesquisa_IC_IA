---
id: SPEC-009
title: Alternancia explicita entre pacote fixo e tools da DW na Bancada
status: done
contract_version: 1
---

# SPEC-009: Alternancia explicita entre pacote fixo e tools da DW na Bancada

## Goal

Na aba **Bancada de testes**, executar o mesmo catalogo de modelos em dois modos
escolhidos explicitamente pelo pesquisador: (A) resposta a partir de um pacote
imutavel ja exportado da DW e (B) pesquisa na DW por chamadas de tools escolhidas
pela LLM. Registrar o modo e a evidencia efetivamente entregue em cada run, sem
chamar o fluxo deterministico atual de escolha autonoma de ferramentas.

## Context

- A [arquitetura cientifica](../../../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md)
  define os cenarios A e B e veda misturar suas pontuacoes. A DW v1 e suas cinco
  consultas fixas existem em `BancoModeloUse/dw/`; a SPEC-007 exporta pacotes
  candidatos com envelope e SHA-256. Nenhum pacote e caso cientifico aprovado.
- A API da SPEC-001 consulta diretamente `db_industrial` e `db_financeiro`; seu
  `route_plan` e escolhido pelo backend a partir do escopo declarado. A Bancada
  React da SPEC-008 apenas consome esse contrato. Logo, o seletor de escopo atual
  nao representa nenhum dos dois modos pedidos.
- O Compose da SPEC-008 tem uma instancia PostgreSQL isolada com copia opcional
  de tres bancos, sem `db_pesquisa_dw`; a imagem nao contem pacotes locais. O
  cluster Windows nao e alcancavel pelo loopback do container.
- A [documentacao oficial de vLLM](https://docs.vllm.ai/en/stable/features/tool_calling/)
  descreve `--enable-auto-tool-choice` e `--tool-call-parser hermes` para Qwen2.5.
  O serving local atual nao usa essas flags; nenhum adapter foi testado em
  tool calling real. Implementar o protocolo e testar com servidor simulado nao
  confirma que os pesos servidos retornarao chamadas validas na RunPod.

## Scope

- Mudar apenas o interior da aba Bancada no front. Preservar login, identidade,
  limite global de uma inferencia, prompts/criterios, feedback, historico e as
  quatro abas do BI.
- Criar seletor obrigatorio `Modo de evidencia` com **Pacote fixo da DW**
  (`dw_snapshot`) e **LLM consulta a DW por tools** (`dw_tools`). Nao escolher um
  modo por padrao silencioso nem inferi-lo do escopo. A tela mostra campos,
  disponibilidade e descricao propria para cada modo.
- Integrar a API aos pacotes gerados pela SPEC-007 e as consultas fixas da DW.
  Reusar a implementacao de SQL da DW, sem segunda copia divergente.
- Versionar o snapshot dos novos runs e mostrar modo, origem, versoes, hashes,
  chamadas/retornos ou pacote integral, resposta, falhas e verificacoes na
  Bancada. Runs antigos continuam legiveis, identificados como fluxo anterior.
- Preparar o serving local de Qwen2.5 para tool calling e acrescentar ensaio
  local com servidor simulado. Atualizar host e Docker para acesso restrito a
  `db_pesquisa_dw` e a pacotes exportados, sem copiar dados reais automaticamente.

## Non-scope

- Gold set, rubrica, score, classificacao de qualidade cientifica, estatistica
  entre repeticoes ou promocao de pacotes candidatos a casos oficiais.
- Criar/recarregar a DW Windows, copiar seus dados reais ao Docker nesta tarefa,
  implantar/ligar RunPod, abrir ngrok ou fazer inferencia paga.
- SQL livre, credenciais do banco entregues ao modelo, tools de escrita,
  modelos externos ou alteracao dos dados preservados do FineTuning.
- Atualizar os quatro paineis do BI ou usar `private/bi_snapshot.json` como
  evidencia de inferencia. Esse JSON e o retrato offline do BI, nao o pacote da DW.

## Requirements

- REQ-001: `POST /api/runs` exige `evidence_mode` igual a `dw_snapshot` ou
  `dw_tools` para novos runs. Rejeita modo ausente, desconhecido e parametros
  exclusivos do outro modo antes de chamar modelo ou banco. O front apresenta
  um estado inicial `Escolha um modo` e impede envio ate a escolha.
- REQ-002: Em `dw_snapshot`, listar somente pacotes do diretorio privado
  configurado pelo servidor por `GET /api/bench/evidence-packets`, protegido pela
  sessao. Selecionar por `case_id` **e** SHA-256; nunca aceitar caminho passado
  pelo cliente. Validar bytes canonicos, schema e checksum via
  `model_evaluation/export.py::verify_packet_bytes`, rejeitando arquivos
  adulterados, duplicados, links simbolicos, pacote acima do limite ou hash
  diferente. O servidor nao exporta nem recalcula pacote ao executar.
- REQ-003: Em `dw_snapshot`, usar exatamente a pergunta e o dominio do corpo
  do pacote selecionado; mostrar a pergunta como somente leitura na UI. O
  pesquisador pode editar prompt, criterios, alias e parametros, e essas
  variacoes ficam no snapshot. Registrar bytes/hash do pacote, fingerprint da
  fonte, versoes de schema/consulta e evidencia JSON exata enviada ao modelo.
  Ausencia de pacote deixa esse modo indisponivel com acao de preparacao
  documentada, sem fallback para a DW ao vivo.
- REQ-004: Em `dw_tools`, a pergunta e livre. O backend anuncia somente as
  cinco tools de leitura `machine`, `product`, `financial`, `quality`, `material`
  com os mesmos parametros da SPEC-007: `year` inteiro 2015..2026; `id`
  positivo obrigatorio exceto para `financial`, que o proibe. A LLM escolhe
  chamadas por `tool_choice: auto`; usar `parallel_tool_calls: false`. O
  backend valida cada resposta antes de executar a consulta fixa, em transacao
  somente leitura contra `db_pesquisa_dw`, sem aceitar SQL ou nome arbitrario.
- REQ-005: O loop de tools tem no maximo cinco chamadas aceitas e seis turnos
  de modelo, uma chamada por turno, no maximo 200 linhas e 16 KiB canonicos de
  retornos de tool acumulados. Ultrapassar limite, resposta malformada, tool
  desconhecida ou argumentos invalidos resulta em falha explicita registrada;
  nao truncar, executar parcialmente ou produzir resposta fingida. Um turno
  final sem tool e sem evidencia fica `insufficient_evidence`, nao resposta
  sustentada. Registrar request/response brutos, argumentos validados,
  resultado, erro, ordem e timestamps por passo. Esses limites sao operacionais
  para a Bancada exploratoria, nao protocolo cientifico aprovado.
- REQ-006: O modelo recebe somente contexto, descricoes das tools e resultados
  das consultas autorizadas. O resultado preserva formula, unidade, cobertura,
  grão e ressalva da DW. O prompt explicita ausencia de dados, associacao sem
  causalidade e que a tool financeira nao gera total anual. Falha de backend,
  parsing ou serving permanece distinta de falha de consulta e de falta de
  evidencia.
- REQ-007: Os dois modos usam o mesmo catalogo de alias, revisoes de prompt e
  criterios, identidade e reserva global. O novo contrato de run (`schema_version`
  incrementado) registra `evidence_mode`, `case_id`/hash no modo fixo ou catalogo
  e traco de tools no modo ao vivo, fingerprint/versionamento da DW quando
  disponivel, modelo efetivo, prompt, parametros, resposta bruta e checks
  exploratorios. Nao reescrever snapshots antigos; `RunDetail` rotula os
  anteriores como `Fluxo anterior: escopo e consultas do backend`.
- REQ-008: A comparacao visual destaca diferenca de modo, pergunta, pacote/hash,
  fingerprint da DW, catalogo/traco de tools, prompt, modelo e parametros.
  Sempre exibe que modos A e B respondem perguntas de avaliacao distintas;
  igualdade de insumos nao equivale a validade cientifica. Sem score.
- REQ-009: No host, aceitar somente o DW em `127.0.0.1:5544/db_pesquisa_dw`;
  em Docker, somente `db:5432/db_pesquisa_dw`. O acesso ao DW e read only em
  cada transacao. O Compose monta o diretorio de pacotes privados apenas para
  leitura, sem incluir pacotes na imagem. Estender a preparacao de copia logica
  para admitir o quarto banco **somente por comando explicito**, com recusa de
  destino ocupado, checks de hash/contagem/readback e fixture descartavel; nao
  executar a copia real nesta SPEC. Sem DW no volume, `dw_tools` informa
  indisponibilidade, sem consultar origens como fallback.
- REQ-010: Ajustar `runpod/serving/serving.py` com as flags de auto tool choice
  e parser Hermes para Qwen2.5, conservando a validacao de manifesto e aliases.
  A resposta de cada turno ainda deve conferir sessao/proveniencia do gateway;
  mudanca de sessao aborta o run. Registrar que o ensaio com pesos reais na
  RunPod depende de acionamento futuro e nao e substituido por mock.
- REQ-011: Inspecionar consumidores de `orchestrator.py`, `evidence.py` e do
  fluxo antigo de `POST /api/runs`. Migrar ou retirar codigo ativo que ficar
  sem uso, preservando apenas leitura dos snapshots historicos e artefatos
  cientificos. Atualizar READMEs, arquitetura e indice de SPECs na mesma
  mudanca; nao deixar o seletor de escopo antigo anunciado como modo tools.

## Business or domain rules

- BR-001: O pacote da SPEC-007 e candidato; modo `dw_snapshot` nao o promove
  automaticamente a caso validado. A DW v1 nao e gold set.
- BR-002: Uma escolha de consulta feita pelo backend a partir de escopo humano
  nunca e contada como escolha de tool pela LLM.
- BR-003: Comparar A e B apenas de forma estratificada e exploratoria; o
  gabarito nao entra no prompt, nas tools nem no JSON enviado ao modelo.
- BR-004: `no_observation` e ausencia de observacao, nao valor zero. Chaves de
  periodos distintos nao se consolidam por nome e associacao temporal nao
  estabelece causalidade.

## Decisions already made

- O usuario pediu alternancia explicita dentro da Bancada, entre a DW atual
  com tools escolhidas pelo modelo e snapshot ja preparado. A arquitetura
  cientifica de 16/10/2026 define os dois cenarios e seus limites.
- A primeira entrega e **interativa/exploratoria**. A avaliacao cientifica
  formal permanece em contrato separado, conforme `BancoModeloUse/docs/`.
- Os limites de REQ-005 sao guardrails operacionais versionados desta entrega;
  nao representam tolerancias, rubricas ou budget do futuro experimento formal.

## Constraints

- O checkout e compartilhado por threads: somente uma escreve por vez. O
  cluster Windows e dados/weights/resultados/artigos preservados nao sao
  modificados. Nao rodar RunPod, ngrok nem `terraform apply`.
- Nao copiar bancos reais nesta tarefa. Testes com PostgreSQL usam fixture
  descartavel; conexao somente leitura da carga existente e opcional, deve ser
  registrada como tal, e nao prova geracao real da LLM.
- Em caso de servico de modelo sem suporte a tool calling, falhar claramente
  em `dw_tools`; nunca simular escolha pelo backend. O modo fixo permanece
  independente desse suporte.

## Acceptance criteria

- AC-001: No browser autenticado, trocar de modo muda campos e explicacao;
  nenhuma execucao ocorre sem escolha. O historico identifica ambos e os runs
  antigos, sem alterar Visao integrada, Financeiro, Industrial ou Dados e metodo.
- AC-002: Um pacote exportado valido e selecionado por ID/hash e enviado
  inalterado ao servidor de modelo simulado. Hash incorreto, pacote adulterado,
  ausencia e arquivo indevido falham antes da geracao.
- AC-003: O modelo simulado solicita uma ou mais tools, recebe apenas resultados
  fixos da DW fixture e produz resposta. Trace/limites/erros ficam no snapshot;
  nenhum teste usa rota escolhida pelo backend para fingir tool choice.
- AC-004: O modo host e o Compose passam em testes com fixtures; Compose sem DW
  ou sem pacotes mostra estado honesto. Nenhuma copia de banco real, chamada
  RunPod ou abertura de ngrok e feita.
- AC-005: Contratos antigos seguem legiveis; codigo, testes e documentacao
  ativos nao descrevem a rota antiga como modo A ou B. Revisao independente
  confere seguranca da tool, isolamento do banco, proveniencia e UX.

## Affected areas

- `inference_api/frontend/src/features/bench/`, `inference_api/src/inference_api/`,
  `inference_api/tests/`, `inference_api/compose.yaml`, `inference_api/Dockerfile`,
  `inference_api/scripts/copy_logical_databases.py` e `inference_api/README.md`.
- `BancoModeloUse/dw/` e `model_evaluation/` apenas para compartilhar consultas
  e verificacao dos pacotes, preservando os contratos da SPEC-006/007.
- `runpod/serving/serving.py`, README de serving, docs de arquitetura e indices.

## References

- `AGENTS.md`, `README.md`, `specs/README.md`: orientacao e estados.
- `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`: cenarios A/B,
  comparabilidade, limites e decisoes cientificas ainda pendentes.
- `BancoModeloUse/dw/README.md`, `BancoModeloUse/dw/cli.py`: DW e SQL fixo.
- `model_evaluation/README.md`, `model_evaluation/export.py`,
  `model_evaluation/schemas/evidence_packet.schema.json`: pacote imutavel.
- `inference_api/README.md`, `docs/arquitetura_inferencia_compartilhada.md`,
  `inference_api/src/inference_api/service.py`, `config.py`, `models.py`,
  `server.py`, `inference_api/frontend/src/features/bench/BenchPage.tsx`,
  `RunDetail.tsx`, `benchService.ts`: contrato vigente a migrar.
- `runpod/serving/serving.py` e documentacao oficial de vLLM de tool calling:
  configuracao de Qwen2.5; suporte real dos adapters continua nao provado.

## Skills

- Nenhuma skill especializada de implementacao e obrigatoria: o contrato ja
  define a arquitetura Python/React e os limites operacionais. A revisao
  independente e obrigatoria pelo impacto no contrato e nas evidencias.

## Validation requirements

- VAL-001: `git diff --check`.
- VAL-002: `inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v`.
- VAL-003: `BancoModeloUse/.venv/Scripts/python.exe -m unittest discover -s model_evaluation/tests -v`.
- VAL-004: `npm --prefix inference_api/frontend run typecheck`.
- VAL-005: `npm --prefix inference_api/frontend run lint`.
- VAL-006: `npm --prefix inference_api/frontend run test -- --run`.
- VAL-007: `npm --prefix inference_api/frontend run build`.
- VAL-008: Testar HTTP autenticado e browser com servidor vLLM simulado nos
  dois modos, erros e comparacao; nao contatar endpoint real.
- VAL-009: Validar `docker compose config --quiet`, build e smoke isolado com
  fixture DW e pacotes de teste, sem copiar dados reais nem usar RunPod.
- VAL-010: Inspecionar diff e consumidores; conferir ausencia de fallback para
  origens e correspondencia entre codigo, READMEs e mapa do projeto.

## Review requirements

Revisao independente critica apos a implementacao. Conferir que a escolha de
tool veio da LLM, que banco/pacotes permanecem privados e read only, que
falhas/limites nao viram sucesso, que snapshots antigos nao mudaram e que a
Bancada nao confunde runs exploratorios com benchmark cientifico.

## Execution and runtime

Ver `SPEC.execution.json`. A thread dedicada implementa somente este contrato,
registra evidencias locais e para antes de qualquer RunPod, ngrok ou copia real.
