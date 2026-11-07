# Auditoria inicial Astra — 05/11/2026

Inspeção independente, sem aprovação final. Referência: chat Auditoria de engenharia da Bancada e SPEC-013.

**Parecer inicial: encontrei oito lacunas técnicas; uma afeta diretamente o teto operacional aprovado.** Não aprovei a SPEC nem gerei `review.json`. A matriz científica e a adjudicação das respostas **não são bloqueios ao aceite técnico** do contrato 2.

Inspecionei o checkout com alterações locais sobre `13d7df5`, 17 snapshots Groq e o snapshot de emergência indicado. Executei 55 testes selecionados, todos aprovados, com carregamento de credenciais, conexões ao banco e rede bloqueados. As reproduções adicionais abaixo usaram fixtures, sem editar arquivos do checkout.

1. **[P1] O orçamento conta apenas consultas concluídas e permite ultrapassar três tentativas.**  
   Em [engine.py:410](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/src/inference_api/agent_harness/engine.py:410), a correção pode executar novamente o adaptador; `queries` só aumenta após validar o resultado, na linha 486. Reproduzi **seis invocações com limite três**, terminando `answered_unverified` e reportando três consultas. `row_limit_exceeded` pode ocorrer depois do SELECT e ainda receber nova tentativa.  
   **Correção:** contabilizar tentativas globalmente, distinguir execução e resultado aceito e encerrar nos estouros de linhas/bytes conforme a política aprovada.

2. **[P2] O Planejador não recebe a evidência necessária para consultas encadeadas.**  
   [engine.py:382](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/src/inference_api/agent_harness/engine.py:382) entrega necessidade resumida, rota, mapa e IDs `result_XX`; omite pergunta literal, resultados anteriores e lacuna atual. Confirmei essa ausência na segunda rodada. Uma navegação `contributors → trace`, por exemplo, precisa dos IDs retornados pela consulta anterior; referências ao resultado não fornecem esses valores.  
   **Correção:** projetar a pergunta e a evidência necessária ao plano, com IDs e proveniência, dentro do orçamento explícito.

3. **[P2] A chamada de correção não recebe a tentativa que precisa corrigir.**  
   [engine.py:256](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/src/inference_api/agent_harness/engine.py:256) e [engine.py:453](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/src/inference_api/agent_harness/engine.py:453) acrescentam erro e orientação, mas não a saída/plano recusado nem sua referência. Como cada papel recebe contexto novo, o candidato não conhece sua tentativa anterior. O contrato textual exige esse vínculo.  
   **Correção:** incluir a tentativa recusada, sua referência e restrição violada no schema de correção; tratar explicitamente eventual excesso de tamanho.

4. **[P2] `source_event_ids` registra os últimos três eventos, não as dependências reais.**  
   [engine.py:215](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/src/inference_api/agent_harness/engine.py:215) usa uma janela fixa. No I3 v7 mais recente, `call_16` recebe ambos os resultados, mas referencia apenas `call_14`, `call_15` e `tool_02`, omitindo `tool_01`. O Selecionador também omite um especialista cujo trecho recebeu. A UI apresenta esses IDs como “Usou eventos”.  
   **Correção:** construir referências a partir das dependências efetivamente projetadas e testar reconstrução de cada entrada por essas referências.

5. **[P2] O teto de entrada desconsidera instruções e schemas enviados ao modelo.**  
   [engine.py:218](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/src/inference_api/agent_harness/engine.py:218) mede somente o envelope. [real_pilot.py:81](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/src/inference_api/agent_harness/real_pilot.py:81) acrescenta tarefa, protocolo e schemas depois. Uma fixture com envelope de **32.760 bytes** produziu mensagens de **37.075 bytes**, ultrapassando 32 KiB. O snapshot real inspecionado permaneceu abaixo do teto.  
   **Correção:** medir o payload completo antes do transporte, com serialização definida e tamanho registrado.

6. **[P2] A trajetória esconde a segunda tentativa do Redator.**  
   [HarnessRounds.tsx:110](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/frontend/src/features/bench/HarnessRounds.tsx:110) exclui todos os eventos do Redator da investigação e usa `find` para mostrar apenas o primeiro. Reproduzi renderização com primeira tentativa rejeitada e segunda validada: a resposta final aparece, mas a chamada corrigida fica inacessível na trajetória.  
   **Correção:** apresentar todas as tentativas do Redator, preservando ordem, entradas, saídas e erros.

7. **[P2] A comparação ignora contratos e mapas do harness.**  
   [benchService.ts:32](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/inference_api/frontend/src/features/bench/benchService.ts:32) compara campos antigos, mas não os hashes de `harness_result` nem o fingerprint em `evidence_source`. Alterei contratos de entrada/saída e mapa em duas fixtures: `comparisonDifferences` retornou `[]`, permitindo a mensagem “Insumos registrados iguais”.  
   **Correção:** incluir protocolo, hashes dos contratos/mapas, identidade da carga e limites efetivos; distinguir condições fixas de decisões produzidas pelo candidato.

8. **[P2] A adjudicação não está vinculada aos bytes do run revisado.**  
   [harness_score.py:114](D:/Projetos/Github_ViniciusJ/Pesquisa_IC_IA/model_evaluation/harness_score.py:114) verifica `run_id`, caso e hash do caso, mas não o conteúdo do run. Em controle sintético, substituí a resposta mantendo o ID: a adjudicação anterior continuou produzindo `scored`. A persistência normal é append-only, mas o avaliador offline aceita diretamente um objeto.  
   **Correção:** exigir hash canônico do run/snapshot revisado e rejeitar adjudicação divergente. Isso é integridade do instrumento, sem exigir adjudicar respostas reais agora.

A evidência disponível sustenta distinções importantes:

- **Provedor:** o I3 v7 de 04/11 corresponde ao hash publicado, registra 17 chamadas, duas consultas e HTTP 429 no Redator. Não houve resposta final.
- **Infraestrutura:** o snapshot de emergência também corresponde ao hash publicado e registra `OperationalError`, nove chamadas e nenhuma consulta concluída. Não permite atribuir a causa da queda ao modelo.
- **Candidato:** referências inválidas foram recusadas e corrigidas explicitamente. Uma decisão `suficiente` validada pelo schema comprova apenas conformidade contratual, não suficiência semântica.
- **Controles existentes:** há separação entre motor e acesso a dados, planos parametrizados, catálogo restrito, leitura somente, isolamento do avaliador e ausência de importação de gabaritos pelo caminho dos agentes. Os testes selecionados confirmaram esses caminhos simulados.

**Para a revisão final ainda faltam:** correções e regressões dos achados; validação da implementação OpenAI concluída, incluindo gates separados e parâmetros autorizados; execução completa iniciada pela UI com readback de job, resposta, trajetória e histórico; e validações finais sobre a revisão exata do código. A leitura dos três domínios possui recibos anteriores com modelo programado, mas não foi reexecutada nesta auditoria. A revisão final deverá reconciliar esses recibos com o código entregue e os artefatos de conclusão.
