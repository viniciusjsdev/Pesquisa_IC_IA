---
id: SPEC-006
title: DW local rastreavel para associacoes industriais e financeiras
status: done
contract_version: 1
---

# SPEC-006: DW local rastreavel para associacoes industriais e financeiras

## Goal

Criar uma primeira camada analitica local, reproduzivel e consultavel, separada dos bancos de origem, que responda perguntas industriais, financeiras e integradas sem inventar vinculos nem causalidade. Esta SPEC implementa o DW; o harness formal e sua integracao com a API permanecem em contratos posteriores.

## Context

Em 13/10/2026, sobre `ad6edcb` mais mudancas locais, o importador de `BancoModeloUse/scripts/bootstrap_local.py` importa 75 CSVs para `db_industrial` e `db_financeiro`, preservando `raw_p0..p2` e IDs deslocados por `period_index * 1000000`. A carga existente foi validada anteriormente; uma nova verificacao deve preceder esta carga. `db_datamind_dw` preexistente e legado, sem contrato/carga validada, e nao sera consultado ou alterado. As cinco SPECs de inferencia compartilham o checkout e estavam inativas na inspeção de 13/10/2026; apenas esta thread escrevera durante esta etapa.

Perguntas representativas, respondidas com recorte explicito e linhas rastreaveis:

1. Como variam registros e quantidade reportada de operacoes e minutos de parada por maquina/ano? A quantidade pode contar etapas repetidas, nao producao final; a parada com inicio no dia pertence ao dia de inicio.
2. Como variam vendas observadas por produto/ano e registros de operacao do mesmo produto/ano? `vendas.produto_id` aponta para `produtos` no mesmo indice de importacao; a comparacao nao atribui venda a ordem/maquina nem identifica efeito causal.
3. Que observacoes de resultados financeiros existem em cada ano, com quais lacunas de cobertura? `resultados_financeiros` nao tem chave de ordem/produto/maquina nem um calendario mensal confiavel; nao publicar sua soma como receita anual completa.
4. Que inspecoes e consumos de material se ligam por chaves existentes a lote, ordem, produto e registro? Um preco historico de material/lote e uma observacao de preco, nao custo realizado de um registro sem regra de vigencia e transacao.

## Scope

- Criar `BancoModeloUse/dw/` e banco **novo** `db_pesquisa_dw` apenas no cluster isolado `127.0.0.1:5544`, sem reusar `db_datamind_dw` nem objetos da aplicacao.
- Versionar migracao SQL inicial, manifest dos 75 arquivos com SHA-256/contagem, dimensoes `day`, `source_period`, `product`, `machine`, `material`, `material_lot`, e fatos de operacao, parada, venda, resultado financeiro observado, qualidade, consumo e preco historico de material.
- Implementar preflight que valida CSVs e a carga tipada/bruta existente via importador em modo somente leitura; carga nova transacional, repeticao identica sem escrita e recusa de divergencia de fingerprint/versao. Banco de destino parcialmente criado mas sem objetos pode ser retomado; nunca apagar ou substituir uma carga divergente automaticamente.
- Reconciliar chaves, contagens por fonte/tabela, somas aditivas apropriadas, linagem e flags de qualidade; oferecer consultas SQL fixas e parametrizadas por ano e dimensao, sem SQL livre.
- Atualizar os README e a arquitetura cientifica, com limites de cobertura e causalidade observados.

## Non-scope

- Alterar `db_industrial`, `db_financeiro`, `db_datamind_dw`, CSVs, dados congelados, adapters, resultados, artigo ou esquema de `db_inference_app`.
- Executar RunPod/ngrok, integrar a API da SPEC-001 ao DW, criar gold set/harness formal ou declarar avaliacao cientifica concluida.
- Consolidar entidades entre periodos por nome, imputar datas ausentes, atribuir receita a maquina ou transformar preco historico em custo realizado.

## Requirements

