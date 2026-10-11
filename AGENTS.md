# Orientação para agentes

Leia o `README.md` da raiz para escolher a frente antes de editar. Em `FineTuning/`, siga também `FineTuning/AGENTS.md`, que define a ordem das fontes de verdade e prevalece para aquela pasta. Para dados locais, leia `BancoModeloUse/README.md`; para execução remota, `runpod/README.md`.

Preserve dados congelados, splits, pesos, checkpoints, resultados brutos e artigos. Para o texto editorial do artigo, prevalece o [Google Doc canônico](https://docs.google.com/document/d/1LExZ17IkPXIKYGCHLEJ3mEZSsCU2It1X/edit); `FineTuning/artigo_canonico/` contém apenas snapshots exportados. Não misture as frentes: o novo DW e o harness por API ainda não existem. Não mova `runpod/*.sh` isoladamente: o watcher localiza o script de avaliação na própria pasta. Confira manifests e métricas antes de descrever um resultado experimental como concluído ou válido.
