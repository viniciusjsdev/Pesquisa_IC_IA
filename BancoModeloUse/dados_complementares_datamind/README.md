> **Localização vigente em 07/11/2026:** conjunto integrado no checkout principal. O worktree anterior é histórico; [mapa das fontes](../../docs/fontes_ativas_e_arquivo.md).

# Dados Complementares para a Plataforma V&N DataMind

Este diretório reúne os CSVs complementares ativos e os CSVs sintéticos
derivados para estudar as análises do **V&N DataMind**. É um único conjunto
canônico descrito em `manifesto_canonico.json`: 69 arquivos originais intactos,
três arquivos de custo de material e três de custo operacional revisados em
`../dados_simulados/`,
39 complementares aqui, nove cadastros de referência derivados e 43 arquivos
sintéticos para análises (51 arquivos derivados em `gerados/` e a composição
tarifária inferida na raiz),
totalizando 166 CSVs. O manifesto registra
caminho, classe, linhas e SHA-256. A base PostgreSQL foi reconstruída em
31/10/2026; a [leitura de volta](../docs/carga_canonica_2026-10-31.md)
conferiu esquema, partições e contagens.
O manifesto é a lista única do que foi ingerido: a validação falha se houver
qualquer CSV do projeto fora dele. As pastas `dados_simulados/` e
`dados_complementares_datamind/` guardam partes diferentes do mesmo conjunto,
sem duas versões da mesma observação.
O arquivo `contrato_tabelas_canonicas.json` fixa as 56 tabelas de origem
e a estrutura da DW desenhadas no DER. A cópia local do XML está em
`../docs/datamind_erd_canonical.drawio.xml`; o `canonical_ingest.py plan`
compara o XML, o contrato e o código antes de permitir `load`.
O validador exige que cada um dos 166 CSVs tenha uma tabela
e que cabeçalho, tipos e chave por período coincidam; esse pré-voo é offline,
seguido de conferência read-only no PostgreSQL após a carga.

Os nove CSVs de IA recebidos no commit foram retirados do checkout e
arquivados fora do projeto com inventário e hashes; estão **fora do conjunto
canônico atual**. A funcionalidade de alertas de IA permanece como
[conceito de produto](../../docs/produto_datamind_alertas_ia.md).

Os 75 arquivos de origem continuam distribuídos pelos três períodos. Em
29/10/2026, os três `materiais_custo_historico.csv` e os três
`custos_operacionais_variaveis.csv` foram revisados;
as versões anteriores estão arquivadas fora do checkout em
`C:\Users\vinic\.codex\archives\datamind_material_lot_20261029`, com
inventário e SHA-256. As versões anteriores dos custos operacionais estão em
`C:\Users\vinic\.codex\archives\datamind_operational_unit_20261029`, também
com inventário e SHA-256. Os outros 69 permaneceram byte a byte intactos.

Nesses três arquivos, `material_id` e os valores monetários foram mantidos.
Em 161 de 180 linhas, `lote_material_id` foi trocado por um ID de lote já
cadastrado para o mesmo material e período. A escolha é determinística:
recebimento mais próximo da compra, priorizando a mesma data ou data posterior;
em empate, menor ID. `lote_material_id_original` preserva o valor anterior e
`origem_vinculo_lote` distingue `original_coerente` de
`reassociado_por_material_e_data`. Os lotes são registros existentes, mas os
CSVs não comprovam que esses foram os lotes efetivamente comprados.
Nenhum `produto_id` foi alterado: essa tabela contém `material_id`, não produto.

Nos três `custos_operacionais_variaveis.csv`, apenas `unidade_medida` de
`Energia` (`l` → `kWh`) e `Manutencao Tecnologica` (`l` → `servico`) foi corrigida.
`unidade_medida_original` e `origem_ajuste_unidade` preservam o valor anterior
e distinguem as 46 correções das outras 96 linhas. Preços, datas, IDs e nomes
de insumo foram mantidos. A unidade corrigida é uma escolha coerente com o
tipo de insumo para o cenário, não comprovação da unidade do preço histórico.

