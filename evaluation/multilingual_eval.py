"""
Multilingual evaluation: for each language, measure script correctness (fraction
of output rendered in the requested script) and translation fidelity (fraction
of numeric facts from the English source preserved in the translated output).

Uses the production explainer, which serves each scheme in en/hi/bn/ta from the
curated + translated knowledge base.

  python multilingual_eval.py
"""
import re
from collections import defaultdict

from utils import OUTPUTS, LANGUAGES, LANG_NAME, ensure_dirs, write_csv
from services import ai_service, kb_service

_BLOCKS = {"hi": (0x0900, 0x097F), "bn": (0x0980, 0x09FF), "ta": (0x0B80, 0x0BFF)}


def script_ratio(text, lang):
    if lang == "en" or lang not in _BLOCKS:
        return 1.0
    lo, hi = _BLOCKS[lang]
    letters = [c for c in (text or "") if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if lo <= ord(c) <= hi) / len(letters)


def _numbers(text):
    return set(re.findall(r"\d[\d,]*", text or ""))


def _explainer_text(d):
    parts = [d.get("what_is", "")]
    for key in ("benefits", "eligibility"):
        v = d.get(key)
        if isinstance(v, list):
            parts.append(" ".join(v))
    return " ".join(p for p in parts if p)


def evaluate():
    ensure_dirs()
    schemes = kb_service.all_schemes()
    print(f"[INFO] Multilingual evaluation: {len(schemes)} schemes x {len(LANGUAGES)} languages.")

    # english reference numbers per scheme (for fidelity)
    ref_numbers = {}
    for s in schemes:
        d = ai_service.generate_explainer(s.title, "en").model_dump()
        ref_numbers[s.slug] = _numbers(_explainer_text(d))

    per_rows = []
    agg = defaultdict(lambda: {"script": [], "fidelity": []})
    for s in schemes:
        for lang in LANGUAGES:
            d = ai_service.generate_explainer(s.title, lang).model_dump()
            text = _explainer_text(d)
            sr = script_ratio(text, lang)
            ref = ref_numbers[s.slug]
            got = _numbers(text)
            fidelity = 1.0 if not ref else len(ref & got) / len(ref)
            per_rows.append({"scheme": s.slug, "language": lang,
                             "script_ratio": round(sr, 4),
                             "script_correct": int(sr >= 0.6),
                             "numeric_fidelity": round(fidelity, 4)})
            agg[lang]["script"].append(sr)
            agg[lang]["fidelity"].append(fidelity)

    write_csv(f"{OUTPUTS}/multilingual_results.csv", per_rows)

    metric_rows = []
    for lang in LANGUAGES:
        sr = agg[lang]["script"]
        fi = agg[lang]["fidelity"]
        metric_rows.append({
            "language": LANG_NAME[lang],
            "script_correct_pct": round(100 * sum(1 for x in sr if x >= 0.6) / len(sr), 2),
            "mean_script_ratio": round(sum(sr) / len(sr), 4),
            "mean_numeric_fidelity": round(sum(fi) / len(fi), 4),
        })
    write_csv(f"{OUTPUTS}/multilingual_metrics.csv", metric_rows)

    print("\n[RESULT] Multilingual:")
    print(f"  {'language':10s} {'script_correct%':>16s} {'script_ratio':>13s} {'num_fidelity':>13s}")
    for r in metric_rows:
        print(f"  {r['language']:10s} {r['script_correct_pct']:16.1f} "
              f"{r['mean_script_ratio']:13.3f} {r['mean_numeric_fidelity']:13.3f}")
    print("[INFO] Multilingual evaluation done.")


if __name__ == "__main__":
    evaluate()
