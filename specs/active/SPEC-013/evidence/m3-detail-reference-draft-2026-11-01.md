# M3 · referência privada de detalhe e linhagem (01/11/2026)

`model_evaluation/spec013_detail_reference_draft.py` leu, em modo somente
leitura, as 13 paradas **geradas** da máquina `2000002` em 2021, as 11 vendas
observadas em 2021 e a lista completa de 38 IDs de fatos de parada
contribuintes para o agregado `machine(2021,2000002)`. Os 13 IDs gerados foram
encontrados entre os contribuintes da DW; a checagem foi por ID de importação,
sem join SQL entre bancos. O catálogo do disco permaneceu desabilitado;
somente uma cópia em memória autorizou as duas leituras tipadas para preparar
o rascunho. Não houve chamada a provedor.

O pacote com valores e proveniência está apenas no diretório privado ignorado
pelo Git:

`model_evaluation/.local/spec013-pilot-detail-reference-draft-2026-11-01-v2.json`

SHA-256: `33c8005b327e1209c6bc49feefff702daf9af0e49b9f85f9a3abdfb5743f69bb`;
12.511 bytes. O primeiro arquivo sem a checagem adicional foi preservado;
ambos têm bytes idênticos. Estes dados ainda não são gabarito aprovado e
**não** podem entrar em payloads dos agentes. Faltam cálculo/critério por
pergunta, revisão humana e verificação de limites no harness real.

Atualização: o [conteúdo dos nove casos foi aprovado](m3-human-case-content-approval-2026-11-01.md)
na versão do pacote revisado. O vínculo técnico com os casos e a revisão de
respostas dos runs permanecem pendentes.
