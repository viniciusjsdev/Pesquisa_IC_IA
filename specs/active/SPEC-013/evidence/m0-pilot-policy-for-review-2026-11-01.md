# SPEC-013 · política piloto aprovada

**Estado:** aprovada pelo pesquisador no
[recibo M0](m0-pilot-policy-approval-2026-11-01.md). O recorte das 12 fontes
sem joins entre bancos também foi aprovado. Este documento não habilita o catálogo,
consultas reais no harness, envio a provedor ou pontuação científica.

## DEC-001 · perguntas e relações

O piloto deve cobrir três famílias de perguntas, todas observacionais:

1. Parada por máquina e período na DW, seguida de `contributors`/`trace` e
   detalhe de parada industrial quando o agregado não identifica o evento.
2. Observação financeira datada e vendas registradas, com distinção explícita
   entre valor de vendas e receita/lucro contábil.
3. Pergunta integrada sobre operação, parada e observação financeira no mesmo
   período, com resultados lado a lado e lacuna causal declarada. Coincidência
   de data não cria relação entre as linhas.

Cada fonte mantém seus campos, grão, unidade, caveat e filtros do candidato M0.
`physical_relations` documenta FKs, sem autorizar joins adicionais. A revisão
semântica de cada coluna e a forma de saída de `contributors`/`trace` ainda
precisam ser assinadas antes da ativação.

## DEC-002 · teto para uma execução piloto

Teto piloto aprovado: 3 consultas a dados, até 3 rodadas de investigação, até 3 domínios
por rodada e 3 fontes escolhidas por especialista; 48 chamadas de modelo no
run, incluindo uma correção explícita por papel/consulta. Uma consulta lê no
máximo 20 linhas, 32 KiB de resultado e 10 s de tempo; cada entrada de papel
tem teto de 32 KiB e cada saída 8 KiB. Ao exceder qualquer teto, registrar
erro específico e encerrar sem corte silencioso, sem trocar fonte/modelo e
sem inferir dado ausente. Esses números exigem medição em payloads completos
antes de se tornarem configuração ativa. O teto M1 de 16 chamadas/2 consultas
permanece exclusivo da fixture.

## DEC-003 · seleção de casos

Começar com uma matriz revisável de 9 casos: três por família acima, buscando
um caso com evidência suficiente, um com ausência de observação e um que
exija aprofundamento. Se uma célula não ocorrer na carga, registrá-la como
`unavailable` e substituí-la apenas por novo caso documentado. Pergunta,
fonte, filtros, fingerprint, consulta de referência, regra de exclusão e
limite de conclusão devem constar no manifesto. O preparo identifica seu autor
ou processo, distinto do pesquisador que revisará humanamente cada gabarito;
exemplos existentes não entram automaticamente.
Controles sintéticos de contradição, erro de cálculo e causalidade ficam fora
da bateria real.

## DEC-004 · acesso e transmissão

Criar credencial PostgreSQL exclusiva do harness com `CONNECT`, `USAGE` e
`SELECT` apenas nas tabelas permitidas; sem escrita, criação, função perigosa
ou acesso a outras bases. Verificar privilégios no banco antes do modo real.
Continuar usando transação `READ ONLY`, SQL parametrizado, allowlist, timeout
e conferência de schema/fingerprint. Guardar segredos fora do repositório.
Leitura local e envio de resultados a provedor são gates distintos. Nenhum
detalhe industrial/financeiro sai do host sem autorização específica de
provedor, classes de dados e payload.

## DEC-005 · avaliação

Manter rota, referência de evidência, cálculo e conclusão como quatro campos
separados, com justificativa e sem média ou ranking no piloto. Checks de rota
e referências são automáticos; cálculo e conclusão precisam de adjudicação
humana por run. Cada caso aprovado traz fórmula de referência, tolerância
numérica, interpretação aceitável e inferências vedadas. Três
repetições por caso e modelo com prompts, ferramentas, mapas, dados e limites
idênticos; runs incompletos contam como falha de conclusão, sem nota numérica
imputada. Relatar distribuições por caso/domínio e falhas; não misturar
cenários A e B.

## Antes de promover a `ready`

Revisar os campos e contratos de linhagem, medir os limites acima, preparar
a matriz e os gabaritos para revisão individual do pesquisador e provisionar
a conta de leitura. Só então promover o mapa e o manifest. A autorização de
transmissão pode permanecer fechada; nesse estado, M2 é verificável localmente
sem executar agentes externos sobre dados reais.
