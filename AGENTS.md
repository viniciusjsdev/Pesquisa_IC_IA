# Orientação para agentes

Leia o `README.md` da raiz para escolher a frente antes de editar. Em `FineTuning/`, siga também `FineTuning/AGENTS.md`, que define a ordem das fontes de verdade e prevalece para aquela pasta. Para dados locais, leia `BancoModeloUse/README.md`; para execução remota, `runpod/README.md`.

Preserve dados congelados, splits, pesos, checkpoints, resultados brutos e artigos. Não misture as frentes: o novo DW e o harness por API ainda não existem. Não mova `runpod/*.sh` isoladamente: o watcher localiza o script de avaliação na própria pasta. Confira manifests e métricas antes de descrever um resultado experimental como concluído ou válido.
