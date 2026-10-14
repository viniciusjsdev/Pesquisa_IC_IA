# Inferência compartilhada: primeira implementação local

**Estado em 14/10/2026 (checkout `ad6edcb` mais mudanças locais sem commit):**
cadeia exploratória determinística da SPEC-001 implementada localmente e aprovada
em revisão independente. Ainda não há serving na RunPod,
túnel ngrok, verificação de identidade individual ou benchmark científico. A
arquitetura acordada e seus limites estão em
[`../docs/arquitetura_inferencia_compartilhada.md`](../docs/arquitetura_inferencia_compartilhada.md).
As frentes seguintes têm contratos e ordem próprios em
[`../specs/README.md`](../specs/README.md).
O [desenho da avaliação](../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md)
separa raciocínio sobre evidências fixas de pesquisa com tools escolhidas pelo
modelo. A API atual escolhe suas duas consultas pelo escopo declarado pelo
pesquisador; a [SPEC-007](../specs/active/SPEC-007/SPEC.md) prepara pacotes
fixos fora da API e não muda esse comportamento.

## Contrato implementado

- `GET /api/models`: sete aliases candidatos (base e seis adapters), marcados
  disponíveis somente quando aparecem em `GET /v1/models` do vLLM configurado.
  O catálogo local é uma lista de candidatos, não prova de pesos carregados.
- `GET/POST /api/prompts`: revisão imutável de nome, autor e texto do sistema.
  `POST` exige `expected_revision` para recusar salvamentos simultâneos sobre
  a mesma versão. O front permite usar uma revisão ou um rascunho.
- `POST /api/runs`: `author`, `question`, `model_alias`, exatamente um de
  `prompt_revision_id` ou `system_prompt`, `scope` (`financeiro`, `industrial`
  ou `integrado`), `year`, `temperature` e `max_tokens`. O escopo é declarado
  pelo pesquisador; não há classificação automática. Para compatibilidade,
  `evidence_route` aceita isoladamente as duas rotas antigas. `scope` e
  `evidence_route` juntos são inválidos. O campo opcional `tools`, se enviado,
  deve coincidir exatamente com a allowlist do escopo. Campos desconhecidos
  falham antes de consultar as fontes. A escolha do modelo vale só para a chamada.
  A linha da execução é gravada uma vez, após a tentativa; não é reescrita.
- `GET /api/runs` e `GET /api/runs/{id}`: histórico. `POST
  /api/runs/{id}/feedback` anexa feedback humano sem alterar o snapshot.
- A allowlist de ferramentas contém `financeiro_vendas_ano` e
  `industrial_operacoes_ano`, com ano inteiro de 2015 a 2026. `integrado`
  executa ambas para o mesmo ano. SQL é fixo e parametrizado; cada conexão de
  origem usa transação somente leitura, timeout de consulta e limite implícito
  de uma linha agregada. Não se aceita SQL do navegador.
- O servidor escuta somente `127.0.0.1:8765`; a API exige o token
  `INFERENCE_API_TOKEN`. A página não armazena o token e envia chamadas apenas
  ao mesmo host. Um token compartilhado **não comprova autoria individual**;
  o campo `author` é uma identificação declarada pelo usuário.

O snapshot novo usa `schema_version: 2` e os contratos `question_request`,
`route_plan`, `evidence_bundle`, `model_output` e `checks`. Cada item de evidência
registra ID estável (`ferramenta:ano`), fonte, campos, filtros, ano, granularidade,
unidade, valor, fórmula, SQL fixo parametrizado, qualidade e ressalva. O bundle
integrado inclui aviso de associação temporal sem causalidade. O agente de
resposta recebe apenas pergunta, prompt exato e o bundle gravado, além do alias
e parâmetros; o retorno bruto do servidor é preservado em `model_output.serving`.
O verificador confere schema, itens obrigatórios, resposta e IDs citados no
formato `[evidence:financeiro_vendas_ano:2020]`. Verdade numérica e causalidade
ficam `not_checked`.

`answered_unverified` significa apenas resposta gerada e checagem exploratória;
um ID citado inexistente gera check `failed` sem reescrever a resposta. Falhas
ficam distintas como `route_error`, `query_error`, `evidence_error`,
`insufficient_evidence`, `model_error`, `response_error` ou
`verification_error`. Sem evidência obrigatória, a LLM não é chamada. Sem
endpoint/modelo servido, a tentativa guarda o bundle e `model_error`; não se
fabrica resposta. JSON inválido ou resposta fora do contrato do servidor gera
`response_error` e preserva o corpo recebido em `model_output.serving`, inclusive
os bytes originais em Base64. Snapshots anteriores com `schema_version: 1` continuam
legíveis sem migração ou reescrita. As verificações formais, o gold set, a
comparação estruturada, a integração do [DW local v1](../BancoModeloUse/dw/README.md)
e consultas científicas adicionais permanecem
fora desta primeira fatia. A revisão/hash da base e os hashes dos adapters
permanecem ausentes nos snapshots até a configuração e conferência do Pod;
portanto ainda não há reprodução científica de inferência.

