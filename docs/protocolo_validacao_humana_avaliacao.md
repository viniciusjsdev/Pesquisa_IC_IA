# Validação humana da avaliação de modelos

**Escopo vigente em 05/11/2026:** a [decisão do pesquisador](../specs/active/SPEC-013/evidence/engineering-scope-2026-11-05.md)
separa conclusão de engenharia e avaliação científica. SPEC-013 contrato 2
exige testes técnicos, cadeia real completa pela Bancada e auditoria Astra.
A matriz científica e a adjudicação humana das respostas ficam posteriores;
sem elas, não há score científico. OpenAI está autorizada para o piloto de
engenharia. Os estados e critérios datados abaixo são históricos quando
contrariarem essa decisão. A SPEC permanece `in_progress`.


Este protocolo acompanha a [SPEC-013](../specs/active/SPEC-013/SPEC.md) e
vale para pesquisadores que prepararem novos casos, revisarem respostas ou
publicarem comparações. Um teste técnico pode passar enquanto a pergunta, a
interpretação do dado ou a conclusão continuam erradas. Portanto, a aprovação
humana é registrada como **decisão sobre um artefato e uma versão exatos**.

## Onde a revisão humana é obrigatória

| Gate | O que a pessoa precisa julgar | Evidência mínima | Efeito da ausência |
| --- | --- | --- | --- |
| Mapa de dados | Significado de campos, grão, unidade, cobertura, filtros, chaves e relações permitidas. Existência física e FK não autorizam interpretação ou join. | Mapa versionado, inventário físico, ressalvas, hash, pessoa revisora e decisão. | A fonte permanece desabilitada no harness real. |
| Caso e gabarito | Pergunta, escopo, estado da evidência, consulta de referência reexecutável, cálculo/tolerância, resposta aceitável e inferências proibidas. | Caso identificado, dados/consultas/fingerprint congelados, referências privadas com hash e decisão humana vinculada ao hash do pacote revisado. | O caso fica `not_scored`, mesmo que a consulta funcione. |
| Resposta de cada run | Se o cálculo apresentado corresponde à evidência e se a conclusão respeita cobertura, unidades e limites causais. | Snapshot imutável do run, `case_id`/hash, referências usadas, decisão e justificativa da pessoa revisora. | Checks automáticos de rota/citação podem aparecer, mas não há nota final de cálculo/conclusão. |
| Resultado científico | Seleção e exclusões dos casos, igualdade do protocolo entre modelos, repetições, falhas, variação e interpretação do relatório. | Relatório estratificado, manifests, hashes, resultados brutos, revisão técnica independente e aprovação editorial/científica. | Não publicar ranking nem afirmar superioridade de modelo. |
| Envio de dados a provedor externo | Destino, classes de dados, payload exato, retenção e finalidade do teste. | Autorização específica e recibo do envio. | A leitura local não autoriza transmissão. |

O backend confere permissões, formatos, limites, fingerprints e referências.
Esses checks não substituem a revisão do significado dos dados ou da
qualidade da resposta. Um juiz LLM pode auxiliar a triagem, mas não aprova
gabarito, cálculo ou conclusão por conta própria.

## Como aprovar um caso

1. O preparador registra pergunta literal, família/domínio, estado esperado
   (`observed`, `no_observation` ou contraditório), filtros, grão, unidade,
   relações e rotas aceitáveis. Registra também o que **não** se pode inferir.
2. Reexecuta as consultas de referência em leitura somente e congela versão
   da carga, fingerprint, versão/hash do código de consulta, resultados e
   proveniência. Valores de gabarito ficam separados dos inputs das tools e
   dos agentes; um índice com hashes pode ficar na documentação pública.
3. Define fórmula, tolerância e critério para ausência de dado. `no_observation`
   nunca vira zero por conveniência. Aceita rotas equivalentes quando
   sustentadas pela mesma evidência, sem exigir uma sequência arbitrária.
4. Outra pessoa, ou o pesquisador responsável quando o preparo foi assistido
   por IA, lê **o pacote inteiro** e decide cada `case_id`. Uma mensagem única
   pode aprovar vários IDs apenas se a pergunta listar todos eles, apontar
   para um pacote imutável com hash e a resposta não deixar ambiguidade sobre
   o alcance. Registre as decisões separadamente no recibo, inclusive
   ressalvas, rejeições ou ausência de justificativa individual.
