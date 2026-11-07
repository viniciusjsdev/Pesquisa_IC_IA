# SPEC-013: conclusão de engenharia e ensaio OpenAI pela Bancada

## Decisão do pesquisador em 05/11/2026

O pesquisador esclareceu nesta sessão que a SPEC entrega a estrutura de agentes,
harness e core pronta para os experimentos. A revisão humana das respostas e a
comparação científica ocorrem depois. Autorizou a API OpenAI já configurada para
executar o piloto em substituição à Groq, e pediu execução pela interface da
Bancada. Confirmou Astra em um chat separado para auditoria de engenharia.

Esta decisão revisa o contrato da SPEC para versão 2 e substitui a exigência
anterior de completar a matriz científica e adjudicar cada resposta para marcar
a implementação como done. Não aprova respostas, não modifica os gabaritos,
não altera os dados nem concede pontuação científica.

## Critérios de conclusão da engenharia

1. Testes dos contratos JSON, isolamento de contexto/gabaritos, projeção dos
   mapas, permissões, limites, correção limitada, aprofundamento e falhas.
2. Leitura real aprovada nos três domínios, sem joins entre bancos, com
   resultados rastreáveis e sem mudança de carga.
3. Pelo menos uma execução real completa no protocolo atual iniciada pela UI
   da Bancada, passando por autenticação, job, agentes, consultas, Revisor,
   Redator, persistência, trajetória e histórico. Registrar a identidade e
   configuração do modelo, as evidências e os limites do teste.
4. Avaliador e instrumentos de revisão disponíveis e testados, mantendo
   not_scored/awaiting_run_review para respostas sem adjudicação. A matriz
   de nove casos e três repetições permanece como experimento futuro.
5. Auditoria técnica independente Astra, correção dos achados bloqueantes,
   evidências de validação e completion/review reconciliados antes de done.

Uma falha de provedor ou banco permanece uma falha observada. Um diagnóstico
incompleto não substitui o caminho positivo completo. O parecer do auditor
deve distinguir erro de software, limite de infraestrutura e decisão incorreta
do modelo; não exige acertar todas as perguntas para aprovar o motor.

## Autorização operacional OpenAI

Destino: https://api.openai.com/v1/responses. Reutilizar o adaptador existente,
modelo fixo gpt-6-luna, esforço medium, contexto novo por papel, store=false,
até 4096 tokens de saída por chamada, 48 chamadas e três consultas por run,
com limites de bytes já vigentes. Essas configurações são uma condição de
engenharia distinta do diagnóstico Groq; não misturar resultados para comparação.

Pode enviar pergunta, schemas/templates, trechos selecionados dos mapas aprovados
e resultados reais limitados da DW, industrial e financeiro. Gabaritos, credenciais
de bancos e chave de API não entram nos prompts. A chave já existente permanece
no ambiente local ignorado pelo Git. Não há autorização para RunPod, mudança de
dados ou envio de todo o banco. Não repetir automaticamente chamadas com falha.

O backend exige recibo desta decisão e ativação específica para OpenAI. Uma
autorização Groq não abre OpenAI nem o inverso. A interface deve mostrar o
destino selecionado e o histórico preservar snapshots e provedores antigos.
store=false não é afirmação de retenção zero do provedor.

Referência de integração: [streaming da Responses API](https://developers.openai.com/api/docs/guides/streaming-responses).

## Auditoria separada

O chat Astra recebe código, contratos, evidências técnicas e trajetória privada
dos runs para revisar a engenharia. Não atua como agente do experimento nem
altera respostas. Inicialmente inspeciona sem editar o checkout e sem executar
novas chamadas a provedores; a thread principal implementa e testa.

## Avaliação científica posterior

Continuam obrigatórios os gates de docs/protocolo_validacao_humana_avaliacao.md
antes de pontuar respostas ou publicar conclusões. A aprovação dos casos já
registrada permanece válida para seus bytes; não se solicita novamente.
