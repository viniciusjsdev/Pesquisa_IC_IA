> **Nota de localização em 07/11/2026:** a V2 foi integrada ao checkout principal. Os caminhos de worktree abaixo registram a execução histórica. Para uso atual, consulte [fontes vigentes](../../docs/fontes_ativas_e_arquivo.md).

# Reconciliação do DER com o checkout de dados — 31/10/2026

Escopo: leitura do XML da página **Modelagem integrada — 3 bancos** em
`IC-Datamind.drawio`, do checkout principal em HEAD `13d7df5` com alterações
locais não commitadas, e do worktree separado
`C:/Users/vinic/.codex/worktrees/datamind-dw-rebuild/Pesquisa_IC_IA`, também
com alterações não commitadas. Esta é uma verificação de inventário e código,
não uma nova carga nem uma validação científica.

| Item | DER | Checkout e código | Estado |
| --- | --- | --- | --- |
| Arquivos CSV | 166 previstos, 56 tipos lógicos em três períodos | O checkout principal tem 123 arquivos (75 originais + 48 complementares). O worktree `datamind-dw-rebuild` tem os 166 arquivos, manifesto e contrato das 56 fontes; `canonical_ingest.py plan` passou offline. | A diferença de 43 arquivos é entre checkouts. A carga V2 foi encontrada posteriormente nos três bancos locais, com fingerprint igual aos arquivos canônicos atuais. |
| Paradas geradas | `paradas_maquinas_geradas` aparece como fonte gerada; `fact_downtime` prevê ampliação. | No worktree canônico, três CSVs contêm 25 + 20 + 45 = 90 eventos, com IDs distintos dos 1.200 originais. O código histórico da DW carrega apenas os originais. | O carregador canônico e a carga local V2 incluem as 90 linhas adicionais: readback de 1.200 originais + 90 geradas na DW. |
| DW v1 | 15 tabelas detalhadas no DER. | `dw/migrations/001_init.sql` define as mesmas 15 tabelas, colunas e marcações PK/FK. | O DER foi corrigido para mostrar os tipos SQL físicos. |
| Ampliação da DW | As 20 tabelas têm, em uma seção inferior da mesma página, nomes, fontes, colunas, tipos e chaves que refletem a criação dinâmica do carregador canônico. | `canonical_ingest.py` une as colunas tipadas das fontes e acrescenta `source_file_id`, `period_index` e `original_id`; a PK é (`source_file_id`, `original_id`) e as duas primeiras colunas apontam para `dw.source_file` e `dw.dim_source_period`. | As 20 tabelas existem na DW local com 240 colunas físicas e essas PKs/FKs; o esquema ainda não recebeu aprovação semântica para o harness. |

`bootstrap_local.inventory()` passou em leitura local no checkout principal
para os **75 CSVs originais e 540.600 linhas** em 31/10/2026. Separadamente,
`canonical_ingest.py plan` passou no worktree canônico para **166 CSVs,
56 tabelas de origem e 1.565.666 linhas**, sem acesso ao banco. Nenhuma das
duas verificações offline, isoladamente, comprova a carga canônica. O readback
posterior documentado abaixo encontrou a carga V2.

Os 19 ajustes de tipo na DW v1 são 13 `int` → `smallint`, dois `text` →
`char(64)`, um `datetime` → `timestamptz`, dois `decimal` → `double precision`
e um `json` → `jsonb` (`schema_migrations.source_checks`). A lista anterior
de 18 omitia este último campo. Nenhuma coluna, chave, tipo da migração ou
linha da DW foi alterada; a correção foi feita na página do DER.

Na mesma página, foi incluído abaixo dos quadros existentes o detalhe das 20
tabelas novas com todas as colunas tipadas e a chave composta física. As
colunas de negócio herdadas das fontes não recebem FKs físicas nessa criação;
os vínculos entre entidades permanecem lógicos até uma decisão explícita de
modelagem. O detalhe representa o código de criação atual do worktree; a carga
V2 posterior confirmou o mesmo esquema físico, sem aprovar seu uso científico.