Os períodos do projeto são:

- `periodo_2015_2016/` (Período 0 - Linha de Base / Início da Operação)
- `periodo_2017_2020/` (Período 1 - Modernização e Transição Digital)
- `periodo_2021_2025/` (Período 2 - Indústria 4.0 Plena e Expansão com Robô Cobot)

---

## 1. Inventário complementar ativo (13 CSVs por pasta = 39 arquivos)

| Domínio | Arquivo | Grão / Descrição | Chaves Estrangeiras de Integração |
| :--- | :--- | :--- | :--- |
| **Operações** | `turnos_trabalho.csv` | 1 linha por turno (1º, 2º e 3º) com horários e metas | `turno_id` |
| **Operações** | `metas_producao_maquina.csv` | Metas de produtividade, OEE, disponibilidade por máquina | `maquina_id` |
| **Manutenção** | `componentes_maquinas.csv` | Cadastro de peças e subconjuntos críticos por equipamento | `componente_id`, `maquina_id` |
| **Manutenção** | `ordens_manutencao.csv` | Ordens de serviço (OM) com tipo, horas, custos e status | `om_id`, `maquina_id`, `componente_id` |
| **Manutenção** | `telemetria_preditiva.csv` | Leituras de temperatura, vibração e probabilidade de falha | `leitura_id`, `maquina_id`, `componente_id` |
| **Energia** | `tarifas_energia.csv` | Estrutura tarifária horária (Ponta, Fora Ponta, Madrugada) | `tarifa_id`, `posto_tarifario` |
| **Energia** | `metas_energia_equipamento.csv` | Metas de intensidade energética (kWh/unid) e IEE por máquina | `meta_id`, `maquina_id` |
| **Energia** | `consumo_energia_turno.csv` | Consumo por dia, máquina e turno; não é medição horária | `registro_id`, `maquina_id`, `turno_id` |
| **ESG** | `emissoes_co2.csv` | Histórico mensal de emissões totais e CO₂ evitado vs. meta | `registro_id`, `mes_ano` |
| **ESG** | `consumo_recursos_esg.csv` | Histórico mensal de água, resíduos reciclados e % renovável | `registro_id`, `mes_ano` |
| **ESG** | `projetos_investimento_verde.csv` | Portfólio de projetos CAPEX (Solar, Reuso de Água, LED) | `projeto_id` |
| **ESG** | `certificacoes_ambientais.csv` | Normas ISO 9001, ISO 14001, ISO 50001 e LEED com vigência | `certificacao_id` |
| **Financeiro** | `resultados_financeiros_mensais.csv` | Série mensal contínua e completa (DRE, ICPR e DPR) | `id`, `mes_ano` |

---

## 2. Mudanças Intencionais e Transição de Regime entre Períodos

Assim como nos dados originais do projeto, estes conjuntos incorporam variações intencionais de maturidade, tecnologia e custos ao longo do tempo:

1. **Parque de Máquinas:**
   - `periodo_2015_2016` e `periodo_2017_2020`: 4 máquinas (`1: ROBO SMT`, `2: ROBO PTH`, `3: ROBO SCARA`, `4: MAQUINA SOLDA`).
   - `periodo_2021_2025`: Adição da 5ª máquina (`5: ROBO COBOT`), totalizando 25 componentes monitorados.

2. **Maturidade da Manutenção:**
   - `2015_2016`: Predominância corretiva (60.8% corretiva, 39.2% preventiva, 0% preditiva). Custos por falha mais altos e maior tempo de reparo (MTTR ~4.1h).
   - `2017_2020`: Transição estruturada (52.9% preventiva, 38.8% corretiva, 8.3% preditiva). MTTR cai para ~3.2h.
   - `2021_2025`: Manutenção 4.0 plena (56.0% preventiva, 28.0% preditiva, apenas 16.0% corretiva). MTTR cai para ~2.4h.

3. **Gestão Energética e Tarifária:**
   - As tarifas refletem a inflação do setor elétrico brasileiro (tarifa de ponta evoluindo de R$ 0,65 para R$ 0,78 e R$ 0,92/kWh).
   - A desagregação horária em `gerados/` é **simulação** que preserva exatamente os totais por turno; não comprova deslocamento de carga ou economia realizada.

