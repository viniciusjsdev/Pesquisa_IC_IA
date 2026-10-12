# Orientação para agentes

Leia o `README.md` da raiz para escolher a frente antes de editar. Em `FineTuning/`, siga também `FineTuning/AGENTS.md`, que define a ordem das fontes de verdade e prevalece para aquela pasta. Para dados locais, leia `BancoModeloUse/README.md`; para execução remota, `runpod/README.md`.

Para o novo front, backend e serving de modelos, leia `docs/arquitetura_inferencia_compartilhada.md`. Esse documento registra a topologia decidida e os contratos pendentes; não trate os diretórios de código ali propostos como já existentes. A arquitetura científica do futuro harness e DW permanece em `BancoModeloUse/docs/arquitetura_avaliacao_modelos.md`.

Preserve dados congelados, splits, pesos, checkpoints, resultados brutos e artigos. Para o texto editorial do artigo, prevalece o [Google Doc canônico](https://docs.google.com/document/d/1LExZ17IkPXIKYGCHLEJ3mEZSsCU2It1X/edit); `FineTuning/artigo_canonico/` contém apenas snapshots exportados. Não misture as frentes: o novo DW e o harness por API ainda não existem. Não mova `runpod/*.sh` isoladamente: o watcher localiza o script de avaliação na própria pasta. Confira manifests e métricas antes de descrever um resultado experimental como concluído ou válido.

Ao mudar código, configuração ou fluxo, revise na mesma mudança o README e os documentos da frente afetada. Confirme caminhos, comandos e estados no checkout; separe o que foi implementado, o que foi verificado por execução e o que está apenas planejado ou é histórico. Registre a evidência e o commit/data para afirmações que podem envelhecer. Não use documentação legada para substituir o comportamento observado no código nem promova um status de manifest a validação independente.

Código, configuração e documentação comprovadamente fora de uso não devem permanecer no fluxo ativo do repositório. Antes de retirar material, confira referências e consumidores; preserve dados, resultados e artigos protegidos e arquive o histórico necessário fora do checkout com inventário verificável.
