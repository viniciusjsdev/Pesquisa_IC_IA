# Ensaio de engenharia sem teto de saída imposto pela aplicação

Decisão do pesquisador em 05/11/2026: retirar o limite de tokens de saída
nesta rodada e usar o consumo observado para decidir os limites posteriores.
Este adendo substitui apenas o teto de saída descrito no escopo de engenharia;
o documento e recibo anteriores permanecem intactos para preservar seus hashes.

## Contrato da rodada

- Somente `agent_harness_pilot` com `openai_harness_pilot`: omitir
  `max_output_tokens` na requisição Responses, sem fallback para 4.096.
- Remover também o teto de 8.192 bytes da saída dos agentes nesse piloto.
  `null` no snapshot significa ausência de teto da aplicação, não saída infinita.
- Manter validação JSON/schema/semântica, 48 chamadas, 3 tentativas de consulta,
  uma correção por papel, limites de entrada e de resultado das consultas.
  Se uma saída maior exceder a entrada da etapa seguinte, registrar falha
  explícita, sem truncamento silencioso. Esse caso será evidência para ajustar
  a projeção de contexto; retirar teto de saída não retira teto de entrada.
- Limites nativos do modelo/provedor e timeout continuam existindo. Resposta
  incompleta não é sucesso. Groq e modos OpenAI fora deste piloto conservam
  seus limites anteriores.
- Registrar política `engineering_output_observation_20261105`, tokens de uso
  quando retornados, tamanho UTF-8 de cada saída e limites efetivos no trace.
- Aguardar autorização para clicar em Executar. Esta mudança não autoriza
  iniciar inferência, repetir chamadas, pontuar respostas ou marcar SPEC done.

## Verificação exigida

Testes locais com transporte simulado devem demonstrar ausência do parâmetro
no POST, preservação do padrão nos demais modos, aceitação integral de JSON
válido maior que 8 KB no piloto, rejeição de JSON inválido e registro correto
dos limites no snapshot. Nenhum teste desta alteração precisa chamar provedor.

## Evidência local em 05/11/2026

- Implementação em `openai_provider.py`, `agent_harness/openai_pilot.py`,
  `agent_harness/engine.py` e `service.py`.
- `test_spec013_openai_pilot.py`: 5 testes passaram; `test_spec012.py`: 9;
  `test_agent_harness.py`: 34. Total de 48 testes locais, transporte simulado,
  sem chamada real ao provedor. O teste de saída longa preservou o texto
  integral e demonstrou que schema inválido ainda é rejeitado.
- `git diff --check` passou (avisos de CRLF em arquivos preexistentes).
- Antes de recarregar a API local, consulta somente leitura confirmou zero
  jobs `accepted`/`running`. Servidor reiniciado com a configuração autorizada;
  nenhuma inferência iniciada. A SPEC continua `in_progress`.

Referência oficial: [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning)
explica tokens de saída/raciocínio e respostas incompletas por limites. A
ausência de teto configurado na aplicação não remove limites do provedor.
