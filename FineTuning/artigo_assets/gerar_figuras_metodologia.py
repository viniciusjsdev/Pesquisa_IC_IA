#!/usr/bin/env python3
"""
Regenera as figuras da METODOLOGIA (análise exploratória) a partir dos dados
reais do projeto e do tokenizer do Qwen2.5-7B-Instruct (modelo base atual).

Saída: FineTuning/artigo_assets/figuras_metodologia/
Também imprime estatísticas de tokenização para atualizar o texto do artigo.
"""
from __future__ import annotations
import json, re
from collections import Counter
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from transformers import AutoTokenizer

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 11, "axes.titlesize": 12, "axes.titleweight": "bold",
    "savefig.dpi": 200, "savefig.bbox": "tight",
})

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "FineTuning" / "artigo_assets" / "figuras_metodologia"
OUT.mkdir(parents=True, exist_ok=True)
MAXLEN = 1024
C_FIN, C_FAIL = "#1F77B4", "#2CA02C"

print("carregando dados...")
rows = []
for split in ["train", "val", "test"]:
    for ln in (ROOT / f"FineTuning/data/processed/hybrid_v1/{split}.jsonl").read_text(encoding="utf-8").splitlines():
        rows.append(json.loads(ln))
fin = [r for r in rows if (r.get("meta") or {}).get("dataset") == "FinQA"]
fail = [r for r in rows if (r.get("meta") or {}).get("dataset") == "FailureSensorIQ"]
print(f"FinQA={len(fin)}  Failure={len(fail)}  total={len(rows)}")

print("carregando tokenizer Qwen2.5...")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

def tok_lens(items, field_full=False):
    if field_full:
        texts = [f"{r.get('prompt','')} {r.get('resposta','')}" for r in items]
    else:
        texts = [r.get("prompt", "") for r in items]
    out = tok(texts, add_special_tokens=True)["input_ids"]
    return np.array([len(x) for x in out])

print("tokenizando (Qwen)...")
fin_p, fail_p = tok_lens(fin), tok_lens(fail)            # prompt
fin_s, fail_s = tok_lens(fin, True), tok_lens(fail, True)  # prompt+resposta (sequência)
all_s = np.concatenate([fin_s, fail_s])

def pct(a, q): return float(np.percentile(a, q))
trunc_fin = float((fin_s > MAXLEN).mean() * 100)
trunc_fail = float((fail_s > MAXLEN).mean() * 100)
trunc_all = float((all_s > MAXLEN).mean() * 100)
print("\n===== ESTATÍSTICAS (tokens Qwen) =====")
print(f"Prompt FinQA  -> mediana {np.median(fin_p):.0f}, p90 {pct(fin_p,90):.0f}, máx {fin_p.max()}")
print(f"Prompt Failure-> mediana {np.median(fail_p):.0f}, p90 {pct(fail_p,90):.0f}, máx {fail_p.max()}")
print(f"Sequência (prompt+resp) global -> mediana {np.median(all_s):.0f}, p90 {pct(all_s,90):.0f}")
print(f"Faixa central (p10-p90) global -> {pct(all_s,10):.0f} a {pct(all_s,90):.0f} tokens")
print(f"Truncamento >1024 -> FinQA {trunc_fin:.2f}%  Failure {trunc_fail:.2f}%  Global {trunc_all:.2f}%")
print("======================================\n")

# ---- Fig 1: distribuição de tamanhos de prompt (tokens) ----
fig, ax = plt.subplots(figsize=(6.6, 4.0))
bins = np.linspace(0, max(fin_p.max(), fail_p.max()), 60)
ax.hist(fin_p, bins=bins, alpha=0.6, color=C_FIN, label="FinQA", edgecolor="white", linewidth=0.2)
ax.hist(fail_p, bins=bins, alpha=0.6, color=C_FAIL, label="FailureSensorIQ", edgecolor="white", linewidth=0.2)
ax.set_xlabel("Tamanho do prompt (tokens Qwen2.5)"); ax.set_ylabel("Frequência")
ax.set_title("Distribuição comparativa de tamanhos de prompts")
ax.legend(); ax.grid(axis="y", linestyle="--", alpha=0.4); ax.set_axisbelow(True)
fig.savefig(OUT / "fig1_prompts.png"); plt.close(fig)

# ---- Fig 2: boxplot de tokens por dataset ----
fig, ax = plt.subplots(figsize=(6.0, 4.0))
bp = ax.boxplot([fin_p, fail_p], labels=["FinQA", "FailureSensorIQ"], patch_artist=True, showfliers=True,
                flierprops=dict(marker="o", markersize=2, alpha=0.3))
for patch, c in zip(bp["boxes"], [C_FIN, C_FAIL]):
    patch.set_facecolor(c); patch.set_alpha(0.6)
for med in bp["medians"]: med.set_color("black")
ax.set_ylabel("Tokens por prompt (Qwen2.5)")
ax.set_title("Distribuição de tokens por dataset")
ax.grid(axis="y", linestyle="--", alpha=0.4); ax.set_axisbelow(True)
fig.savefig(OUT / "fig2_tokens.png"); plt.close(fig)

# ---- Fig 3: tipo de pergunta ----
ops = Counter((r["meta"].get("program", "") or "").split("(")[0].strip() for r in fin)
ops_lbl = {"subtract": "Subtração", "divide": "Divisão", "add": "Soma", "multiply": "Multiplic.",
           "greater": "Comparação", "table_average": "Tab. média", "table_max": "Tab. máx.",
           "table_sum": "Tab. soma", "table_min": "Tab. mín."}
