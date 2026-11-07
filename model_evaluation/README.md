> **SPEC-014 concluída em engenharia local (06/11/2026):** preflight do catálogo e bloqueio de fonte corrigidos e aprovados em nova revisão independente. Não há nova inferência remota nem pontuação científica. Ver `specs/active/SPEC-014/evidence/local-integration.json`.

# Pacotes locais de evidências da DW (SPEC-007)


**SPEC-013 · Done de engenharia em 06/11/2026:** [parecer global Astra aprovado](../specs/active/SPEC-013/evidence/review.json),
[completion](../specs/active/SPEC-013/evidence/completion.json) e [validação final](../specs/active/SPEC-013/evidence/engineering-closeout-2026-11-06.md).
O harness de cinco papéis está implementado na Bancada, com leitura controlada
na DW, industrial e financeiro. O ensaio real completo, testes locais, replays
e histórico foram verificados. A matriz científica e a revisão humana de cada
resposta continuam posteriores, sem score atribuído. Este estado substitui
as descrições históricas de implementação pendente abaixo.

**Revisão de runs — 06/11/2026:** `harness_score.evaluate` exige também
`run_sha256`, calculado sobre o objeto integral recebido (JSON canônico). Alterar
resposta, evidências, trace ou configurações presentes invalida a adjudicação.
Para preparar a futura revisão científica, use arquivos privados e um destino novo:

```powershell
inference_api/.venv/Scripts/python.exe model_evaluation/prepare_run_review.py model_evaluation/.local/run.json model_evaluation/.local/case.json --output model_evaluation/.local/review-bundle.json
```

`run.json` é o resultado integral do harness passado a `evaluate`, não somente
o texto da resposta; `case.json` é o contrato privado aprovado compatível.
O pacote contém run, caso, checks e `adjudication_template` pendente. A pessoa
revisora preenche decisão, identificação, data, justificativa e notas; o comando
não aprova, não envia gabaritos, não consulta banco e não chama modelo.
Revisões antigas sem hash não são aceitas. Este gate científico é posterior
à conclusão de engenharia da SPEC-013.

**06/11/2026:** o [contrato 3 da SPEC-013](../specs/active/SPEC-013/specialist-query-contract.md)
substitui o Planejador pelo Especialista que constrói a consulta. Os hashes dos
contratos/mapas mudaram. A matriz científica antiga permanece congelada nos
hashes revisados; não é evidência da arquitetura nova e não deve ser atualizada
silenciosamente. A mudança atual foi testada localmente, sem score científico.


**SPEC-013 em 02/11/2026:** o executor da matriz Groq/Qwen usa protocolo v7
e rótulos `v7-*`, conforme [evidência da entrada do Revisor](../specs/active/SPEC-013/evidence/m2-reviewer-question-context-v7-2026-11-02.md).
Os runs anteriores são diagnósticos. Cada run concluído continua
`awaiting_run_review` até adjudicação humana da resposta e dos cálculos.
O protocolo v7 passou localmente, mas a matriz real ainda não começou: dois
diagnósticos Groq v7 foram limitados por HTTP 429 antes da consulta, conforme
o recibo de evidência acima. Nenhuma nota científica foi atribuída.

Em 02/11/2026, a SPEC-013 acrescentou `--dw-v2` para a carga local V2 de
fingerprint conhecido. O pacote mantém o envelope v1 e distingue
`source_snapshot.schema_version: 2` e
`quality_summary.scope: local_dw_v2_readback`. O readback V2 confere a migração,
167 partições de origem e a divisão de `fact_downtime` em 1.200 paradas
originais e 90 geradas. Ele não faz a verificação completa dos 166 CSVs
executada pelo caminho histórico V1. Use um diretório de saída novo:

```powershell
BancoModeloUse/.venv/Scripts/python.exe model_evaluation/export.py model_evaluation/examples/cases_2020.json --dw-v2 --output-dir model_evaluation/.local/packets-dw-v2
```

Um [ensaio local do caminho V2](../specs/active/SPEC-013/evidence/m2-dw-v2-packet-export-2026-11-02.md)
produziu um pacote candidato com `product` observado e `financial` sem
observação; nenhum gabarito ou modelo foi envolvido. Pacotes V1 antigos
continuam aceitos por `verify_packet_bytes()`.