4. **Sustentabilidade & ESG:**
   - **Energia Renovável:** Evolui de 4.5% (2015–2016) para 15.5% (2017–2020) e alcança 27.1% (2021–2025) com a usina solar fotovoltaica própria.
   - **Água:** Consumo específico reduz de 3.17 m³/unid para 2.37 m³/unid através dos sistemas de reuso.
   - **CO₂ Evitado:** Salta de ~4.0 kg/mês para 38.1 kg/mês no período recente.
   - **Certificações:** Saída de uma ISO 14001 "Em Processo" para certificações ativas ISO 14001, ISO 50001 e processo LEED.

---

## 3. Arquivos gerados e regras

`../scripts/generate_canonical_csvs.py` cria dezessete arquivos por período em
`gerados/`: intervalos de energia, vínculos e novas ordens/paradas simuladas
de manutenção, alocação mensal de custo/receita por produto, eventos de
máquina/turno, metas ESG, resultados ESG por projeto, três cadastros mínimos
de referência, dois rateios de custos financeiros, custos horários estimados
para operadores sem tarifa, consumo operacional simulado, um resumo exclusivo
de estado de máquina e OEE de cenário por turno.
`composicao_tarifaria_inferida.csv` registra a
mistura 40% ponta/60% fora de ponta que reproduz os custos dos 1.087 registros
`MISTO_PONTA` originais dentro do arredondamento de centavos. Ela é uma
**inferência matemática**, não medição horária. Os 51 CSVs em `gerados/`
incluem nove cadastros de IDs observados e 42 arquivos sintéticos. As
alocações trazem coluna `origem`; nenhum deles substitui as observações originais.

- **Energia:** oito intervalos por registro de turno. A soma de kWh e custo
  reproduz cada linha de `consumo_energia_turno.csv`. A distribuição por hora
  é sintética; no período 2017–2020, a simulação aloca zero kWh nas horas de
  ponta do segundo turno para preservar o posto `FORA_PONTA` reportado.
- **Manutenção:** a regra escolhe, sem reutilizar, alertas do mesmo componente
  nos sete dias anteriores à ordem e paradas da mesma máquina a até um dia da
  abertura. Para alertas não pareados, cria ordens simuladas com IDs próprios;
  alertas críticos recebem também uma parada simulada. Isto gera associações
  **simuladas**, não prova que os registros originais tenham relação causal.
  Ordens originais sem par continuam sem vínculo.
- **Financeiro:** a receita e o CPV mensais são distribuídos entre produtos
  pelo peso da quantidade reportada nas operações daquele mês; a soma fecha
  exatamente os totais mensais. Essa quantidade não é produção final nem
  venda medida, e a margem por produto resultante é simulada.
- **Identificadores:** clientes, operadores e inspetores referenciados nas
  fontes recebem uma linha por ID e período. Operadores são a união dos IDs
  de operações e custos de mão de obra. `nome_exibicao_simulado` é um rótulo
  determinístico, como `Operador simulado P1-001`, e não o nome de uma pessoa.
  Os CSVs não têm identidade verificada; `identidade_cadastrada=false` explicita
  esse limite. Os IDs
  podem se repetir entre períodos e não identificam necessariamente a mesma pessoa.
- **Rateio de custos:** cada linha de `custos_producao` é distribuída entre
  produtos pela quantidade reportada nas operações do mês. Cada linha de
  `custos_indiretos_rateio` é distribuída entre máquinas pelas horas
  reportadas nas operações do mês, coerente com a base `Horas Maquina` da
  fonte. Cada rateio fecha ao centavo com sua linha de origem. São cenários
  de atribuição, não registros de custo real do produto ou da máquina, e
  não devem ser somados ao CPV já distribuído em
  `custos_produto_mensais_simulados.csv` como se fossem despesas adicionais.