5. A aprovação do conteúdo não ativa o caso automaticamente. O manifesto
   executável ainda precisa vincular exatamente pergunta, mapa, carga,
   consultas, referências e tolerâncias aprovadas. Só depois da validação
   técnica desse vínculo o caso pode passar a `approved_for_scoring`.

Se pergunta, filtro, unidade, fórmula, mapa, carga, código de consulta ou
referência mudar, gere nova versão e repita a revisão do trecho afetado. Não
edite silenciosamente o pacote que foi aprovado. Preserve o recibo antigo e
seu hash; ele explica o que foi aprovado **naquela versão**.

Confira a integridade dos arquivos de um recibo com:

```powershell
inference_api/.venv/Scripts/python.exe model_evaluation/verify_human_review_receipt.py specs/active/SPEC-013/evidence/m3-human-case-content-approval-2026-11-01.json
```

O verificador compara hashes e IDs enumerados no pacote. Ele **não autentica a
identidade humana**, não decide se o conteúdo é correto e não habilita score.
Para uma auditoria futura, o hash sozinho não basta: o responsável deve manter
o pacote privado e as referências em armazenamento controlado, com inventário,
regra de acesso e cópia dos bytes aprovados. Se esses arquivos não estiverem
disponíveis, o recibo documenta a decisão histórica, mas outra pessoa não
consegue reproduzir a revisão nem reexecutar o gabarito.

## Como revisar uma resposta de modelo

O avaliador isolado em [`harness_score.py`](../model_evaluation/harness_score.py)
confere mecanicamente rota e integridade das referências a evidências. A
pessoa revisora recebe o run e o gabarito **somente depois** de a resposta ser
congelada. Ela marca cálculo e conclusão separadamente, com justificativa e
identidade, vinculadas a `run_id`, hash do caso e `run_sha256` do objeto integral
de run recebido pelo avaliador. O hash usa JSON canônico UTF-8, sem espaços,
chaves ordenadas e sem números não finitos. Alterar resposta, evidência, trace
ou configuração invalida a revisão, mesmo com o mesmo ID. Hash não autentica
a pessoa revisora. Verifique especialmente:

- número, unidade, período, granularidade e cobertura da fonte citada;
- omissão de observação, linha vazia e contradição entre fontes;
- soma de observações que não representam total anual ou produção única;
- atribuição de receita/lucro a máquina, produto ou parada sem chave válida;
- afirmação causal baseada apenas em proximidade temporal;
- se uma falha de tool/modelo foi apresentada como lacuna, sem inventar dado.

Runs incompletos permanecem visíveis como falha; não recebem uma resposta
fictícia ou nota imputada. A pontuação por rota, evidência, cálculo e conclusão
fica separada. Cenários de evidência fixa e pesquisa com tools não são
agregados em uma média única.

## Exemplo auditável do piloto SPEC-013

O pesquisador aprovou o **conteúdo dos nove casos I1–I3, F1–F3 e X1–X3** em
resposta à pergunta que os enumerava e apontava para o pacote privado de
SHA-256 `75927ad3cdc81b7aaa59527c51c89809205243263bce08d857d67b1dd18fa27c`.
O [recibo individualiza as nove decisões](../specs/active/SPEC-013/evidence/m3-human-case-content-approval-2026-11-01.json).
O verificador local confirmou os nove IDs e os hashes do pacote e das duas
referências privadas; a decisão humana continua documentada pela resposta
registrada no recibo.
Os resultados privados usados no preparo têm inventário e hashes no
[pacote de revisão](../specs/active/SPEC-013/evidence/m3-case-review-packet-2026-11-01.md).
Essa aprovação não prova ainda a ligação dos nove casos a manifests
executáveis nem valida respostas de modelos. Até esses gates, nenhum score
científico é atribuído.

**Atualização de 02/11/2026:** o pesquisador aprovou depois a v4 executável
dos nove casos, com SHA-256
`27214d0acc5424f11bf9c27e3f4c5ee0be1d977dc169524fceb3a8900fa2018a`.
O [recibo novo](../specs/active/SPEC-013/evidence/m3-executable-case-approval-2026-11-02.json)
individualiza os IDs. A verificação técnica reexecutou a geração e produziu
uma v5 privada aprovada para entrada no avaliador, mantendo a v4 intacta.
Nenhuma resposta futura foi aprovada por esse ato: cada run continua a exigir
decisão humana de cálculo e conclusão antes de receber nota.
