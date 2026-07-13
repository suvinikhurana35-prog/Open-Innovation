"""
Grounding evaluation: faithfulness, hallucination rate, grounded %, unsupported %.

Compares JanNiti's grounded answers against an ungrounded baseline (the same
model with no retrieval) using the production inference-time faithfulness scorer.
The grounded answer's context is the curated scheme document; the ungrounded
answer is scored against the same context, so any content not supported by the
official text counts as unsupported.

  python grounding_eval.py
The ungrounded arm needs a working LLM key; if none is reachable it is skipped
and only the grounded arm is reported.
"""
import sys
from collections import defaultdict

from utils import DATASETS, OUTPUTS, ensure_dirs, read_json, write_csv
import metrics
from services import ai_service, kb_service, faithfulness
from services.llm import llm_chat, LLM_UNAVAILABLE
import config

FAITH_THRESHOLD = 0.45  # matches the production scorer's support threshold


def _ungrounded(question):
    sysmsg = ("You are a helpful assistant. Answer the question about the Indian "
              "government scheme concisely and factually.")
    r = llm_chat(messages=[{"role": "system", "content": sysmsg},
                           {"role": "user", "content": question}])
    return None if r == LLM_UNAVAILABLE else r


def evaluate():
    ensure_dirs()
    bench = read_json(f"{DATASETS}/benchmark.json")
    # use scheme-fact questions (skip comparison/implicit for a clean single-scheme context)
    qs = [q for q in bench if q["intent"] in ("benefits", "eligibility", "documents",
                                              "application", "dates", "conditions")]
    print(f"[INFO] Grounding evaluation over {len(qs)} scheme-fact questions.")

    llm_up = False
    if config.llm_configured() and _ungrounded("Reply OK.") is not None:
        llm_up = True
    print(f"[INFO] Ungrounded baseline available: {llm_up}")

    rows = []
    for q in qs:
        sch = kb_service.match(q["query"])
        if sch is None:
            continue
        ctx = sch.raw
        grounded = ai_service.chat_with_ai(q["query"], language="en").get("reply", "")
        gf, gok, guns = faithfulness.score(grounded, ctx)
        row = {"id": q["id"], "intent": q["intent"],
               "grounded_faithfulness": round(gf, 4),
               "grounded_supported": int(gok),
               "grounded_unsupported_sents": len(guns)}
        if llm_up:
            ung = _ungrounded(q["query"]) or ""
            uf, uok, uuns = faithfulness.score(ung, ctx)
            row.update({"ungrounded_faithfulness": round(uf, 4),
                        "ungrounded_supported": int(uok),
                        "ungrounded_unsupported_sents": len(uuns)})
        rows.append(row)

    write_csv(f"{OUTPUTS}/grounding_results.csv", rows)

    def agg(prefix):
        f = [r[f"{prefix}_faithfulness"] for r in rows if f"{prefix}_faithfulness" in r]
        sup = [r[f"{prefix}_supported"] for r in rows if f"{prefix}_supported" in r]
        if not f:
            return None
        return {
            "mean_faithfulness": round(sum(f) / len(f), 4),
            "grounded_pct": round(100 * sum(sup) / len(sup), 2),
            "hallucination_rate_pct": round(100 * (1 - sum(sup) / len(sup)), 2),
        }

    g = agg("grounded")
    u = agg("ungrounded")
    metric_rows = [{"system": "JanNiti (grounded)", **g}]
    if u:
        metric_rows.append({"system": "Ungrounded LLM", **u})
    write_csv(f"{OUTPUTS}/grounding_metrics.csv", metric_rows)

    print("\n[RESULT] Grounding:")
    print(f"  {'system':22s} {'faithfulness':>13s} {'grounded%':>10s} {'halluc.%':>9s}")
    for r in metric_rows:
        print(f"  {r['system']:22s} {r['mean_faithfulness']:13.3f} "
              f"{r['grounded_pct']:10.1f} {r['hallucination_rate_pct']:9.1f}")
    print("[INFO] Grounding evaluation done.")


if __name__ == "__main__":
    evaluate()