- **Tarifas de operadores:** `custo_hora_operador_estimado.csv` cobre somente
  operadores presentes em operações e ausentes de `custo_mao_obra_historico`.
  A tarifa simulada usa a mediana das tarifas observadas no mesmo período,
  válida a partir da primeira operação daquele ID. Ela não informa salário
  nem custo real daquele operador.
- **Consumo de insumos:** `consumo_insumos_operacionais_simulado.csv` cria
  quantidades por linha de preço e máquina. Água usa 12 l/h, detergente 0,15
  l/h e lubrificante 0,08 l/h das horas reportadas de operação. Energia usa
  os kWh das operações; manutenção tecnológica usa a contagem de ordens no
  mês. Os fatores de água, detergente e lubrificante são premissas de cenário,
  sem medição de consumo. O CSV de origem anterior chamava energia e manutenção
  tecnológica de `l`; o canônico foi corrigido para `kWh` e `servico` e guarda
  o valor antigo em `unidade_medida_original`. O custo calculado
  resulta do preço unitário da fonte multiplicado pela quantidade simulada;
  não deve ser somado ao custo de energia ou ao CPV como despesa nova.
- **Produção:** eventos de setup/produção vêm dos intervalos e minutos de
  setup das operações originais; paradas vêm da fonte original. As unidades
  boas são uma hipótese sintética de 98%. Eventos de fontes diferentes podem
  se sobrepor; ainda não constituem uma linha de estado exclusivo da máquina
  nem um OEE observado.
- **Estado por turno:** `resumo_estado_maquina_turno_simulado.csv` varre os
  eventos derivados e aplica prioridade PARADA, depois SETUP, depois PRODUCAO.
  Cada turno com eventos fecha 28.800 segundos entre esses estados e
  SEM_EVENTO; `segundos_sobreposicao_fonte` preserva o conflito entre fontes.
  As unidades reportadas e boas simuladas ficam separadas do tempo exclusivo.
  O arquivo não afirma OEE real nem preenche turnos sem evento registrado.
- **OEE de cenário:** `oee_maquina_turno_simulado.csv` aplica a meta de
  produtividade da máquina e turno planejado de oito horas ao tempo exclusivo
  de produção. Disponibilidade = tempo exclusivo/tempo planejado; performance
  = unidades reportadas/(meta por hora × horas exclusivas), limitada a 100%;
  qualidade = unidades boas simuladas/unidades reportadas. O produto dessas
  três parcelas é o OEE simulado. O arquivo preserva a performance bruta,
  marca cortes acima de 100%, conflitos de tempo e metas usadas fora da
  vigência por turnos que cruzam o limite do período. Não é OEE medido.
- **ESG:** metas sintéticas usam o primeiro mês do período como base; a meta
  de emissão já presente no CSV é preservada. Resultados de projetos são
  atribuições sintéticas por categoria após aprovação do projeto e não medem
  efeito causal ou economia financeira realizada.

Nesta revisão, a atribuição de resultados a projetos ESG ficou fora do escopo;
o arquivo sintético anterior foi mantido, sem nova regra ou comprovação.
Continuam sem fonte factual os nomes/identidades das pessoas, o consumo
real de cada insumo, as tarifas reais dos operadores sem registro, medições
horárias reais de energia, causalidade histórica alerta-ordem-parada e OEE
observado com unidades boas medidas. Os arquivos novos oferecem cenários
reproduzíveis, não observações desses fatos.

Para verificar os arquivos existentes, sem conexão ao banco:

```powershell
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/validate_canonical_csvs.py
BancoModeloUse/.venv/Scripts/python.exe BancoModeloUse/scripts/canonical_ingest.py plan
```

A carga canônica foi executada em 31/10/2026 e reconciliada com o checkout
principal em 07/11/2026; o [readback atual](../../docs/evidence/organizacao-2026-11-07/canonical-readback.json)
confere o banco existente. O carregador vigente é `canonical_ingest.py`.
`generate_canonical_csvs.py` preserva as regras da geração e fornece funções
ao validador; não é um comando de uso cotidiano. Regenerar altera arquivos e
manifestos, exige uma mudança própria e preservação do pacote anterior.
