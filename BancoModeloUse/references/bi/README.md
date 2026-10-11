# Referência histórica: observatório financeiro-industrial

Este BI pertence à aplicação anterior. Código, consultas e testes foram preservados para consulta durante o desenho do novo DW. As descrições abaixo são históricas e não constituem instruções executáveis neste checkout. O código está em `BancoModeloUse/references/bi/`; os caminhos antigos `BancoModeloUse/bi/` e `BancoModeloUse/exports/` não existem aqui. O BI não integra o fluxo ativo de importação ou avaliação e não foi revalidado nesta estrutura.

## Guia anterior, preservado para consulta

## Versão independente para compartilhar

O arquivo antigo `BancoModeloUse/exports/BI_Pesquisa_Offline.html` reunia os dados
agregados, estilos, gráficos e filtros em um único HTML. Ele não está presente
neste checkout; não há uma exportação atual pronta para envio. Na versão
anterior, o destinatário podia abrir esse HTML em um navegador moderno, sem
Python, PostgreSQL ou internet.

A versão independente mantinha filtros, seções e exportação CSV. Exibia a data
da consulta original e não atualizava os dados automaticamente. Não incorporava
senhas ou configurações de conexão. Uma política de conteúdo bloqueava conexões
de rede no arquivo exportado.

O gerador antigo está preservado em `BancoModeloUse/references/bi/export_offline.py`,
mas não foi revalidado após a mudança de estrutura. Revise suas dependências,
consultas e destino antes de tentar produzir outra exportação; o comando antigo
em `BancoModeloUse/bi/export_offline.py` não funciona neste checkout.

## Versão conectada

O BI anterior era local, em HTML/CSS/JavaScript, com gráficos SVG, sem serviços
externos ou CDNs. O servidor Python consultava o PostgreSQL em transações
somente leitura.

## Abrir

O servidor antigo está preservado em `BancoModeloUse/references/bi/server.py`,
sem validação de execução na estrutura atual. O comando antigo em
`BancoModeloUse/bi/server.py` não funciona neste checkout. Na instalação
anterior, o acesso era por <http://127.0.0.1:8501>, com escuta em `127.0.0.1`;
o HTML consultava `/api/data` pelo servidor.

Na instalação inicial, o servidor foi iniciado em segundo plano, com logs e PID
em `BancoModeloUse/.local/bi.*`. Não é um serviço de início automático do Windows.

## Recursos

- Visão integrada: vendas, volume registrado, OEE, rejeição, custo por unidade e
  tabela temporal comparativa.
- Financeiro: vendas, receita e lucro reportados, custos totais e componentes.
- Industrial: volume, consumo de energia, indicadores de equipamentos,
  qualidade e duração dos eventos de parada.
- Dados e método: contagens das 25 tabelas de origem, cobertura das sete fontes
  do painel, fórmulas e limites de interpretação.
- Filtro por intervalo de anos, agregação anual ou mensal e atualização manual.
- Exportação CSV de todos os indicadores do período, independentemente da seção
  selecionada. UTF-8 com BOM, separador `;`, decimal `,`, taxas em fração (0–1),
  valores ausentes vazios. Os gráficos mostram taxas em porcentagem.

O intervalo inicial é 2015–2025. O ano 2026 está disponível no filtro para
inspecionar os registros industriais de fronteira temporal.

## Cálculos e cobertura

As séries são agregadas por mês no banco. O navegador combina somas e contagens
para obter indicadores anuais ou do período completo. OEE não usa uma média
não ponderada das médias mensais: divide a soma das observações pela contagem
de observações. Custo unitário divide custo total pelas unidades da mesma fonte.
Rejeição divide rejeitadas pelo total inspecionado.

Períodos sem observações não viram zero. Por exemplo, custos e resultados
financeiros não têm dados após 2023 e também apresentam lacunas anteriores.
Vendas não são reconciliadas com receita reportada. Volume das operações pode
contar a mesma unidade em etapas diferentes. OEE é o valor fornecido na base,
não o produto recalculado das médias de seus componentes.

Os dados monetários usam **u.m.**, porque a base não declara a moeda.
O alinhamento temporal entre as duas bases não constitui ETL do DW nem
evidência causal. A tela Dados e método explica as fontes detalhadamente.

O cache do servidor dura 60 segundos; o botão Atualizar dados força uma nova
leitura. Não há atualização automática da tela. Se uma atualização falhar,
a tela informa o erro e preserva o último resultado bem-sucedido com sua data.
Cada banco é lido em uma transação consistente separada.

## Verificação

Os testes antigos estão preservados em `BancoModeloUse/references/bi/test_bi.py`
e `BancoModeloUse/references/bi/test_aggregates.cjs`. Não foram executados nem
adaptados nesta estrutura; os antigos comandos em `BancoModeloUse/bi/` não
funcionam neste checkout.

Os testes comparavam valores da API a consultas independentes, conferiam inventário,
ausência de períodos fabricados e modo somente leitura. Os testes JavaScript
verificavam filtros, médias ponderadas, razões, lacunas e divisão por zero.
`node` era necessário apenas para os testes JavaScript, não para usar o BI.

Também foi verificado no Chrome: renderização, navegação, filtro mensal e estado
financeiro sem dados de custos em 2024–2025.
