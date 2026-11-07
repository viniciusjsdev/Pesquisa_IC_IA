# DEC-001 · aprovação do recorte piloto (01/11/2026)

O pesquisador respondeu **“Aprovar esse recorte piloto (Recommended)”** à
pergunta apresentada nesta conversa:

> A SPEC-013 exige revisão humana do catálogo antes de habilitar consultas
> reais. Você aprova como recorte piloto as 12 fontes do relatório M0 (5
> consultas DW, contributors/trace, paradas e operações industriais, resultados
> financeiros e vendas), sem joins entre bancos?

Portanto, o **escopo piloto** de 12 fontes do
[relatório M0](m0-catalog-review-2026-11-01.md) está aprovado, com a proibição
de joins entre bancos. O [mapa JSON](m0-semantic-map-candidate-2026-11-01.json)
continua com todas as entradas `enabled: false` porque aprovação de escopo não
substitui a definição de contratos de saída, limites, credenciais de leitura,
conferência de cobertura e gates de transmissão. Não houve consulta real do
novo harness, envio a provedor, alteração de banco ou pontuação científica
por efeito desta aprovação.

DEC-001 permanece **parcial**: faltam a matriz de perguntas piloto obrigatórias
e a revisão da cobertura e dos contratos detalhados de `contributors`/`trace`.
DEC-002–005 continuam abertas. A habilitação exige gates específicos da SPEC.
