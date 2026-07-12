"""
Upgrade the knowledge base into RAG-optimized structured Markdown.

Input : data/knowledge_base/*.txt  (already OCR'd, clean, deduped)
Output: data/knowledge_base_md/<slug>.md  with:
  - YAML frontmatter (scheme_name, type, beneficiary, tags, keywords, source, ...)
  - hierarchical sections (## Overview / Benefits / Eligibility / Documents /
    Application Process / Important Dates / Generated FAQs / Full Official Text)
  - generated FAQs
  - source citation line

Sections are heuristic (keyword-routed) but ALWAYS include the complete official
text under "## Full Official Text", so nothing is ever lost — the structured
sections improve retrieval precision while the full text guarantees recall.
"""
import os, re, json, glob

SRC = "knowledge_base"
OUT = "knowledge_base_md"

CUES = {
    "benefits": ["benefit", "assistance", "amount", "provides", "provided", "support",
                 "pension", "insurance", "cover", "installment", "instalment", "subsidy",
                 "grant", "scholarship", "rs.", "rs ", "₹", "rupees", "per year", "per month"],
    "eligibility": ["eligib", "applicant", "must be", "should be", "age ", "income",
                    "farmer", "resident", "citizen", "criteria", "qualify", "beneficiary",
                    "below poverty", "bpl", "years of age"],
    "documents": ["document", "aadhaar", "aadhar", "ration card", "certificate", "proof",
                  "bank account", "passbook", "photograph", "id card", "identity"],
    "apply": ["apply", "application", "portal", "register", "registration", "online",
              "csc", "common service", "website", "form", "submit"],
    "dates": ["last date", "deadline", "before", "valid till", "launched", "w.e.f",
              "financial year", "20"],
}
TAG_RULES = {
    "agriculture": ["farmer", "kisan", "crop", "agricultur", "fasal"],
    "women": ["women", "woman", "girl", "mahila", "widow"],
    "students": ["student", "scholarship", "education", "school", "merit"],
    "pension": ["pension", "old age", "retirement", "atal"],
    "health": ["health", "hospital", "medical", "ayushman", "insurance", "bima"],
    "employment": ["employment", "job", "rozgar", "skill", "loan", "startup", "business"],
    "housing": ["housing", "awas", "house", "shelter"],
    "financial-inclusion": ["jan dhan", "bank account", "savings", "suraksha"],
}


def sents(text):
    out = []
    for s in re.split(r"(?<=[.!?])\s+|\n+", text or ""):
        s = re.sub(r"\s+", " ", s).strip()
        if 20 <= len(s) <= 320:
            out.append(s)
    return out


def pick(ss, key, limit=6):
    cues, hits, seen = CUES[key], [], set()
    for s in ss:
        low = s.lower()
        if any(c in low for c in cues) and low[:50] not in seen:
            seen.add(low[:50]); hits.append(s)
        if len(hits) >= limit:
            break
    return hits


def tags_for(text):
    low = text.lower()
    return [t for t, kws in TAG_RULES.items() if any(k in low for k in kws)] or ["welfare"]


def keywords_for(name, text):
    base = [w for w in re.findall(r"[A-Za-z]{4,}", name)]
    common = re.findall(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})\b", text)
    freq = {}
    for c in common:
        freq[c] = freq.get(c, 0) + 1
    top = sorted(freq, key=freq.get, reverse=True)[:8]
    return list(dict.fromkeys(base + top))[:10]


def md_list(items):
    return "\n".join(f"- {i}" for i in items) if items else "_See full official text below._"


def build_md(name, slug, source_pdf, body):
    ss = sents(body)
    overview = " ".join(ss[:2]) if ss else name
    benefits = pick(ss, "benefits")
    elig = pick(ss, "eligibility")
    docs = pick(ss, "documents")
    apply_ = pick(ss, "apply", 4)
    dates = pick(ss, "dates", 3)
    tags = tags_for(body)
    kws = keywords_for(name, body)
    btype = "Central" if any(w in body.lower() for w in ["ministry", "government of india", "central"]) else "Scheme"

    faqs = [
        ("Who can apply / who is eligible?", " ".join(elig[:3]) or "See eligibility section."),
        ("What benefits does it provide?", " ".join(benefits[:3]) or "See benefits section."),
        ("How do I apply?", " ".join(apply_[:2]) or "Apply via the official portal or nearest CSC."),
        ("Which documents are required?", " ".join(docs[:3]) or "See documents section."),
    ]

    fm = {
        "scheme_name": name, "slug": slug, "scheme_type": btype,
        "beneficiary": ", ".join(tags), "tags": tags, "keywords": kws,
        "source_pdf": source_pdf, "last_updated": "from indexed document",
    }
    fm_yaml = "---\n" + "\n".join(
        f"{k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v}" for k, v in fm.items()
    ) + "\n---\n"

    faq_md = "\n".join(f"**Q: {q}**\n\n{a}\n" for q, a in faqs)

    return f"""{fm_yaml}
# {name}

## Overview
{overview}

## Key Benefits
{md_list(benefits)}

## Eligibility Criteria
{md_list(elig)}

## Required Documents
{md_list(docs)}

## Application Process
{md_list(apply_)}

## Important Dates
{md_list(dates)}

## Generated FAQs
{faq_md}

## Full Official Text
{body.strip()}

---
Source: {source_pdf}
""", {"scheme": name, "slug": slug, "tags": tags, "keywords": kws,
      "scheme_type": btype, "source_pdf": source_pdf,
      "faqs": [{"q": q, "a": a} for q, a in faqs]}


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = json.load(open(os.path.join(SRC, "manifest.json"), encoding="utf-8"))
    meta_all = []
    for m in manifest:
        raw = open(os.path.join(SRC, m["file"]), encoding="utf-8").read()
        body = re.split(r"={10,}", raw, 1)[-1].strip() if "=" * 10 in raw else raw
        md, meta = build_md(m["scheme"], m["slug"], m["source_pdf"], body)
        open(os.path.join(OUT, m["slug"] + ".md"), "w", encoding="utf-8").write(md)
        meta_all.append(meta)
        print(f"  {m['slug']}.md  tags={meta['tags']}")
    json.dump(meta_all, open(os.path.join(OUT, "metadata.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"\nStructured Markdown KB: {len(meta_all)} schemes -> {OUT}/")


if __name__ == "__main__":
    main()