## Mapa do código

| Caminho | Responsabilidade atual |
| --- | --- |
| `run.py` e `src/inference_api/server.py` | Entrada por linha de comando, servidor HTTP, rotas e entrega do front. |
| `web/index.html` | Interface local para prompts, modelos, execuções e histórico. |
| `src/inference_api/service.py` | Coordena uma execução e grava seu snapshot final. |
| `src/inference_api/orchestrator.py` | Valida a entrada e planeja as consultas permitidas conforme o escopo declarado. |
| `src/inference_api/evidence.py` | Executa as consultas fixas de leitura e monta o bundle com origem e ressalvas. |
| `src/inference_api/response_agent.py` e `models.py` | Montam a entrada do modelo, consultam o catálogo vLLM e tratam a resposta HTTP. O serving remoto ainda não foi implantado. |
| `src/inference_api/verifier.py` | Confere estrutura e IDs das evidências citadas; não valida verdade numérica ou causalidade. |
| `src/inference_api/contracts.py`, `config.py` e `storage.py` | Contratos versionados, configuração local e persistência de prompts, execuções e feedback. |
| `tests/test_contract.py` | Testes locais dos contratos da SPEC-001. |

O contrato e a revisão independente dessa implementação ficam em
[`specs/active/SPEC-001/`](../specs/active/SPEC-001/SPEC.md).

## Rodar localmente

Use o Python de um ambiente próprio com as dependências de
[`requirements.txt`](requirements.txt). Na raiz do repositório, em PowerShell:

```powershell
BancoModeloUse/.venv/Scripts/python.exe -m venv inference_api/.venv
inference_api/.venv/Scripts/python.exe -m pip install -r inference_api/requirements.txt
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/local_postgres.py start
$env:INFERENCE_API_TOKEN = '<token-local-forte>'
inference_api/.venv/Scripts/python.exe inference_api/run.py init-db
inference_api/.venv/Scripts/python.exe inference_api/run.py serve
```

`init-db` cria apenas `db_inference_app` e suas três tabelas se faltarem.
Ele não recria nem importa as bases de origem. É uma ação explícita, separada
do início do servidor. As credenciais locais são lidas do
`BancoModeloUse/.env.local` ignorado pelo Git; todas as conexões exigem host
`127.0.0.1`, porta `5544` e nomes de bancos conhecidos. Não há fallback para
`localhost:5432`.

Abra `http://127.0.0.1:8765` e digite o token e um identificador de autor.
Sem Pod, o catálogo mostra os modelos indisponíveis. A API pode receber
`INFERENCE_VLLM_URL` HTTPS e, se aplicável, `INFERENCE_VLLM_TOKEN` somente no
ambiente do backend. A URL é a origem do servidor, sem o sufixo `/v1`. O alias do modelo na API remota deve coincidir com o
catálogo; os comandos de serving ainda não estão implementados.

Testes locais sem infraestrutura remota:

```powershell
$env:PYTHONPATH = 'inference_api/src'
inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v
```

**Validação local em 13/10/2026:** a carga existente foi lida, sem nova importação:
o bundle integrado retornou 13 vendas em `db_financeiro.public.vendas` e
35.136 registros em `db_industrial.public.registros_operacao` para 2020.
Os testes locais da SPEC-001 cobrem rotas, limites, falhas, isolamento entre
aliases, payload da LLM e checks parciais. Antes da SPEC-001, o esquema foi criado
no cluster isolado e um teste de integração confirmou revisão de prompt,
conflito de edição, snapshot de erro sem vLLM e feedback; os registros de teste
foram retirados em seguida. O HTTP retornou página 200, catálogo com sete
aliases indisponíveis, 401 sem token e 400 para alias inválido. Três testes de
contrato passaram no ambiente próprio. O cluster foi parado ao fim. Isso é
validação local de leitura e fluxo, não nova carga das fontes nem teste de
inferência remota.

## Segurança e operação pendentes

Não abra o túnel ngrok ainda. Antes do uso compartilhado, implementar e testar
identidade individual, controle de acesso e limites de uso; conferir a proteção
da API remota e os aliases/versões/hashes dos pesos. O servidor HTTP atual é uma
ferramenta local de desenvolvimento, sem política de retenção ou migração além
do esquema inicial. Não usar as respostas como métricas do artigo.
