"""
Publication-quality figures (matplotlib only, 300 DPI, grayscale-friendly)
generated from the metric CSVs in outputs/. Each figure is written as both PNG
and PDF. Missing CSVs are skipped with a notice (so partial runs still plot what
they can).

  python plotting.py
"""
import os
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import OUTPUTS, FIGURES, ensure_dirs

# grayscale-friendly hatches + greys
HATCH = ["", "//", "xx", ".."]
GREYS = ["#3b3b3b", "#6f6f6f", "#9a9a9a", "#c3c3c3"]


def _read(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(f"{FIGURES}/{name}.png", dpi=300)
    fig.savefig(f"{FIGURES}/{name}.pdf")
    plt.close(fig)
    print(f"[INFO] figures/{name}.{{png,pdf}}")


def _grouped_bar(systems, metric_key, title, ylabel, fname, rows):
    overall = [r for r in rows if r.get("scope", "overall") == "overall"]
    order = [r for s in systems for r in overall if r["system"] == s]
    if not order:
        return
    labels = [r["system"] for r in order]
    vals = [float(r[metric_key]) for r in order]
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    bars = ax.bar(labels, vals, color=GREYS[:len(labels)], edgecolor="black", linewidth=0.7)
    for b, h in zip(bars, HATCH[:len(labels)]):
        b.set_hatch(h)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_ylim(0, max(vals) * 1.25 if vals else 1)
    for i, v in enumerate(vals):
        ax.text(i, v + max(vals) * 0.02, f"{v:.3f}", ha="center", fontsize=8)
    _save(fig, fname)


def plot_retrieval():
    rows = _read(f"{OUTPUTS}/retrieval_metrics.csv")
    if not rows:
        print("[skip] retrieval_metrics.csv not found")
        return
    systems = ["BM25", "Dense", "Hybrid", "JanNiti"]
    for key, title, fname in [
        ("precision@5", "Retrieval Precision@5", "retrieval_precision"),
        ("recall@5", "Retrieval Recall@5", "retrieval_recall"),
        ("mrr", "Retrieval MRR", "retrieval_mrr"),
        ("ndcg@5", "Retrieval NDCG@5", "retrieval_ndcg"),
        ("hit@5", "Retrieval Hit@5", "retrieval_hit5"),
    ]:
        _grouped_bar(systems, key, title, key.upper(), fname, rows)


def plot_multilingual():
    rows = _read(f"{OUTPUTS}/multilingual_metrics.csv")
    if not rows:
        print("[skip] multilingual_metrics.csv not found")
        return
    labels = [r["language"] for r in rows]
    sc = [float(r["script_correct_pct"]) for r in rows]
    fi = [float(r["mean_numeric_fidelity"]) * 100 for r in rows]
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    w = 0.38
    b1 = ax.bar([i - w / 2 for i in x], sc, w, label="Script correct %",
               color=GREYS[0], edgecolor="black", linewidth=0.7)
    b2 = ax.bar([i + w / 2 for i in x], fi, w, label="Numeric fidelity %",
               color=GREYS[2], edgecolor="black", linewidth=0.7, hatch="//")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    ax.set_ylabel("Percent"); ax.set_ylim(0, 110)
    ax.set_title("Multilingual quality")
    ax.legend(fontsize=8)
    _save(fig, "multilingual")


def plot_recommendation():
    rows = _read(f"{OUTPUTS}/recommendation_metrics.csv")
    if not rows:
        print("[skip] recommendation_metrics.csv not found")
        return
    labels = [r["metric"] for r in rows]
    vals = [float(r["value"]) for r in rows]
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    bars = ax.bar(labels, vals, color=GREYS[:len(labels)], edgecolor="black", linewidth=0.7)
    for b, h in zip(bars, HATCH * 2):
        b.set_hatch(h)
    ax.set_ylabel("Percent"); ax.set_ylim(0, 110)
    ax.set_title("Recommendation performance")
    ax.tick_params(axis="x", rotation=20)
    for i, v in enumerate(vals):
        ax.text(i, v + 2, f"{v:.1f}", ha="center", fontsize=8)
    _save(fig, "recommendation")


def plot_grounding():
    rows = _read(f"{OUTPUTS}/grounding_metrics.csv")
    if not rows:
        print("[skip] grounding_metrics.csv not found")
        return
    labels = [r["system"] for r in rows]
    faith = [float(r["mean_faithfulness"]) for r in rows]
    hall = [float(r["hallucination_rate_pct"]) / 100 for r in rows]
    x = range(len(labels))
    w = 0.38
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    ax.bar([i - w / 2 for i in x], faith, w, label="Faithfulness",
           color=GREYS[0], edgecolor="black", linewidth=0.7)
    ax.bar([i + w / 2 for i in x], hall, w, label="Hallucination rate",
           color=GREYS[2], edgecolor="black", linewidth=0.7, hatch="xx")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Score / rate"); ax.set_ylim(0, 1.1)
    ax.set_title("Grounding: grounded vs ungrounded")
    ax.legend(fontsize=8)
    _save(fig, "grounding")


def plot_latency():
    rows = _read(f"{OUTPUTS}/latency_metrics.csv")
    if not rows:
        print("[skip] latency_metrics.csv not found")
        return
    labels = [r["operation"] for r in rows]
    vals = [float(r["avg_ms"]) for r in rows]
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    bars = ax.bar(labels, vals, color=GREYS[1], edgecolor="black", linewidth=0.7)
    ax.set_ylabel("Avg latency (ms)")
    ax.set_title("Latency per operation")
    ax.tick_params(axis="x", rotation=25)
    for i, v in enumerate(vals):
        ax.text(i, v + max(vals) * 0.02, f"{v:.1f}", ha="center", fontsize=8)
    _save(fig, "latency")


def plot_ablation():
    rows = _read(f"{OUTPUTS}/ablation_metrics.csv")
    if not rows:
        print("[skip] ablation_metrics.csv not found")
        return
    ret = [r for r in rows if r.get("hit@5") not in ("", None)]
    if ret:
        labels = [r["configuration"] for r in ret]
        vals = [float(r["ndcg@5"]) for r in ret]
        fig, ax = plt.subplots(figsize=(5.6, 3.2))
        bars = ax.bar(labels, vals, color=GREYS[:len(labels)], edgecolor="black", linewidth=0.7)
        for b, h in zip(bars, HATCH):
            b.set_hatch(h)
        ax.set_ylabel("NDCG@5")
        ax.set_title("Ablation: retrieval configuration")
        ax.tick_params(axis="x", rotation=15)
        _save(fig, "ablation")


def plot_summary():
    """One overview figure combining the headline number from each dimension."""
    pairs = []
    r = _read(f"{OUTPUTS}/retrieval_metrics.csv")
    if r:
        jn = next((x for x in r if x["system"] == "JanNiti" and x.get("scope") == "overall"), None)
        if jn:
            pairs.append(("Retrieval\nHit@5", float(jn["hit@5"]) * 100))
    g = _read(f"{OUTPUTS}/grounding_metrics.csv")
    if g:
        gg = next((x for x in g if "grounded" in x["system"].lower()), None)
        if gg:
            pairs.append(("Grounded\nfaithfulness", float(gg["mean_faithfulness"]) * 100))
    m = _read(f"{OUTPUTS}/multilingual_metrics.csv")
    if m:
        pairs.append(("Script\ncorrect %", sum(float(x["script_correct_pct"]) for x in m) / len(m)))
    rec = _read(f"{OUTPUTS}/recommendation_metrics.csv")
    if rec:
        t1 = next((x for x in rec if x["metric"] == "Top-1 accuracy"), None)
        if t1:
            pairs.append(("Recommend\nTop-1 %", float(t1["value"])))
    fn = _read(f"{OUTPUTS}/functional_metrics.csv")
    if fn:
        pairs.append(("Functional\npass %", sum(float(x["pass_rate_pct"]) for x in fn) / len(fn)))
    if not pairs:
        print("[skip] no metrics for summary")
        return
    labels = [p[0] for p in pairs]
    vals = [p[1] for p in pairs]
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    bars = ax.bar(labels, vals, color=GREYS[1], edgecolor="black", linewidth=0.7)
    ax.set_ylabel("Percent"); ax.set_ylim(0, 110)
    ax.set_title("JanNiti overall evaluation summary")
    for i, v in enumerate(vals):
        ax.text(i, v + 2, f"{v:.1f}", ha="center", fontsize=8)
    _save(fig, "overall_summary")


def main():
    ensure_dirs()
    print("[INFO] Generating figures...")
    plot_retrieval()
    plot_multilingual()
    plot_recommendation()
    plot_grounding()
    plot_latency()
    plot_ablation()
    plot_summary()
    print("[INFO] Plotting done.")


if __name__ == "__main__":
    main()