Este exportador prepara entradas candidatas para o cenário A da [arquitetura de avaliação](../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md). Ele valida um manifesto JSON v1 e executa somente as cinco consultas fixas compartilhadas em `BancoModeloUse/dw/fixed_queries.py`. Por padrão, usa `dw.cli.verify()` para a DW V1; `--dw-v2` usa o readback local delimitado descrito acima. Não carrega bancos, chama LLM ou produz resposta, gold set, rubrica e pontuação.

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

## Avaliador isolado da SPEC-013 (M3 parcial)

`harness_score.py` recebe um snapshot concluído do harness **depois** da
resposta. O gabarito nunca entra no motor A1–A5. Sem caso aprovado por revisão
humana, devolve `not_scored`; sem revisão do run, devolve
`awaiting_run_review` e apenas checks automáticos, sem pontuação final.
Um caso aprovado precisa de `case_id`, SHA-256 da pergunta, hashes dos mapas,
rotas equivalentes aceitas e recibo de revisão (`reviewer`, `reviewed_at`,
`evidence_receipt`), além de `prepared_by` distinto da pessoa revisora e das
fontes que a resposta precisa citar. Uma revisão do run identifica o mesmo caso/hash e run,
registra autor, data, justificativa e decisões binárias sobre cálculo e
conclusão. Hash divergente ou referência duplicada é erro de contrato.

Os checks automáticos conferem a rota de fontes consultadas e a integridade
das referências a resultados no estado esperado. Eles **não** determinam
se um número calculado está correto nem se uma conclusão científica é válida.
Para casos cuja referência aprovada espera `no_observation`, a citação de um
resultado vazio com esse estado também é evidência válida; ela não equivale a
zero medido. O contrato do caso declara o estado esperado por fonte.
As quatro dimensões ficam separadas; não há média ou ranking. Os testes em
`tests/test_harness_score.py` usam apenas fixture inventada. O conteúdo dos
nove casos piloto foi [aprovado pelo pesquisador](../specs/active/SPEC-013/evidence/m3-human-case-content-approval-2026-11-01.md)
na versão e no hash do pacote revisado. Ainda faltam manifests executáveis
vinculados às referências, revisão das respostas de cada run, repetições e
revisão independente antes de qualquer comparação científica.

`spec013_candidate_profile.py` levanta somente anos, IDs e contagens da DW em
transação `READ ONLY`, sem ler valores de linhas ou chamar provedor. O
[perfil v3 de 01/11](../specs/active/SPEC-013/evidence/m3-candidate-profile-2026-11-01-v3.json)
sustenta uma [matriz de nove perguntas candidatas](../specs/active/SPEC-013/evidence/m3-case-matrix-draft-2026-11-01.md).
Ela registra a seleção inicial. O conteúdo dos nove casos foi aprovado depois,
com recibo e hash próprios; o manifesto executável ainda não está pronto para
pontuação.

`spec013_reference_draft.py` reexecuta seis consultas DW do rascunho em
transação `READ ONLY`, exige o fingerprint da carga no catálogo candidato e
grava os valores apenas em `model_evaluation/.local/` (ignorado pelo Git). O
[recibo sem valores](../specs/active/SPEC-013/evidence/m3-dw-reference-draft-2026-11-01.md)
registra hash, contagens e limites. O arquivo privado é um gabarito **rascunho**
e nunca é enviado aos agentes. A preparação detectou e levou à correção de um
`KeyError` em metadados de `financial`; há teste de regressão local.
Um [segundo pacote privado](../specs/active/SPEC-013/evidence/m3-detail-reference-draft-2026-11-01.md)
traz detalhe tipado de paradas geradas e vendas, mais contribuintes da DW,
para preparar as perguntas de aprofundamento. Os dois pacotes são rascunhos
isolados, com hashes e sem revisão científica.
O [pacote de revisão dos nove casos](../specs/active/SPEC-013/evidence/m3-case-review-packet-2026-11-01.md)
aponta para um Markdown privado em `.local/` com perguntas, valores de
referência, ressalvas e pendências por caso. O pesquisador aprovou o conteúdo
dos nove IDs enumerados na solicitação, sem alterações, em um único recibo
que individualiza as decisões. O pacote privado permanece intacto com o
mesmo SHA-256. Essa aprovação não pontua respostas de modelos.

