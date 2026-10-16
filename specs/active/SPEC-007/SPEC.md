---
id: SPEC-007
title: Pacotes fixos e rastreaveis de evidencia da DW
status: done
contract_version: 1
---

# SPEC-007: Pacotes fixos e rastreaveis de evidencia da DW

## Goal

Preparar, sem chamar LLM, pacotes imutaveis de evidencias para que modelos diferentes recebam os mesmos dados no cenario A da [arquitetura de avaliacao](../../../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md). O resultado e uma entrada reproduzivel para um harness futuro, sem criar gabarito ou pontuacao cientifica.

## Context

Em 14/10/2026, sobre `ad6edcb` mais mudancas locais sem commit, a SPEC-006 implementou `db_pesquisa_dw` com cinco consultas fixas (`machine`, `product`, `financial`, `quality`, `material`), `verify` e linhagem ate CSV/raw/public. A carga local foi verificada naquela etapa; a [revisao independente da SPEC-006](../SPEC-006/evidence/review.json) foi aprovada em 16/10/2026 apos correcoes de reconciliacao e drill-through. A API exploratoria da SPEC-001 le diretamente os dois bancos de origem, escolhe as duas tools anuais por escopo declarado e guarda bundle `schema_version: 2`; ela nao consulta a DW nem mede escolha autonoma de tools. A SPEC-001 foi aprovada em revisao independente em 14/10/2026, o que nao equivale a um benchmark cientifico.

Esta SPEC e o primeiro passo local do desenho de dois cenarios. O cenario B (modelo escolhe tools), a comparacao de respostas e o gold set pertencem a contratos posteriores. Pacotes exportados aqui sao candidatos a casos; nao sao casos cientificamente aprovados.

## Scope

- Criar uma frente local isolada `model_evaluation/` com schema e CLI `export.py` para receber um manifesto de casos sem gabarito e exportar um pacote JSON por `case_id`. A saida local padrao fica em `model_evaluation/.local/packets/`, ignorada pelo Git.
- Aceitar apenas as cinco consultas parametrizadas ja existentes em `BancoModeloUse/dw/cli.py`; cada item do manifesto declara `query`, `year` de 2015 a 2026 e `id` quando o recorte por entidade for necessario. Recusar nomes, filtros e campos desconhecidos antes de abrir conexao.
- Executar `verify` da carga existente antes da exportacao e registrar `schema_version`, fingerprint de origem, versao da consulta, caminho/versao do schema, filtros, grao, unidades, formulas, cobertura, linhas, interpretacao, tabelas de origem retornadas pela DW e resumo global de qualidade separado dos itens do caso.
- Gerar JSON canonico UTF-8 e SHA-256 do conteudo, com ordenacao definida de itens e linhas. Repetir o mesmo manifesto contra a mesma carga/versao deve produzir bytes identicos. Recusar sobrescrever pacote existente com hash diferente; gravar arquivos novos atomicamente. Limites iniciais: ate 5 consultas, 200 linhas e 512 KiB por pacote; exceder qualquer limite gera erro, sem truncamento.
- Provar com testes locais que o pacote nao contem gold set, resposta esperada, rubrica, credenciais ou dados de conexao, e que ressalvas, resumo global de qualidade e ausencia de observacao continuam visiveis.
- Documentar formato, comando, leitura da carga existente, limites e relacao com a API/harness futuros. Manter saidas geradas ignoradas pelo Git, salvo fixtures pequenas e deliberadamente revisadas.

## Non-scope

- Alterar bancos de origem, `db_pesquisa_dw`, seus fatos/dimensoes, CSVs, dados congelados, pesos, adapters, manifests cientificos ou resultados brutos.
- Integrar a DW ao `/api/runs`, criar endpoint de tools, oferecer SQL livre, usar LLM, iniciar RunPod/ngrok ou registrar metricas do artigo.
- Selecionar os casos oficiais, criar gold set, tolerancias/rubrica, comparar modelos ou implementar o cenario B de escolha de tools pela LLM.
- Consolidar entidades entre particoes ou inferir causalidade de coincidencia temporal.

## Requirements

