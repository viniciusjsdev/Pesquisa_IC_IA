# Conferência do diagrama corrigido e handoff — 06/11/2026

Conferência documental feita antes do despacho solicitado pelo usuário. Não é auditoria independente nem validação de implementação. SPEC-014 permanece pronta para implementação; SPEC-013 permanece done no seu escopo de engenharia.

Foi comparado o conteúdo do diagrama canônico local, sincronizado com o readback do editor na correção visual, com SPEC.md, architecture-contract.md e implementation-handoff.md. Não houve nova alteração no desenho nesta conferência.

| Elementos do desenho | Contrato correspondente | Resultado |
|---|---|---|
| Bancada, harness e cinco papéis; Especialista analisa A / planeja B | REQ-001/002/007 e tabela de papéis | Fluxo alinhado, sem Planejador separado |
| Painel A: pacote fixo, análise e lacunas, sem acesso aos bancos | REQ-003 e BR-002/003 | Alinhado |
| Fluxo B: índice, contrato da fonte, Especialista, validação e leitura | REQ-004 e BR-006 | Alinhado; DW, industrial e financeiro |
| Plano recusado volta ao Especialista; falta de evidência volta ao Selecionador | Contrato de erros, contexto e limites | Alinhado; contadores e encerramentos detalhados no texto |
| Serviço comum, adaptadores e endpoint; RunPod como hospedagem | REQ-005/006 e fronteiras | Alinhado |
| JSON, evidências, origem, erros, contexto e mesmo modelo | REQ-007/008/011 | Alinhado; critérios completos permanecem na SPEC |

Os quadros JSON são exemplos compactos de conteúdo, não JSON Schemas executáveis completos. Na implementação, incluir os campos do envelope comum e os discriminadores exigidos no contrato funcional, especialmente `action=query_source` no B e `action=analyze_packet` no A. Os exemplos B herdados ilustram o plano interno; sua ausência de campos do envelope não os torna opcionais. Não copiar o desenho literalmente como schema.

“Rota recusada” na nota do desenho deve ser lida com a política de erros: seleção inválida corrigível pode voltar ao Selecionador; negação de acesso ou ação proibida não autoriza uma nova rota para contornar o bloqueio. A tabela de erros do contrato funcional é normativa.

Os detalhes de migração da UI/API, histórico, capacidades, parâmetros, exportação, testes e aceite são complementares ao desenho simplificado, não fluxos adicionais. A árvore de pastas apresentada no chat foi uma proposta de organização; não impõe mover todo o repositório. Criar `model_service/` e realizar somente as extrações necessárias, com verificação de consumidores e documentação antes de código.

## Artefatos da versão visual conferida

- Página: `rC3Onoxkcgc0oOyFh0Ck`, no mesmo arquivo diagrams.net.
- `diagram-spec014.drawio`: SHA-256 `00b5dd89d7ae6f5315b85aadfcb885cbf16c63617ffed2bbd8ceee4a34f7f932`.
- `diagram-spec014.xml`: SHA-256 `2c5bdf445344e35883993dde95ab64c92da68bd13539ebe69d11344ca43874ca`.
- `diagram-layout-repair.json` registra o readback e substitui hashes visuais anteriores.
- `diagram-layout-repaired.png` documenta a apresentação corrigida. Preservar organização e proporções; não redesenhar ou esticar o canvas durante implementação sem necessidade funcional.

## Verificação e despacho

O validador `validate_spec.py ... --project-root . --require-ready` passou sem erros em 06/11/2026. Isso verifica estrutura documental, não execução do produto. O pedido explícito atual autoriza iniciar a implementação em outro chat local do projeto, com os marcos M1–M5 e critérios AC-001–008.

Primeiro registrar baseline do checkout compartilhado e reconciliar o runtime efetivo da thread com o manifest. A criação do chat usa o modelo padrão configurado pelo usuário; não é seleção de candidato científico. Registrar eventual diferença do runtime de execução, sem promover mudança silenciosa de configuração experimental. A origem não continuará editando código ou contratos em paralelo.
