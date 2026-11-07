# M0 · catálogo candidato e conferência estrutural (01/11/2026)

O [inventário físico](m0-physical-schema-2026-11-01.json) lista todas as
35 tabelas DW, 39 objetos `public` industriais e 19 financeiros (38 e 18
tabelas tipadas de origem, mais `canonical_source_file` em cada banco). O
[recorte semântico candidato](m0-semantic-map-candidate-2026-11-01.json) **não**
oferece automaticamente todos esses objetos aos agentes. Ele define 12 fontes
para revisão, todas `enabled: false`:

| Domínio | Fontes candidatas | Finalidade do primeiro recorte |
| --- | --- | --- |
| DW | `machine`, `product`, `financial`, `quality`, `material` | Cinco consultas fixas já existentes, com grão, outputs e ressalvas. |
| DW/linhagem | `contributors`, `trace` | Descer de agregado para fatos e linha de origem; ainda não são tools do harness. |
| Industrial | `paradas_maquinas`, `paradas_maquinas_geradas`, `registros_operacao` | Detalhe tipado de parada e operação, incluindo as 90 paradas geradas. |
| Financeiro | `resultados_financeiros`, `vendas` | Observações datadas e vendas registradas, sem transformar venda em receita contábil. |

O mapa guarda IDs, campos selecionados, tipos físicos das tabelas tipadas,
chaves, FKs físicas declaradas, filtros candidatos, unidades conhecidas, grão
e ressalvas. `physical_relations` documenta uma FK existente; **não** aprova
automaticamente um join do serviço de consultas. Não há relação entre domínios
aprovada. `vendas.produto_id` não possui FK física; data semelhante não liga
resultados financeiros a máquina, produto ou parada.
Os tipos dos **outputs agregados** das consultas fixas e os formatos completos
de `contributors`/`trace` ainda precisam de contrato versionado; a checagem
atual compara seus nomes, não prova os tipos de cada valor devolvido.

## Verificação executada

Uma nova leitura **somente de metadados** do cluster `127.0.0.1:5544` retornou
o mesmo SHA-256 lógico do inventário: `ca7f44f371fe5403b203d11bbc82a0d01553b5d4783d34cc6f9ebdd750343b62`.
Não foram lidas linhas de pesquisa, alterados bancos ou chamados provedores.

Após a aprovação do recorte piloto, uma [conferência adicional de proveniência
por contagem](m0-catalog-provenance-2026-11-01.json) leu as cinco tabelas
tipadas em transações `READ ONLY`. Todas as 431.047 linhas do recorte encontraram
uma partição em `canonical_source_file` pela regra de ID do importador; as
contagens registradas por arquivo fecharam em cada tabela. O relatório contém
somente contagens, nomes e hash, sem valores de linhas. Essa conferência não
prova, isoladamente, igualdade de cada valor com o CSV; o readback canônico
existente cobre uma verificação de carga separada.

O [relatório do validador](m0-semantic-catalog-validation-2026-11-01.json)
retornou `valid_structurally=true`, `eligible_for_activation=false`, sem erros
ou avisos estruturais: 12 fontes, 32 campos tipados, 25 outputs de consultas
fixas, 16 referências a tabelas DW e 3 FKs físicas conferidas. O índice
candidato mede 1.221 bytes para DW, 538 para industrial e 449 para financeiro;
o maior detalhe de uma fonte mede 1.081 bytes. Isso não mede o envelope final
nem assegura que qualquer conjunto de três fontes caiba no limite M1.

Para reproduzir da raiz:

```powershell
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/validate_semantic_catalog.py --catalog specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json --inventory specs/active/SPEC-013/evidence/m0-physical-schema-2026-11-01.json --fixed-queries BancoModeloUse/dw/fixed_queries.py --lineage-cli BancoModeloUse/dw/cli.py
inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -p test_spec013_catalog.py -v
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/verify_catalog_provenance.py --catalog specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json
```

## Revisão necessária para habilitar

1. **DEC-001:** revisar significado, unidade, cobertura temporal, filtros e
   utilidade das 12 fontes; decidir se esse recorte atende as perguntas piloto.
   As cinco consultas DW são estáveis no código exploratório, mas o detalhe
   industrial/financeiro ainda não tem contrato de tool nem relação aprovada.
2. **DEC-002:** testar casos representativos e fixar o orçamento. Ponto de
   partida proposto: até 3 consultas, 24 chamadas de modelo, 3 rodadas, 3
   domínios por rodada e 3 tabelas por especialista, com uma correção visível
   por papel. Definir também limites de linhas/bytes/tempo e o estado de
   overflow; os números são hipótese de piloto, não configuração ativa.
3. **DEC-003–005:** selecionar casos e revisores, definir credencial de leitura
   local e gate separado para envio de resultados a provedor, depois fixar
   gabaritos, tolerâncias, rubrica e repetições. Sem essas decisões, a SPEC
   continua `design` e nenhum score pode ser publicado.

Este relatório prova compatibilidade **estrutural** com o snapshot do cluster e
com os nomes de outputs atuais. Ele não prova cobertura semântica, resultado
de consulta, compatibilidade com um provedor nem validade científica.SS
