"""
JanNiti evaluation harness.
=================================================================
Two kinds of measurement:

  A) SYSTEM metrics (offline, no API key needed) — completeness, coverage,
     language correctness, retrieval accuracy, latency.

  B) GROUNDED-vs-UNGROUNDED experiment (needs a working LLM key) — the same
     questions are answered (i) by JanNiti's grounded KB path and (ii) by the
     SAME model with NO retrieval, then both are scored with the identical
     inference-time faithfulness metric and a script-correctness metric. This
     is the fair, publishable comparison: it isolates the effect of grounding.

Honesty note: this does NOT compare against POLIS-Bench / IndicParam / RAGAS or
other systems' published numbers (that needs a labelled ground-truth set, which
the paper lists as future work). It gives a within-study, apples-to-apples
grounded-vs-ungrounded comparison on your own 18-scheme corpus, plus the system
metrics above. Report them as such.

Run:
  python -m scripts.evaluate
  python -m scripts.evaluate --langs en hi
The model under test is whatever LLM_PROVIDER / ANTHROPIC_MODEL / OPENAI_MODEL
point to in .env — run repeatedly with different models to build a per-model
table. Output: printed tables + results/eval_report.json
"""
import os
import sys
import json
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import kb_service
from services import faithfulness
from services.ai_service import (
    generate_explainer, generate_eli5, detect_conditions,
    compare_schemes, chat_with_ai,
)
import config

LANGS = ["en", "hi", "bn", "ta"]
LANG_NAME = {"en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil"}
_BLOCKS = {"hi": (0x0900, 0x097F), "bn": (0x0980, 0x09FF), "ta": (0x0B80, 0x0BFF)}


def _script_ratio(text, lang):
    if lang == "en" or lang not in _BLOCKS:
        return 1.0
    lo, hi = _BLOCKS[lang]
    letters = [c for c in (text or "") if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if lo <= ord(c) <= hi) / len(letters)


def _pct(n, d):
    return round(100.0 * n / d, 1) if d else 0.0


_PROBES = {
    "pm-kisan": ["PM-KISAN eligibility", "Kisan Samman Nidhi benefits"],
    "kisan-credit-card": ["Kisan Credit Card limit", "KCC interest rate"],
    "fasal-bima": ["Fasal Bima premium", "PMFBY crop insurance"],
    "atal-pension": ["Atal Pension Yojana", "APY pension amount"],
    "jeevan-jyoti-bima": ["Jeevan Jyoti Bima", "PMJJBY life cover"],
    "suraksha-bima": ["Suraksha Bima Yojana", "PMSBY accident cover"],
    "jan-dhan": ["Jan Dhan account", "PMJDY zero balance account"],
    "garib-kalyan-anna": ["Garib Kalyan Anna Yojana", "PMGKAY free ration"],
    "mudra": ["MUDRA loan", "Pradhan Mantri Mudra Yojana"],
    "stand-up-india": ["Stand-Up India loan", "Stand Up India women SC ST"],
    "viksit-bharat-rozgar": ["Viksit Bharat Rozgar Yojana", "PM-VBRY employment"],
    "kaushal-vikas": ["Kaushal Vikas Yojana", "PMKVY skill training"],
    "skill-loan": ["Skill Loan Scheme", "Model Skill Loan"],
    "cbse-single-girl-child": ["CBSE single girl child scholarship", "CBSE SGC merit scholarship"],
    "pg-indira-gandhi-sgc": ["Indira Gandhi single girl child PG scholarship", "PG-IGSSGC"],
    "national-pg-scholarship": ["National Scholarship for Post Graduate", "NSPG postgraduate"],
    "icar-national-talent": ["ICAR National Talent Scholarship", "National Talent Scholarship undergraduate"],
    "ugc-jrf-engineering": ["UGC JRF engineering", "Junior Research Fellowship engineering technology"],
}

_BASELINE = [
    ("What is the benefit amount under PM-KISAN?", "pm-kisan"),
    ("What premium does PM Suraksha Bima Yojana charge?", "suraksha-bima"),
    ("What is the pension range in Atal Pension Yojana?", "atal-pension"),
    ("What life cover does PMJJBY provide and at what premium?", "jeevan-jyoti-bima"),
    ("What interest subvention applies to the Kisan Credit Card?", "kisan-credit-card"),
    ("Who is eligible for Stand-Up India and for how much loan?", "stand-up-india"),
    ("What foodgrain does the Garib Kalyan Anna Yojana give per person?", "garib-kalyan-anna"),
    ("What does the Jan Dhan Yojana offer account holders?", "jan-dhan"),
]