- REQ-001: Cada fato tem uma linha por ID tipado da tabela de origem correspondente, PK imutavel, data efetiva, periodo de importacao, identificador de arquivo e ID original. O par arquivo/ID original identifica a linha bruta; a PK tipada usa o deslocamento documentado.
- REQ-002: `dim_day` usa datas efetivas, nao nomes de pastas. `dim_source_period` e particao de importacao, nao uma faixa temporal garantida. Produtos, maquinas, materiais e lotes mantem IDs por periodo, sem deduplicacao semantica entre periodos.
- REQ-003: FK comprovada permite operacao -> ordem -> produto; qualidade -> lote de producao -> ordem -> produto; consumo -> registro/material/lote; preco historico -> material/lote; venda -> produto. Resultado financeiro tem apenas dia, sem ponte para produto ou maquina. Paradas tem maquina, sem FK para operacao.
- REQ-004: Comparacao entre fatos por ano/dia/maquina/produto e uma associacao declarada, sem bridge causal. Os valores de operacao, qualidade e vendas mantem unidades e denominadores separados. Minutos de parada sao atribuidos ao dia/ano do inicio e nunca somados como tempo de operacao.
- REQ-005: Flags preservam, no minimo, ordem com cronologia invertida, intervalo de operacao/parada invalido, data fora do rotulo da fonte, inspecao maior que lote e linha financeira de fonte `Float`. Nao corrigir dados brutos. Relatorios registram contagem e exemplos de IDs por flag.
- REQ-006: Consultas deterministicas retornam valor, periodo, grão, unidade, formula, cobertura e restricao de interpretacao, com chave para drill-through a `db_*.raw_pN` e `public`; sem SQL fornecido por usuario.
- REQ-007: Carregamento e verificacao recusam host/porta/diretorio de dados inesperados, destino existente nao reconhecido, fingerprint divergente e falha de reconciliacao. Segredos permanecem em `.env.local`; saidas versionadas nao os contêm.

## Business or domain rules

- BR-001: `sum(quantidade_vendida * preco_unitario_venda)` e valor das vendas observadas, nao igualado a `resultados_financeiros.receita_total`.
- BR-002: `sum(quantidade_produzida_real)` e soma dos registros de operacao, nao unidades finais unicas. Lotes e inspecoes podem repetir/contradizer esse numero.
- BR-003: `resultados_financeiros` e `custos_producao` têm observacoes datadas, com anos faltantes; nao atribuir periodicidade mensal regular ou cobertura anual completa.
- BR-004: `dim_product`/`dim_machine`/`dim_material` representam o registro de cada particao. Nome igual em particoes distintas nao prova identidade historica.
- BR-005: Janela temporal comum gera associacao exploratoria; causalidade requer evidencia adicional. Preco historico de material nao e custo efetivo de consumo sem regra de aplicabilidade.

## Decisions already made

- `BancoModeloUse/README.md` documenta os dois bancos fonte e o mapeamento `id_original + indice * 1000000`; `bootstrap_local.py` implementa e verifica esse contrato.
- `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md` exige fatos rastreaveis, qualidade e distincao entre FK e hipotese temporal.
- A SPEC cria um banco com nome novo e explicito; a existencia de `db_datamind_dw` nao e evidencia de uma DW valida.
- O primeiro recorte usa consultas seguras para as quatro perguntas acima. Ampliar indicadores ou integrar ao backend exige outro contrato, pois as inconsistencias nao autorizam inferencia automatica.

## Constraints

- O carregamento inicial do DW e uma nova escrita local autorizada nesta frente; so pode ocorrer depois do preflight e da migracao revisada. Nunca recriar fontes ou apagar bases existentes.
- SQL de leitura em bancos fonte deve usar transacoes `READ ONLY`; a carga de destino deve ser atomica e idempotente por fingerprint.
- Os CSVs sao simulados e contêm anomalias. Na inspeção estatica de 13/10/2026: 339/650 ordens têm inicio apos fim; `registros_operacao` inclui 4 linhas de 2017 no primeiro pacote, 4 de 2021 no segundo e 5 de 2026 no terceiro; `resultados_financeiros` cobre 2015, 2017-18 e 2021-23, com 72 linhas no total. Recalcular no build/verify antes de apresentar isso como estado da carga.

