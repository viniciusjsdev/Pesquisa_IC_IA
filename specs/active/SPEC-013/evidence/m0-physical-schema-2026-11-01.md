# Inventário físico dos três schemas — 01/11/2026

**Tipo de evidência:** leitura somente de metadados do cluster já carregado,
`127.0.0.1:5544`. Não houve ingestão, alteração de banco, consulta de linhas
de pesquisa ou inferência. O programa confere o `data_directory` do cluster
isolado, usa `SET TRANSACTION READ ONLY` e extrai nomes, tipos, nulabilidade,
PKs, FKs, unicidade e a versão/fingerprint da DW.

Comando executado da raiz:

```powershell
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/export_schema_inventory.py --output specs/active/SPEC-013/evidence/m0-physical-schema-2026-11-01.json
```

O [JSON gerado](m0-physical-schema-2026-11-01.json) registra SHA-256 lógico
`ca7f44f371fe5403b203d11bbc82a0d01553b5d4783d34cc6f9ebdd750343b62`.
Foram encontrados 39 objetos `public` industriais, 19 financeiros e 35 tabelas
`dw`. Os dois schemas de origem incluem `canonical_source_file`, uma tabela
auxiliar além das 38/18 tabelas tipadas de origem já verificadas. A DW declara
migração V2 e fingerprint
`66f8808cf83902ff6c7fd277937bf8e0671482058f540f3ea9c1ec8c5a182800`.

Serializando cada domínio em JSON compacto, ainda sem descrições semânticas:
DW **53.047 bytes/362 colunas**, industrial **37.418 bytes/314 colunas** e
financeiro **17.202 bytes/147 colunas**. O limite do protótipo M1 é 16.384
bytes para o envelope inteiro. Logo, injetar o schema físico completo em uma
chamada A2a não cabe nem para o domínio financeiro. Instruções, pergunta,
evidência e significados das colunas aumentariam esse tamanho.

O inventário permite conferir se um mapa proposto cita colunas e restrições
existentes. Ele **não** determina grão, unidade, cobertura real, validade de
joins, fonte habilitada nem qualidade dos dados. Relações físicas ausentes não
podem ser inferidas por nomes semelhantes; relações físicas presentes ainda
precisam de revisão semântica. A proposta DEC-001 continua sem aprovação.