_CHAT_Q = [
    "Do I qualify for PM-KISAN?",
    "What are the benefits of Jan Dhan Yojana?",
    "How to apply for PM Fasal Bima Yojana?",
    "What documents are needed for Atal Pension Yojana?",
    "Is there a hidden rule in MUDRA loan?",
    "Who is eligible for Stand-Up India?",
    "What is Kisan Credit Card?",
    "Tell me about Suraksha Bima Yojana.",
    "which scheme should I apply for?",
    "which scheme helps farmers?",
]


def _ungrounded(question, lang):
    from services.llm import llm_chat, LLM_UNAVAILABLE
    sysmsg = (f"You are a helpful assistant. Answer the user's question about the "
              f"Indian government scheme concisely. Respond entirely in {LANG_NAME.get(lang, 'English')}.")
    r = llm_chat(messages=[{"role": "system", "content": sysmsg},
                           {"role": "user", "content": question}])
    return None if r == LLM_UNAVAILABLE else r


def run(langs):
    schemes = kb_service.all_schemes()
    report = {"n_schemes": len(schemes), "languages": langs,
              "model_under_test": {"provider": config.LLM_PROVIDER,
                                   "model": config.ANTHROPIC_MODEL if config.LLM_PROVIDER == "anthropic" else config.OPENAI_MODEL}}
    lat = {}

    core = ["what_is", "benefits", "eligibility", "documents", "how_to_apply", "source"]
    complete = 0
    t0 = time.perf_counter()
    for s in schemes:
        d = generate_explainer(s.title, "en").model_dump()
        if all(d.get(k) for k in core):
            complete += 1
    lat["explainer"] = (time.perf_counter() - t0) / len(schemes)
    report["explainer_completeness_pct"] = _pct(complete, len(schemes))

    story_ok = cond_ok = 0
    t0 = time.perf_counter()
    for s in schemes:
        e = generate_eli5(s.title, "en")
        story_ok += 1 if (e.story and e.simple_explanation) else 0
    lat["simple_story"] = (time.perf_counter() - t0) / len(schemes)
    for s in schemes:
        cond_ok += 1 if detect_conditions(s.title, "en").get("conditions") else 0
    report["simple_story_coverage_pct"] = _pct(story_ok, len(schemes))
    report["hidden_conditions_coverage_pct"] = _pct(cond_ok, len(schemes))

    hit = tot = 0
    for slug, probes in _PROBES.items():
        for p in probes:
            tot += 1
            m = kb_service.match(p)
            if m is not None and m.slug == slug:
                hit += 1
    report["retrieval_accuracy_pct"] = _pct(hit, tot)
    report["retrieval_probes"] = tot

    lang_stats = {}
    for lang in [l for l in langs if l != "en"]:
        ok = 0
        ratios = []
        t0 = time.perf_counter()
        for s in schemes:
            e = generate_eli5(s.title, lang)
            r = _script_ratio(e.story, lang)
            ratios.append(r)
            ok += 1 if r >= 0.6 else 0
        lat[f"simple_story_{lang}"] = (time.perf_counter() - t0) / len(schemes)
        lang_stats[lang] = {"correct_script_pct": _pct(ok, len(schemes)),
                            "mean_script_ratio": round(sum(ratios) / len(ratios), 3)}
    report["language_correctness"] = lang_stats

    pairs = [("PM-KISAN", "Kisan Credit Card"),
             ("PM Fasal Bima Yojana", "PM Suraksha Bima Yojana"),
             ("Atal Pension Yojana", "PM Jeevan Jyoti Bima Yojana"),
             ("MUDRA", "Stand-Up India")]
    cmp_ok = cmp_tot = 0
    t0 = time.perf_counter()
    for lang in langs:
        for a, b in pairs:
            r = compare_schemes(a, b, lang)
            cmp_tot += 1
            cmp_ok += 1 if (r.get("comparisons") and len(r["comparisons"]) >= 6) else 0
    lat["compare"] = (time.perf_counter() - t0) / max(cmp_tot, 1)
    report["compare_coverage_pct"] = _pct(cmp_ok, cmp_tot)

    conf = {"High": 0, "Medium": 0, "Low": 0}
    grounded = 0
    faiths = []
    t0 = time.perf_counter()
    for q in _CHAT_Q:
        r = chat_with_ai(q, language="en", profile={"occupation": "farmer", "age": 35})
        conf[r.get("confidence", "Low")] = conf.get(r.get("confidence", "Low"), 0) + 1
        grounded += 1 if r.get("grounded") else 0
        if isinstance(r.get("faithfulness"), (int, float)):
            faiths.append(r["faithfulness"])
    lat["chat"] = (time.perf_counter() - t0) / len(_CHAT_Q)
    report["chat"] = {"n_questions": len(_CHAT_Q),
                      "grounding_rate_pct": _pct(grounded, len(_CHAT_Q)),
                      "confidence_distribution": conf,
                      "mean_faithfulness": round(sum(faiths) / len(faiths), 3) if faiths else None}

    baseline = {"llm_available": False}
    if config.llm_configured():
        probe = _ungrounded("Reply with OK.", "en")
        if probe is not None:
            g_faith, u_faith = [], []
            g_hall = u_hall = 0
            g_lang, u_lang = [], []
            n = 0
            for q, slug in _BASELINE:
                sch = kb_service.match(slug)
                ctx = sch.raw if sch else ""
                g = chat_with_ai(q, language="en").get("reply", "")
                gf, gg, _ = faithfulness.score(g, ctx)
                g_faith.append(gf); g_hall += 0 if gg else 1
                u = _ungrounded(q, "en") or ""
                uf, ug, _ = faithfulness.score(u, ctx)
                u_faith.append(uf); u_hall += 0 if ug else 1
                gh = chat_with_ai(q, language="hi").get("reply", "")
                uh = _ungrounded(q, "hi") or ""
                g_lang.append(_script_ratio(gh, "hi"))
                u_lang.append(_script_ratio(uh, "hi"))
                n += 1
            baseline = {
                "llm_available": True, "n_questions": n,
                "grounded": {"mean_faithfulness": round(sum(g_faith) / n, 3),
                             "hallucination_rate_pct": _pct(g_hall, n),
                             "hindi_script_correctness_pct": round(100 * sum(1 for r in g_lang if r >= 0.6) / n, 1)},
                "ungrounded": {"mean_faithfulness": round(sum(u_faith) / n, 3),
                               "hallucination_rate_pct": _pct(u_hall, n),
                               "hindi_script_correctness_pct": round(100 * sum(1 for r in u_lang if r >= 0.6) / n, 1)},
            }
    report["grounded_vs_ungrounded"] = baseline
    report["latency_ms"] = {k: round(v * 1000, 1) for k, v in lat.items()}

    os.makedirs("results", exist_ok=True)
    with open("results/eval_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    m = report["model_under_test"]
    print("\n" + "=" * 64)
    print("  JanNiti - Evaluation Report")
    print(f"  Model under test: {m['provider']} / {m['model']}")
    print("=" * 64)
    print("[A] SYSTEM METRICS (offline, KB-grounded)")
    print(f"  Schemes evaluated:            {report['n_schemes']}")
    print(f"  Explainer completeness:       {report['explainer_completeness_pct']}%")
    print(f"  Simple-Story coverage:        {report['simple_story_coverage_pct']}%")
    print(f"  Hidden-Conditions coverage:   {report['hidden_conditions_coverage_pct']}%")
    print(f"  Compare coverage (langs):     {report['compare_coverage_pct']}%")
    print(f"  Retrieval accuracy:           {report['retrieval_accuracy_pct']}%  ({report['retrieval_probes']} probes)")
    for lang, st in report["language_correctness"].items():
        print(f"  Language correctness {LANG_NAME[lang]:8s}: {st['correct_script_pct']}%  (ratio {st['mean_script_ratio']})")
    ch = report["chat"]
    print(f"  Chat grounding rate:          {ch['grounding_rate_pct']}%")
    print(f"  Chat mean faithfulness:       {ch['mean_faithfulness']}")
    print("-" * 64)
    b = report["grounded_vs_ungrounded"]
    print("[B] GROUNDED vs UNGROUNDED (same model, same metric)")
    if not b.get("llm_available"):
        print("  Skipped - no reachable LLM. Add a valid key and re-run to fill")
        print("  this table (this is the head-to-head your paper needs).")
    else:
        g, u = b["grounded"], b["ungrounded"]
        print(f"  {'metric':30s} {'grounded':>10s} {'ungrounded':>12s}")
        print(f"  {'mean faithfulness':30s} {g['mean_faithfulness']:>10} {u['mean_faithfulness']:>12}")
        print(f"  {'hallucination rate %':30s} {g['hallucination_rate_pct']:>10} {u['hallucination_rate_pct']:>12}")
        print(f"  {'Hindi script correct %':30s} {g['hindi_script_correctness_pct']:>10} {u['hindi_script_correctness_pct']:>12}")
    print("-" * 64)
    print("Mean latency per call (ms):")
    for k, v in report["latency_ms"].items():
        print(f"  {k:20s}: {v} ms")
    print("=" * 64)
    print("Saved -> results/eval_report.json\n")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", nargs="+", default=LANGS, choices=LANGS)
    args = ap.parse_args()
    run(args.langs)
