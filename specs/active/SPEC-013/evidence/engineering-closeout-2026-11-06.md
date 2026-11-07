# Fechamento da engenharia — SPEC-013 contrato 3 — 06/11/2026

Escopo autorizado: concluir a engenharia, corrigir os achados técnicos e obter
auditoria global Astra. A matriz científica e a adjudicação das respostas são
posteriores, conforme `engineering-scope-2026-11-05.md`. Sem novas chamadas
externas neste fechamento. Checkout compartilhado sem commit novo; base
`13d7df5c748f79387d34f39cd30b6cf82c96c869`. Artefatos antigos preservados.

## Correções e verificação

1. **Entrada completa:** os adaptadores medem os bytes do corpo HTTP serializado
   antes do transporte. Inclui instruções, schemas, envelope e parâmetros.
   Registro `http_json_body_utf8_v1` tem tamanho, limite e SHA-256. Overflow é
   explícito e terminal, sem truncamento. HTTP, timeout, conexão e stream inválido
   mantêm o recibo da tentativa; não afirmam recebimento remoto nem repetem envio.
2. **Comparação:** contratos, mapas, limites, protocolo, política de contexto,
   código executável e cargas são condições fixas. Identidade do candidato e
   trajetórias/respostas ficam separadas. Manifestos das fontes industrial e
   financeira são lidos antes/depois, para todas as fontes habilitadas, sem
   depender das rotas escolhidas. Proveniência conflitante é divergência;
   metadados incompletos são compatibilidade indeterminada. Identifica a carga
   registrada; não é prova de inexistência de edição manual no banco.
3. **Revisão científica futura:** adjudicação exige `run_sha256` do run integral
   recebido, além de caso/hash e identificação. Alteração de resposta, evidência,
   trace ou configuração invalida o parecer. `prepare_run_review.py` gera pacote
   pendente privado, não aprovação. Sem gabarito nos agentes.

O diagrama vigente mantém os mesmos papéis e decisões: são controles internos,
sem novo agente ou novo caminho de consulta. Documentação antecedeu o código em
`../engineering-closeout-contract.md`.

| Gate | Evidência observada |
|---|---|
| Backend completo | 143 testes, zero falhas, oito pulados por ambiente; `unittest discover -s inference_api/tests -q` |
| Avaliador completo | 21 testes aprovados; `unittest discover -s model_evaluation/tests -q` |
| Frontend | 16 testes aprovados; typecheck, lint e build aprovados pelo wrapper `validate_frontend.py` |
| HTTP + PostgreSQL local | Autenticação, idempotência, job, snapshot e limpeza dos próprios UUIDs aprovados; modelo programado, oito chamadas e duas consultas fictícias |
| Três bancos reais locais | Catálogo aprovado, 11 chamadas programadas, três leituras, linhas 1/13/13, `answered_unverified`; zero provedor |
| Manifestos das fontes | Industrial nove arquivos; financeiro seis arquivos; leitor restrito e transação somente leitura |
| Replay do ensaio real | 12 saídas gravadas, três resultados gravados, mesmas entradas de papel, resposta e evidências; adaptador real com transporte mockado |
| Corpo HTTP no replay | Máximo 22.760 bytes, limite 32.768; tamanho/hash conferidos contra os bytes passados ao transporte mockado |
| Replay completo do serviço atual | 12 respostas gravadas pelo adaptador mockado, três consultas reais, resposta/evidência idênticas; manifestos antes/depois iguais e 33 arquivos no contrato executável; sem persistir um novo run de pesquisa |
| Gabaritos e referências | Recibo dos nove casos íntegro; duas referências reexecutadas com hashes exatamente iguais aos revisados |
| UI autenticada | Histórico e comparação abertos no Chrome; runs antigos mostram falta de metadados e diferenças dos contratos/mapas, sem inferir compatibilidade |
| Whitespace | `git diff --check` aprovado; avisos LF/CRLF não são falhas |

Os oito testes pulados não são descritos como executados. Integrações locais
acima complementam a suíte. VAL-015 usa o ensaio real já registrado em
`specialist-query-openai-ui-2026-11-06.md`: run
`769ecfc1-62a0-42a1-9fdf-95bbe9f2ea36`, OpenAI `gpt-6-luna`, três domínios,
12 chamadas e correção do plano financeiro. Replay não é nova inferência.

## Artefatos privados preservados

Todos em `inference_api/.local/`, salvo indicação:

- `spec013-contract3-openai-ui-20261106.json`: export original;
  SHA-256 `8ae24c1cd61e9b2e2ebf60ce3c9542d79f71145d2a8cc22fca2dffc4d25fe356`.
- `spec013-closeout-replay-final-20261106.json`: replay final;
  SHA-256 `9b28a225ca1f802a2919c9d06c7aec578003fd3256dd4cbede0c162499f5768f`.
- `spec013-closeout-chain-20261106.json`: três bancos com modelo programado.
- `spec013-closeout-http-fixed-20261106.json`: HTTP/DB e cleanup aprovado.
- `spec013-closeout-source-manifests-20261106.json`: manifestos completos.
  Industrial `00e7237eff997ee74ab670002af10123e1e73dd0687ddf32c46260789eaf13b5`;
  financeiro `48aeb1cba4b18dcef3909656622ac22d56a73e935ae65445e8f00bcbc9169073`.
- `spec013-closeout-service-replay-20261106.json`: serviço completo, queries reais e modelo gravado;
  SHA-256 `56e9047e1e67695136b5dd9de5e634c73b0aa6dd40f541922f97cf97ace5cf7f`.
- `spec013-closeout-comparison-final-20261106.png`: screenshot do aviso na versão final da comparação; screenshot anterior preservado.
- `model_evaluation/.local/spec013-closeout-dw-reference-20261106.json`:
  SHA-256 `04769e61cf5095ff8372b52e91d9cecbdfa65b61a468a7d73b6628c88cd22afd`.
- `model_evaluation/.local/spec013-closeout-detail-reference-20261106.json`:
  SHA-256 `33c8005b327e1209c6bc49feefff702daf9af0e49b9f85f9a3abdfb5743f69bb`.

As referências usam `BancoModeloUse/.venv/Scripts/python.exe`; a venv da API não
tem SQLAlchemy. Ambas executam somente leituras. Aprovações anteriores mantidas.

## Intercorrências e limites

- O script HTTP ainda esperava 12 chamadas da fixture antiga; o contrato 3 faz
  oito. Corrigido para exigir a quantidade de saídas programadas, duas consultas
  e `answered_unverified`. Primeiro relatório com falha preservado.
- Uma tentativa HTTP de recusa 401 foi interrompida por WinError 10053 antes de
  criar job. Repetição manual e suíte completa passaram; não houve retry de
  provedor. A causa dessa intermitência Windows não foi comprovada. Isso não
  equivale à queda histórica do PostgreSQL, cuja causa também não foi atribuída.
- A primeira execução do novo teste de falhas OpenAI usou chave fictícia curta,
  recusada antes do transporte. Ajustada a fixture ao contrato de formato;
  nenhum segredo real foi usado pelo teste.
- A auditoria global encontrou e exigiu os complementos de manifesto de detalhe,
  abrangência dos hashes executáveis e recibos em falhas; todos receberam testes.

`completion.json` consolida AC/VAL. `review.json` é o parecer independente:
somente sua aprovação permite marcar Done técnico. Não houve score científico,
reescrita de runs antigos, alteração das aprovações ou ampliação de permissões.
