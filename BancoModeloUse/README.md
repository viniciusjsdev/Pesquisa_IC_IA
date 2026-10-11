# Bases de origem para a avaliação de modelos

Este diretório mantém os 75 CSVs originais, os modelos SQLAlchemy industriais e
financeiros e o importador verificável para PostgreSQL. O desenho da nova
avaliação está em [arquitetura_avaliacao_modelos.md](docs/arquitetura_avaliacao_modelos.md).
O harness e o novo DW ainda não foram implementados.

O RAG/agentes, o esquema DW anterior, os repositórios da aplicação anterior e
os scripts antigos de criação/carga/limpeza foram retirados do caminho ativo.
As versões rastreadas são recuperáveis pelo Git. O BI antigo foi guardado apenas
como [referência de consultas e testes](references/bi/README.md); não integra a
nova aplicação. Seus artefatos gerados locais ficam em
`references/bi/generated/` e são ignorados pelo Git.

PostgreSQL exclusivo deste checkout em **127.0.0.1:5544**. Os executáveis
instalados do PostgreSQL 15 são reutilizados, mas o cluster fica em
`BancoModeloUse/.local/postgres`. O serviço Windows da porta 5432 não é alterado.

| Banco | Conteúdo |
| --- | --- |
| `db_industrial` | Tabelas industriais e cópias brutas dos CSVs |
| `db_financeiro` | Tabelas financeiras e cópias brutas dos CSVs |

O banco local `db_datamind_dw` preexistente não é consultado, alterado ou
recriado pelo importador atual. Ele pode permanecer até o novo DW reproduzir
os dados, mas não constitui uma fonte analítica validada.

## Preparação e primeira carga

Na raiz do repositório, em PowerShell:

```powershell
python -m venv BancoModeloUse/.venv
BancoModeloUse/.venv/Scripts/python.exe -m pip install -r BancoModeloUse/requirements-local.txt
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py start
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/bootstrap_local.py
```

O gerenciador aceita `--pg-bin` caso os executáveis estejam em outro diretório.
Ele gera uma senha aleatória em `.env.local`, ignorado pelo Git, e exige
autenticação SCRAM. A instância escuta apenas no loopback. O importador verifica
host, porta e diretório real do cluster antes de criar os bancos.

O bootstrap atua somente nos dois bancos de origem e recusa bancos que já
tenham tabelas. Não apaga, substitui ou ignora registros conflitantes. Cada
domínio é carregado em uma transação; uma falha
posterior não desfaz domínios já concluídos. Nesse caso, investigar o erro antes
de qualquer limpeza ou nova carga. Os scripts legados de limpeza e carga foram
retirados.

## Uso cotidiano

```powershell
# Iniciar novamente depois de reiniciar o computador (não recarrega dados).
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py start

# Verificar processo e conferir a carga existente.
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py status
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/bootstrap_local.py --verify

# Parar somente esta instância quando necessário.
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py stop
```

O cluster persiste em disco, mas não foi instalado como serviço de início
automático. `--verify` executa transações de leitura nos bancos e atualiza o
relatório local `reports/local_database_validation.json`.

## Conectar pelo DBeaver

- Driver: PostgreSQL.
- Host: `127.0.0.1`; porta: `5544`.
- Banco: `db_industrial` ou `db_financeiro`.
- Usuário: `pesquisa_local`.
- Senha: consultar localmente a variável correspondente em `.env.local`.
- Tabelas para consulta: schema `public`.

As conexões do projeto e o gerenciador de criação leem esse mesmo arquivo.
Variáveis de ambiente explícitas têm precedência. Não compartilhar ou versionar
`.env.local`, o cluster ou seus logs.

## Contrato da importação

São **75 CSVs, com 540.600 linhas de origem**. A carga mantém duas representações:

1. `raw_p0`, `raw_p1` e `raw_p2`: uma tabela por CSV, com todas as colunas textuais,
   valores originais e IDs originais. Campos vazios do CSV tornam-se `NULL`.
2. `public`: tabelas tipadas conforme os modelos SQLAlchemy existentes. O campo
   `consumo_materiais.data_registro`, presente nos CSVs, também é preservado.
   Colunas do modelo ausentes da fonte ficam nulas; não são inventadas datas de
   registro nem valores calculados.

| Índice | Pasta industrial | Pasta financeira |
| --- | --- | --- |
| 0 | `dados_industriais_automotivo_eletronica_2015_2017` | `dados_financeiros_2015_2016` |
| 1 | `dados_industriais_automotivo_eletronica_2017_2020` | `dados_financeiros_2017_2020` |
| 2 | `dados_industriais_automotivo_eletronics_2021_2025` | `dados_financeiros_2021_2025` |

Os IDs reiniciam entre arquivos de períodos diferentes. Para preservar todas as
linhas, a chave em `public` é `id_original + indice_periodo * 1000000`.
As FKs recebem o mesmo deslocamento, inclusive `vendas.produto_id` e
`materiais_custo_historico.material_id/lote_material_id` entre domínios.
IDs de operadores, clientes e inspetores não são remapeados: não há cadastros
correspondentes nos CSVs que permitam determinar sua identidade.

Cadastros são preservados como registros por período, inclusive contas contábeis
repetidas. Um produto com IDs 1, 1000001 e 2000001 não foi automaticamente
consolidado em uma dimensão histórica. Essa consolidação pertence ao DW.
O arquivo `processo_industrial.csv` alimenta a tabela ORM `processos_industriais`.

## Validação e limites

O relatório registra SHA-256, contagens e intervalos de datas por arquivo.
A validação confere:

- unicidade das chaves dentro de cada fonte;
- referências locais e referências financeiras ao domínio industrial;
- igualdade de todos os valores da camada bruta com os CSVs;
- igualdade bidirecional (`EXCEPT ALL`) entre a transformação esperada e as
  tabelas tipadas, além de contagens por tabela;
- tabelas do modelo sem CSV permanecem vazias.

Esses controles provam fidelidade da importação. Não provam consistência
econômica, cobertura temporal completa, validade causal, correção dos KPIs
fornecidos nem integração analítica do DW. Os nomes das pastas não substituem
as datas efetivamente presentes nos dados. Os tipos numéricos existentes no
ORM foram mantidos, incluindo `Float` em parte dos indicadores; os valores
textuais originais continuam disponíveis na camada bruta.

Na carga verificada, `registros_operacao.hora_inicio` vai de `2015-01-01`
até `2026-01-01 00:00:00`, apesar do rótulo 2021–2025 da última pasta.
Esse limite foi preservado e deverá ser considerado no recorte do benchmark.

Próximo passo: estudar perguntas e granularidade do novo DW; então definir o
contrato de evidências e o harness que chamará todos os modelos por API.
Inferência, benchmark e preenchimento do novo DW são etapas posteriores.

## Consulta inicial

No banco `db_financeiro`:

```sql
SELECT extract(year FROM data_venda)::integer AS ano,
       count(*) AS registros_venda,
       sum(quantidade_vendida * preco_unitario_venda) AS receita_das_vendas
FROM public.vendas
GROUP BY 1
ORDER BY 1;
```

Essa consulta soma as vendas disponíveis; não pressupõe que sejam equivalentes
à receita agregada fornecida em `resultados_financeiros`.
