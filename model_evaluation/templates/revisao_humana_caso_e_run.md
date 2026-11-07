# Ficha de revisão humana — caso e resposta

Copie esta ficha para cada **versão** de caso. Siga o
[protocolo de validação humana](../../docs/protocolo_validacao_humana_avaliacao.md).
Um pacote pode reunir vários casos, desde que o recibo identifique cada ID e
o hash dos bytes que a pessoa revisou.

## 1. Caso e gabarito, antes de executar modelos

- `case_id` e versão:
- Família/domínio e estado esperado da evidência:
- Pergunta literal e filtros:
- Dados: banco, versão, fingerprint, período e proveniência:
- Catálogo/mapa, contrato de consulta e hashes de código:
- Consulta de referência reexecutável e hash do resultado privado:
- Rota(s) e fontes de evidência aceitáveis:
- Fórmula, unidade, tolerância e regra para `no_observation`:
- Afirmações aceitáveis, lacunas e inferências proibidas:
- Exclusões ou ambiguidade que impedem pontuação:
- Preparador/ processo de preparo:
- Pessoa revisora e data/fuso:
- Hash do pacote efetivamente lido:
- Decisão por `case_id`: aprovar conteúdo / ajustar / rejeitar:
- Correções e justificativa da decisão, quando fornecidas:
- Manifesto executável vinculado aos hashes acima? sim / não:
- Estado final: rascunho / conteúdo aprovado pendente de contrato /
  `approved_for_scoring` / rejeitado:

Mudou pergunta, filtro, mapa, dados, consulta, fórmula, tolerância ou referência?
Crie outra versão e obtenha nova revisão. Nunca altere o pacote aprovado no
mesmo caminho sem guardar o original e seu hash.

## 2. Resposta de um run, depois de congelá-la

- `run_id`, `case_id` e hash do caso:
- `run_sha256` do objeto integral de run revisado (JSON canônico do avaliador):
- Modelo efetivamente servido, parâmetros, cenário A/B e repetições:
- Evidências consultadas, IDs citados e cobertura:
- Check automático de rota e referências (não decide veracidade):
- Cálculo correto? sim / não / não aplicável; valores e justificativa:
- Conclusão sustentada? sim / não / não aplicável; justificativa:
- Houve inferência causal, soma indevida, unidade incorreta ou dado inventado?
- Falha de tool/modelo ou orçamento esgotado? Como foi contabilizada?
- Pessoa revisora, data/fuso e decisão vinculada ao hash do snapshot:

Uma resposta sem esta adjudicação pode mostrar checks automáticos, mas não
recebe nota final de cálculo/conclusão. Falhas e casos sem evidência válida
permanecem visíveis; não se imputam respostas ou notas fictícias.
