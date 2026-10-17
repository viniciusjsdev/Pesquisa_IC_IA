# Arquitetura da inferência compartilhada

**SPEC-009, implementação local de 16/10/2026:** novos runs da Bancada
selecionam explicitamente pacote fixo candidato da DW ou tools da DW escolhidas
pela LLM. As cinco consultas fixas são compartilhadas com o exportador; o
backend usa apenas `db_pesquisa_dw` em transações somente leitura. Pacotes
privados são montados `:ro` no Compose e não entram na imagem. Sem DW ou
pacotes, a Bancada informa indisponibilidade. O fluxo anterior continua apenas
como snapshot histórico; o harness científico, RunPod e ngrok não foram
executados por esta mudança.


**Atualização local em 16/10/2026 (checkout baseado em `772ea0d`):** a
[SPEC-008](../specs/active/SPEC-008/SPEC.md) integrou o Observatório sintético
e a Bancada em um front React servido pela mesma API Python. O snapshot BI
privado exige sessão; o Docker Compose acrescentou um PostgreSQL 15 isolado
com cópia lógica manual testada somente entre bancos descartáveis. Nenhum banco
real foi copiado. A [revisão independente da SPEC-008](../specs/active/SPEC-008/evidence/review.json)
aprovou o escopo local na quinta rodada em 16/10/2026; a
[evidência local](../specs/active/SPEC-008/evidence/local-2026-10-16.md)
delimita os testes. A topologia com ngrok e RunPod abaixo
descreve uma sessão futura, não uma implantação realizada.

**Registro histórico de 15/10/2026:** SPECs 001–004 haviam implementado a primeira
cadeia exploratória, identidade, critérios e comparação. Naquela data o DW
local v1 ainda não alimentava a API. A SPEC-009 substituiu esse fluxo para
novos runs em 16/10/2026; a descrição operacional vigente está no
[README da `inference_api`](../inference_api/README.md). A SPEC-002 preparou
serving vLLM, Terraform e [procedimento de custo e aplicação futura](../runpod/serving/README.md)
apenas no checkout. Pod, ngrok e validação compartilhada não foram executados.
A decisão original foi registrada no commit `ba79b36`.

## Objetivo e limites

Disponibilizar por uma sessão científica curta e compartilhada uma interface para editar prompts, escolher a LLM de inferência, ler respostas, inspecionar evidências e registrar verificações. A primeira implantação deve ser simples e de baixo custo: banco, backend e interface no notebook; GPU apenas na RunPod. O período de uso previsto é inferior a 24 horas, sem requisito de disponibilidade contínua.

O [protocolo de fine-tuning](../FineTuning/docs/protocol_v1.md), os [dados de origem](../BancoModeloUse/README.md), os [adapters e seus manifests](../FineTuning/docs/modelos_disponiveis.md) e os resultados já registrados permanecem preservados. O DW local v1 alimenta os novos runs exploratórios da Bancada por pacote exportado ou tools; o harness científico formal por API continua planejado.

Para a comparação científica futura, a [arquitetura de avaliação](../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md) distingue evidências fixas, iguais entre modelos, de pesquisa com tools. O [exportador da SPEC-007](../model_evaluation/README.md) foi implementado localmente em 16/10/2026 e prepara pacotes candidatos reproduzíveis a partir da DW. A Bancada exploratória v3 usa pacote candidato ou cinco tools escolhidas pela LLM; pontuação formal ainda exige contrato e implementação próprios.

## Topologia escolhida

```mermaid
flowchart LR
    U[Pesquisadores no navegador] --> N[URL HTTPS do ngrok]
    N --> A[Notebook: front e inference_api]
    S[(Bancos de origem preservados)] -->|carga v1 ja realizada| D[(db_pesquisa_dw)]
    D --> E[Exportador de pacotes]
    E --> F[(Pacotes privados imutáveis)]
    A -->|modo tools: leitura fixa| D
    A -->|modo snapshot: bytes por ID e hash| F
    A --> X[(db_inference_app: runs e revisões)]
    A --> V[RunPod: API vLLM]
    V --> Q[Qwen base e adapters LoRA selecionados]
```