- REQ-001: O manifesto de entrada e versionado e identifica `case_id`, pergunta, dominio (`financeiro`, `industrial` ou `integrado`) e lista ordenada de consultas/filtros. `case_id` e unico, segue `[A-Za-z0-9][A-Za-z0-9._-]{0,63}` e nao vira caminho arbitrario; pergunta nao vazia tem no maximo 2.000 caracteres. Dados desconhecidos ou fora da allowlist falham sem consulta.
- REQ-002: A exportacao usa somente leitura no cluster isolado `127.0.0.1:5544`; `verify` confirma a carga e fingerprint antes de cada lote. A fonte permanece inalterada. O resultado de cada consulta conserva `coverage.state`, inclusive `no_observation`.
- REQ-003: O pacote registra `case_id`, pergunta, dominio, versao de schema, fingerprint, `query_contract_version: 1` e `query_code_sha256` dos bytes de `BancoModeloUse/dw/cli.py`, itens ordenados com grao, formulas, unidades, tabelas fonte, linhas, cobertura e interpretacao; registra em campo separado o resumo global de flags de `verify`, identificado como global. O checksum canonico fica fora do corpo hasheado. Serializar o corpo com chaves ordenadas, separadores compactos, UTF-8, `ensure_ascii=False` e `allow_nan=False`, sem timestamps.
- REQ-004: Os pacotes da mesma versao do caso sao identicos para todos os modelos. O exportador nao inclui prompt especifico de modelo, saida de modelo, gold set, rubrica ou resposta esperada.
- REQ-005: Pacote ja existente com hash identico e reutilizado sem reescrita; hash divergente, fingerprint/versao incompatível ou arquivo parcialmente gravado falham sem substituir a evidencia anterior.
- REQ-006: O CLI aceita no maximo 5 consultas, 200 linhas e 512 KiB por pacote; se uma consulta ultrapassar o limite, falha com estado identificavel em vez de truncar evidencias silenciosamente.
- REQ-007: O codigo e a documentacao distinguem pacote candidato, verificacao da carga local, revisao independente do DW e futuro caso cientifico aprovado.

## Business or domain rules

- BR-001: Venda observada nao e receita contabil; soma de registros de operacao nao e producao final unica.
- BR-002: `resultados_financeiros` tem lacunas de cobertura; `no_observation` nao significa valor zero.
- BR-003: Chaves de produto e material/lote mapeadas podem ligar fatos, mas nomes iguais entre particoes nao provam identidade continua. Comparacao temporal permite associacao exploratoria, nao causa.
- BR-004: Flag de qualidade global e ressalva da consulta nao podem ser removidas para tornar um pacote mais simples ao modelo. Uma flag global nao prova que toda linha de um agregado a possui.

## Decisions already made

- O usuario definiu dois cenarios separados: dados preparados para comparar raciocinios e pesquisa com tools para avaliar tambem a busca; ver arquitetura de avaliacao, secao "Dois cenarios de comparacao".
- A SPEC-006 fixa as cinco consultas, seus parametros e seus limites; esta SPEC reutiliza esse contrato sem ampliar o DW.
- Esta fatia prepara entradas locais para o cenario A. A decisao sobre protocolo de tool-call, rodadas e limites do cenario B pertence a outra SPEC, depois de verificar capacidade do serving real.
- O gold set nao e entregue a LLM nem exportado por esta frente; criterios oficiais exigem revisao cientifica separada.

### Formato minimo do manifesto

```json
{
  "schema_version": 1,
  "cases": [
    {
      "case_id": "integrado-produto-2020-01",
      "question": "Como se comparam operacoes e vendas deste produto em 2020, e ha observacoes de resultado financeiro no ano?",
      "domain": "integrado",
      "queries": [
        {"query": "product", "year": 2020, "id": 1000001},
        {"query": "financial", "year": 2020}
      ]
    }
  ]
}
```

O segundo item do exemplo retorna ausencia de observacao para `resultados_financeiros` em 2020; isso testa cobertura e nao autoriza preencher zero. O manifesto e a lista de consultas preservam sua ordem declarada; linhas dentro de cada resultado seguem a ordenacao fixa do CLI da DW. O pacote inclui o corpo canonico e um checksum SHA-256 desse corpo em envelope externo, evitando auto-referencia do hash.

## Constraints

- O executor nao deve iniciar Pod, ngrok, treino ou inferencia por implicacao desta SPEC. Nao abrir outra thread automaticamente; `automatic_handoff` e falso.
- O checkout e compartilhado; apenas um escritor ativo por vez. Preservar mudancas locais preexistentes e resultados protegidos.
- A implementacao foi validada localmente e as revisoes independentes das SPECs 006 e 007 foram aprovadas em 16/10/2026. Os pacotes nao podem ser rotulados como benchmark cientifico oficial antes da selecao de casos e do gold set aprovados.
- A consulta `financial` nao possui filtro por ID; `machine`, `product`, `quality` e `material` devem exigir ID no manifesto para limitar o pacote a uma entidade. Nao alterar a semantica do CLI da DW por conveniencia do exportador.
- As consultas agregadas da DW retornam tabelas fonte e filtros, nao a lista completa de IDs contribuintes. `trace` comprova a linhagem de um fato individual quando seu ID e conhecido. O exportador nao deve afirmar linhagem por linha de cada agregado.

