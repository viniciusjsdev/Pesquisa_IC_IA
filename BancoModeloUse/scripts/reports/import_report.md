# Relatório de Importação - 2025-10-25T21:02:33.936478 UTC
- Modo: Dry-Run
- CSVs encontrados: 75
- CSVs processados: 75
- Sucessos: 72 | Skips: 3 | Erros: 0

## Detalhes por arquivo
### BancoModeloUse/dados_simulados/dados_financeiros_2015_2016/contas_contabeis.csv
- Status: ok
- Tabela alvo: `contas_contabeis` (financeiro)
- Colunas CSV: conta_id, numero_conta, nome_conta, tipo_conta
- Colunas modelo: conta_id, numero_conta, nome_conta, tipo_conta, data_registro
- Faltando no CSV: data_registro
- Linhas no CSV: 7
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2015_2016/custo_mao_obra_historico.csv
- Status: ok
- Tabela alvo: `custo_mao_obra_historico` (financeiro)
- Colunas CSV: custo_mo_id, operador_id, custo_hora, data_vigencia, tipo_custo
- Colunas modelo: custo_mo_id, operador_id, custo_hora, data_vigencia, tipo_custo
- Linhas no CSV: 10
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2015_2016/custos_indiretos_rateio.csv
- Status: ok
- Tabela alvo: `custos_indiretos_rateio` (financeiro)
- Colunas CSV: rateio_id, descricao, custo_total_mes, base_rateio, data_referencia
- Colunas modelo: rateio_id, descricao, custo_total_mes, base_rateio, data_referencia
- Linhas no CSV: 12
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2015_2016/custos_operacionais_variaveis.csv
- Status: ok
- Tabela alvo: `custos_operacionais_variaveis` (financeiro)
- Colunas CSV: custo_operacional_id, insumo, valor_unitario, unidade_medida, data_leitura
- Colunas modelo: custo_operacional_id, insumo, valor_unitario, unidade_medida, data_leitura
- Linhas no CSV: 24
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2015_2016/custos_padrao.csv
- Status: ok
- Tabela alvo: `custos_padrao` (financeiro)
- Colunas CSV: custo_padrao_id, tipo_custo, unidade_medida, valor_unitario_padrao, data_vigencia
- Colunas modelo: custo_padrao_id, tipo_custo, unidade_medida, valor_unitario_padrao, data_vigencia, data_registro
- Faltando no CSV: data_registro
- Linhas no CSV: 5
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2015_2016/custos_producao.csv
- Status: ok
- Tabela alvo: `custos_producao` (financeiro)
- Colunas CSV: id, materia_prima, mao_obra_direta, custos_indiretos, estoque_inicial_elaboracao, estoque_final_elaboracao, estoque_inicial_acabados, estoque_final_acabados, unidades_produzidas, custo_total, custo_unitario, data_registro
- Colunas modelo: id, materia_prima, mao_obra_direta, custos_indiretos, estoque_inicial_elaboracao, estoque_final_elaboracao, estoque_inicial_acabados, estoque_final_acabados, unidades_produzidas, custo_total, custo_unitario, data_registro
- Linhas no CSV: 12
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2015_2016/kpis_gerenciais.csv
- Status: ok
- Tabela alvo: `kpis_gerenciais` (financeiro)
- Colunas CSV: kpi_id, nome_kpi, valor_kpi, data_referencia
- Colunas modelo: kpi_id, nome_kpi, valor_kpi, data_referencia
- Linhas no CSV: 12
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2015_2016/lancamentos_financeiros.csv
- Status: ok
- Tabela alvo: `lancamentos_financeiros` (financeiro)
- Colunas CSV: lancamento_id, conta_id, data_lancamento, valor, descricao
- Colunas modelo: lancamento_id, conta_id, data_lancamento, valor, descricao
- Linhas no CSV: 30
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2015_2016/materiais_custo_historico.csv
- Status: ok
- Tabela alvo: `materiais_custo_historico` (financeiro)
- Colunas CSV: custo_material_id, material_id, custo_unitario, data_compra, lote_material_id
- Colunas modelo: custo_material_id, material_id, custo_unitario, data_compra, lote_material_id
- Linhas no CSV: 20
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2015_2016/resultados_financeiros.csv
- Status: ok
- Tabela alvo: `resultados_financeiros` (financeiro)
- Colunas CSV: id, receita_total, custos_variaveis, despesas_variaveis, custos_fixos, despesas_operacionais, juros, impostos, custo_ativo, valor_residual, vida_util_anos, custo_investimento, ativos_circulantes, passivos_circulantes, margem_contribuicao, ponto_equilibrio, lucro_bruto, lucro_liquido, depreciacao_anual, roi_percentual, capital_de_giro, data_registro
- Colunas modelo: id, receita_total, custos_variaveis, despesas_variaveis, custos_fixos, despesas_operacionais, juros, impostos, custo_ativo, valor_residual, vida_util_anos, custo_investimento, ativos_circulantes, passivos_circulantes, margem_contribuicao, ponto_equilibrio, lucro_bruto, lucro_liquido, depreciacao_anual, roi_percentual, capital_de_giro, data_registro
- Linhas no CSV: 12
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2015_2016/vendas.csv
- Status: ok
- Tabela alvo: `vendas` (financeiro)
- Colunas CSV: venda_id, produto_id, quantidade_vendida, preco_unitario_venda, data_venda, cliente_id
- Colunas modelo: venda_id, produto_id, quantidade_vendida, preco_unitario_venda, data_venda, cliente_id
- Linhas no CSV: 20
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2017_2020/contas_contabeis.csv
- Status: ok
- Tabela alvo: `contas_contabeis` (financeiro)
- Colunas CSV: conta_id, numero_conta, nome_conta, tipo_conta
- Colunas modelo: conta_id, numero_conta, nome_conta, tipo_conta, data_registro
- Faltando no CSV: data_registro
- Linhas no CSV: 10
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2017_2020/custo_mao_obra_historico.csv
- Status: ok
- Tabela alvo: `custo_mao_obra_historico` (financeiro)
- Colunas CSV: custo_mo_id, operador_id, custo_hora, data_vigencia, tipo_custo
- Colunas modelo: custo_mo_id, operador_id, custo_hora, data_vigencia, tipo_custo
- Linhas no CSV: 19
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2017_2020/custos_indiretos_rateio.csv
- Status: ok
- Tabela alvo: `custos_indiretos_rateio` (financeiro)
- Colunas CSV: rateio_id, descricao, custo_total_mes, base_rateio, data_referencia
- Colunas modelo: rateio_id, descricao, custo_total_mes, base_rateio, data_referencia
- Linhas no CSV: 48
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2017_2020/custos_operacionais_variaveis.csv
- Status: ok
- Tabela alvo: `custos_operacionais_variaveis` (financeiro)
- Colunas CSV: custo_operacional_id, insumo, valor_unitario, unidade_medida, data_leitura
- Colunas modelo: custo_operacional_id, insumo, valor_unitario, unidade_medida, data_leitura
- Linhas no CSV: 47
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2017_2020/custos_padrao.csv
- Status: ok
- Tabela alvo: `custos_padrao` (financeiro)
- Colunas CSV: custo_padrao_id, tipo_custo, unidade_medida, valor_unitario_padrao, data_vigencia
- Colunas modelo: custo_padrao_id, tipo_custo, unidade_medida, valor_unitario_padrao, data_vigencia, data_registro
- Faltando no CSV: data_registro
- Linhas no CSV: 5
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2017_2020/custos_producao.csv
- Status: ok
- Tabela alvo: `custos_producao` (financeiro)
- Colunas CSV: id, materia_prima, mao_obra_direta, custos_indiretos, estoque_inicial_elaboracao, estoque_final_elaboracao, estoque_inicial_acabados, estoque_final_acabados, unidades_produzidas, custo_total, custo_unitario, data_registro
- Colunas modelo: id, materia_prima, mao_obra_direta, custos_indiretos, estoque_inicial_elaboracao, estoque_final_elaboracao, estoque_inicial_acabados, estoque_final_acabados, unidades_produzidas, custo_total, custo_unitario, data_registro
- Linhas no CSV: 24
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2017_2020/kpis_gerenciais.csv
- Status: ok
- Tabela alvo: `kpis_gerenciais` (financeiro)
- Colunas CSV: kpi_id, nome_kpi, valor_kpi, data_referencia
- Colunas modelo: kpi_id, nome_kpi, valor_kpi, data_referencia
- Linhas no CSV: 196
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2017_2020/lancamentos_financeiros.csv
- Status: ok
- Tabela alvo: `lancamentos_financeiros` (financeiro)
- Colunas CSV: lancamento_id, conta_id, data_lancamento, valor, descricao
- Colunas modelo: lancamento_id, conta_id, data_lancamento, valor, descricao
- Linhas no CSV: 60
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2017_2020/materiais_custo_historico.csv
- Status: ok
- Tabela alvo: `materiais_custo_historico` (financeiro)
- Colunas CSV: custo_material_id, material_id, custo_unitario, data_compra, lote_material_id
- Colunas modelo: custo_material_id, material_id, custo_unitario, data_compra, lote_material_id
- Linhas no CSV: 60
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2017_2020/resultados_financeiros.csv
- Status: ok
- Tabela alvo: `resultados_financeiros` (financeiro)
- Colunas CSV: id, receita_total, custos_variaveis, despesas_variaveis, custos_fixos, despesas_operacionais, juros, impostos, custo_ativo, valor_residual, vida_util_anos, custo_investimento, ativos_circulantes, passivos_circulantes, margem_contribuicao, ponto_equilibrio, lucro_bruto, lucro_liquido, depreciacao_anual, roi_percentual, capital_de_giro, data_registro
- Colunas modelo: id, receita_total, custos_variaveis, despesas_variaveis, custos_fixos, despesas_operacionais, juros, impostos, custo_ativo, valor_residual, vida_util_anos, custo_investimento, ativos_circulantes, passivos_circulantes, margem_contribuicao, ponto_equilibrio, lucro_bruto, lucro_liquido, depreciacao_anual, roi_percentual, capital_de_giro, data_registro
- Linhas no CSV: 24
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2017_2020/vendas.csv
- Status: ok
- Tabela alvo: `vendas` (financeiro)
- Colunas CSV: venda_id, produto_id, quantidade_vendida, preco_unitario_venda, data_venda, cliente_id
- Colunas modelo: venda_id, produto_id, quantidade_vendida, preco_unitario_venda, data_venda, cliente_id
- Linhas no CSV: 40
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2021_2025/contas_contabeis.csv
- Status: ok
- Tabela alvo: `contas_contabeis` (financeiro)
- Colunas CSV: conta_id, numero_conta, nome_conta, tipo_conta
- Colunas modelo: conta_id, numero_conta, nome_conta, tipo_conta, data_registro
- Faltando no CSV: data_registro
- Linhas no CSV: 12
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2021_2025/custo_mao_obra_historico.csv
- Status: ok
- Tabela alvo: `custo_mao_obra_historico` (financeiro)
- Colunas CSV: custo_mo_id, operador_id, custo_hora, data_vigencia, tipo_custo
- Colunas modelo: custo_mo_id, operador_id, custo_hora, data_vigencia, tipo_custo
- Linhas no CSV: 39
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2021_2025/custos_indiretos_rateio.csv
- Status: ok
- Tabela alvo: `custos_indiretos_rateio` (financeiro)
- Colunas CSV: rateio_id, descricao, custo_total_mes, base_rateio, data_referencia
- Colunas modelo: rateio_id, descricao, custo_total_mes, base_rateio, data_referencia
- Linhas no CSV: 60
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2021_2025/custos_operacionais_variaveis.csv
- Status: ok
- Tabela alvo: `custos_operacionais_variaveis` (financeiro)
- Colunas CSV: custo_operacional_id, insumo, valor_unitario, unidade_medida, data_leitura
- Colunas modelo: custo_operacional_id, insumo, valor_unitario, unidade_medida, data_leitura
- Linhas no CSV: 71
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2021_2025/custos_padrao.csv
- Status: ok
- Tabela alvo: `custos_padrao` (financeiro)
- Colunas CSV: custo_padrao_id, tipo_custo, unidade_medida, valor_unitario_padrao, data_vigencia
- Colunas modelo: custo_padrao_id, tipo_custo, unidade_medida, valor_unitario_padrao, data_vigencia, data_registro
- Faltando no CSV: data_registro
- Linhas no CSV: 5
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2021_2025/custos_producao.csv
- Status: ok
- Tabela alvo: `custos_producao` (financeiro)
- Colunas CSV: id, materia_prima, mao_obra_direta, custos_indiretos, estoque_inicial_elaboracao, estoque_final_elaboracao, estoque_inicial_acabados, estoque_final_acabados, unidades_produzidas, custo_total, custo_unitario, data_registro
- Colunas modelo: id, materia_prima, mao_obra_direta, custos_indiretos, estoque_inicial_elaboracao, estoque_final_elaboracao, estoque_inicial_acabados, estoque_final_acabados, unidades_produzidas, custo_total, custo_unitario, data_registro
- Linhas no CSV: 36
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2021_2025/kpis_gerenciais.csv
- Status: ok
- Tabela alvo: `kpis_gerenciais` (financeiro)
- Colunas CSV: kpi_id, nome_kpi, valor_kpi, data_referencia
- Colunas modelo: kpi_id, nome_kpi, valor_kpi, data_referencia
- Linhas no CSV: 244
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2021_2025/lancamentos_financeiros.csv
- Status: ok
- Tabela alvo: `lancamentos_financeiros` (financeiro)
- Colunas CSV: lancamento_id, conta_id, data_lancamento, valor, descricao
- Colunas modelo: lancamento_id, conta_id, data_lancamento, valor, descricao
- Linhas no CSV: 100
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2021_2025/materiais_custo_historico.csv
- Status: ok
- Tabela alvo: `materiais_custo_historico` (financeiro)
- Colunas CSV: custo_material_id, material_id, custo_unitario, data_compra, lote_material_id
- Colunas modelo: custo_material_id, material_id, custo_unitario, data_compra, lote_material_id
- Linhas no CSV: 100
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2021_2025/resultados_financeiros.csv
- Status: ok
- Tabela alvo: `resultados_financeiros` (financeiro)
- Colunas CSV: id, receita_total, custos_variaveis, despesas_variaveis, custos_fixos, despesas_operacionais, juros, impostos, custo_ativo, valor_residual, vida_util_anos, custo_investimento, ativos_circulantes, passivos_circulantes, margem_contribuicao, ponto_equilibrio, lucro_bruto, lucro_liquido, depreciacao_anual, roi_percentual, capital_de_giro, data_registro
- Colunas modelo: id, receita_total, custos_variaveis, despesas_variaveis, custos_fixos, despesas_operacionais, juros, impostos, custo_ativo, valor_residual, vida_util_anos, custo_investimento, ativos_circulantes, passivos_circulantes, margem_contribuicao, ponto_equilibrio, lucro_bruto, lucro_liquido, depreciacao_anual, roi_percentual, capital_de_giro, data_registro
- Linhas no CSV: 36
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_financeiros_2021_2025/vendas.csv
- Status: ok
- Tabela alvo: `vendas` (financeiro)
- Colunas CSV: venda_id, produto_id, quantidade_vendida, preco_unitario_venda, data_venda, cliente_id
- Colunas modelo: venda_id, produto_id, quantidade_vendida, preco_unitario_venda, data_venda, cliente_id
- Linhas no CSV: 60
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/consumo_materiais.csv
- Status: ok
- Tabela alvo: `consumo_materiais` (industrial)
- Colunas CSV: consumo_id, registro_id, material_id, lote_material_id, quantidade_consumida, data_registro
- Colunas modelo: consumo_id, registro_id, material_id, lote_material_id, quantidade_consumida
- Extras no CSV: data_registro
- Linhas no CSV: 300
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/controle_qualidade.csv
- Status: ok
- Tabela alvo: `controle_qualidade` (industrial)
- Colunas CSV: controle_id, lote_producao_id, data_inspecao, inspetor_id, unidades_aprovadas, unidades_rejeitadas, motivo_rejeicao
- Colunas modelo: controle_id, lote_producao_id, data_inspecao, inspetor_id, unidades_aprovadas, unidades_rejeitadas, motivo_rejeicao
- Linhas no CSV: 732
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/equipamentos.csv
- Status: ok
- Tabela alvo: `equipamentos` (industrial)
- Colunas CSV: id, nome, disponibilidade, performance, qualidade, oee, taxa_producao, capacidade_producao, eficiencia_linha, produtividade_mao_obra, data_registro
- Colunas modelo: id, nome, disponibilidade, performance, qualidade, oee, taxa_producao, capacidade_producao, eficiencia_linha, produtividade_mao_obra, data_registro
- Linhas no CSV: 17545
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/fornecedores.csv
- Status: ok
- Tabela alvo: `fornecedores` (industrial)
- Colunas CSV: fornecedor_id, nome_fornecedor, data_registro
- Colunas modelo: fornecedor_id, nome_fornecedor, data_registro
- Linhas no CSV: 10
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/lotes_materiais.csv
- Status: ok
- Tabela alvo: `lotes_materiais` (industrial)
- Colunas CSV: lote_id, material_id, fornecedor_id, data_recebimento, lote_fornecedor
- Colunas modelo: lote_id, material_id, fornecedor_id, data_recebimento, lote_fornecedor
- Linhas no CSV: 100
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/lotes_producao.csv
- Status: ok
- Tabela alvo: `lotes_producao` (industrial)
- Colunas CSV: lote_producao_id, ordem_producao_id, data_lote, quantidade_total
- Colunas modelo: lote_producao_id, ordem_producao_id, data_lote, quantidade_total
- Linhas no CSV: 100
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/maquinas.csv
- Status: ok
- Tabela alvo: `maquinas` (industrial)
- Colunas CSV: maquina_id, nome_maquina, linha_producao, capacidade_producao_max, data_registro
- Colunas modelo: maquina_id, nome_maquina, linha_producao, capacidade_producao_max, data_registro
- Linhas no CSV: 4
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/materiais.csv
- Status: ok
- Tabela alvo: `materiais` (industrial)
- Colunas CSV: material_id, nome_material, unidade_medida, data_registro
- Colunas modelo: material_id, nome_material, unidade_medida, data_registro
- Linhas no CSV: 10
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/ordens_producao.csv
- Status: ok
- Tabela alvo: `ordens_producao` (industrial)
- Colunas CSV: ordem_producao_id, produto_id, quantidade_planejada, data_planejamento, data_inicio_real, data_fim_real, status_ordem
- Colunas modelo: ordem_producao_id, produto_id, quantidade_planejada, data_planejamento, data_inicio_real, data_fim_real, status_ordem, data_registro
- Faltando no CSV: data_registro
- Linhas no CSV: 100
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/paradas_maquinas.csv
- Status: ok
- Tabela alvo: `paradas_maquinas` (industrial)
- Colunas CSV: parada_id, maquina_id, hora_inicio_parada, hora_fim_parada, motivo_parada, data_registro
- Colunas modelo: parada_id, maquina_id, hora_inicio_parada, hora_fim_parada, motivo_parada, data_registro
- Linhas no CSV: 200
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/processo_industrial.csv
- Status: skipped
- Erro: Nenhuma tabela ORM correspondente encontrada pelo nome do arquivo

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/produtos.csv
- Status: ok
- Tabela alvo: `produtos` (industrial)
- Colunas CSV: produto_id, nome_produto, descricao, unidade_medida, data_registro
- Colunas modelo: produto_id, nome_produto, descricao, unidade_medida, data_registro
- Linhas no CSV: 5
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/registros_operacao.csv
- Status: ok
- Tabela alvo: `registros_operacao` (industrial)
- Colunas CSV: registro_id, ordem_producao_id, maquina_id, operador_id, hora_inicio, hora_fim, tempo_setup_real_min, quantidade_produzida_real, consumo_energia_kwh, data_registro
- Colunas modelo: registro_id, ordem_producao_id, maquina_id, operador_id, hora_inicio, hora_fim, tempo_setup_real_min, quantidade_produzida_real, consumo_energia_kwh, data_registro
- Linhas no CSV: 70180
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2015_2017/roteiros_producao.csv
- Status: ok
- Tabela alvo: `roteiros_producao` (industrial)
- Colunas CSV: roteiro_id, produto_id, versao, data_registro
- Colunas modelo: roteiro_id, produto_id, versao, data_registro
- Linhas no CSV: 5
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/consumo_materiais.csv
- Status: ok
- Tabela alvo: `consumo_materiais` (industrial)
- Colunas CSV: consumo_id, registro_id, material_id, lote_material_id, quantidade_consumida, data_registro
- Colunas modelo: consumo_id, registro_id, material_id, lote_material_id, quantidade_consumida
- Extras no CSV: data_registro
- Linhas no CSV: 600
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/controle_qualidade.csv
- Status: ok
- Tabela alvo: `controle_qualidade` (industrial)
- Colunas CSV: controle_id, lote_producao_id, data_inspecao, inspetor_id, unidades_aprovadas, unidades_rejeitadas, motivo_rejeicao
- Colunas modelo: controle_id, lote_producao_id, data_inspecao, inspetor_id, unidades_aprovadas, unidades_rejeitadas, motivo_rejeicao
- Linhas no CSV: 1462
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/equipamentos.csv
- Status: ok
- Tabela alvo: `equipamentos` (industrial)
- Colunas CSV: id, nome, disponibilidade, performance, qualidade, oee, taxa_producao, capacidade_producao, eficiencia_linha, produtividade_mao_obra, data_registro
- Colunas modelo: id, nome, disponibilidade, performance, qualidade, oee, taxa_producao, capacidade_producao, eficiencia_linha, produtividade_mao_obra, data_registro
- Linhas no CSV: 35065
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/fornecedores.csv
- Status: ok
- Tabela alvo: `fornecedores` (industrial)
- Colunas CSV: fornecedor_id, nome_fornecedor, data_registro
- Colunas modelo: fornecedor_id, nome_fornecedor, data_registro
- Linhas no CSV: 20
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/lotes_materiais.csv
- Status: ok
- Tabela alvo: `lotes_materiais` (industrial)
- Colunas CSV: lote_id, material_id, fornecedor_id, data_recebimento, lote_fornecedor
- Colunas modelo: lote_id, material_id, fornecedor_id, data_recebimento, lote_fornecedor
- Linhas no CSV: 200
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/lotes_producao.csv
- Status: ok
- Tabela alvo: `lotes_producao` (industrial)
- Colunas CSV: lote_producao_id, ordem_producao_id, data_lote, quantidade_total
- Colunas modelo: lote_producao_id, ordem_producao_id, data_lote, quantidade_total
- Linhas no CSV: 200
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/maquinas.csv
- Status: ok
- Tabela alvo: `maquinas` (industrial)
- Colunas CSV: maquina_id, nome_maquina, linha_producao, capacidade_producao_max, data_registro
- Colunas modelo: maquina_id, nome_maquina, linha_producao, capacidade_producao_max, data_registro
- Linhas no CSV: 4
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/materiais.csv
- Status: ok
- Tabela alvo: `materiais` (industrial)
- Colunas CSV: material_id, nome_material, unidade_medida, data_registro
- Colunas modelo: material_id, nome_material, unidade_medida, data_registro
- Linhas no CSV: 10
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/ordens_producao.csv
- Status: ok
- Tabela alvo: `ordens_producao` (industrial)
- Colunas CSV: ordem_producao_id, produto_id, quantidade_planejada, data_planejamento, data_inicio_real, data_fim_real, status_ordem
- Colunas modelo: ordem_producao_id, produto_id, quantidade_planejada, data_planejamento, data_inicio_real, data_fim_real, status_ordem, data_registro
- Faltando no CSV: data_registro
- Linhas no CSV: 200
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/paradas_maquinas.csv
- Status: ok
- Tabela alvo: `paradas_maquinas` (industrial)
- Colunas CSV: parada_id, maquina_id, hora_inicio_parada, hora_fim_parada, motivo_parada, data_registro
- Colunas modelo: parada_id, maquina_id, hora_inicio_parada, hora_fim_parada, motivo_parada, data_registro
- Linhas no CSV: 400
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/processo_industrial.csv
- Status: skipped
- Erro: Nenhuma tabela ORM correspondente encontrada pelo nome do arquivo

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/produtos.csv
- Status: ok
- Tabela alvo: `produtos` (industrial)
- Colunas CSV: produto_id, nome_produto, descricao, unidade_medida, data_registro
- Colunas modelo: produto_id, nome_produto, descricao, unidade_medida, data_registro
- Linhas no CSV: 5
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/registros_operacao.csv
- Status: ok
- Tabela alvo: `registros_operacao` (industrial)
- Colunas CSV: registro_id, ordem_producao_id, maquina_id, operador_id, hora_inicio, hora_fim, tempo_setup_real_min, quantidade_produzida_real, consumo_energia_kwh, data_registro
- Colunas modelo: registro_id, ordem_producao_id, maquina_id, operador_id, hora_inicio, hora_fim, tempo_setup_real_min, quantidade_produzida_real, consumo_energia_kwh, data_registro
- Linhas no CSV: 140260
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronica_2017_2020/roteiros_producao.csv
- Status: ok
- Tabela alvo: `roteiros_producao` (industrial)
- Colunas CSV: roteiro_id, produto_id, versao, data_registro
- Colunas modelo: roteiro_id, produto_id, versao, data_registro
- Linhas no CSV: 10
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/consumo_materiais.csv
- Status: ok
- Tabela alvo: `consumo_materiais` (industrial)
- Colunas CSV: consumo_id, registro_id, material_id, lote_material_id, quantidade_consumida, data_registro
- Colunas modelo: consumo_id, registro_id, material_id, lote_material_id, quantidade_consumida
- Extras no CSV: data_registro
- Linhas no CSV: 900
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/controle_qualidade.csv
- Status: ok
- Tabela alvo: `controle_qualidade` (industrial)
- Colunas CSV: controle_id, lote_producao_id, data_inspecao, inspetor_id, unidades_aprovadas, unidades_rejeitadas, motivo_rejeicao
- Colunas modelo: controle_id, lote_producao_id, data_inspecao, inspetor_id, unidades_aprovadas, unidades_rejeitadas, motivo_rejeicao
- Linhas no CSV: 1827
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/equipamentos.csv
- Status: ok
- Tabela alvo: `equipamentos` (industrial)
- Colunas CSV: id, nome, disponibilidade, performance, qualidade, oee, taxa_producao, capacidade_producao, eficiencia_linha, produtividade_mao_obra, data_registro
- Colunas modelo: id, nome, disponibilidade, performance, qualidade, oee, taxa_producao, capacidade_producao, eficiencia_linha, produtividade_mao_obra, data_registro
- Linhas no CSV: 43825
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/fornecedores.csv
- Status: ok
- Tabela alvo: `fornecedores` (industrial)
- Colunas CSV: fornecedor_id, nome_fornecedor, data_registro
- Colunas modelo: fornecedor_id, nome_fornecedor, data_registro
- Linhas no CSV: 30
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/lotes_materiais.csv
- Status: ok
- Tabela alvo: `lotes_materiais` (industrial)
- Colunas CSV: lote_id, material_id, fornecedor_id, data_recebimento, lote_fornecedor
- Colunas modelo: lote_id, material_id, fornecedor_id, data_recebimento, lote_fornecedor
- Linhas no CSV: 350
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/lotes_producao.csv
- Status: ok
- Tabela alvo: `lotes_producao` (industrial)
- Colunas CSV: lote_producao_id, ordem_producao_id, data_lote, quantidade_total
- Colunas modelo: lote_producao_id, ordem_producao_id, data_lote, quantidade_total
- Linhas no CSV: 350
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/maquinas.csv
- Status: ok
- Tabela alvo: `maquinas` (industrial)
- Colunas CSV: maquina_id, nome_maquina, linha_producao, capacidade_producao_max, data_registro
- Colunas modelo: maquina_id, nome_maquina, linha_producao, capacidade_producao_max, data_registro
- Linhas no CSV: 5
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/materiais.csv
- Status: ok
- Tabela alvo: `materiais` (industrial)
- Colunas CSV: material_id, nome_material, unidade_medida, data_registro
- Colunas modelo: material_id, nome_material, unidade_medida, data_registro
- Linhas no CSV: 10
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/ordens_producao.csv
- Status: ok
- Tabela alvo: `ordens_producao` (industrial)
- Colunas CSV: ordem_producao_id, produto_id, quantidade_planejada, data_planejamento, data_inicio_real, data_fim_real, status_ordem
- Colunas modelo: ordem_producao_id, produto_id, quantidade_planejada, data_planejamento, data_inicio_real, data_fim_real, status_ordem, data_registro
- Faltando no CSV: data_registro
- Linhas no CSV: 350
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/paradas_maquinas.csv
- Status: ok
- Tabela alvo: `paradas_maquinas` (industrial)
- Colunas CSV: parada_id, maquina_id, hora_inicio_parada, hora_fim_parada, motivo_parada, data_registro
- Colunas modelo: parada_id, maquina_id, hora_inicio_parada, hora_fim_parada, motivo_parada, data_registro
- Linhas no CSV: 600
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/processo_industrial.csv
- Status: skipped
- Erro: Nenhuma tabela ORM correspondente encontrada pelo nome do arquivo

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/produtos.csv
- Status: ok
- Tabela alvo: `produtos` (industrial)
- Colunas CSV: produto_id, nome_produto, descricao, unidade_medida, data_registro
- Colunas modelo: produto_id, nome_produto, descricao, unidade_medida, data_registro
- Linhas no CSV: 5
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/registros_operacao.csv
- Status: ok
- Tabela alvo: `registros_operacao` (industrial)
- Colunas CSV: registro_id, ordem_producao_id, maquina_id, operador_id, hora_inicio, hora_fim, tempo_setup_real_min, quantidade_produzida_real, consumo_energia_kwh, data_registro
- Colunas modelo: registro_id, ordem_producao_id, maquina_id, operador_id, hora_inicio, hora_fim, tempo_setup_real_min, quantidade_produzida_real, consumo_energia_kwh, data_registro
- Linhas no CSV: 219125
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

### BancoModeloUse/dados_simulados/dados_industriais_automotivo_eletronics_2021_2025/roteiros_producao.csv
- Status: ok
- Tabela alvo: `roteiros_producao` (industrial)
- Colunas CSV: roteiro_id, produto_id, versao, data_registro
- Colunas modelo: roteiro_id, produto_id, versao, data_registro
- Linhas no CSV: 15
- Linhas inseridas: 0
- Duplicatas ignoradas: 0