O [mapa visual completo](assets/fluxo_arquitetura_pesquisa.png) também mostra
o DW local e distingue as ligações implementadas das previstas. O
[SVG editável](assets/fluxo_arquitetura_pesquisa.svg) preserva a fonte do desenho.

- O ngrok expõe **somente a aplicação HTTP** por uma URL HTTPS. O PostgreSQL permanece no loopback do notebook. A RunPod não precisa iniciar conexão com o notebook; o backend local faz chamadas de saída para a API do modelo. [Referência: túnel HTTP do ngrok](https://ngrok.com/use-cases/share-localhost).
- O front é servido pela mesma aplicação e pela mesma URL do ngrok. Ele chama apenas o backend local, sem receber credenciais da RunPod ou do PostgreSQL.
- O backend orquestra consultas permitidas e de leitura, monta um pacote de evidências e chama a LLM. A LLM não recebe acesso direto ao banco nem SQL arbitrário do navegador.
- O notebook, o cluster local, a aplicação, o túnel e o Pod precisam permanecer ativos durante o uso. Ao encerrar a sessão, o serviço de modelo pode ser parado para interromper o custo de GPU, observadas as regras de cobrança e armazenamento do provedor.

## Responsabilidades do código

| Frente | Responsabilidade e estado atual |
| --- | --- |
| [`BancoModeloUse/`](../BancoModeloUse/README.md) | Contém os CSVs preservados, modelos SQLAlchemy, importador e dois bancos locais `db_industrial` e `db_financeiro`. O [DW v1](../BancoModeloUse/dw/README.md) está em `db_pesquisa_dw`, separado das fontes e da aplicação. A Bancada v3 lê apenas a DW ou pacotes já exportados; os bancos de origem permanecem fontes preservadas. |
| [`FineTuning/`](../FineTuning/AGENTS.md) | Continua sendo a fonte de verdade dos experimentos, configurações, adapters, manifests e resultados. Seus scripts de treino não serão executados para atender requisições do front. |
| [`runpod/`](../runpod/README.md) | Contém scripts históricos de preparação, treino e avaliação. [`runpod/serving/`](../runpod/serving/README.md) contém preparação local do vLLM, gateway protegido, verificador e Terraform; nenhum Pod foi criado. |
| [`inference_api/`](../inference_api/README.md) | HTTP local, login individual da SPEC-003 e cliente vLLM. A SPEC-008 serve React após login, com quatro abas BI de snapshot sintético; a SPEC-009 oferece pacote fixo ou tools da DW na Bancada exploratória. Compose local usa banco isolado; exposição compartilhada e verificação científica seguem pendentes. |
| [Arquitetura da avaliação](../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md) | Define perguntas, evidências, gold set e verificações científicas. O DW local v1 existe sob SPEC-006 e alimenta a Bancada exploratória pela SPEC-009; o harness formal segue pendente. |

Estrutura local atual:

```text
inference_api/
  README.md
  frontend/src/         # React: login, Observatório e Bancada
  frontend/dist/        # build gerado e ignorado pelo Git
  private/bi_snapshot.json  # retrato sintético, apenas endpoint autenticado
  Dockerfile
  compose.yaml          # app HTTP e PostgreSQL sem porta de banco publicada
  scripts/copy_logical_databases.py  # cópia manual e por recusa
  src/
    inference_api/      # HTTP, evidências, cliente vLLM, serviço e persistência
runpod/
  serving/              # manifesto, preflight, gateway, verificador e Terraform locais
```

O contrato HTTP e o esquema inicial estão descritos no [README da API](../inference_api/README.md). Não criar diretórios vazios nem reaproveitar o antigo RAG/agentes retirado do checkout. O modo direto da aplicação exige o cluster isolado em `127.0.0.1:5544`; o modo Docker exige somente `db:5432` na rede do Compose. Nenhum modo aceita os valores padrão `localhost:5432` de [`database_config.py`](../BancoModeloUse/infrastructure/config/database_config.py). A conexão falha se a configuração estiver ausente ou apontar para outro host.

## Modelos na RunPod e troca pelo front

Os pesos disponíveis no checkout são adapters PEFT/LoRA, não cópias completas da LLM. O [catálogo de modelos](../FineTuning/docs/modelos_disponiveis.md) identifica a base `Qwen/Qwen2.5-7B-Instruct`, os seis adapters locais, suas runs e seus manifests. A versão exata dos pesos da base ainda não está fixada por hash nesse catálogo. Antes de servir, registrar a revisão efetivamente obtida da base e conferir os arquivos dos adapters escolhidos.

O [manifesto de serving](../runpod/serving/manifest.json) registra aliases, baterias, runs e hashes dos seis adapters. O preflight local recusa divergências antes de montar o comando estático do vLLM. A revisão exata da base é entrada obrigatória da sessão futura, pois não ficou registrada nos treinos históricos. O backend marca um modelo disponível somente se aparecer em `/v1/models` e marca geração confirmada apenas com recibo da mesma sessão. Ao clicar em outro modelo fine-tunado, o front muda o alias na próxima requisição; não reinicia o Pod nem altera a escolha dos demais usuários. A capacidade concreta ainda requer teste no Pod escolhido. [Referência: serving LoRA do vLLM](https://docs.vllm.ai/en/stable/features/lora/).

O comando local registra os seis adapters autorizados na inicialização. O gateway exige token e permite somente `GET /v1/models` e `POST /v1/chat/completions`; o vLLM escuta apenas no loopback do Pod. O carregamento dinâmico de LoRA permanece fora do fluxo. Uma LLM com outra base de pesos pode exigir outro processo ou endpoint; nesse caso, o backend roteará pelo catálogo, e o custo/capacidade devem ser avaliados antes de disponibilizá-la no seletor.

## Front e histórico compartilhado

O front local permite editar prompt e critérios estruturados, selecionar um alias disponível por run, escolher explicitamente pacote fixo ou tools da DW, executar perguntas, inspecionar histórico e comparar snapshots lado a lado. O navegador busca disponibilidade do backend e não escolhe SQL. No modo tools, a LLM solicita uma das cinco consultas fixas; no modo snapshot, a pergunta vem do pacote. A interface mostra evidência, resposta, checks e erro, marcando `answered_unverified` como não verificado cientificamente. A comparação avisa quando modo, pergunta, evidência, prompt, critérios, parâmetros ou modelo/versão diferem; não agrega pontuação. Os testes locais da SPEC-009 usaram API e modelo simulados, não o Pod nem a URL futura do ngrok.

Cada salvamento de prompt ou critério cria uma **nova revisão**; cada execução guarda um snapshot imutável com texto exato do prompt e configuração exata dos critérios, mesmo quando partiu de rascunho. O registro identifica autor autenticado, data, versões, modelo/endpoint/adapter quando confirmados, parâmetros, pergunta, rota, consultas, evidências com origem e período, resposta, verificações e estado de erro. Feedback humano fica separado do snapshot. A escolha do modelo pertence à execução de cada usuário, sem configuração global.

O armazenamento editável da aplicação usa `db_inference_app` no mesmo cluster PostgreSQL. `init-db` cria o esquema inicial; iniciar a API não altera o esquema. A migração 001 acrescentou identidade, sessões e uso. A migração explícita 002 acrescentou revisões de critérios após backup lógico, com readback das versões 1 e 2. Ambas têm SQL reverso. A política de retenção ainda não foi implementada. Novos runs consultam apenas `db_pesquisa_dw` em leitura por SQL fixo; snapshots anteriores registram consultas históricas às origens. Dados congelados, adapters, manifests e resultados brutos existentes não são editados pelo front.

Experimentos livres no front e avaliação formal têm estados distintos. Uma comparação científica exigirá um caso e protocolo versionados, mesmo recorte de dados e contexto, parâmetros declarados e verificações apropriadas. O gold set e os critérios oficiais de avaliação ficam fora do contexto entregue à LLM. A [arquitetura de avaliação](../BancoModeloUse/docs/arquitetura_avaliacao_modelos.md) continua sendo a fonte dessa separação.

## Contratos: primeira fatia e pendências

1. **Entrada e saída HTTP:** implementadas para pergunta, revisão ou rascunho, alias, parâmetros e snapshot com evidência, resposta, estado e erro. A API não aceita SQL livre. Veja o [contrato executável](../inference_api/README.md).
2. **Evidência dos runs:** novos snapshots usam `schema_version: 3` e `evidence_mode` explícito: pacote candidato da DW por ID/hash ou tools fixas da DW escolhidas pela LLM. O fluxo anterior (`schema_version: 1` e `2`) usava escopos declarados financeiro, industrial e integrado e agregações das origens; seus snapshots permanecem legíveis, sem novos runs nessa rota. Nenhum desses checks equivale à validação científica.
3. **Catálogo de modelos:** sete aliases candidatos do manifesto e consulta de disponibilidade em `/v1/models` implementados. Headers de uma sessão cujo manifesto coincide com o local permitem registrar revisão da base, run e hash do adapter no snapshot; um recibo da mesma sessão distingue geração confirmada. Nenhuma sessão remota foi validada. Janela efetivamente suportada e identidade da base usada no treino continuam sem prova. Segredos ficam apenas no ambiente dos processos, fora do Git.
4. **Persistência e concorrência:** esquema inicial de revisões de prompt, snapshots de execução e feedback implementado, com conflito por revisão esperada. A migração 001 de identidade foi aplicada localmente em 15/10/2026 após backup lógico e o SQL reverso foi testado em banco isolado. Novos registros usam autoria verificada no backend; registros históricos mantêm autoria declarada. A política de retenção ainda falta.
5. **Acesso compartilhado:** a SPEC-003 implementou localmente login exclusivo para Nicoli e Vinicius, sessões revogáveis e uma vaga global de inferência. Ambos podem permanecer logados; a segunda inferência simultânea recebe HTTP 429 antes de consultar fontes ou chamar a LLM. O limite diário está desativado. O front mostra teto manual informativo de US$ 10 e saldo real apenas quando a API de leitura da RunPod responde, sem transformar o teto em bloqueio de cobrança. Os [testes locais de 15/10/2026](../specs/active/SPEC-003/evidence/local-2026-10-15.md) passaram e a [revisão independente](../specs/active/SPEC-003/evidence/review.json) aprovou o escopo local; o ngrok ainda não foi aberto. O gateway remoto foi escrito com bearer token e allowlist de duas rotas; sua proteção ainda requer teste real pela URL HTTPS da RunPod. A chave nativa do vLLM não protege todos os seus endpoints. [Referência: segurança do vLLM](https://docs.vllm.ai/en/stable/serving/online_serving/openai_compatible_server/).
6. **Capacidade e operação:** Terraform e comandos de preflight/start/verificação estão preparados localmente. O [runbook](../runpod/serving/README.md) contém fórmula de custo de GPU e discos, procedimento de `plan` e sequência de implantação para outra interação. GPU/VRAM, quantização, concorrência, compatibilidade real dos seis adapters, parada/remoção externas e teste de ponta a ponta continuam pendentes. A oferta concreta da Pod não foi escolhida; `terraform apply` exige confirmação explícita do usuário após revisar plano e estimativa.

## Evidência e manutenção

Antes de dizer que o serviço compartilhado está pronto, verificar separadamente: carga da base e dos adapters com seus identificadores; tool calling real e resposta da API do vLLM; leitura da DW v1 e validação dos pacotes privados; persistência de revisões e execuções; front pela URL do ngrok; autenticação; e uma execução ponta a ponta com proveniência legível. Um teste local ou um manifest com estado `completed` não equivale a essa validação.

Atualizar este documento e os README das frentes afetadas na mesma mudança que alterar topologia, contratos ou comandos. Marcar decisões propostas e partes ainda não implementadas; registrar data/commit e evidência para afirmações que envelhecem. Remover instruções e código comprovadamente fora de uso após conferir consumidores, preservando dados e resultados protegidos conforme o [AGENTS.md da raiz](../AGENTS.md).

Em 16/10/2026, a [SPEC-005](sessao_inferencia_curta.md) acrescentou verificações
e runbook para a sessão curta, com [revisão independente](../specs/active/SPEC-005/evidence/review.json)
aprovada no escopo local. O pré-voo lê bancos locais e valida adapters;
o teste do túnel e o ensaio com gerações exigem `--execute` e ativação
autorizada. Implementar esses comandos não constitui prova de Pod, ngrok ou
avaliação científica: cada camada precisa de seu próprio readback na sessão.
