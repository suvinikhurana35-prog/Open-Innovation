"""
Latency evaluation: average, median, P95, and std of wall-clock time per
operation (explainer, simple story, hidden conditions, compare, chat), measured
over all 18 schemes. Deterministic set, warm cache (each op is run once to warm,
then timed).

  python latency_eval.py
"""
import time
from collections import defaultdict

from utils import OUTPUTS, ensure_dirs, write_csv
import metrics
from services import ai_service, kb_service


def _time(fn):
    t0 = time.perf_counter()
    fn()
    return (time.perf_counter() - t0) * 1000.0  # ms


def evaluate():
    ensure_dirs()
    schemes = kb_service.all_schemes()
    titles = [s.title for s in schemes]
    print(f"[INFO] Latency evaluation over {len(schemes)} schemes.")

    ops = {
        "explainer": lambda t: ai_service.generate_explainer(t, "en"),
        "simple_story": lambda t: ai_service.generate_eli5(t, "en"),
        "hidden_conditions": lambda t: ai_service.detect_conditions(t, "en"),
        "chat": lambda t: ai_service.chat_with_ai(t, language="en"),
    }
    samples = defaultdict(list)

    # warm
    for fn in ops.values():
        fn(titles[0])
    # compare warm
    ai_service.compare_schemes(titles[0], titles[1], "en")

    for op, fn in ops.items():
        for t in titles:
            samples[op].append(_time(lambda: fn(t)))
    for i in range(len(titles) - 1):
        a, b = titles[i], titles[i + 1]
        samples["compare"].append(_time(lambda: ai_service.compare_schemes(a, b, "en")))

    metric_rows = []
    for op, vals in samples.items():
        s = metrics.summarize(vals)
        metric_rows.append({"operation": op,
                            "avg_ms": round(s["mean"], 3),
                            "median_ms": round(s["median"], 3),
                            "p95_ms": round(s["p95"], 3),
                            "std_ms": round(s["std"], 3),
                            "n": s["n"]})
    write_csv(f"{OUTPUTS}/latency_metrics.csv", metric_rows)

    print("\n[RESULT] Latency (ms):")
    print(f"  {'operation':18s} {'avg':>9s} {'median':>9s} {'p95':>9s} {'std':>9s}")
    for r in metric_rows:
        print(f"  {r['operation']:18s} {r['avg_ms']:9.3f} {r['median_ms']:9.3f} "
              f"{r['p95_ms']:9.3f} {r['std_ms']:9.3f}")
    print("[INFO] Latency evaluation done.")


if __name__ == "__main__":
    evaluate()
