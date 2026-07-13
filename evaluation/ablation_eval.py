"""
Ablation study: Dense -> Hybrid -> +Grounding -> JanNiti.

Retrieval rows (Dense, Hybrid, JanNiti) are taken from retrieval_metrics.csv
(overall scope). The grounding effect (+Grounding) is taken from
grounding_metrics.csv (grounded vs ungrounded faithfulness / hallucination).
This module assembles the ablation view from those computed results rather than
re-running retrieval, so there is no duplicated logic.

  python ablation_eval.py         # requires retrieval_metrics.csv + grounding_metrics.csv
Run retrieval_eval.py and grounding_eval.py first (run_all.py does this in order).
"""
import os
import csv
import sys

from utils import OUTPUTS, ensure_dirs, write_csv


def _read_csv(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def evaluate():
    ensure_dirs()
    retr = _read_csv(f"{OUTPUTS}/retrieval_metrics.csv")
    grnd = _read_csv(f"{OUTPUTS}/grounding_metrics.csv")
    if retr is None:
        sys.exit("[ERROR] retrieval_metrics.csv missing. Run retrieval_eval.py first.")

    overall = {r["system"]: r for r in retr if r.get("scope") == "overall"}
    rows = []
    for stage in ("Dense", "Hybrid", "JanNiti"):
        if stage in overall:
            r = overall[stage]
            rows.append({"configuration": stage,
                         "hit@5": r["hit@5"], "ndcg@5": r["ndcg@5"],
                         "mrr": r["mrr"], "faithfulness": "", "hallucination_pct": ""})

    if grnd is not None:
        g = {r["system"]: r for r in grnd}
        gk = next((k for k in g if "grounded" in k.lower()), None)
        uk = next((k for k in g if "ungrounded" in k.lower()), None)
        if uk:
            rows.append({"configuration": "Ungrounded (no retrieval)",
                         "hit@5": "", "ndcg@5": "", "mrr": "",
                         "faithfulness": g[uk]["mean_faithfulness"],
                         "hallucination_pct": g[uk]["hallucination_rate_pct"]})
        if gk:
            rows.append({"configuration": "JanNiti + Grounding",
                         "hit@5": "", "ndcg@5": "", "mrr": "",
                         "faithfulness": g[gk]["mean_faithfulness"],
                         "hallucination_pct": g[gk]["hallucination_rate_pct"]})

    write_csv(f"{OUTPUTS}/ablation_metrics.csv", rows)
    print("\n[RESULT] Ablation:")
    print(f"  {'configuration':28s} {'Hit@5':>7s} {'NDCG@5':>7s} {'Faith':>7s} {'Halluc%':>8s}")
    for r in rows:
        print(f"  {r['configuration']:28s} {str(r['hit@5']):>7s} {str(r['ndcg@5']):>7s} "
              f"{str(r['faithfulness']):>7s} {str(r['hallucination_pct']):>8s}")
    print("[INFO] Ablation evaluation done.")


if __name__ == "__main__":
    evaluate()