## Acceptance criteria

- AC-001: Um manifesto valido com caso industrial, financeiro e integrado gera pacotes com IDs, perguntas, fingerprint, versoes, itens, limites e hashes verificaveis; nenhum pacote contem gabarito ou credencial.
- AC-002: Duas exportacoes da mesma entrada/carga produzem bytes e SHA-256 iguais; alteracao de pergunta, filtros, codigo de consulta ou fingerprint resulta em pacote diferente e nao sobrescreve o anterior.
- AC-003: Consulta desconhecida, ano invalido, ID ausente, caso duplicado e limite de saida excedido falham antes de publicar pacote parcial.
- AC-004: Um caso sem observacao conserva `no_observation`; as ressalvas de associacao/cobertura da consulta e o resumo de qualidade global de `verify` permanecem distintos no JSON, sem atribuir flags globais a cada item.
- AC-005: Testes com fixtures validam o schema sem PostgreSQL; uma leitura local da carga existente verifica pelo menos um pacote integrado e reconcilia seus valores com duas consultas fixas da DW. Nenhuma fonte recebe escrita.
- AC-006: README, arquitetura, indice de SPECs e arquivos gerados deixam explicito que exportacao local nao e avaliacao de modelos nem revisao cientifica da DW.

## Affected areas

- `model_evaluation/` novo (schema, CLI, testes e README), `.gitignore`, `README.md`, `AGENTS.md`, `BancoModeloUse/README.md`, `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`, `BancoModeloUse/dw/README.md`, `inference_api/README.md`, `docs/arquitetura_inferencia_compartilhada.md`, `specs/README.md` e esta SPEC. A API exploratoria e os bancos existentes sao apenas referencias de leitura; somente a documentacao da API foi atualizada.

## References

- `AGENTS.md` e `README.md`: fronteiras do checkout, fontes de verdade e estado local.
- `BancoModeloUse/README.md` e `BancoModeloUse/dw/README.md`: origem, carga, consultas, anomalias e limites.
- `BancoModeloUse/dw/cli.py`: `verify` e `query`, contratos executaveis que o exportador deve reutilizar.
- `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`: desenho dos dois cenarios, comparabilidade e limites cientificos.
- `inference_api/README.md` e `specs/active/SPEC-001/SPEC.md`: bundle exploratorio atual e ausencia de escolha autonoma de tools.
- `specs/active/SPEC-006/SPEC.md`: grao, linhagem, regras de dominio e revisao local aprovada do DW.

## Skills

- `project-spec-architect` foi usado para preparar este contrato. Nenhuma skill especializada e obrigatoria para a implementacao Python local.

## Validation requirements

- VAL-001: `git diff --check` na raiz do projeto.
- VAL-002: `BancoModeloUse/.venv/Scripts/python.exe -m unittest discover -s model_evaluation/tests -v` com fixtures, determinismo, rejeicoes e ausencia de gold/segredos.
- VAL-003: `BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py verify` como leitura da carga existente antes do teste integrado; conferir fingerprint e `schema_version`.
- VAL-004: Exportar um caso integrado local de 2020 com o CLI novo e comparar itens/valores/ressalvas com `BancoModeloUse/dw/cli.py query product --year 2020 --id 1000001` e `BancoModeloUse/dw/cli.py query financial --year 2020`, que deve expor `no_observation`. Registrar comandos, hashes e saida sem segredo.
- VAL-005: Inspecionar que bancos de origem, DW e dados protegidos nao foram alterados, e que nenhum payload contem gold set.

## Review requirements

Revisao independente Sol/high do contrato publico de evidencias, determinismo, linhagem e separacao entre pacote, gold set e comparacao cientifica. As revisoes das SPECs 006 e 007 foram aprovadas separadamente para seus escopos locais; a promocao de pacotes a casos oficiais ainda depende de contrato cientifico e gold set.

## Execution and runtime

Implementacao local realizada nesta conversa em 16/10/2026 sobre `772ea0d`, sem criar thread propria, por pedido do usuario para prosseguir. O exportador e os schemas estao em [`model_evaluation/`](../../../model_evaluation/README.md); a [evidencia local](evidence/local-2026-10-16.md) registra os testes e a leitura da carga existente. O manifest registra a thread efetiva. As [revisoes desta SPEC](evidence/review.json) e da [SPEC-006](../SPEC-006/evidence/review.json) aprovaram o escopo local; o harness, o gold set e RunPod/ngrok nao foram executados.
