# Bancada OpenAI preparada, sem envio — 05/11/2026

O usuário autorizou OpenAI para engenharia, depois pediu expressamente que o
botão Executar só fosse acionado após novo comando. Essa espera prevalece.
Nenhuma inferência OpenAI real foi iniciada nesta etapa.

Implementação local: openai_pilot.py valida recibo/destino/hash e chave de
ativação própria; cria contexto novo por papel, reutiliza role_messages e
Responses com gpt-6-luna/medium/4096. service.py despacha o mesmo motor e
adaptador de consultas, registra provedor e parâmetros reais no snapshot.
models.py e BenchPage.tsx expõem o piloto OpenAI sem abrir os gates Groq.

O achado P1 do auditor foi corrigido: todas as invocações do adaptador de
consulta contam no teto, mesmo rejeitadas. query_attempts e queries ficam
separados; limites efetivos são registrados; estouro de linhas/bytes no caminho
real encerra sem repetição. Demais achados P2 do parecer inicial continuam
abertos para revisão/correção; não há aprovação técnica final nem done.

Verificações desta etapa:

- Suíte API anterior ao ajuste do contador: 124 testes, 8 opcionais ignorados,
  sem falhas; cinco novos testes OpenAI passaram depois.
- Após o ajuste do contador: 33 testes do motor passaram, incluindo regressão
  de tentativa rejeitada consumindo orçamento e recuperação com limite suficiente.
- Smoke com modelo programado: 17 chamadas, três consultas reais (machine,
  paradas_maquinas_geradas, resultados_financeiros); sem provedor e sem score.
- Build/typecheck, lint e nove testes de componentes passaram; novo build
  depois da alteração do texto do piloto passou.
- Manifesto contrato 2 validado pelo schema local; git diff --check passou.

O PostgreSQL 5544 estava parado e recuperou seu estado ao iniciar. A API foi
iniciada em 127.0.0.1:8765 com INFERENCE_SPEC013_OPENAI_REAL_DATA=1 no processo,
sem alterar credenciais. O usuário fez login na UI com seu próprio acesso.
Navegação no Chrome confirmou modelos, histórico, mapas e piloto disponíveis.

Tela preparada: Piloto de agentes em camadas, OpenAI gpt-6-luna, pergunta X3
do pacote aprovado sobre máquina 2000002 em 2021: agregado DW, detalhe de
paradas geradas industrial e observações financeiras, sem atribuir causalidade.
Botão Executar habilitado, mas não acionado. Evidência visual privada:
inference_api/.local/spec013-openai-prepared-20261105.png.

A página do diagrams foi lida em 05/11: confirma os três especialistas,
duas chamadas por especialista, plano tipado, backend de leitura, Revisor,
aprofundamento e Redator. Suas legendas de estágio ainda citam proposta/M1
parcial; não foram editadas nesta etapa e não provam implementação.
