# Guia Completo — RunPod Setup para Fine-Tuning

## Resposta direta às suas perguntas

| Pergunta | Resposta |
|---|---|
| Preciso enviar o modelo Qwen2.5-7B? | **Não.** Ele é baixado do HuggingFace direto na nuvem |
| O projeto está pronto para ir? | **Quase.** Precisa criar 1 arquivo de config adaptado para a nuvem |
| O que enviar? | **~60MB** de dados + scripts + configs |
| Escolho o modelo localmente ou lá? | **Lá.** O HuggingFace cuida disso automaticamente |
| Os adapters treinados ficam onde? | Na nuvem — você baixa de volta ao final |

---

## O que existe no projeto e o que cada coisa faz

```
FineTuning/
├── finetune_qwen_wsl/
│   ├── 1_download_wsl.py        ← baixa o Qwen2.5-7B (roda na nuvem)
│   ├── 2_treinar_wsl.py         ← script principal de treino
│   ├── 5_avaliar_batch_wsl.py   ← avaliação em lote
│   ├── requirements_wsl.txt     ← dependências Python
│   └── common/                  ← módulos compartilhados (metrics, modeling...)
├── configs/
│   ├── train/
│   │   ├── base.yaml            ← config base (r=8, alpha=16, 3 épocas...)
│   │   ├── ft_finqa_v1.yaml     ← config do treino FinQA
│   │   ├── ft_failure_v1.yaml   ← config do treino FailureSensorIQ
│   │   └── ft_hibrido_v1.yaml   ← config do treino Híbrido
│   ├── eval/
│   │   ├── base.yaml            ← config de avaliação
│   │   └── cross_domain.yaml    ← config de avaliação cruzada
│   └── paths.local.yaml         ← ⚠️ PRECISA SER ADAPTADO para a nuvem
└── data/
    ├── manifests/               ← metadados dos datasets
    └── processed/               ← datasets prontos (59MB total)
        ├── hybrid_v1/           ← 11.560 treino + val + test
        ├── finqa_v1/            ← 4.924 treino + val + test
        └── failure_v1/          ← 6.636 treino + val + test
```

---

## O que NÃO enviar

| O que | Motivo |
|---|---|
| `finetune_qwen_wsl/venv/` | Reinstala na nuvem com `pip install` |
| `finetune_qwen_wsl/output/` | Artefatos do modelo legado, não necessários |
| `runs/` | Serão criados do zero na nuvem |
| Modelo Qwen2.5-7B (~15GB) | Baixado automaticamente do HuggingFace |

---

## O que precisa ser ajustado antes de enviar

### Criar configs/paths.cloud.yaml

O arquivo `paths.local.yaml` aponta para `D:/` e `/mnt/e/` — paths que não existem na nuvem.
Na RunPod, o storage persistente fica em `/workspace/`.

O arquivo `configs/paths.cloud.yaml` já existe no repositório com o conteúdo abaixo
(modelo base: Qwen2.5-7B-Instruct). Confira apenas se está presente:

```yaml
repo:
  root_windows: "/workspace/FineTuning"
  root_wsl: "/workspace/FineTuning"
hf:
  cache_dir: "/workspace/Qwen"
legacy:
  adapter_dir: "/workspace/FineTuning/finetune_qwen_wsl/output/legacy"
  checkpoints_dir: "/workspace/FineTuning/finetune_qwen_wsl/output/checkpoints"
```

Esse arquivo será usado no lugar do `paths.local.yaml` na nuvem, passando `--paths-config ../configs/paths.cloud.yaml` nos comandos.

---

## Passo a Passo — Contratar a instância no RunPod

### 1. Criar conta

- Acesse https://www.runpod.io
- Clique em **Sign Up** → crie conta com email
- Adicione créditos: menu superior → **Billing** → mínimo sugerido **$15** (sobra margem para repetir se necessário)

### 2. Criar um volume persistente (importante)

O volume evita perder os checkpoints e o modelo baixado se a instância for pausada.

- Menu esquerdo → **Storage** → **+ New Volume**
- Nome: `ic-finetune`
- Tamanho: **50 GB** (modelo ~15GB + checkpoints ~5GB por run × 3 + dados)
- Região: mesma que vai usar para a GPU (ex: US-TX-3)
- Clique em **Create**

### 3. Lançar a instância GPU

