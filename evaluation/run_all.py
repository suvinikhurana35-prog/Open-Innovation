"""
Master evaluation runner. Executes every stage in dependency order, then builds
figures and tables, and prints a final summary.

  python run_all.py

Stages that need the vector index (retrieval, ablation-retrieval rows) require
chromadb + sentence-transformers and a populated collection (run `python main.py`
once first). If the index is unavailable those stages are skipped with a clear
message; the rest still run.
"""
import os
import sys
import time

from utils import DATASETS, OUTPUTS, FIGURES, ensure_dirs
from services import kb_service


def _check_deps():
    ok = True
    try:
        import matplotlib  # noqa
    except Exception:
        print("[FAIL] matplotlib missing -> pip install matplotlib"); ok = False
    try:
        import openpyxl  # noqa
    except Exception:
        print("[WARN] openpyxl missing (xlsx export disabled) -> pip install openpyxl")
    try:
        from services.rag_service import rag_service
        rag_ok = rag_service.available and rag_service.count_documents() > 0
    except Exception as e:
        rag_ok = False
        print(f"[WARN] RAG unavailable: {e}")
    return ok, rag_ok


def main():
    ensure_dirs()
    t_start = time.perf_counter()
    print("=" * 60)
    print("  JanNiti Evaluation — run_all")
    print("=" * 60)

    deps_ok, rag_ok = _check_deps()
    if not deps_ok:
        sys.exit("[ERROR] Required dependencies missing. See messages above.")
    print(f"[INFO] Vector retrieval available: {rag_ok}")

    import benchmark
    print("\n>>> Benchmark")
    sys.argv = ["benchmark.py"]
    _safe(benchmark.main)

    if rag_ok:
        print("\n>>> Retrieval"); _safe(lambda: __import__("retrieval_eval").evaluate())
    else:
        print("\n>>> Retrieval [SKIPPED — no vector index]")

    print("\n>>> Grounding"); _safe(lambda: __import__("grounding_eval").evaluate())
    print("\n>>> Multilingual"); _safe(lambda: __import__("multilingual_eval").evaluate())
    print("\n>>> Recommendation"); _safe(lambda: __import__("recommendation_eval").evaluate())
    print("\n>>> Latency"); _safe(lambda: __import__("latency_eval").evaluate())
    print("\n>>> Functional"); _safe(lambda: __import__("functional_eval").evaluate())
    print("\n>>> Ablation"); _safe(lambda: __import__("ablation_eval").evaluate())
    print("\n>>> Plotting"); _safe(lambda: __import__("plotting").main())
    print("\n>>> Tables"); _safe(lambda: __import__("tables").main())

    figs = [f for f in os.listdir(FIGURES) if f.endswith((".png", ".pdf"))] if os.path.isdir(FIGURES) else []
    tabs = [f for f in os.listdir(OUTPUTS) if f.startswith("table") and f.endswith(".tex")] if os.path.isdir(OUTPUTS) else []
    import json
    n_queries = len(json.load(open(f"{DATASETS}/benchmark.json", encoding="utf-8"))) if os.path.exists(f"{DATASETS}/benchmark.json") else 0

    print("\n" + "=" * 60)
    print("  Evaluation Complete")
    print(f"  Total Queries:  {n_queries}")
    print(f"  Total Schemes:  {len(kb_service.all_schemes())}")
    print(f"  Total Runtime:  {time.perf_counter() - t_start:.1f} s")
    print(f"  Output Folder:  {OUTPUTS}")
    print(f"  Figures:        {len(figs)} files in {FIGURES}")
    print(f"  Tables:         {len(tabs)} LaTeX tables (+ csv, +xlsx)")
    print("=" * 60)


def _safe(fn):
    try:
        fn()
    except SystemExit as e:
        print(f"[SKIP] {e}")
    except Exception as e:
        print(f"[ERROR] stage failed: {e}")


if __name__ == "__main__":
    main()
