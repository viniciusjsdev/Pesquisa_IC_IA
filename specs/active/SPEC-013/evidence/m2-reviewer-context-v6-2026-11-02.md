# SPEC-013: projeção de contexto do Revisor, protocolo v6

Em 02/11/2026, a primeira repetição I3 sob o protocolo v5 persistiu uma
consulta industrial de 13 linhas, mas terminou em `provider_request_error`
na chamada `revisor_evidencias`. O erro não trazia código HTTP. Não há prova
de que o tamanho da entrada tenha causado a falha.

O input enviado ao Revisor incluía o mesmo resultado completo duas vezes:
`query_result` (resultado atual) e o último elemento de `evidence_state`.
O motor passou a enviar `query_result` atual uma vez e apenas resultados
anteriores em `evidence_state`. O adaptador Groq agora registra o status HTTP
sanitizado quando disponível, sem registrar o corpo bruto do erro e sem
repetir automaticamente a chamada. O teste local com três bancos e modelo
programado percorreu 17 chamadas e 3 consultas; o maior envelope caiu de
22.110 para 15.068 bytes. Isso verifica a projeção local, não a hipótese
causal do erro Groq.

O protocolo v6 fixa `contracts.json` SHA-256
`69e55335b553f7fde51cdb578e7d53b7d424274630884430193b0c147a160edf`
e `input_contracts.json` SHA-256
`f7e7d4c17f2782c6354d70805053474e4686e719d6c4f17f2d2a4484380e67bc`.
Os runs v5 ficam como diagnósticos históricos. A matriz comparável, se
executada, usa rótulos `v6-*`, sem reutilizar nem repetir os runs anteriores.