Foi feita uma comparação normalizada do XML salvo com `DW_TABLES` e
`contrato_tabelas_canonicas.json` no worktree canônico: **20 nomes de tabelas,
180 pares coluna/tipo e as listas de fontes coincidiram**. As assinaturas
SHA-256, calculadas sobre os mesmos vetores ordenados, foram respectivamente
`7b6927521b2cc4fb165a16d767e2971e701847f8b2b41f9239d7efa7f2f6911c`
e `65b45749e00a391003e033090c01d3167d1ee963f6e84961b4b19bcf112611d8`
em ambos. A nota de chaves do DER também foi conferida contra a instrução
`CREATE TABLE` do carregador. Dois rótulos antigos que ainda afirmavam faltar
colunas foram corrigidos. Esta é igualdade do **esquema proposto no desenho**
com o **código atual**. Um readback posterior confirmou as tabelas físicas,
sem criar garantia automática contra mudanças futuras.

Na verificação inicial, o cluster isolado `127.0.0.1:5544` estava parado. Ele
foi iniciado apenas para consultar o catálogo de bancos: existiam `postgres`,
`db_datamind_dw` (legado) e `db_inference_app`; `db_industrial`,
`db_financeiro` e `db_pesquisa_dw` não existiam nessa instância. O cluster foi
parado novamente. Logo, as contagens históricas da DW v1 documentadas em
`dw/README.md` não eram um readback dessa carga. Naquele momento, as 90
paradas estavam nos CSVs canônicos, ainda fora de `db_industrial`. O estado
mudou depois, conforme o readback registrado abaixo.

## Reconciliação de `fact_downtime`

1. Os três CSVs gerados foram localizados no worktree canônico e conferidos
   offline: 90 eventos com IDs separados dos 1.200 originais. O plano da
   ingestão inclui 166 arquivos e identifica as duas fontes de paradas.
2. O código canônico agora projeta os 90 eventos em `fact_downtime` com
   `source_file_id`, período, ID original e duração, além dos 1.200 originais.
   A migração v1 e sua carga histórica permanecem intactas.
3. A carga V2 local agora contém 1.290 linhas separadas por origem (1.200 + 90).
   Antes de habilitar esse mapa no harness, ainda é preciso conferir
   `contributors`, `trace`, consultas agregadas e a semântica das relações.

O M0 da SPEC-013 deve consumir esta reconciliação. A aprovação de mapas de
agentes depende das fontes e relações efetivamente carregadas, não somente
dos CSVs ou nomes propostos no diagrama.

## Atualização do desenho em 01/11/2026

Na página [Modelagem integrada — 3 bancos](https://app.diagrams.net/#G1RbtLePrWCTs8GjCAmAegFv7XBcAtzN8E#%7B%22pageId%22%3A%22LoO58KlvWIB3R87rbpOu%22%7D),
os rótulos de estado foram alinhados ao
[readback canônico somente leitura](../../specs/active/SPEC-013/evidence/canonical-load-readback-2026-11-01.md):
três bancos locais carregados, DW V2 com 35 tabelas, 20 ampliações fisicamente
presentes e `fact_downtime` com 1.200 linhas originais e 90 geradas. O quadro
`paradas_maquinas_geradas`, o título e a legenda da DW nova também deixaram
de afirmar carga pendente. Os 166 CSVs do worktree canônico e os 123 deste
checkout continuam descritos separadamente. As colunas, tipos, chaves e
relações do DER não foram modificados nesta atualização. Os rótulos de carga
física não aprovam vínculos semânticos nem habilitam consultas dos agentes.

Na página [Fluxo da Bancada e harness](https://app.diagrams.net/#G1RbtLePrWCTs8GjCAmAegFv7XBcAtzN8E#%7B%22pageId%22%3A%22rC3Onoxkcgc0oOyFh0Ck%22%7D),
o fluxo e os quadros JSON dos especialistas passaram a mostrar duas chamadas
do mesmo modelo por domínio: seleção de IDs em índice compacto, validação dos
IDs pelo backend e análise do detalhe selecionado. Essa é a arquitetura
proposta na [SPEC-013](../../specs/active/SPEC-013/SPEC.md); o núcleo M1
ainda usa uma chamada por especialista com mapa sintético pequeno.

## Readback posterior no mesmo dia

Após a checagem inicial que encontrou os bancos ausentes, uma consulta
**somente leitura** encontrou os três bancos de pesquisa no cluster isolado.
A [evidência M0 da SPEC-013](../../specs/active/SPEC-013/evidence/m0-inventory-2026-10-31.md)
registra a versão 2 carregada, o fingerprint igual ao manifesto/contrato
atuais, 56 tabelas de origem com schema coincidente, 20 tabelas novas da DW
com 240 colunas e PK/FKs coincidentes, 167 partições de origem e as 1.290
paradas na `fact_downtime`. O readback não substitui a revisão semântica dos
mapas, nem comprova comparação linha a linha ou avaliação científica.