## Acceptance criteria

- AC-001: `build` em ambiente isolado cria somente `db_pesquisa_dw` e preserva hash/contagens dos 75 CSVs e a carga dos dois bancos de origem; `verify` reconcilia contagens, somas relevantes e amostras de linagem.
- AC-002: Segunda chamada `build` com mesmo fingerprint termina como `already_current` sem alterar a carga; fingerprint divergente ou destino estranho falha sem substituicao.
- AC-003: Fatos e dimensoes têm chaves/FKs demonstradas; testes com fixtures conferem grao, mapeamento de periodo, data efetiva e drill-through para raw/public.
- AC-004: Consultas fixas respondem as quatro perguntas com filtros de ano, valores e ressalvas; agregados de venda e operacao reconciliam fontes. Nenhum resultado chama receita contábil, producao final ou causalidade aquilo que os dados nao provam.
- AC-005: Relatorio apresenta flags e cobertura; as anomalias conhecidas permanecem visiveis e nenhuma linha das sete tabelas de fatos selecionadas e descartada. Os demais CSVs ficam preservados nos bancos de origem e no manifest, sem fato DW nesta versao.
- AC-006: Documentos distinguem desenho, codigo implementado, verificacao de carga existente, nova carga local e pendencias de API/harness.

## Affected areas

- `BancoModeloUse/dw/`, `BancoModeloUse/README.md`, `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`, `README.md`, `docs/arquitetura_inferencia_compartilhada.md`, `specs/README.md` e esta SPEC.

## References

- `AGENTS.md`, `README.md`, `BancoModeloUse/README.md`: limites e comandos do checkout.
- `BancoModeloUse/scripts/bootstrap_local.py`: manifest, mapeamento, preflight e validacao de fontes.
- `BancoModeloUse/core/models/industrial/` e `financeiro/`: colunas e FKs tipadas.
- `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`: perguntas, associacao e limites cientificos.
- `docs/arquitetura_inferencia_compartilhada.md` e `inference_api/README.md`: fronteira com a API atual.

## Skills

- `project-spec-architect` foi usado no desenho. A implementacao segue este contrato, sem skill especializado adicional.

## Validation requirements

- VAL-001: `git diff --check`.
- VAL-002: `BancoModeloUse/.venv/Scripts/python.exe -m unittest discover -s BancoModeloUse/dw/tests -v`.
- VAL-005: com o cluster local já carregado, `BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/tests/run_existing_load.py` executa as provas de leitura integral, grão, FKs, consultas, paginação e rastreio.
- VAL-003: `BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py verify` apos carga nova; registrar DB, fingerprints, contagens e flags sem expor credenciais.
- VAL-004: Comparar saídas de consultas do DW com SQL de leitura nos dois bancos fonte e conferir IDs raw/public.

## Review requirements

Revisao independente da migracao/carga e das afirmacoes cientificas antes de considerar esta SPEC aprovada. A conclusao local pode registrar implementado e validado sem promover o harness.

## Execution and runtime

Executar conforme `SPEC.execution.json`. Esta thread ja foi criada para a frente DW e e a unica escritora durante esta etapa.

Implementação local concluída no histórico `622fc0f` e corrigida em 16/10/2026 no checkout sobre `772ea0d` após a [primeira revisão independente](evidence/review-round-1.json). A correção acrescentou reconciliação de todas as linhas/colunas carregadas, navegação `contributors` → `trace`, testes com fixtures e integração somente leitura. A [segunda revisão independente](evidence/review.json) aprovou a implementação local sem achados restantes. `done` se refere a esta SPEC local; integração à API, harness, gold set e avaliação científica permanecem fora do escopo.