- Menu esquerdo → **Pods** → **+ Deploy**
- Selecionar **Secure Cloud** (mais estável para runs longos)
- Filtrar por GPU: selecionar **RTX 4090**
- Template: **RunPod PyTorch 2.1** (já tem CUDA 12.1, Python 3.10, pip)
- Em **Volume**: selecionar o volume `ic-finetune` criado no passo anterior → montar em `/workspace`
- Disk: **20 GB** de container disk (suficiente para o sistema)
- Clicar em **Deploy**

### 4. Acessar a instância

Quando o pod estiver **Running**:
- Clicar em **Connect** → **Start Web Terminal** (ou usar SSH se configurou chave)

---

## Passo a Passo — Enviar o projeto

### Opção A — Via Git (recomendado se o repositório estiver no GitHub)

```bash
# No terminal do RunPod
cd /workspace
git clone https://github.com/<seu-usuario>/<seu-repositorio>.git FineTuning
cd FineTuning
```

> Se o repositório for privado: usar token de acesso pessoal do GitHub no lugar da senha.

### Opção B — Upload direto (se não usar Git)

No painel do RunPod, enquanto o pod está rodando:
- Clicar em **Connect** → **File Browser**
- Navegar até `/workspace`
- Fazer upload do zip do projeto

O que zipar para envio (total ~65MB):
```
FineTuning/
├── finetune_qwen_wsl/   (sem venv/ e sem output/)
├── configs/
├── data/processed/
├── data/manifests/
└── docs/
```

---

## Passo a Passo — Configurar o ambiente na nuvem

```bash
# 1. Navegar para o projeto
cd /workspace/FineTuning/finetune_qwen_wsl

# 2. Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements_wsl.txt

# 4. Verificar GPU
python -c "import torch; print(torch.cuda.get_device_name(0)); print(torch.cuda.get_device_properties(0).total_memory / 1e9, 'GB')"
```

Saída esperada:
```
NVIDIA GeForce RTX 4090
24.0 GB
```

---

## Passo a Passo — Baixar o modelo Qwen2.5-7B na nuvem

O modelo é baixado do HuggingFace direto na instância — você não envia nada.

```bash
# Baixar Qwen2.5-7B-Instruct para o volume persistente
HF_HOME=/workspace/Qwen \
TRANSFORMERS_CACHE=/workspace/Qwen \
python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='Qwen/Qwen2.5-7B-Instruct',
    cache_dir='/workspace/Qwen',
    resume_download=True
)
print('Modelo baixado com sucesso')
"
```

Tempo estimado: **10–20 minutos** dependendo da largura de banda do datacenter (~15GB).

O modelo fica em `/workspace/Qwen/` — por isso o volume persistente é importante: só precisa baixar uma vez, mesmo que pause e retome o pod.

---

## Passo a Passo — Executar os treinamentos

Com o ambiente configurado e o modelo baixado:

```bash
cd /workspace/FineTuning/finetune_qwen_wsl
source venv/bin/activate

# Validar estrutura antes de treinar (sem GPU, rápido)
python 2_treinar_wsl.py --modelo finqa \
  --paths-config ../configs/paths.cloud.yaml \
  --run-name run_v1_seed42 \
  --dry-run

# ── TREINO 1 ── ft_finqa_v1 (~2-3h na RTX 4090)
python 2_treinar_wsl.py --modelo finqa \
  --paths-config ../configs/paths.cloud.yaml \
  --run-name run_v1_seed42

# ── TREINO 2 ── ft_failure_v1 (~3-4h na RTX 4090)
python 2_treinar_wsl.py --modelo failure \
  --paths-config ../configs/paths.cloud.yaml \
  --run-name run_v1_seed42

# ── TREINO 3 ── ft_hibrido_v1 (~4-5h na RTX 4090)
python 2_treinar_wsl.py --modelo hibrido \
  --paths-config ../configs/paths.cloud.yaml \
  --run-name run_v1_seed42
```

Os adapters ficam em:
```
/workspace/FineTuning/runs/ft_finqa_v1/run_v1_seed42/adapter/
/workspace/FineTuning/runs/ft_failure_v1/run_v1_seed42/adapter/
/workspace/FineTuning/runs/ft_hibrido_v1/run_v1_seed42/adapter/
```

---

## Passo a Passo — Executar as avaliações

