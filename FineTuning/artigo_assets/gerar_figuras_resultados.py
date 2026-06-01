#!/usr/bin/env python3
"""
Gera as figuras de RESULTADOS do artigo a partir dos JSONs reais de avaliacao
e dos logs de treino (protocolo v1, modelo base Qwen2.5-7B-Instruct, RunPod H100).

Saida: PNGs em FineTuning/artigo_assets/figuras/
Fonte dos dados: FineTuning/runpod_results_2026-05-31/
"""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "FineTuning" / "runpod_results_2026-05-31"
OUT = ROOT / "FineTuning" / "artigo_assets" / "figuras"
OUT.mkdir(parents=True, exist_ok=True)

# Paleta consistente por modelo
COR = {
    "Base": "#8C8C8C",
    "FT-FinQA": "#1F77B4",
    "FT-Failure": "#2CA02C",
    "FT-Híbrido": "#D62728",
}
MODELOS = ["Base", "FT-FinQA", "FT-Failure", "FT-Híbrido"]

# ---- Dados reais extraidos dos JSONs de metrics ----
# FinQA numeric_accuracy (metrica principal do dominio financeiro)
FINQA_NUMACC = {"Base": 0.0149, "FT-FinQA": 0.1045, "FT-Failure": 0.0829, "FT-Híbrido": 0.1061}
# FailureSensorIQ accuracy (metrica principal do dominio industrial)
FAIL_ACC = {"Base": 0.0012, "FT-FinQA": 0.2936, "FT-Failure": 0.9976, "FT-Híbrido": 0.9615}
FAIL_F1 = {"Base": 0.0000, "FT-FinQA": 0.0249, "FT-Failure": 0.9986, "FT-Híbrido": 0.9558}

# Breakdown por operacao no FinQA (numeric_match)
OPS = ["add", "divide", "subtract", "multiply", "table_max", "table_min"]
OPS_LABEL = ["Soma", "Divisão", "Subtração", "Multiplic.", "Tab. máx.", "Tab. mín."]
BREAKDOWN = {
    "Base":       [0.0133, 0.0227, 0.0000, 0.0000, 0.125, 0.50],
    "FT-FinQA":   [0.1467, 0.1000, 0.1008, 0.0244, 0.250, 0.50],
    "FT-Híbrido": [0.1067, 0.1091, 0.0887, 0.1220, 0.250, 0.75],
}


def barras_dominio(dados, titulo, ylabel, fname, fmt_pct=True):
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    vals = [dados[m] * 100 for m in MODELOS]
    cores = [COR[m] for m in MODELOS]
    bars = ax.bar(MODELOS, vals, color=cores, edgecolor="black", linewidth=0.6, width=0.62)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.015,
                f"{v:.2f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.set_title(titulo)
    ax.set_ylim(0, max(vals) * 1.18)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    fig.savefig(OUT / fname)
    plt.close(fig)
    print("ok:", fname)


def grafico_crossdomain(fname):
    """Barras agrupadas: desempenho de cada modelo nos dois dominios (equilibrio)."""
    import numpy as np
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = np.arange(len(MODELOS))
    w = 0.38
    fin = [FINQA_NUMACC[m] * 100 for m in MODELOS]
    fail = [FAIL_ACC[m] * 100 for m in MODELOS]
    b1 = ax.bar(x - w/2, fin, w, label="FinQA (Acur. numérica)", color="#1F77B4", edgecolor="black", linewidth=0.5)
    b2 = ax.bar(x + w/2, fail, w, label="FailureSensorIQ (Acurácia)", color="#2CA02C", edgecolor="black", linewidth=0.5)
    for bars in (b1, b2):
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width()/2, h + 1.2, f"{h:.1f}", ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels(MODELOS)
    ax.set_ylabel("Desempenho (%)")
    ax.set_title("Avaliação por domínio e transferência cruzada")
    ax.set_ylim(0, 108)
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.4); ax.set_axisbelow(True)
    fig.savefig(OUT / fname); plt.close(fig); print("ok:", fname)


def grafico_ganho(fname):
    """Ganho percentual (pontos) sobre o baseline, por dominio."""
    import numpy as np
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    fts = ["FT-FinQA", "FT-Failure", "FT-Híbrido"]
    x = np.arange(len(fts))
    w = 0.38
    g_fin = [(FINQA_NUMACC[m] - FINQA_NUMACC["Base"]) * 100 for m in fts]
    g_fail = [(FAIL_ACC[m] - FAIL_ACC["Base"]) * 100 for m in fts]
    b1 = ax.bar(x - w/2, g_fin, w, label="FinQA (Δ acur. numérica)", color="#1F77B4", edgecolor="black", linewidth=0.5)
    b2 = ax.bar(x + w/2, g_fail, w, label="FailureSensorIQ (Δ acurácia)", color="#2CA02C", edgecolor="black", linewidth=0.5)
    for bars in (b1, b2):
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width()/2, h + 1.0, f"+{h:.1f}", ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels(fts)
    ax.set_ylabel("Ganho sobre o Base (pontos percentuais)")
    ax.set_title("Ganho do fine-tuning em relação ao modelo base")
    ax.set_ylim(0, 108)
    ax.legend(fontsize=9, loc="upper center")
    ax.grid(axis="y", linestyle="--", alpha=0.4); ax.set_axisbelow(True)
    fig.savefig(OUT / fname); plt.close(fig); print("ok:", fname)


