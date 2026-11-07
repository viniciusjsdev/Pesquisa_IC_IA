# Leitura da carga canônica existente — 01/11/2026

Escopo: verificação **somente leitura** dos três bancos locais já carregados.
Não houve ingestão, migração, escrita em banco, inferência ou commit nesta
verificação. O verificador e o manifesto canônico estão no worktree separado
`C:\Users\vinic\.codex\worktrees\datamind-dw-rebuild\Pesquisa_IC_IA`; o
cluster lido é o de `D:\Projetos\Github_ViniciusJ\Pesquisa_IC_IA\BancoModeloUse`.

Comando executado com a venv `BancoModeloUse/.venv` deste checkout:

```powershell
& 'D:\Projetos\Github_ViniciusJ\Pesquisa_IC_IA\BancoModeloUse\.venv\Scripts\python.exe' 'C:\Users\vinic\.codex\worktrees\datamind-dw-rebuild\Pesquisa_IC_IA\BancoModeloUse\scripts\verify_canonical_load.py' --database-home 'D:\Projetos\Github_ViniciusJ\Pesquisa_IC_IA\BancoModeloUse'
```

O comando terminou com código 0 e gerou o [relatório JSON](canonical-load-readback-2026-11-01.json):

- Industrial: 38 tabelas tipadas, 113 partições CSV, 1.561.794 linhas, 12 FKs físicas.
- Financeiro: 18 tabelas tipadas, 54 partições CSV, 3.872 linhas, 1 FK física.
- DW: 35 tabelas, 167 partições de origem, 1.565.666 linhas de origem; 20 tabelas novas conferidas contra contrato físico.
- `fact_downtime`: 1.290 linhas, sendo 1.200 de `paradas_maquinas` e 90 de `paradas_maquinas_geradas`.
- Versão 2 da DW com fingerprint `66f8808cf83902ff6c7fd277937bf8e0671482058f540f3ea9c1ec8c5a182800`.

O verificador compara schema físico, chaves, contagens, partições e proveniência
do manifesto. Ele não compara cada valor de cada linha com o CSV original. A
leitura confirma o estado dessa carga local; não aprova mapas semânticos,
consultas multiagente nem gabaritos da pesquisa.
