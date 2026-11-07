# Bases de origem para a avaliação de modelos

**SPEC-013 · Done de engenharia em 06/11/2026:** [parecer global Astra aprovado](../specs/active/SPEC-013/evidence/review.json),
[completion](../specs/active/SPEC-013/evidence/completion.json) e [validação final](../specs/active/SPEC-013/evidence/engineering-closeout-2026-11-06.md).
O harness de cinco papéis está implementado na Bancada, com leitura controlada
na DW, industrial e financeiro. O ensaio real completo, testes locais, replays
e histórico foram verificados. A matriz científica e a revisão humana de cada
resposta continuam posteriores, sem score atribuído. Este estado substitui
as descrições históricas de implementação pendente abaixo.

Em 02/11/2026, um [adaptador local da SPEC-013](../specs/active/SPEC-013/evidence/m0-semantic-activation-review-2026-11-02.md)
passou por consultas DW, linhagem e detalhe tipado com a conta de leitura
restrita, sem modificar os bancos ou enviar resultados a provedor. Naquele marco o catálogo
semântico estava desabilitado; agora o recorte piloto está aprovado e habilitado,
conforme SPEC-013. A avaliação científica segue pendente.

Este diretório mantém os 75 CSVs originais, os modelos SQLAlchemy industriais e
financeiros e o importador verificável para PostgreSQL. O desenho da nova
avaliação está em [arquitetura_avaliacao_modelos.md](docs/arquitetura_avaliacao_modelos.md).
O [DW local v1](dw/README.md) foi implementado e carregado em banco novo e
isolado para consultas analíticas rastreáveis. O harness da SPEC-013 está implementado na Bancada; a avaliação científica
continua separada.

O [DER integrado foi reconciliado com este checkout em 31/10/2026](docs/reconciliacao_der_2026-10-31.md):
o desenho contém 166 CSVs/56 tipos lógicos, disponíveis no worktree separado
`datamind-dw-rebuild`, enquanto os arquivos deste checkout são 75 originais
e 48 complementares. A ampliação da DW foi corrigida em código naquele
worktree e as 20 tabelas novas agora têm colunas, tipos e chaves detalhados no
DER. Uma [leitura posterior, somente leitura](../specs/active/SPEC-013/evidence/m0-inventory-2026-10-31.md)
confirmou a carga V2 dos três bancos no cluster isolado, incluindo as 90
paradas geradas. O código e os CSVs canônicos ainda estão em outro worktree;
este checkout não contém todos os arquivos dessa carga.

Em 01/11/2026, os rótulos de estado da página do DER foram atualizados para
a carga local V2 verificada: 35 tabelas DW e 1.290 paradas, inclusive as 90
geradas. A [reconciliação do desenho](docs/reconciliacao_der_2026-10-31.md)
registra os textos alterados e separa existência física de aprovação semântica.

O [desenho da avaliação](docs/arquitetura_avaliacao_modelos.md) separa dois
cenários: evidências iguais para comparar raciocínio e pesquisa com tools para
medir também a busca. O [exportador local da SPEC-007](../model_evaluation/README.md)
prepara pacotes fixos candidatos a partir da DW. A avaliação científica e o
harness por API ainda não foram implementados.

A [Bancada exploratória](../inference_api/README.md) usa a DW em dois modos explícitos
para novos runs: pacote candidato já exportado ou consultas fixas escolhidas
pela LLM. O fluxo anterior consultava estes dois bancos de origem e seus
snapshots permanecem legíveis.
O banco de histórico `db_inference_app` é criado separadamente por comando
explícito; o importador desta pasta não é o servidor da aplicação.

## Perguntas de teste e estado científico

- A [seção de fluxo da Bancada](../inference_api/README.md) explica onde cada
  pergunta entra, como a LLM recebe evidências e onde o run fica registrado.
