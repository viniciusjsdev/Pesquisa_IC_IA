# Fechamento técnico da SPEC-013 — 06/11/2026

Complemento do contrato 3 autorizado pelo pesquisador. Documentação antecede
código. Não altera agentes, decisões do fluxo ou modelagem; corrige limites,
comparação e instrumento de revisão previstos no desenho existente.

## Orçamento da entrada

O limite `input_bytes` cobre também os bytes UTF-8 do corpo JSON efetivamente
enviado ao provedor: instruções, schemas, contexto e parâmetros. Medir depois
da montagem e antes de criar/enviar a requisição. Headers com credenciais não
entram no payload nem no registro. Sem corte silencioso, sem retry de overflow.
Registrar tamanho, limite, hash e política `http_json_body_utf8_v1`, inclusive
na recusa local. O limite do envelope permanece uma primeira barreira.
Aplica-se aos adaptadores Groq/OpenAI usados no harness, inclusive diagnóstico
sintético. Os modos históricos fora do harness preservam seu comportamento.

## Comparação

Comparar canonicamente pergunta, cenário, prompt, critérios, parâmetros, fontes,
mapas, contratos de entrada/saída, protocolo, limites, política de dependências
e orçamento de payload. Dados do piloto incluem fingerprint DW e contrato de
dados; detalhe exige proveniência/fingerprints registrados. Ausência de metadados
necessários significa compatibilidade indeterminada, nunca igualdade comprovada.
Identidade do modelo/provedor aparece separada: trocar o candidato é a variável
do experimento. Rotas, consultas e resultados efetivamente escolhidos são saídas
observadas e não tornam, por si sós, os protocolos incompatíveis.
Compatibilidade registrada não é pontuação nem aprovação científica.

Conferência independente: registrar manifesto dos arquivos das fontes habilitadas
industrial/financeiro antes e depois do run, independentemente da rota escolhida.
Leituras de metadados são internas e somente leitura; não são consultas escolhidas
pelo modelo. Ausência ou mudança durante o run impede declarar compatibilidade.
O manifesto identifica a carga registrada, não prova ausência de alterações manuais
nos registros. Comparar também conflitos de proveniência observados nas evidências.
O contrato de execução identifica os módulos de harness, projeção, consulta,
serialização e adaptadores; todos os provedores são incluídos no mesmo conjunto.
Erros HTTP, conexão, timeout e stream preservam o recibo do payload tentado,
sem afirmar recebimento remoto e sem retry automático.

## Revisão de uma resposta

O avaliador exige `run_id`, `case_id`, hash canônico do caso e `run_sha256` do
objeto integral de run recebido pelo avaliador (incluindo resposta, evidências,
trace e configurações presentes). JSON com chaves reordenadas mantém o hash;
qualquer alteração de conteúdo invalida a adjudicação. Hash não autentica pessoa.
Instrumento de preparo gera pacote privado contendo run/caso e um template
pendente de adjudicação com os hashes exatos, sem inventar decisão humana.
Registros antigos sem hash não são promovidos a revisão válida.

## Validação e conclusão

Testar payload no limite e acima dele, instruções grandes com envelope pequeno,
UTF-8 multibyte, ausência de envio/retry no overflow; diferenças de contratos,
mapas, dados e políticas, ordem de chaves, candidato diferente e metadados ausentes;
reuso de revisão após alteração de resposta, evidência, trace e configuração.
Executar suítes, integração local permitida, UI e revisão Astra global. Reutilizar
o ensaio real contrato3 e replay técnico quando suficientes; não apresentar replay
como nova inferência. A matriz e adjudicação científica das respostas são futuras.
`Done` exige completion/review coerentes com os gates técnicos do escopo de 05/11.
