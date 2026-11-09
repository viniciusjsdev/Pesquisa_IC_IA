# Bancada pronta para uso exploratório

Ativação em 08/11/2026, após autorização do usuário. Engenharia local da SPEC-015 e delta de ativação aprovados em revisão independente. Recibo: [ativação](../specs/active/SPEC-015/evidence/activation-2026-11-08/activation.json); [revisão do delta](../specs/active/SPEC-015/evidence/activation-2026-11-08/review.json).

## Abrir e iniciar

Acesse http://127.0.0.1:8765/ e entre com sua identidade existente. O servidor foi deixado ativo e as abas da Bancada e LangSmith abertas. Se o processo estiver parado, na raiz do checkout:

```powershell
./inference_api/scripts/start_bancada.ps1 -WithLangSmith
```

O launcher recusa porta ocupada, inicia somente no loopback, grava PID/logs em `inference_api/.local/bancada-active/` e confirma `/health`. Não interrompe outra instância automaticamente. `-WithLangSmith` habilita coleta somente no processo criado; sem essa opção, tracing fica off. O arquivo persistente `inference_api/.local/observability.env` conserva off para evitar envio acidental em CLIs/testes. Chaves e recibos de autorização ficam em arquivos locais ignorados; não entram no Git.

## Perfil e limites

- Perfil autorizado nesta ativação: OpenAI `gpt-6-luna`, usado em todos os papéis.
- A interface inicia com esforço `low` e limite de saída de 2.048 tokens por chamada; a execução registra os parâmetros efetivamente enviados.
- Limites do harness: até 48 chamadas, três rodadas, três tentativas de consulta em B e zero em A; limites de bytes e linhas existentes continuam ativos. Isso é um teto, não uma quantidade obrigatória de chamadas.
- A admite os dois pacotes já presentes; B usa o catálogo aprovado versão 1. Um bundle backend de recibos separados permite A/B sem trocar de servidor. A validação continua exata para perfil/destino/cenário/hash dos dados/limites; não há herança de aprovação entre fontes/modelos.
- Outros perfis exibidos na interface não recebem autorização externa por esta ativação. Modelos RunPod não foram iniciados.
- Consultas com recorte amplo podem exceder o limite de linhas e ser bloqueadas. Prefira perguntas com período/entidade específicos; não há truncamento silencioso nem repetição automática.

Exemplo B verificado:

> Em janeiro de 2021, quais paradas da máquina 2000002 constam na fonte industrial paradas_maquinas_geradas, com motivo e duração, e quais receitas e lucros líquidos constam na fonte financeira resultados_financeiros no mesmo mês? Consulte os dois domínios, apresente os resultados separadamente, cite IDs e proveniência e explique se os dados permitem atribuir relação causal.

## Monitoramento e resultado da ativação

No detalhe/histórico, **Atualizar monitoramento** lê o trace existente, sem repetir agentes ou consultas. O link abre a árvore no projeto privado `pesquisa-ic-ia-real-engineering`. A paginação hospedada usa até100 eventos na primeira página e até28 na segunda, dentro do máximo de128 spans/três requisições/dez segundos. Falha temporária conserva a confirmação/link anteriores e informa erro da nova consulta.

| Execução | Resultado técnico |
|---|---|
| A `bc701782` | Oito chamadas, zero consultas, resposta parcial `insufficient_evidence` por ausência de observações financeiras no pacote;17 spans confirmados e raiz sem erro. |
| B anual `d362ba9d` | Bloqueado por `row_limit_exceeded`;três chamadas, zero consultas concluídas;erro preservado no histórico e na raiz remota. |
| B janeiro `74fef088` | Oito chamadas, duas consultas industrial/financeiro, `answered_unverified`;19 spans confirmados e raiz sem erro. |

Os três traces foram verificados por IDs/pais e os painéis A/B foram inspecionados na sessão autenticada. O histórico foi reaberto após recarga sem reenviar a execução. Os snapshots permanecem intactos; fingerprints das fontes B antes/depois coincidiram. A primeira submissão A foi recusada antes de criar job por conflito com instância antiga, encerrada durante a ativação; não chamou modelo.

A migração004 foi aplicada apenas em `db_inference_app`, após backup lógico datado de317.203 bytes, validado por `pg_restore --list`. Backup e snapshots integrais permanecem em `.local/`. Nenhuma carga de pesquisa foi alterada.

## Validação e próxima etapa

Delta de ativação:146 testes backend com oito skips antigos de integração configurável;49 métodos SPEC-015;11 de reconciliação;23 frontend, tipos, lint e build aprovados. Os testes foram executados com tracing off. Para repetir:

```powershell
$env:INFERENCE_OBSERVABILITY='off'
inference_api/.venv/Scripts/python.exe -m unittest discover -s inference_api/tests -v
```

Estes resultados aprovam operação e engenharia, sem aprovar cientificamente as respostas. Todos os novos runs permanecem `not_scored`. A próxima etapa segue o [protocolo de validação humana](protocolo_validacao_humana_avaliacao.md): casos/versões, protocolo experimental, cálculo e conclusão de cada resposta.
