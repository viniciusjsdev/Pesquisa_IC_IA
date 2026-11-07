# Reconciliação do projeto e da DW V2 — 07/11/2026

Autorização: reunir históricos e scripts soltos, integrar a V2 no principal,
preservar dados e referências e identificar claramente as fontes vigentes.
Base principal: `b2cfb790a8d33cfe41c87922927bd0d65bd01456`.
Origem V2: alterações locais sobre `13d7df5c748f79387d34f39cd30b6cf82c96c869`
no worktree `datamind-dw-rebuild`. Implementação e validação locais, concluídas
antes do versionamento. Em 07/11/2026, o usuário autorizou o commit e o push
deste conjunto. Não é uma revisão independente. O commit que contém este
relatório registra a integração; o arquivo de segurança permanece local,
fora do Git e do push.

## Resultado

- Projeto ativo: `D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA`.
- Arquivo: `D:/Projetos/Github_ViniciusJ/_arquivo_Pesquisa_IC_IA`.
- Cinco pastas históricas e quatro scripts soltos reunidos, com inventário
  antes da movimentação e comparação SHA-256 integral depois: **2.117 arquivos,
  5.224.829.634 bytes, todos coincidentes**.
- Junctions ocultas preservam os caminhos das cinco pastas. O arquivo
  FineTuning usa nome curto para manter caminhos acessíveis no Windows.
- 166 CSVs, manifesto, contrato, DER, ingestão, verificação e testes da V2
  integrados. Seis CSVs receberam exatamente a versão corrigida já existente
  no worktree; os anteriores e os 12 CSVs retirados foram preservados.
- O worktree foi mantido com avisos de histórico em `README.md` e `AGENTS.md`.
- `fixed_queries.py` mantém a versão mais recente do principal, sem diff.
- Os comandos CLI `bootstrap_local.py --verify` e `dw/cli.py verify`
  encaminham para a verificação canônica; comandos de criação V1 recusam
  uma carga incompleta. A função Python V1 permanece para contratos históricos.
- `.gitattributes` e a atualização do índice Git preservam os bytes exatos
  dos CSVs, manifesto e contrato. A conferência inclui cada blob CSV preparado
  no índice, além dos arquivos no disco; não houve regeneração de CSVs.
  Em 105 CSVs já idênticos entre os dois checkouts, o blob Git antigo tinha
  finais de linha normalizados. Seu diff preparado registra a preservação
  dos bytes atuais, sem alteração dos valores. Os seis corrigidos já vinham
  da V2 histórica e os 55 restantes foram acrescentados ao principal.

## Validação executada

| Verificação | Resultado |
| --- | --- |
| `canonical_ingest.py plan` no principal | Passou: 166 arquivos, 167 partições, 56 tabelas de origem, 1.565.666 linhas, 35 tabelas DW previstas. |
| `verify_canonical_load.py --database-home BancoModeloUse` | Passou nos três bancos, somente leitura. |
| `unittest discover -s BancoModeloUse/scripts/tests -v` | 11 testes passaram: DER, proveniência das paradas e encaminhamento/bloqueio dos comandos V1. |
| `unittest discover -s model_evaluation/tests -v` | 21 testes passaram. |
| `unittest discover -s inference_api/tests -p test_dw_v2_gate.py -v` | 2 testes passaram. |
| `unittest discover -s BancoModeloUse/dw/tests -v` | 5 testes offline passaram; 5 testes de integração V1 foram pulados pelo gate existente. A integração V2 é coberta pelo readback acima. |
| Cinco consultas fixas, `contributors` e `trace` | Passaram contra a V2; o CSV apontado pelo trace existe no principal. |
| Cópia isolada materializada somente do índice Git | O plano offline reproduziu os 166 CSVs e o mesmo fingerprint, sem usar o worktree anterior, credenciais ou banco. |

Total: **39 testes passaram**, além do plano, readback e consultas reais
somente leitura. Os cinco testes V1 pulados não são contados como aprovação.

## Evidências e preservação

- [Readback dos três bancos](canonical-readback.json).
- [Consultas e rastreamento](query-smoke.json).
- [Conferência de arquivos, índice Git e aliases](filesystem-checks.json).
- [Hashes dos arquivos integrados](integrated-files.json).
- [Verificação dos links Markdown locais](markdown-links.json).
- [Plano reproduzido a partir do índice Git](git-index-plan.json).

O inventário completo e os originais anteriores estão no arquivo externo,
em `reconciliacao_2026-11-07/`: `archive_inventory.json`,
`archive_verification.json`, `integration.json`, `preservation_manifest.json`,
`main_before/`, `worktree_before/`, `worktree-before.patch` e
`csvs_substituidos/`. O mapa e os SHA-256 desses inventários permitem conferir
o material sem modificar manifests e recibos históricos.
A pasta `validacao_indice/` nesse arquivo conserva a cópia usada na prova de
reprodução; `operacao/` guarda os scripts pontuais desta organização. Nenhuma
das duas é uma fonte de trabalho. A prova de reprodução usou o índice Git
antes do commit; o relatório `git-index-plan.json` preserva esse marco.

## Limites

O readback confirmou a versão 2 e o fingerprint
`66f8808cf83902ff6c7fd277937bf8e0671482058f540f3ea9c1ec8c5a182800`.
Confere schema, chaves, contagens e proveniência, sem reconciliação célula a
célula. Não houve carga, DROP, migração, alteração de credenciais, inferência
externa ou score científico. Resultados brutos, splits, pesos e artigos não
foram reescritos. As alterações de README em FineTuning atualizam somente a
localização do arquivo histórico.
