# M1 parcial: modo multiagente sintético na Bancada — 01/11/2026

Escopo: código local e testes com transporte simulado. Os [ensaios reais
posteriores com Qwen na Groq](groq-synthetic-m1-followup-2026-11-01.md)
pararam em rejeições de contrato ou `429`. Nenhuma chamada usou GPT ou RunPod.

O alias `groq_harness` anuncia separadamente o modelo padrão
`qwen/qwen3.8-27b`. O modo `agent_harness` usa pergunta, mapas e resultados
inventados. O backend fixa prompt, temperatura zero e 900 tokens por chamada,
recusa `GROQ_HARNESS_MODEL` que contenha `gpt` ou `openai`, e não herda o
`GROQ_MODEL` de outros modos. O mesmo modelo é fixado nas chamadas e cada
etapa recebe somente sua projeção do contexto. O ID aleatório do run fica fora
dos prompts; o fingerprint estável do caso entra no envelope. O snapshot v6
guarda trace, JSON bruto e validado, hashes de contrato/mapas, resultados e estado.

Validação local:

- `python -m unittest discover -s inference_api/tests -p test_agent_harness.py -v`:
  15 testes passaram, incluindo integração `service.execute_run`, despacho por
  job com transporte simulado, contrato corrigível, entradas estáveis entre
  runs e veto a qualquer leitura da DW ou pacote privado.
- `python -m unittest discover -s inference_api/tests -v`:
  83 testes, 8 pulados por integração opcional; zero falhas.
- `pnpm run build` e `pnpm run lint` no frontend: passaram com o runtime Node
  fornecido pelo workspace.

Esses testes não exercitam a cadeia real completa pela API HTTP, o job
persistido ou a interação visual em navegador. O modo é exploratório e a SPEC
continua `design`; mapas reais, política final de limites, acesso e avaliação
científica dependem de DEC-001–005.