def grafico_breakdown(fname):
    import numpy as np
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    x = np.arange(len(OPS))
    w = 0.26
    for i, m in enumerate(["Base", "FT-FinQA", "FT-Híbrido"]):
        vals = [v * 100 for v in BREAKDOWN[m]]
        ax.bar(x + (i - 1) * w, vals, w, label=m, color=COR[m], edgecolor="black", linewidth=0.4)
    ax.set_xticks(x); ax.set_xticklabels(OPS_LABEL)
    ax.set_ylabel("Acurácia numérica (%)")
    ax.set_title("FinQA — desempenho por tipo de operação")
    ax.legend(fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4); ax.set_axisbelow(True)
    fig.savefig(OUT / fname); plt.close(fig); print("ok:", fname)


def carregar_log(nome):
    p = RES / nome / "logs" / "training_log.jsonl"
    train, ev = [], []
    for ln in p.read_text(encoding="utf-8").splitlines():
        d = json.loads(ln)
        if "loss" in d and "learning_rate" in d:
            train.append(d)
        if "eval_loss" in d:
            ev.append(d)
    return train, ev


RUNS = {
    "FT-FinQA": "ft_finqa_v1_run_v1_seed42",
    "FT-Failure": "ft_failure_v1_run_v1_seed42",
    "FT-Híbrido": "ft_hibrido_v1_run_v1_seed42",
}


def grafico_loss(fname):
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    for label, nome in RUNS.items():
        tr, ev = carregar_log(nome)
        ax.plot([d["step"] for d in tr], [d["loss"] for d in tr],
                label=f"{label} (treino)", color=COR[label], linewidth=1.6)
        if ev:
            ax.plot([d["step"] for d in ev], [d["eval_loss"] for d in ev],
                    "o--", color=COR[label], linewidth=1.0, markersize=5, alpha=0.7,
                    label=f"{label} (validação)")
    ax.set_xlabel("Passo de treinamento (step)")
    ax.set_ylabel("Loss")
    ax.set_title("Curvas de perda durante o treinamento (Qwen2.5-7B + QLoRA)")
    ax.legend(fontsize=8, ncol=3)
    ax.grid(linestyle="--", alpha=0.4); ax.set_axisbelow(True)
    fig.savefig(OUT / fname); plt.close(fig); print("ok:", fname)


def grafico_lr(fname):
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    for label, nome in RUNS.items():
        tr, _ = carregar_log(nome)
        ax.plot([d["step"] for d in tr], [d["learning_rate"] for d in tr],
                label=label, color=COR[label], linewidth=1.6)
    ax.set_xlabel("Passo de treinamento (step)")
    ax.set_ylabel("Learning rate")
    ax.set_title("Evolução do learning rate (warmup + decaimento)")
    ax.legend(fontsize=9)
    ax.grid(linestyle="--", alpha=0.4); ax.set_axisbelow(True)
    fig.savefig(OUT / fname); plt.close(fig); print("ok:", fname)


def grafico_gradnorm(fname):
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    for label, nome in RUNS.items():
        tr, _ = carregar_log(nome)
        ax.plot([d["step"] for d in tr], [d.get("grad_norm", float("nan")) for d in tr],
                label=label, color=COR[label], linewidth=1.3, alpha=0.9)
    ax.set_xlabel("Passo de treinamento (step)")
    ax.set_ylabel("Norma do gradiente")
    ax.set_title("Norma do gradiente ao longo do treinamento")
    ax.legend(fontsize=9)
    ax.grid(linestyle="--", alpha=0.4); ax.set_axisbelow(True)
    fig.savefig(OUT / fname); plt.close(fig); print("ok:", fname)


if __name__ == "__main__":
    barras_dominio(FAIL_ACC, "FailureSensorIQ — Acurácia por modelo",
                   "Acurácia (%)", "fig_resultado_failure.png")
    barras_dominio(FINQA_NUMACC, "FinQA — Acurácia numérica por modelo",
                   "Acurácia numérica (%)", "fig_resultado_finqa.png")
    grafico_crossdomain("fig_crossdomain.png")
    grafico_ganho("fig_ganho_baseline.png")
    grafico_breakdown("fig_breakdown_operacao.png")
    grafico_loss("fig_loss.png")
    grafico_lr("fig_learning_rate.png")
    grafico_gradnorm("fig_grad_norm.png")
    print("\nFiguras geradas em:", OUT)