- [`model_evaluation/examples/cases_2020.json`](../model_evaluation/examples/cases_2020.json)
  é um exemplo versionado de pergunta para preparar pacote fixo. O manifesto
  escolhido e o pacote exportado precisam ser identificados por versão/hash;
  esse exemplo não é a bateria oficial.
- No modo tools, a pergunta livre é entrada do run e seu texto fica no snapshot
  de `db_inference_app`, não numa lista de perguntas do repositório.
- O catálogo científico de casos, seus gabaritos e a pontuação permanecem
  pendentes, conforme [arquitetura da avaliação](docs/arquitetura_avaliacao_modelos.md).
  Um rascunho antigo que se intitulava “Gold Set” foi arquivado fora do
  checkout: seus campos, premissas e comandos não correspondiam à DW v1.

O RAG/agentes, o esquema DW anterior, os repositórios da aplicação anterior e
os scripts antigos de criação/carga/limpeza não integram este checkout ativo.
As versões rastreadas são recuperáveis pelo Git. O BI anterior também foi
retirado: sua referência de consultas e testes está preservada fora do repositório
na máquina de origem, em `D:\Projetos\Github_ViniciusJ\Pesquisa_IC_IA_legacy_archive_20261011\BancoModeloUse\references\bi`, com hashes no `inventory.json` do arquivo externo. Esse caminho não é portátil para outros clones.

PostgreSQL exclusivo deste checkout em **127.0.0.1:5544**. Os executáveis
instalados do PostgreSQL 15 são reutilizados, mas o cluster fica em
`BancoModeloUse/.local/postgres`. O serviço Windows da porta 5432 não é alterado.

| Banco | Conteúdo |
| --- | --- |
| `db_industrial` | Tabelas industriais e cópias brutas dos CSVs |
| `db_financeiro` | Tabelas financeiras e cópias brutas dos CSVs |
| `db_pesquisa_dw` | Camada analítica V1 da [SPEC-006](../specs/active/SPEC-006/SPEC.md) com 20 tabelas adicionais V2 na carga local atual; fingerprint conferido no [readback](../specs/active/SPEC-013/evidence/m0-inventory-2026-10-31.md) |

O banco local `db_datamind_dw` preexistente não é consultado, alterado ou
recriado pelo importador atual. Ele pode permanecer até o novo DW reproduzir
os dados, mas não constitui uma fonte analítica validada.

Para a SPEC-013, `scripts/export_schema_inventory.py --output <arquivo.json>`
exporta somente nomes, tipos, nulabilidade e restrições físicas das tabelas dos
três bancos no cluster isolado. A operação usa transações de leitura e recusa
sobrescrever um arquivo existente. O [inventário de 01/11/2026](../specs/active/SPEC-013/evidence/m0-physical-schema-2026-11-01.md)
é evidência de estrutura física, não um catálogo semântico aprovado nem uma
allowlist de consulta.

O M0 mantém esse inventário completo separado do
[recorte semântico candidato](../specs/active/SPEC-013/evidence/m0-semantic-map-candidate-2026-11-01.json),
que permanece desabilitado. A validação offline do recorte confere referências
físicas e outputs das consultas fixas sem consultar linhas nem habilitar tools;
ela não aprova significado, cobertura, unidade ou relação entre domínios.
O comando e o resultado estão no
[pacote de revisão M0](../specs/active/SPEC-013/evidence/m0-catalog-review-2026-11-01.md).
Após aprovação do recorte piloto, `scripts/verify_catalog_provenance.py`
conferiu somente contagens e correspondência de período/arquivo para as cinco
tabelas tipadas selecionadas, em leitura local. O
[relatório](../specs/active/SPEC-013/evidence/m0-catalog-provenance-2026-11-01.json)
não contém valores das linhas e não habilita o harness.

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

As perguntas, o grão e a primeira carga do DW estão em [dw/README.md](dw/README.md).
A SPEC-009 liga a DW à Bancada exploratória por pacotes candidatos e tools
de leitura. O harness científico formal continua posterior; a integração não
valida um caso, score ou inferência real dos pesos.

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
