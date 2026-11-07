# Dados e bancos ativos — DW V2

**Fonte vigente em 07/11/2026:** este diretório do projeto principal contém
todos os **166 CSVs** usados na carga canônica V2, seu manifesto, contrato,
DER e scripts. O worktree `datamind-dw-rebuild` foi integrado e passou a
histórico de segurança. [Mapa completo](../docs/fontes_ativas_e_arquivo.md).

## Fontes de verdade

1. [Manifesto canônico](dados_complementares_datamind/manifesto_canonico.json): caminhos, classes, linhas e SHA-256 de cada CSV.
2. [Contrato de tabelas](dados_complementares_datamind/contrato_tabelas_canonicas.json) e [DER salvo](docs/datamind_erd_canonical.drawio.xml): 56 tabelas de origem e estrutura da DW.
3. [Ingestão](scripts/canonical_ingest.py), [validação offline](scripts/validate_canonical_csvs.py) e [verificação da carga](scripts/verify_canonical_load.py).
4. [Readback da reconciliação](../docs/evidence/organizacao-2026-11-07/canonical-readback.json): estado consultado no banco nesta integração.

`dados_simulados/` contém 75 arquivos: 69 preservados e seis corrigidos em
29/10, com colunas que registram os valores anteriores. Os outros 91 arquivos
estão em `dados_complementares_datamind/`: 39 complementares, nove referências
derivadas e 43 sintéticos derivados. O [README dos complementares](dados_complementares_datamind/README.md)
explica as correções e os limites. Não regenerar nem editar CSVs para ajustar
um teste. As versões anteriores estão preservadas fora da árvore ativa.

## Banco usado pela pesquisa

- Cluster PostgreSQL isolado: `127.0.0.1:5544`, diretório `BancoModeloUse/.local/postgres`.
- `db_industrial`: 38 tabelas tipadas; `db_financeiro`: 18.
- `db_pesquisa_dw`: schema `dw`, 35 tabelas, versão 2.
- Credenciais: `.env.local`, ignorado pelo Git. Não publicar nem copiar para documentação.
- `db_inference_app` guarda a aplicação; `db_datamind_dw` é legado.
- O PostgreSQL do Docker é outra cópia. Seus fixtures não comprovam a carga V2.

A ingestão mantém schemas brutos `raw_p0..p2`, tabelas tipadas e proveniência.
São 167 partições de 166 arquivos, com 1.565.666 linhas de origem. A DW contém
1.200 paradas originais e 90 geradas, identificáveis por fonte. O manifesto e
o contrato fixam o fingerprint
`66f8808cf83902ff6c7fd277937bf8e0671482058f540f3ea9c1ec8c5a182800`.

## Uso cotidiano no checkout principal

Na raiz do projeto, usando a venv já existente:

```powershell
# Validação offline: arquivos, hashes, tipos, chaves, DER e contrato.
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/canonical_ingest.py plan

# Estado do cluster existente. start apenas inicia; não recarrega os bancos.
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py status
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py start

# Verificação dos três bancos, somente leitura.
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/verify_canonical_load.py --database-home BancoModeloUse

# Consultas fixas e rastreáveis.
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py query machine --year 2020 --id 1000001
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py query financial --year 2020

# Testes offline do contrato e dos comandos.
BancoModeloUse/.venv/Scripts/python.exe -m unittest discover -s BancoModeloUse/scripts/tests -v
```

`bootstrap_local.py --verify` e `dw/cli.py verify` encaminham para o mesmo
verificador V2 quando há manifesto canônico. O JSON informa `database_writes: false`.
Esses atalhos não executam a reconciliação célula a célula da antiga V1.
`bootstrap_local.py` sem `--verify` e `dw/cli.py build` recusam a carga parcial V1.

Em um ambiente novo, criar a venv com `python -m venv BancoModeloUse/.venv`
e instalar `BancoModeloUse/requirements-local.txt`. O gerenciador pode criar
um cluster vazio local; isso não restaura a carga atual. Para uma nova carga,
revisar primeiro `canonical_ingest.py plan`; `load --database-home BancoModeloUse`
é uma ação explícita de criação e recusa bancos existentes. Não é rotina de
inicialização e não foi executado nesta reconciliação. Nunca apagar bancos
para contornar uma divergência.

## Limites e histórico

A verificação atual confere schema, chaves, hashes registrados, contagens e
proveniência. Não compara todos os valores armazenados com cada célula dos
CSVs, não valida causalidade e não atribui score científico. Dados derivados
e simulados permanecem classificados como tais.

O protocolo de revisão humana continua em [docs/protocolo_validacao_humana_avaliacao.md](../docs/protocolo_validacao_humana_avaliacao.md).
O harness implementado está na API da Bancada; a arquitetura científica é
[arquitetura_avaliacao_modelos.md](docs/arquitetura_avaliacao_modelos.md).
As descrições da carga V1 de 75 CSVs são históricas da SPEC-006, preservadas
no Git e no arquivo externo. A [reconciliação do DER de outubro](docs/reconciliacao_der_2026-10-31.md)
e a [carga de 31/10](docs/carga_canonica_2026-10-31.md) mantêm sua proveniência;
os caminhos de trabalho atuais são os desta página.
