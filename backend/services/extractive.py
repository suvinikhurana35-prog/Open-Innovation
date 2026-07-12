"""
Extractive fallback — build a real, useful answer straight from the retrieved
official scheme text, WITHOUT needing the LLM.

This is what makes the app work even when OpenAI is out of credit or slow:
instead of showing "Official records not found", we surface the actual indexed
PDF content (benefits, eligibility, documents, how-to-apply) pulled from the
retrieved chunks. When the LLM *is* available it still takes over and writes a
polished, translated answer; this is the graceful floor beneath it.
"""
import re
from typing import List, Optional

_SENT = re.compile(r"(?<=[.!?])\s+|\n+")

CUES = {
    "benefits": ["benefit", "assistance", "amount", "provides", "provided", "support",
                 "pension", "insurance", "cover", "coverage", "installment", "instalment",
                 "subsidy", "grant", "scholarship", "rs.", "rs ", "₹", "rupees", "per year",
                 "per month", "financial"],
    "eligibility": ["eligib", "applicant", "must be", "should be", "age ", "income",
                    "farmer", "resident", "citizen", "criteria", "qualify", "beneficiary",
                    "below poverty", "bpl", "category", "years of age"],
    "documents": ["document", "aadhaar", "aadhar", "ration card", "certificate", "proof",
                  "bank account", "passbook", "photograph", "id card", "identity"],
    "apply": ["apply", "application", "portal", "register", "registration", "online",
              "csc", "common service", "website", "form", "submit"],
    "clauses": ["exclud", "not eligible", "penal", "terminat", "premium", "repay",
                "recover", "disqualif", "lapse", "forfeit", "discontinu", "deduct"],
}


def _sentences(text: str) -> List[str]:
    out = []
    for s in _SENT.split(text or ""):
        s = re.sub(r"\s+", " ", s).strip()
        if 25 <= len(s) <= 320:
            out.append(s)
    return out


def _pick(sents: List[str], key: str, limit: int = 5) -> List[str]:
    cues = CUES[key]
    hits, seen = [], set()
    for s in sents:
        low = s.lower()
        if any(c in low for c in cues):
            k = low[:60]
            if k not in seen:
                seen.add(k)
                hits.append(s)
        if len(hits) >= limit:
            break
    return hits


def _scheme_name(rag_results: List[dict], query: str) -> str:
    for r in rag_results:
        name = (r.get("metadata") or {}).get("name")
        if name:
            return name
    return query.strip().title()


def build_explainer(query: str, rag_results: List[dict], language: str = "en") -> dict:
    """Return a dict matching ExplainerResponse, filled from retrieved text."""
    context = "\n".join(r.get("text", "") for r in rag_results)
    sents = _sentences(context)
    name = _scheme_name(rag_results, query)

    what_is = " ".join(sents[:2]) if sents else \
        f"Details for '{name}' were retrieved from the official document set."
    benefits = _pick(sents, "benefits")
    eligibility = _pick(sents, "eligibility")
    documents = _pick(sents, "documents", limit=6)
    apply_lines = _pick(sents, "apply", limit=3)
    clauses = _pick(sents, "clauses", limit=4)

    note = ("Shown directly from the official scheme document. For a simplified, "
            "translated summary, connect the AI model (add OpenAI billing).")
    if language and language != "en":
        note = ("नीचे आधिकारिक योजना दस्तावेज़ से लिया गया मूल पाठ है। सरल/अनुवादित "
                "सारांश के लिए AI मॉडल जोड़ें।" if language == "hi" else note)

    return {
        "title": name,
        "what_is": what_is,
        "why_introduced": "See the official document for the scheme's objective.",
        "benefits": benefits,
        "eligibility": eligibility,
        "documents": documents,
        "how_to_apply": " ".join(apply_lines) if apply_lines
                        else "Apply via the official portal (myscheme.gov.in) or your nearest CSC.",
        "deadlines": None,
        "misunderstood_clauses": clauses,
        "source": name,
        "ministry": "See official document",
        "last_updated": "From indexed document",
        "confidence": "Medium" if rag_results else "Low",
        "disclaimer": note,
    }


def build_chat_reply(message: str, rag_results: List[dict]) -> str:
    if not rag_results:
        return ("I couldn't find this in the loaded scheme documents. Try a scheme name "
                "like 'PM Kisan', 'Ayushman Bharat', or 'Atal Pension Yojana'.")
    name = _scheme_name(rag_results, message)
    sents = _sentences("\n".join(r.get("text", "") for r in rag_results))
    body = " ".join(sents[:4]) if sents else rag_results[0].get("text", "")[:500]
    return f"From the official document for {name}:\n\n{body}\n\n[Source: {name}]"


def build_conditions(rag_results: List[dict]) -> dict:
    sents = _sentences("\n".join(r.get("text", "") for r in rag_results))
    conditions = []
    for s in _pick(sents, "clauses", limit=6):
        low = s.lower()
        severity = "red" if any(w in low for w in
                   ["not eligible", "penal", "terminat", "disqualif", "forfeit", "repay", "recover"]) \
                   else "yellow"
        conditions.append({"text": s, "severity": severity,
                           "explanation": "Flagged from the scheme text — read this carefully before applying."})
    summary = (f"{len(conditions)} clause(s) worth noting were found in the official text."
               if conditions else "No high-risk clauses were detected in the retrieved text.")
    return {"conditions": conditions, "summary": summary}
