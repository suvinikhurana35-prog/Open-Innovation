"""
Assemble the paper tables (I-VII) from the metric CSVs and export each as CSV,
LaTeX, and a combined Excel workbook (final_metrics.xlsx). Missing inputs are
skipped with a notice.

  python tables.py
"""
import os
import csv

from utils import OUTPUTS, ensure_dirs

TABLES = {
    "table1_retrieval": ("Retrieval Performance", "retrieval_metrics.csv"),
    "table2_recommendation": ("Recommendation Performance", "recommendation_metrics.csv"),
    "table3_grounding": ("Grounding Evaluation", "grounding_metrics.csv"),
    "table4_multilingual": ("Multilingual Evaluation", "multilingual_metrics.csv"),
    "table5_latency": ("Latency (ms)", "latency_metrics.csv"),
    "table6_functional": ("Functional Evaluation", "functional_metrics.csv"),
    "table7_ablation": ("Ablation Study", "ablation_metrics.csv"),
}


def _read(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _latex(caption, label, rows):
    cols = list(rows[0].keys())
    align = "l" + "c" * (len(cols) - 1)
    esc = lambda s: str(s).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")
    lines = [r"\begin{table}[t]", r"\centering",
             rf"\caption{{{esc(caption)}}}", rf"\label{{tab:{label}}}",
             rf"\begin{{tabular}}{{{align}}}", r"\toprule",
             " & ".join(r"\textbf{" + esc(c) + "}" for c in cols) + r" \\", r"\midrule"]
    for r in rows:
        lines.append(" & ".join(esc(r[c]) for c in cols) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


def main():
    ensure_dirs()
    print("[INFO] Building tables...")
    try:
        from openpyxl import Workbook
        wb = Workbook()
        wb.remove(wb.active)
    except Exception:
        wb = None
        print("[WARN] openpyxl missing -> skipping final_metrics.xlsx")

    made = 0
    for name, (caption, src) in TABLES.items():
        rows = _read(f"{OUTPUTS}/{src}")
        if not rows:
            print(f"[skip] {src} not found -> {name}")
            continue
        # CSV (copy through, canonical name)
        with open(f"{OUTPUTS}/{name}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        # LaTeX
        with open(f"{OUTPUTS}/{name}.tex", "w", encoding="utf-8") as f:
            f.write(_latex(caption, name, rows))
        # Excel sheet
        if wb is not None:
            ws = wb.create_sheet(title=name[:31])
            ws.append(list(rows[0].keys()))
            for r in rows:
                ws.append([r[c] for c in rows[0].keys()])
        made += 1
        print(f"[INFO] {name}: csv + tex" + (" + xlsx sheet" if wb else ""))

    if wb is not None and made:
        wb.save(f"{OUTPUTS}/final_metrics.xlsx")
        print("[INFO] outputs/final_metrics.xlsx written")
    print(f"[INFO] Tables done ({made} tables).")


if __name__ == "__main__":
    main()
