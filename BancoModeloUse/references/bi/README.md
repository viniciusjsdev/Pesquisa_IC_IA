# Referência histórica: observatório financeiro-industrial

Este BI pertence à aplicação anterior. Código, consultas e testes foram preservados para consulta durante o desenho do novo DW. Os comandos e caminhos abaixo são históricos; não fazem parte do fluxo ativo de importação ou avaliação e não foram revalidados nesta estrutura.

## Guia anterior, preservado para consulta

## Versão independente para compartilhar

O arquivo `BancoModeloUse/exports/BI_Pesquisa_Offline.html` contém os dados
agregados, estilos, gráficos e filtros em um único HTML. Enviar somente esse
arquivo; o destinatário pode salvá-lo e abri-lo em um navegador moderno,
sem Python, PostgreSQL ou internet. Pré-visualizadores de anexos podem não
executar JavaScript; nesse caso, baixar e abrir no navegador.

A versão independente mantém filtros, seções e exportação CSV. Exibe a data
da consulta original e não atualiza os dados automaticamente. Não incorpora
senhas ou configurações de conexão. Uma política de conteúdo bloqueia conexões
de rede no arquivo exportado.

Para gerar novamente a partir do PostgreSQL local ativo:

```powershell
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/bi/export_offline.py
```

O comando atualiza o HTML em `exports`. É possível escolher outro destino com
`--output caminho/arquivo.html`.

## Versão conectada

BI local em HTML/CSS/JavaScript, com gráficos SVG, sem serviços externos,
CDNs ou dependências adicionais além de `requirements-local.txt`.
O servidor Python consulta o PostgreSQL em transações somente leitura.

## Abrir

Na raiz do repositório:

```powershell
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py start
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/bi/server.py
```

Acessar <http://127.0.0.1:8501>. O servidor escuta somente em `127.0.0.1`.
Usar `--port 8502` se a porta padrão estiver ocupada. Encerrar com `Ctrl+C`
quando executado no terminal. O HTML deve ser aberto pelo servidor, não como
`file://`, pois consulta `/api/data`.

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

Com o servidor e o PostgreSQL ativos:

```powershell
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/bi/test_bi.py
node BancoModeloUse/bi/test_aggregates.cjs
```

Os testes comparam valores da API a consultas independentes, conferem inventário,
ausência de períodos fabricados e modo somente leitura. Os testes JavaScript
verificam filtros, médias ponderadas, razões, lacunas e divisão por zero.
`node` é necessário apenas para os testes JavaScript, não para usar o BI.

Também foi verificado no Chrome: renderização, navegação, filtro mensal e estado
financeiro sem dados de custos em 2024–2025.
