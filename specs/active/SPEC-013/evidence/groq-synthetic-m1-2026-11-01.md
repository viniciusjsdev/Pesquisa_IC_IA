# SPEC-013 M1 — ensaio sintético parcial com Groq (01/11/2026)

Tipo: teste de transporte e contrato de papéis. Não é consulta à DW, carga,
validação de pesos nem avaliação científica.

- O núcleo local usa somente `synthetic_demo.py` e mapas inventados; não há
  cliente PostgreSQL nem SQL no módulo `agent_harness`.
- O modelo configurado originalmente para a Bancada era
  `openai/gpt-oss-120b`. Foi feita uma primeira tentativa de A1 antes de
  identificar essa configuração; ela terminou em `finish_reason=length`, sem
  resposta validada. A pedido do pesquisador, não houve nova chamada a esse
  modelo. O arquivo de configuração não foi alterado.
- O ensaio seguinte definiu `GROQ_HARNESS_MODEL=qwen/qwen3.8-27b` apenas no
  processo de teste. A1 retornou JSON conforme o contrato e foi validado.
  A2a recebeu `provider_rate_limited` (HTTP 429) e o run terminou em
  `contract_error`, com duas chamadas e zero consultas sintéticas. Não houve
  repetição automática. O [trace local](groq-synthetic-m1-2026-11-01.json)
  contém apenas a pergunta e mapas fictícios, saída A1 e códigos de status.
- A tentativa de listar modelos por `GET /models` retornou HTTP 403; a
  disponibilidade de Qwen foi confirmada pela primeira geração, não por um
  inventário completo da conta.
- Testes determinísticos locais cobrem os seis papéis com dois domínios,
  aprofundamento, isolamento do mapa, rejeição de referência fora do mapa,
  correção explícita de JSON, falha registrada da fixture e bloqueio de mapas
  reais.

Limite: o ensaio real com Groq **não** completou a cadeia de papéis. O núcleo
não está integrado à API HTTP/jobs/UI, não persiste eventos no banco da
aplicação e ainda não possui mapas reais nem serviço de consultas da SPEC.
DEC-001–005 continuam abertas e o status da SPEC permanece `design`.