O artefato de M3 é um **manifesto executável privado**, derivado dos
bytes do pacote aprovado e das duas referências já inventariadas. Cada caso
deve vincular pergunta literal e hash, fingerprint da DW, hash do catálogo e
do código de consulta, planos tipados/filtros, hashes dos resultados de
referência, critérios numéricos e rotas aceitáveis. O gerador deve falhar se
qualquer byte aprovado mudar e manter os valores em `.local/`. Mesmo após a
geração, o manifesto não habilita score até a conferência do vínculo técnico
e a revisão posterior de cada run, conforme o protocolo humano.
Em 02/11/2026, o [vínculo dos nove casos e o replay local das referências](../specs/active/SPEC-013/evidence/m3-case-contract-binding-2026-11-02.md)
foram registrados. `materialize_spec013_pilot_cases.py` grava o contrato em
`.local/` e confere os hashes do pacote aprovado, do catálogo e do código de
consulta. A versão v3 é a atual; os replays DW e detalhe reproduziram os hashes
das duas referências privadas revisadas. Ela registra também o estado esperado
da evidência por fonte. O estado dos casos v3 continua
`content_approved_pending_execution`, sem score. Uma [versão v4 privada](../specs/active/SPEC-013/evidence/m3-approved-map-binding-2026-11-02.md)
foi vinculada à cópia local habilitada do catálogo, com hashes dos três mapas,
fontes exigidas, campos, filtros e grão conferidos. Ela continua
`approved_map_bound_pending_case_review`; nenhuma resposta foi adjudicada.

Em 02/11, o pesquisador aprovou exatamente a v4 (SHA-256
`27214d0acc5424f11bf9c27e3f4c5ee0be1d977dc169524fceb3a8900fa2018a`).
`activate_spec013_pilot_cases.py` verificou recibo, bytes da v4 e replay do
vínculo aos mapas/referências, preservou a v4 e criou a [v5 privada
aprovada](../specs/active/SPEC-013/evidence/m3-executable-case-activation-2026-11-02.md).
Cada caso pode entrar no avaliador, mas cada run continua aguardando revisão
humana de cálculo e conclusão. Nenhuma nota científica foi gerada.

Historicamente, o executor `run_spec013_pilot_matrix.py` (retirado do fluxo ativo pela SPEC-014) recebia a v5 aprovada, os contratos de
papéis congelados e o Qwen da Groq. `--check-only` confere o lote sem enviar
dados. Na execução, cada caso/repetição ganha um rótulo único e um único POST;
falha ou resultado incerto interrompe a matriz sem nova tentativa. `--resume`
pula somente runs concluídos cujos hashes forem conferidos. Os traces e o
progresso ficam em `.local/`; o score final continua dependente da revisão
humana individual de cálculo e conclusão.
Após a correção do [formato de filtro de intervalo](../specs/active/SPEC-013/evidence/m2-range-filter-contract-v5-2026-11-02.md),
o executor usa hashes de entrada v4/tarefa v5 e rótulos `v5-*`. Os recibos
`i1-r1` e `i2-r1` anteriores permanecem históricos e não entram nessa matriz.

Para preparar novos casos e revisar runs, use o
[protocolo de validação humana](../docs/protocolo_validacao_humana_avaliacao.md)
e a [ficha reutilizável](templates/revisao_humana_caso_e_run.md). Fonte
física, cálculo numérico e checks de JSON não dispensam revisão semântica;
qualquer alteração de pergunta, dado ou referência exige nova versão e
revisão do artefato afetado.
`verify_human_review_receipt.py` confere os hashes dos arquivos e a lista de
IDs de um recibo; não autentica quem respondeu nem transforma aprovação de
conteúdo em score. O teste de regressão altera os bytes revisados em fixture e
confirma que o recibo deixa de validar.
