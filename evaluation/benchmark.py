"""
Deterministic benchmark generator for JanNiti.

Builds a query set directly from the curated knowledge base (backend/data/kb/*.md)
via the PRODUCTION kb_service parser, so every query is traceable to a real
bullet/section and no questions are invented. Output is byte-stable across runs
(no randomness, no network, no LLM).

  python benchmark.py --verify   # corpus integrity check (writes nothing)
  python benchmark.py            # generate datasets/benchmark.json + summary + figure
"""
import re
import sys
import argparse
from collections import Counter

from utils import DATASETS, OUTPUTS, FIGURES, ensure_dirs, write_json, write_csv
from services import kb_service

# Sections every curated scheme must define (integrity check).
REQUIRED = ["Benefits", "Eligibility", "Required Documents", "How to Apply"]

# Map a curated kb/ section to (intent, gold section-name as stored in the
# ChromaDB metadata's `section` field of the structured MD layer).
INTENT_OF = {
    "benefits": ("benefits", "Key Benefits"),
    "eligibility": ("eligibility", "Eligibility Criteria"),
    "required documents": ("documents", "Required Documents"),
    "how to apply": ("application", "Application Process"),
    "important dates": ("dates", "Application Deadline"),
    "hidden conditions & rules": ("conditions", "Hidden Conditions"),
    "exclusions": ("conditions", "Who Should Not Apply"),
}