order = [k for k, _ in ops.most_common()]
fail_tipo = Counter((r["meta"].get("tipo", "?")) for r in fail)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 4.0))
a1.bar([ops_lbl.get(k, k) for k in order], [ops[k] for k in order], color=C_FIN, edgecolor="black", linewidth=0.4)
a1.set_title("FinQA — tipo de raciocínio numérico"); a1.set_ylabel("Nº de questões")
a1.tick_params(axis="x", rotation=45); a1.grid(axis="y", linestyle="--", alpha=0.4); a1.set_axisbelow(True)
ft_lbl = {"SC-MCQA": "Resposta única\n(SC-MCQA)", "MC-MCQA": "Múltiplas corretas\n(MC-MCQA)"}
fk = list(fail_tipo.keys())
a2.bar([ft_lbl.get(k, k) for k in fk], [fail_tipo[k] for k in fk], color=C_FAIL, edgecolor="black", linewidth=0.4)
a2.set_title("FailureSensorIQ — formato da questão"); a2.set_ylabel("Nº de questões")
a2.grid(axis="y", linestyle="--", alpha=0.4); a2.set_axisbelow(True)
fig.suptitle("Distribuição por tipo de pergunta", fontweight="bold")
fig.savefig(OUT / "fig3_tipo.png"); plt.close(fig)

# ---- Fig 4: word clouds ----
try:
    from wordcloud import WordCloud, STOPWORDS
    stop = set(STOPWORDS) | {"instruction", "context", "response", "following", "based", "given",
                             "question", "answer", "data", "table", "value", "values"}
    def clean(items):
        txt = " ".join((r.get("prompt", "")) for r in items)
        txt = re.sub(r"###\s*\w+:?", " ", txt)
        return txt
    wc_fin = WordCloud(width=900, height=600, background_color="white", stopwords=stop,
                       colormap="Blues", max_words=120).generate(clean(fin))
    wc_fail = WordCloud(width=900, height=600, background_color="white", stopwords=stop,
                        colormap="Greens", max_words=120).generate(clean(fail))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    a1.imshow(wc_fin); a1.axis("off"); a1.set_title("FinQA (financeiro)")
    a2.imshow(wc_fail); a2.axis("off"); a2.set_title("FailureSensorIQ (industrial)")
    fig.suptitle("Vocabulário característico de cada domínio", fontweight="bold")
    fig.savefig(OUT / "fig4_wordcloud.png"); plt.close(fig)
except Exception as e:
    print("[aviso] wordcloud falhou:", e)

# ---- Fig 5: distribuição de comprimentos de sequência ----
fig, ax = plt.subplots(figsize=(6.8, 4.0))
bins = np.linspace(0, min(all_s.max(), 1400), 60)
ax.hist(np.clip(all_s, 0, 1400), bins=bins, color="#6A51A3", alpha=0.8, edgecolor="white", linewidth=0.2)
ax.axvline(MAXLEN, color="red", linestyle="--", linewidth=1.4, label=f"Limite de truncamento ({MAXLEN})")
ax.set_xlabel("Comprimento da sequência (prompt + resposta, tokens Qwen2.5)")
ax.set_ylabel("Frequência"); ax.set_title("Distribuição de comprimentos de sequência")
ax.legend(); ax.grid(axis="y", linestyle="--", alpha=0.4); ax.set_axisbelow(True)
fig.savefig(OUT / "fig5_seqlen.png"); plt.close(fig)

# ---- Fig 6: taxa de truncamento ----
fig, ax = plt.subplots(figsize=(6.2, 4.0))
labels = ["FinQA", "FailureSensorIQ", "Global"]
vals = [trunc_fin, trunc_fail, trunc_all]
bars = ax.bar(labels, vals, color=[C_FIN, C_FAIL, "#8C8C8C"], edgecolor="black", linewidth=0.5, width=0.6)
for b, v in zip(bars, vals):
    ax.text(b.get_x()+b.get_width()/2, v+max(vals)*0.03+0.02, f"{v:.2f}%", ha="center", va="bottom", fontweight="bold")
ax.set_ylabel("Sequências truncadas (%)")
ax.set_title(f"Taxa de truncamento no limite de {MAXLEN} tokens")
ax.set_ylim(0, max(vals)*1.25+0.5); ax.grid(axis="y", linestyle="--", alpha=0.4); ax.set_axisbelow(True)
fig.savefig(OUT / "fig6_padding.png"); plt.close(fig)

# ---- Fig 7: comparação de quantização (memória p/ 7B) ----
fig, ax = plt.subplots(figsize=(6.2, 4.0))
tecn = ["FP16", "INT8", "NF4 (QLoRA)"]
mem = [14.0, 7.0, 3.5]
cores = ["#8C8C8C", "#1F77B4", "#D62728"]
bars = ax.bar(tecn, mem, color=cores, edgecolor="black", linewidth=0.5, width=0.6)
for b, v in zip(bars, mem):
    ax.text(b.get_x()+b.get_width()/2, v+0.2, f"{v:.1f} GB", ha="center", va="bottom", fontweight="bold")
ax.set_ylabel("Memória aproximada do modelo (GB)")
ax.set_title("Comparação de técnicas de quantização (modelo 7B)")
ax.set_ylim(0, 16); ax.grid(axis="y", linestyle="--", alpha=0.4); ax.set_axisbelow(True)
fig.savefig(OUT / "fig7_quant.png"); plt.close(fig)

print("Figuras geradas em:", OUT)
