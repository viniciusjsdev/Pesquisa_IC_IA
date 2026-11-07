# M0 · medida dos resultados candidatos (01/11/2026)

Os dois pacotes privados de referência foram lidos localmente e cada resultado
foi serializado em JSON canônico UTF-8 (`sort_keys`, separadores compactos,
`ensure_ascii=False`) para medir o tamanho que uma tool poderia devolver.
Nenhum valor de linha foi incluído neste relatório ou enviado a provedor.

| Resultado | Bytes |
| --- | ---: |
| `machine(2021,2000002)` | 850 |
| `machine(2026,1)` | 557 |
| `machine(2020,1000002)` | 760 |
| `financial(2021)` | 2.069 |
| `financial(2019)` / `financial(2020)` | 580 cada |
| 13 paradas geradas tipadas | 6.890 |
| 11 vendas tipadas | 4.915 |
| 38 IDs contribuintes | 459 |

Todos esses **resultados individuais** cabem no teto piloto aprovado de
32 KiB por consulta. Para X3, os três resultados previstos somam 9.809 bytes
antes do envelope, mapa, instruções e metadados de trace. Portanto, esta
medição **não** prova que a entrada completa de 32 KiB por papel caiba no
harness real; o montador de contexto precisa medir e rejeitar overflow sem
corte silencioso. O limite de 20 linhas cobre os 13 eventos gerados e as
13 observações financeiras do exemplo, mas não uma paginação geral de fatos.
