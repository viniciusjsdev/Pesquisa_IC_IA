# SPEC-013 · proposta de transmissão real à Groq

**Estado:** proposta para revisão. A aprovação de 02/11/2026 cobre somente
consultas locais. Este documento não concede autorização.

## Destino e finalidade

- Destino: endpoint `https://api.groq.com/openai/v1/chat/completions`, modelo
  Groq Qwen configurado em `GROQ_HARNESS_MODEL` (padrão do modo sintético:
  `qwen/qwen3.8-27b`). Nenhum GPT, OpenAI ou RunPod entra neste piloto.
- Finalidade: auditar a cadeia de papéis A1–A5 com perguntas do piloto e
  resultados da DW, linhagem, industrial e financeiro. Nenhum score científico
  será publicado sem os gates humanos posteriores.

## Dados que saem em cada chamada de papel

O cliente enviará o prompt fixo do papel, seu JSON Schema, a pergunta do caso,
o índice ou trecho selecionado do mapa semântico e apenas a evidência acumulada
que aquele papel precisa. Ao consultar uma fonte, o retorno pode conter até
20 linhas selecionadas e sua cobertura, unidades, fórmula e proveniência.
As fontes aprovadas incluem métricas agregadas da DW, IDs de linhagem,
paradas e operações industriais, observações de resultados financeiros e
vendas. Assim, **valores industriais e financeiros reais podem sair da máquina**.
O envelope de entrada de um papel tem teto de 32 KiB; cada resultado de tool,
32 KiB; o piloto limita a três consultas e 48 chamadas de modelo. O modelo
recebe somente trechos do mapa e resultados necessários à rodada, não o schema
inteiro dos bancos.

Não devem ser enviados: credenciais, SQL livre, CSVs brutos, tabelas completas,
gabaritos privados, rubrica interna de pontuação ou trace integral de outros
papéis. O snapshot completo permanece na Bancada local. Não há promessa aqui
sobre retenção do provedor; a autorização precisa considerar a transmissão ao
serviço externo como efeito próprio.

## Ativação proposta

O código exige simultaneamente (1) recibo específico que aponte ao SHA-256
exato deste documento e identifique a resposta humana e (2) configuração local
`INFERENCE_SPEC013_GROQ_REAL_DATA=1`. O padrão é fechado. A primeira execução
real deve ser curta, com leitura do trace e sem repetição automática em erro.
Qualquer ampliação de fontes, campos, destino ou limites exige outra revisão.