def normalize(name):
    """Drop a trailing parenthetical and lowercase, so
    'Hidden Conditions & Rules (Continuation Conditions)' == 'hidden conditions & rules'."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip().lower()


def _first_currency(bullets):
    for b in bullets:
        if re.search(r"(rs\.?|₹)\s*[\d,]+", b, re.I):
            return b
    return None


def build():
    schemes = kb_service.all_schemes()
    rows = []
    for s in schemes:
        title = s.title
        secmap = {normalize(k): (k, v) for k, v in s.sections.items()}

        def q(section_key, intent, gold_section, query, span):
            rows.append({
                "id": f"{s.slug}-{intent}-{len([r for r in rows if r['scheme']==s.slug and r['intent']==intent])+1}",
                "scheme": s.slug,
                "section": intent,
                "query": query,
                "language": "en",
                "expected_schemes": [title],
                "expected_section": gold_section,
                "expected_answer_span": span,
                "intent": intent,
            })

        # benefits
        if "benefits" in secmap:
            b = kb_service._bullets(secmap["benefits"][1])
            if b:
                q("benefits", "benefits", "Key Benefits",
                  f"What benefits does {title} provide?", b[0])
                cur = _first_currency(b)
                if cur:
                    q("benefits", "benefits", "Key Benefits",
                      f"How much financial benefit does {title} give?", cur)
        # eligibility
        if "eligibility" in secmap:
            e = kb_service._bullets(secmap["eligibility"][1])
            if e:
                q("eligibility", "eligibility", "Eligibility Criteria",
                  f"Who is eligible for {title}?", e[0])
                agey = next((x for x in e if re.search(r"\bage\b|\byears?\b", x, re.I)), None)
                if agey:
                    q("eligibility", "eligibility", "Eligibility Criteria",
                      f"What is the age requirement for {title}?", agey)
        # documents
        if "required documents" in secmap:
            d = kb_service._bullets(secmap["required documents"][1])
            if d:
                q("documents", "documents", "Required Documents",
                  f"What documents are required for {title}?", d[0])
        # application
        if "how to apply" in secmap:
            a = kb_service._bullets(secmap["how to apply"][1]) or [secmap["how to apply"][1].strip()]
            if a and a[0]:
                q("application", "application", "Application Process",
                  f"How do I apply for {title}?", a[0][:200])
        # dates
        if "important dates" in secmap:
            dt = kb_service._bullets(secmap["important dates"][1]) or [secmap["important dates"][1].strip()]
            if dt and dt[0]:
                q("dates", "dates", "Application Deadline",
                  f"What are the important dates or deadlines for {title}?", dt[0][:200])
        # conditions (hidden rules + exclusions)
        for secname in ("hidden conditions & rules", "exclusions"):
            if secname in secmap:
                intent, gold = INTENT_OF[secname]
                c = kb_service._bullets(secmap[secname][1])
                for clause in c[:1]:
                    q(secname, "conditions", gold,
                      f"Are there any hidden conditions or exclusions in {title}?", clause)
        # implicit (no scheme name -> must resolve via vector retrieval)
        benef = kb_service._bullets(secmap.get("benefits", ("", ""))[1]) if "benefits" in secmap else []
        elig = kb_service._bullets(secmap.get("eligibility", ("", ""))[1]) if "eligibility" in secmap else []
        if benef:
            q("benefits", "implicit", "Key Benefits",
              _implicit_from(benef[0]), benef[0])
        if elig:
            q("eligibility", "implicit", "Eligibility Criteria",
              _implicit_from(elig[0]), elig[0])

    # comparison pairs (tag-overlap nearest neighbour, joined on normalized title)
    rows += _comparison_rows(schemes)
    return rows


def _implicit_from(bullet):
    """Turn an answer bullet into a natural need-based query with no scheme name."""
    b = bullet.lower()
    if "pension" in b:
        return "I want a guaranteed monthly pension after I turn 60."
    if "insurance" in b or "cover" in b or "bima" in b:
        return "I need low-cost insurance cover for my family."
    if "loan" in b or "credit" in b:
        return "I need a small loan to start or run my business."
    if "scholarship" in b or "student" in b or "study" in b:
        return "I am a student looking for financial help to continue studies."
    if "bank account" in b or "account" in b:
        return "I want to open a bank account with no minimum balance."
    if "crop" in b or "farmer" in b or "farming" in b:
        return "I am a farmer and need government financial support."
    if "ration" in b or "food" in b or "grain" in b:
        return "I need free or subsidised food grains for my family."
    return "Which government scheme can help someone in my situation?"


def _comparison_rows(schemes):
    by_title = {normalize(s.title): s for s in schemes}
    tagset = {}
    for s in schemes:
        text = " ".join(s.sections.values()).lower()
        tagset[s.slug] = set(re.findall(r"[a-z]{4,}", text))
    pairs, used = [], set()
    slugs = [s.slug for s in schemes]
    for a in slugs:
        if a in used:
            continue
        best, bj = None, -1
        for b in slugs:
            if b == a or b in used:
                continue
            j = len(tagset[a] & tagset[b])
            if j > bj:
                best, bj = b, j
        if best:
            used.add(a); used.add(best)
            sa = next(s for s in schemes if s.slug == a)
            sb = next(s for s in schemes if s.slug == best)
            pairs.append((sa, sb))
    rows = []
    for sa, sb in pairs:
        rows.append({
            "id": f"{sa.slug}-comparison-1",
            "scheme": sa.slug,
            "section": "comparison",
            "query": f"Compare {sa.title} and {sb.title}.",
            "language": "en",
            "expected_schemes": [sa.title, sb.title],
            "expected_section": "Scheme Comparison Metadata",
            "expected_answer_span": f"{sa.title} vs {sb.title}",
            "intent": "comparison",
        })
    return rows


def verify():
    schemes = kb_service.all_schemes()
    print(f"[INFO] Curated knowledge base: {len(schemes)} schemes")
    ok = 0
    for s in schemes:
        have = {normalize(k) for k in s.sections}
        missing = [r for r in REQUIRED if normalize(r) not in have]
        usable = [k for k in s.sections if normalize(k) in INTENT_OF]
        flag = "OK" if not missing else "MISSING " + ",".join(missing)
        print(f"  {s.slug:26s} sections={len(s.sections):2d} usable={len(usable)}  {flag}")
        if not missing:
            ok += 1
    print(f"[INFO] Schemes with all required sections: {ok}/{len(schemes)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        verify()
        return
    ensure_dirs()
    print("[INFO] Building benchmark from the curated knowledge base...")
    rows = build()
    assert len({r["id"] for r in rows}) == len(rows), "duplicate ids"
    assert all(r["expected_answer_span"] for r in rows), "empty answer span"
    write_json(f"{DATASETS}/benchmark.json", rows)
    print(f"[INFO] Wrote {len(rows)} queries to datasets/benchmark.json")

    # summary CSV: Scheme, Intent, Question Count, Section Count
    by_scheme = Counter(r["scheme"] for r in rows)
    sec_count = {s.slug: len(s.sections) for s in kb_service.all_schemes()}
    summary = []
    for (scheme, intent), c in sorted(Counter((r["scheme"], r["intent"]) for r in rows).items()):
        summary.append({"Scheme": scheme, "Intent": intent,
                        "Question Count": c, "Section Count": sec_count.get(scheme, 0)})
    write_csv(f"{OUTPUTS}/benchmark_summary.csv", summary)
    print(f"[INFO] Wrote {len(summary)} rows to outputs/benchmark_summary.csv")

    _plot_distribution(rows)
    print("[INFO] Queries per intent:")
    for intent, c in sorted(Counter(r["intent"] for r in rows).items(), key=lambda x: -x[1]):
        print(f"  {intent:12s} {c}")
    print(f"[INFO] Total {len(rows)} queries across {len(by_scheme)} schemes")


def _plot_distribution(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from collections import Counter as C
    counts = C(r["intent"] for r in rows)
    items = sorted(counts.items(), key=lambda x: -x[1])
    labels = [k for k, _ in items]
    vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ax.bar(labels, vals, color="#4C72B0", edgecolor="black", linewidth=0.6)
    ax.set_ylabel("Number of queries")
    ax.set_title("Benchmark query distribution by intent")
    ax.tick_params(axis="x", rotation=30)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.3, str(v), ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{FIGURES}/benchmark_distribution.png", dpi=300)
    fig.savefig(f"{FIGURES}/benchmark_distribution.pdf")
    plt.close(fig)
    print("[INFO] Figure saved: figures/benchmark_distribution.{png,pdf}")


if __name__ == "__main__":
    main()
