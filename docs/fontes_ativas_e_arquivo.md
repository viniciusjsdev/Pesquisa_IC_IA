# Fonte ativa e arquivo histórico

Conferência de 07/11/2026, partindo de `main` em `b2cfb79`. Esta organização
integra arquivos locais da DW V2; não é uma nova carga nem avaliação científica.

## Onde trabalhar

**Projeto principal e única fonte de trabalho:**
`D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA`.

| Material | Fonte vigente |
| --- | --- |
| Bancada, API, harness e contratos | Este checkout: `inference_api/`, `model_evaluation/` e `specs/`. |
| Dados da DW V2 | Os 166 CSVs listados em [manifesto_canonico.json](../BancoModeloUse/dados_complementares_datamind/manifesto_canonico.json), com classes e hashes. |
| Estrutura e ingestão V2 | [Contrato](../BancoModeloUse/dados_complementares_datamind/contrato_tabelas_canonicas.json), [DER](../BancoModeloUse/docs/datamind_erd_canonical.drawio.xml) e [carregador](../BancoModeloUse/scripts/canonical_ingest.py), todos neste checkout. |
| Banco efetivamente consultado | Cluster isolado `127.0.0.1:5544`, em `BancoModeloUse/.local/postgres`: `db_industrial`, `db_financeiro`, `db_pesquisa_dw`. |
| FineTuning | Fontes técnicas definidas em [FineTuning/AGENTS.md](../FineTuning/AGENTS.md); dados congelados, adapters e resultados preservados. |
| Texto editorial do artigo | [Google Doc canônico](https://docs.google.com/document/d/1LExZ17IkPXIKYGCHLEJ3mEZSsCU2It1X/edit); arquivos locais são snapshots. |

O banco da aplicação (`db_inference_app`) guarda jobs/histórico e não é uma
fonte de CSV. O banco `db_datamind_dw` é legado. O Docker pode conter uma cópia
separada com fixtures: não presumir que seja a carga V2 desta máquina.

## O que foi reconciliado

O worktree `C:/Users/vinic/.codex/worktrees/datamind-dw-rebuild/Pesquisa_IC_IA`
continha a V2 ainda sem commit sobre `13d7df5`. Seus CSVs, manifesto, contrato,
DER, carregador, verificador e testes foram integrados ao projeto principal.
O conjunto tem 69 originais intactos, seis originais corrigidos anteriormente,
39 complementares, nove referências derivadas e 43 sintéticos derivados.
Os seis CSVs corrigidos foram copiados byte a byte da V2 já usada no banco;
as versões anteriores deste checkout foram preservadas no arquivo.

Doze CSVs anteriores (nove de IA e três de energia por horário substituídos
pelos de turno) saíram da árvore ativa, com cópias e SHA-256 registrados.
A consulta compartilhada `dw/fixed_queries.py` foi mantida na versão mais
recente do principal; ela já continha correções posteriores ao worktree.
`.gitattributes` impede normalização de finais de linha dos CSVs, manifesto
e contrato, para preservar a identidade exata em futuros checkouts Git.

O worktree antigo foi preservado e identificado como histórico. Não é mais
necessário para executar os comandos atuais. Não desenvolver nem regenerar
dados nele. Sua remoção futura depende da política de retenção do usuário.

## Arquivo de segurança

Diretório único para os arquivos retirados da pasta de projetos:
`D:/Projetos/Github_ViniciusJ/_arquivo_Pesquisa_IC_IA`.

| Local dentro do arquivo | Conteúdo e finalidade |
| --- | --- |
| `finetuning/` | Arquivo de 11/10: checkpoints intermediários, fontes antigas, renders e versões editoriais. Nome curto para compatibilidade com caminhos Windows. |
| `historico/Pesquisa_IC_IA_legacy_archive_20261011/` | Código, documentação e dados retirados do fluxo ativo. |
| `historico/Pesquisa_IC_IA_untracked_archive_2026-10-11/` | `artifacts/`, `tmp/` e seu manifesto histórico. |
| `historico/Pesquisa_IC_IA_spec014_baseline_01a1b284/` | Snapshot anterior à implementação da SPEC-014. |
| `historico/IC_4Semestre_FineTuning/` | Repositório de 2025 completo, incluindo `.git`. Não é o projeto atual. |
| `scripts_pontuais_2026-10-11/` | Quatro scripts soltos de edição, validação e arquivamento daquela etapa. Não executar como rotina atual. |
| `reconciliacao_2026-11-07/` | Inventários, hashes, arquivos anteriores do principal, patch e snapshot das alterações do worktree e recibos da organização. |

Os caminhos antigos das cinco pastas continuam como **junctions ocultas de
compatibilidade**, não cópias. Isso preserva caminhos absolutos de evidências
e manifests históricos sem editar seu conteúdo. Ativar “itens ocultos” no
Explorer pode mostrá-los. Não apagar arquivos através desses atalhos: eles
acessam o arquivo real. O índice é `README.md` na raiz do arquivo, e a relação
origem/destino está em `reconciliacao_2026-11-07/archive_inventory.json`.
Os quatro scripts não tinham consumidores encontrados no projeto; seus novos
caminhos estão no mesmo inventário. Não há cópias ativas na pasta de projetos.

Backups anteriores do PostgreSQL e das correções também permanecem nos locais
já citados nas evidências: `C:/Users/vinic/.codex/archives/` sob os nomes
`datamind_db_before_canonical_20261029`, `datamind_material_lot_20261029` e
`datamind_operational_unit_20261029`. São backups externos, não fontes ativas.
O índice do arquivo também aponta para eles. `Bancos.txt` permaneceu na pasta
de projetos porque não foi estabelecido vínculo com esta pesquisa.

## Verificação e limites

Ver [evidência da reconciliação](evidence/organizacao-2026-11-07/README.md).
O fingerprint esperado da V2 é
`66f8808cf83902ff6c7fd277937bf8e0671482058f540f3ea9c1ec8c5a182800`.
O plano confere arquivos e contrato offline; o readback confere schema,
chaves, contagens e proveniência no banco. Não é comparação célula a célula,
aprovação semântica dos dados ou pontuação de respostas de modelos.

Documentos e evidências datados de outubro que falam em “outro worktree” ou
em apenas 123 CSVs descrevem o estado anterior; esta página e os READMEs atuais
definem os caminhos de trabalho a partir de 07/11/2026.
