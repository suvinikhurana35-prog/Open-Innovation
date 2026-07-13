"""
Functional validation: for each core feature, verify it returns a well-formed,
non-empty, grounded response across the 18 schemes. Reports a pass rate per
feature (chat, comparison, recommendation, explainer, hidden conditions).

  python functional_eval.py
"""
from collections import defaultdict

from utils import OUTPUTS, ensure_dirs, write_csv
from services import ai_service, kb_service


def evaluate():
    ensure_dirs()
    schemes = kb_service.all_schemes()
    titles = [s.title for s in schemes]
    print(f"[INFO] Functional validation over {len(schemes)} schemes.")

    counts = defaultdict(lambda: [0, 0])  # feature -> [pass, total]

    def check(feature, ok):
        counts[feature][1] += 1
        if ok:
            counts[feature][0] += 1

    for s in schemes:
        t = s.title
        ex = ai_service.generate_explainer(t, "en").model_dump()
        check("explainer", bool(ex.get("what_is")) and bool(ex.get("benefits")))

        st = ai_service.generate_eli5(t, "en")
        check("simple_story", bool(st.story) and bool(st.simple_explanation))

        hc = ai_service.detect_conditions(t, "en")
        check("hidden_conditions", bool(hc.get("conditions")))

        ch = ai_service.chat_with_ai(f"Who is eligible for {t}?", language="en")
        check("chat", bool(ch.get("reply")) and ch.get("grounded", False))

    # comparison + recommendation over adjacent pairs
    for i in range(len(titles) - 1):
        a, b = titles[i], titles[i + 1]
        cmp = ai_service.compare_schemes(a, b, "en")
        check("comparison", bool(cmp.get("comparisons")) and len(cmp["comparisons"]) >= 6)
        rec = ai_service.recommend_for_profile(a, b, {"occupation": "farmer", "age": 35}, "en")
        check("recommendation", bool(rec.get("recommended_scheme")))

    rows = []
    for feature, (p, tot) in sorted(counts.items()):
        rows.append({"feature": feature, "passed": p, "total": tot,
                     "pass_rate_pct": round(100 * p / tot, 2) if tot else 0.0})
    write_csv(f"{OUTPUTS}/functional_metrics.csv", rows)

    print("\n[RESULT] Functional validation:")
    print(f"  {'feature':20s} {'pass':>6s} {'total':>6s} {'rate%':>7s}")
    for r in rows:
        print(f"  {r['feature']:20s} {r['passed']:6d} {r['total']:6d} {r['pass_rate_pct']:7.1f}")
    print("[INFO] Functional evaluation done.")


if __name__ == "__main__":
    evaluate()