```bash
cd /workspace/FineTuning/finetune_qwen_wsl
source venv/bin/activate

# Base model
python 5_avaliar_batch_wsl.py \
  --base-only \
  --eval-config ../configs/eval/base.yaml \
  --paths-config ../configs/paths.cloud.yaml \
  --experiment-id base_eval

# ft_finqa_v1
python 5_avaliar_batch_wsl.py \
  --adapter-only \
  --eval-config ../configs/eval/base.yaml \
  --paths-config ../configs/paths.cloud.yaml \
  --run-dir ../runs/ft_finqa_v1/run_v1_seed42

# ft_failure_v1
python 5_avaliar_batch_wsl.py \
  --adapter-only \
  --eval-config ../configs/eval/base.yaml \
  --paths-config ../configs/paths.cloud.yaml \
  --run-dir ../runs/ft_failure_v1/run_v1_seed42

# ft_hibrido_v1
python 5_avaliar_batch_wsl.py \
  --adapter-only \
  --eval-config ../configs/eval/base.yaml \
  --paths-config ../configs/paths.cloud.yaml \
  --run-dir ../runs/ft_hibrido_v1/run_v1_seed42

# Avaliações cruzadas
python 5_avaliar_batch_wsl.py \
  --adapter-only \
  --eval-config ../configs/eval/cross_domain.yaml \
  --paths-config ../configs/paths.cloud.yaml \
  --run-dir ../runs/ft_finqa_v1/run_v1_seed42 \
  --domains failure

python 5_avaliar_batch_wsl.py \
  --adapter-only \
  --eval-config ../configs/eval/cross_domain.yaml \
  --paths-config ../configs/paths.cloud.yaml \
  --run-dir ../runs/ft_failure_v1/run_v1_seed42 \
  --domains finqa
```

---

## Passo a Passo — Baixar os resultados de volta

Ao final, os arquivos que precisam voltar para sua máquina são:

```
runs/
├── base_eval/<run>/metrics/        ← JSONs com métricas do modelo base
├── ft_finqa_v1/run_v1_seed42/
│   ├── adapter/                    ← pesos do adapter (~300MB)
│   ├── metrics/                    ← JSONs com métricas
│   └── predictions/                ← predições para análise de erro
├── ft_failure_v1/run_v1_seed42/    ← mesma estrutura
└── ft_hibrido_v1/run_v1_seed42/    ← mesma estrutura
```

**Como baixar:**

Opção A — File Browser do RunPod (para arquivos pequenos como metrics/ e predictions/):
- Connect → File Browser → navegar → Download

Opção B — rsync via SSH (para os adapters ~300MB cada):
```bash
# Na sua máquina local
rsync -avz <user>@<runpod-ip>:/workspace/FineTuning/runs/ ./runs_cloud/
```

Opção C — Git push dos resultados (se usar GitHub):
```bash
# No pod
git add runs/*/metrics runs/*/predictions runs/*/meta
git commit -m "resultados experimentos v1"
git push
```

> Os adapters (pesos LoRA) são necessários para rodar inferência futura.
> As métricas e predições são o que vai diretamente para o artigo.

---

## Checklist de prontidão do projeto

- [x] Datasets processados prontos: `data/processed/` (59MB, 3 splits cada)
- [x] Manifests criados: `data/manifests/*.json`
- [x] Scripts de treino funcionais: `2_treinar_wsl.py`
- [x] Script de avaliação funcional: `5_avaliar_batch_wsl.py`
- [x] Configs de treino prontas: `configs/train/ft_*.yaml` (r=8, alpha=16, 3 épocas)
- [x] Configs de avaliação prontas: `configs/eval/*.yaml`
- [x] Métricas implementadas: `common/metrics.py`
- [ ] **Criar `configs/paths.cloud.yaml`** ← único passo pendente antes de enviar

---

## Custo estimado total

| Fase | Tempo estimado | Custo (RTX 4090 Secure ~$0.59/hr) |
|---|---|---|
| Download do modelo | ~20min | ~$0.20 |
| Setup do ambiente | ~10min | ~$0.10 |
| Treino ft_finqa_v1 | ~2-3h | ~$1.20-1.80 |
| Treino ft_failure_v1 | ~3-4h | ~$1.80-2.40 |
| Treino ft_hibrido_v1 | ~4-5h | ~$2.40-3.00 |
| Avaliações (9 rodadas) | ~3-4h | ~$1.80-2.40 |
| **Total** | **~13-17h** | **~$7.50-10** |

Recomendação: depositar **$15** para ter margem de segurança.
