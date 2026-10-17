# Pacotes locais de evidências da DW (SPEC-007)

Este exportador prepara entradas candidatas para o cenário A da [arquitetura de avaliação](../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md). Ele valida um manifesto JSON v1, executa `dw.cli.verify()` na carga existente e depois somente as cinco consultas fixas compartilhadas em `BancoModeloUse/dw/fixed_queries.py`. Não carrega bancos, chama LLM ou produz resposta, gold set, rubrica e pontuação.

## Execução

Use o ambiente Python local configurado em [BancoModeloUse/README.md](../BancoModeloUse/README.md) e o cluster isolado já carregado em `127.0.0.1:5544`. O início do cluster é uma operação local explícita; `export.py` apenas lê os três bancos e grava arquivos de pacote no diretório de saída.

```powershell
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py start
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/dw/cli.py verify
BancoModeloUse/.venv/Scripts/python.exe model_evaluation/export.py model_evaluation/examples/cases_2020.json --output-dir model_evaluation/.local/packets-dw-review-2026-10-16
```

O diretório padrão `model_evaluation/.local/packets/` é ignorado pelo Git. `--output-dir` permite escolher outro diretório. Cada `case_id` produz `<case_id>.json`. O CLI informa caminho, estado `created` ou `reused` e SHA-256 do corpo. O exemplo integrado reúne `product(2020, 1000001)` e `financial(2020)`; a segunda consulta retorna `no_observation`, que não deve ser interpretado como zero.

Se `BancoModeloUse/dw/fixed_queries.py` mudar depois de um pacote ser criado, `query_code_sha256` muda e o mesmo `case_id` no diretório antigo será recusado. Preserve o pacote antigo e use `--output-dir` para uma nova versão; essa recusa impede substituir silenciosamente a evidência histórica. Pacotes anteriores à extração das consultas pela SPEC-009 mantêm seus hashes históricos e não são reescritos.

## Contrato

- Entrada: [schema do manifesto](schemas/cases_manifest.schema.json), com `schema_version: 1`, `cases[]` e consultas ordenadas. Os nomes permitidos são `machine`, `product`, `financial`, `quality` e `material`; o ano deve ser 2015–2026. `financial` não aceita `id`; as demais exigem ID positivo. Campos desconhecidos, IDs de caso duplicados, JSON com chave duplicada, Unicode inválido na pergunta e filtros extras são rejeitados antes do acesso ao banco.
- Saída: [schema do pacote](schemas/evidence_packet.schema.json). O envelope contém `body` e `sha256`, calculado sobre os bytes JSON canônicos do corpo (`sort_keys`, separadores compactos, UTF-8, `ensure_ascii=False`, `allow_nan=False`). Sem timestamp. `source_snapshot` registra schema e fingerprint; para novos pacotes, `query_code_sha256` identifica os bytes de `BancoModeloUse/dw/fixed_queries.py`. `quality_summary.scope = global_dw_load` separa flags globais de cada resultado. O schema fecha filtros, cobertura e linhas por tipo de consulta; `verify_packet_bytes()` confere também checksum, bytes canônicos, igualdade entre filtros e metadados e contagem de linhas, relações que o JSON Schema não compara sozinho.
- Os itens mantêm ordem do manifesto; as linhas preservam a ordem fixa retornada pela DW. Cada item traz filtros, grão, tabelas de origem, fórmula, unidade, cobertura, linhas e ressalva de interpretação. O pacote não embute todos os IDs contribuintes de um agregado. Use `dw.cli.contributors` com consulta/ano/ID da linha para paginar os IDs e `dw.cli.trace` para ver DW/raw/public de cada fato.
- Limites: 5 consultas, 200 linhas somadas e 512 KiB por pacote. Excedê-los falha sem truncamento. O lote é preparado antes de publicar. Arquivos existentes com bytes idênticos são reutilizados sem regravação; divergência ou arquivo parcial gera erro e preserva o anterior. Arquivos novos são publicados por criação atômica no mesmo sistema de arquivos.

Para validar o schema e o comportamento sem PostgreSQL:

```powershell
BancoModeloUse/.venv/Scripts/python.exe -m pip install -r model_evaluation/requirements-test.txt
BancoModeloUse/.venv/Scripts/python.exe -m unittest discover -s model_evaluation/tests -v
```

Esses pacotes são **candidatos locais**. As [revisões independentes da DW](../specs/active/SPEC-006/evidence/review.json) e [deste exportador](../specs/active/SPEC-007/evidence/review.json) foram aprovadas em 16/10/2026 para o escopo local. A seleção científica dos casos e do gold set, o harness por API e a avaliação de modelos ainda exigem trabalho separado. A Bancada exploratória em `inference_api/` consome estes pacotes no modo `dw_snapshot` ou consulta a DW no modo `dw_tools`; não consulta os dois bancos de origem em novos runs.

## Consumo na Bancada (SPEC-009)

O servidor lista arquivos privados por `GET /api/bench/evidence-packets` após
autenticação, valida bytes canônicos, schema e checksum com
`verify_packet_bytes`, e exige `case_id` junto ao SHA-256 do corpo. O run
`dw_snapshot` usa os bytes já exportados, sem nova consulta à DW; pergunta e
domínio vêm do corpo. A listagem vazia indica que falta preparar pacotes.
Esses pacotes continuam candidatos, sem status de caso científico aprovado.
