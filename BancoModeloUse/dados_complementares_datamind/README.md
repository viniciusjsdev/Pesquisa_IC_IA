# Dados Complementares para a Plataforma V&N DataMind

Este diretório contém os conjuntos de dados em formato CSV desenvolvidos para preencher todas as lacunas identificadas entre a base original do projeto e os requisitos da plataforma analítica **V&N DataMind**.

Para preservar a integridade estrita e o fingerprint SHA-256 dos 75 CSVs congelados originais de `BancoModeloUse/dados_simulados/`, estes arquivos foram estruturados em pastas correspondentes aos três períodos do projeto:

- `periodo_2015_2016/` (Período 0 - Linha de Base / Início da Operação)
- `periodo_2017_2020/` (Período 1 - Modernização e Transição Digital)
- `periodo_2021_2025/` (Período 2 - Indústria 4.0 Plena e Expansão com Robô Cobot)

---

## 1. Inventário de Arquivos por Período (16 CSVs por pasta = 48 arquivos)

| Domínio | Arquivo | Grão / Descrição | Chaves Estrangeiras de Integração |
| :--- | :--- | :--- | :--- |
| **Operações** | `turnos_trabalho.csv` | 1 linha por turno (1º, 2º e 3º) com horários e metas | `turno_id` |
| **Operações** | `metas_producao_maquina.csv` | Metas de produtividade, OEE, disponibilidade por máquina | `maquina_id` |
| **Manutenção** | `componentes_maquinas.csv` | Cadastro de peças e subconjuntos críticos por equipamento | `componente_id`, `maquina_id` |
| **Manutenção** | `ordens_manutencao.csv` | Ordens de serviço (OM) com tipo, horas, custos e status | `om_id`, `maquina_id`, `componente_id` |
| **Manutenção** | `telemetria_preditiva.csv` | Leituras de temperatura, vibração e probabilidade de falha | `leitura_id`, `maquina_id`, `componente_id` |
| **Energia** | `tarifas_energia.csv` | Estrutura tarifária horária (Ponta, Fora Ponta, Madrugada) | `tarifa_id`, `posto_tarifario` |
| **Energia** | `metas_energia_equipamento.csv` | Metas de intensidade energética (kWh/unid) e IEE por máquina | `meta_id`, `maquina_id` |
| **Energia** | `consumo_energia_horario.csv` | Consumo por máquina, turno, posto tarifário e custo apurado | `registro_id`, `maquina_id`, `turno_id` |
| **ESG** | `emissoes_co2.csv` | Histórico mensal de emissões totais e CO₂ evitado vs. meta | `registro_id`, `mes_ano` |
| **ESG** | `consumo_recursos_esg.csv` | Histórico mensal de água, resíduos reciclados e % renovável | `registro_id`, `mes_ano` |
| **ESG** | `projetos_investimento_verde.csv` | Portfólio de projetos CAPEX (Solar, Reuso de Água, LED) | `projeto_id` |
| **ESG** | `certificacoes_ambientais.csv` | Normas ISO 9001, ISO 14001, ISO 50001 e LEED com vigência | `certificacao_id` |
| **IA & Governança** | `ia_modelos_registry.csv` | Catálogo de modelos (Falhas, Energia, Anomalias, Financeiro) | `modelo_id` |
| **IA & Governança** | `ia_insights_log.csv` | Log de anomalias e diagnósticos com severidade e impacto R$ | `insight_id`, `modelo_id`, `maquina_id`, `produto_id` |
| **IA & Governança** | `ia_impacto_mensal.csv` | Histórico mensal de economia gerada pela IA e taxa de ações | `registro_id`, `mes_ano` |
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
   - No período 2021–2025, o consumo em horário de ponta (18h às 21h nos dias úteis) é ativamente deslocado, reduzindo a carga em 15–20% e gerando economia comprovada no card de energia.

4. **Sustentabilidade & ESG:**
   - **Energia Renovável:** Evolui de 4.5% (2015–2016) para 15.5% (2017–2020) e alcança 27.1% (2021–2025) com a usina solar fotovoltaica própria.
   - **Água:** Consumo específico reduz de 3.17 m³/unid para 2.37 m³/unid através dos sistemas de reuso.
   - **CO₂ Evitado:** Salta de ~4.0 kg/mês para 38.1 kg/mês no período recente.
   - **Certificações:** Saída de uma ISO 14001 "Em Processo" para certificações ativas ISO 14001, ISO 50001 e processo LEED.

5. **Inteligência Artificial & ROI:**
   - `2015_2016`: Modelos em fase de concepção e planejamento (acurácia baseline 74%, economia residual).
   - `2017_2020`: Primeiros modelos pilotos ativos (Detector de Anomalias e Otimizador de Energia), gerando ~R$ 10.800/mês.
   - `2021_2025`: Ecossistema de IA maduro com 4 modelos e acurácia média de 91.2%, gerando ~R$ 28.150/mês de economia registrada.

---

## 3. Guia de Integração e Modelagem DW

Para incorporar estes dados ao Data Warehouse (`db_pesquisa_dw`):
1. **Dimensões a criar:** `dim_turno`, `dim_componente_maquina`, `dim_posto_tarifario`, `dim_modelo_ia`, `dim_projeto_esg`, `dim_certificacao`.
2. **Fatos a criar:**
   - `fact_maintenance_order` (ligando a `dim_machine`, `dim_componente_maquina` e `dim_day`).
   - `fact_telemetry_reading` (ligando a `dim_machine` e `dim_componente_maquina`).
   - `fact_energy_hourly_consumption` (ligando a `dim_machine`, `dim_turno`, `dim_posto_tarifario` e `dim_day`).
   - `fact_esg_monthly_summary` (ligando a `dim_day`).
   - `fact_ai_insight` (ligando a `dim_modelo_ia`, `dim_machine` e `dim_product`).
3. **Chaves Primárias por Período:** Seguir o padrão do projeto:
   $$\text{ID}_{\text{DW}} = \text{ID}_{\text{original}} + (\text{indice\_periodo} \times 1.000.000)$$
