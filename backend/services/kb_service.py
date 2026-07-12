"""
Structured Knowledge Base (KB) service — JanNiti v2.0.

Loads the curated per-scheme markdown files in backend/data/kb/ (built from
the official scheme PDFs stored in backend/data/chroma/policies/) and matches
user queries to a scheme. When a scheme matches, the AI layer uses the FULL
curated document as context instead of noisy RAG chunks, which eliminates:
  * "not available in the loaded records" for benefits/documents/eligibility
  * half-sentence bullets caused by chunk boundaries
  * cross-scheme content leaking into an answer

Chroma/RAG remains the fallback for free-form questions that don't map to a
single scheme. No re-ingestion is needed — the KB is read straight from disk
(cached in memory) at first use.
"""
import logging
import os
import re
from typing import Dict, List, Optional

logger = logging.getLogger("janniti.kb")

_KB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "kb")

_STOPWORDS = {
    "the", "a", "an", "of", "for", "and", "in", "to", "is", "what", "scheme",
    "yojana", "yojna", "pradhan", "mantri", "pm", "about", "tell", "me",
}


class Scheme:
    def __init__(self, slug: str, title: str, meta: Dict[str, str],
                 sections: Dict[str, str], raw: str):
        self.slug = slug
        self.title = title
        self.meta = meta                # ministry, apply, official, mode, aliases
        self.sections = sections        # heading -> body text
        self.raw = raw                  # full markdown (clean context for the LLM)
        self.aliases = [a.strip().lower() for a in meta.get("aliases", "").split("|") if a.strip()]
        # tokens from the title for fuzzy scoring
        self.tokens = {t for t in re.split(r"[^a-z0-9]+", title.lower()) if t and t not in _STOPWORDS}


_cache: Optional[List[Scheme]] = None


def _parse(path: str) -> Optional[Scheme]:
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        logger.error("KB read failed %s: %s", path, e)
        return None

    title_m = re.search(r"^#\s+(.+)$", raw, re.M)
    title = title_m.group(1).strip() if title_m else os.path.basename(path)

    meta: Dict[str, str] = {}
    for key in ("ministry", "apply", "official", "mode", "aliases"):
        m = re.search(rf"^{key}:\s*(.+)$", raw, re.M)
        if m:
            meta[key] = m.group(1).strip()

    sections: Dict[str, str] = {}
    parts = re.split(r"^##\s+(.+)$", raw, flags=re.M)
    # parts = [preamble, H2-title, body, H2-title, body, ...]
    for i in range(1, len(parts) - 1, 2):
        sections[parts[i].strip()] = parts[i + 1].strip()

    return Scheme(os.path.splitext(os.path.basename(path))[0], title, meta, sections, raw)


def _load() -> List[Scheme]:
    global _cache
    if _cache is not None:
        return _cache
    schemes: List[Scheme] = []
    if os.path.isdir(_KB_DIR):
        for name in sorted(os.listdir(_KB_DIR)):
            if name.endswith(".md"):
                s = _parse(os.path.join(_KB_DIR, name))
                if s:
                    schemes.append(s)
    else:
        logger.warning("KB directory not found: %s", _KB_DIR)
    _cache = schemes
    logger.info("Structured KB loaded: %d schemes", len(schemes))
    return schemes


def all_schemes() -> List[Scheme]:
    return _load()


def match(query: str) -> Optional[Scheme]:
    """Match a query to a scheme. Alias substring match wins outright;
    otherwise score by title-token overlap and require a solid majority."""
    q = (query or "").lower().strip()
    if not q:
        return None
    schemes = _load()

    # 1) exact/substring alias match (longest alias first = most specific)
    best_alias, best_scheme = "", None
    for s in schemes:
        for a in s.aliases + [s.title.lower()]:
            if a and a in q and len(a) > len(best_alias):
                best_alias, best_scheme = a, s
    if best_scheme:
        return best_scheme

    # 2) token-overlap score
    q_tokens = {t for t in re.split(r"[^a-z0-9]+", q) if t and t not in _STOPWORDS}
    if not q_tokens:
        return None
    scored = []
    for s in schemes:
        inter = len(q_tokens & s.tokens)
        if inter:
            scored.append((inter / max(1, len(s.tokens)), inter, s))
    if not scored:
        return None
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    ratio, inter, s = scored[0]
    if inter >= 2 or ratio >= 0.6:
        return s
    return None


def context_for(query: str) -> Optional[str]:
    """Full clean markdown context for a matched scheme, or None."""
    s = match(query)
    return s.raw if s else None


# --- Translated markdown layer -------------------------------------------
# Pre-built translated scheme files live in data/kb_<lang>/<slug>.md (e.g.
# data/kb_or/pm-kisan.md for Odia). If present, the app reads them straight
# from disk — instant, no AI call, ships in the zip. Built once by
# scripts/build_translated_kb.py.

_DATA_DIR = os.path.dirname(_KB_DIR)
_lang_cache = {}  # (slug, lang) -> Scheme  (parsed translated file)


def _translated_dir(lang: str) -> str:
    return os.path.join(_DATA_DIR, f"kb_{lang}")


def translated_scheme(slug: str, lang: str):
    """Return a parsed Scheme from the translated .md file for this slug+lang,
    or None if that file doesn't exist. Cached in memory."""
    if not lang or lang == "en":
        return None
    key = (slug, lang)
    if key in _lang_cache:
        return _lang_cache[key]
    path = os.path.join(_translated_dir(lang), f"{slug}.md")
    scheme = _parse(path) if os.path.exists(path) else None
    _lang_cache[key] = scheme
    return scheme


def match_localized(query: str, lang: str = "en"):
    """Match a scheme, returning the TRANSLATED version if a pre-built file
    exists for this language, else the English one. Returns (scheme, is_translated)."""
    s = match(query)
    if s is None:
        return None, False
    if lang and lang != "en":
        t = translated_scheme(s.slug, lang)
        if t is not None:
            # keep the English slug/meta apply-links; use translated text
            t.slug = s.slug
            for k in ("apply", "official", "ministry", "mode"):
                if k not in t.meta and k in s.meta:
                    t.meta[k] = s.meta[k]
            return t, True
    return s, False


def scheme_names() -> List[str]:
    return [s.title for s in _load()]


# --- Grounded chatbot answer (point-to-point, no hallucination) ----------
_INTENTS = [
    ("eligibility", ("eligib", "qualify", "who can", "am i", "can i get", "eligible", "apply for it")),
    ("Required Documents", ("document", "paper", "proof", "kyc", "certificate", "id ")),
    ("How to Apply", ("how to apply", "apply", "register", "process", "where to", "link", "portal", "website")),
    ("Benefits", ("benefit", "amount", "money", "how much", "get", "subsidy", "pension", "loan", "cover")),
    ("Important Dates", ("date", "deadline", "last date", "when", "renew")),
    ("Hidden Conditions & Rules", ("condition", "rule", "catch", "exclusion", "penalty", "hidden")),
]


def chat_lines(query: str, lang: str = "en"):
    """Return (scheme_title, lines[], is_translated) — a short, point-to-point
    answer built ONLY from the matched scheme's KB record, so it cannot
    hallucinate. Uses the pre-built translated .md file when one exists for the
    language (instant, no AI). Returns (None, None, False) if no scheme matches."""
    s = match(query)
    if s is None:
        return None, None, False
    is_translated = False
    if lang and lang != "en":
        t = translated_scheme(s.slug, lang)
        if t is not None:
            for k in ("apply", "official"):
                if k not in t.meta and k in s.meta:
                    t.meta[k] = s.meta[k]
            s = t
            is_translated = True
    q = (query or "").lower()

    def bullets(section: str, limit: int = 6):
        return _bullets(s.sections.get(section, ""))[:limit]

    # pick the section the user asked about
    chosen = None
    for section, kws in _INTENTS:
        if any(k in q for k in kws):
            chosen = section
            break

    lines: List[str] = []
    if chosen == "eligibility":
        lines.append("Who is eligible:")
        lines += [f"- {b}" for b in bullets("Eligibility")]
    elif chosen == "Required Documents":
        lines.append("Documents you need:")
        lines += [f"- {b}" for b in bullets("Required Documents")]
    elif chosen == "How to Apply":
        how = " ".join(l.strip() for l in s.sections.get("How to Apply", "").splitlines() if l.strip())
        lines.append("How to apply:")
        if how:
            lines.append(how[:400])
        if s.meta.get("apply"):
            lines.append(f"Apply here: {s.meta['apply']}")
    elif chosen == "Benefits":
        lines.append("What you get:")
        lines += [f"- {b}" for b in bullets("Benefits")]
    elif chosen == "Important Dates":
        dt = " ".join(l.strip() for l in s.sections.get("Important Dates", "").splitlines() if l.strip())
        lines.append("Important dates:")
        lines.append(dt[:300] if dt else "- No fixed deadline is listed; check the official portal.")
    elif chosen == "Hidden Conditions & Rules":
        lines.append("Rules to watch out for:")
        lines += [f"- {b}" for b in bullets("Hidden Conditions & Rules")]
    else:
        # general summary
        whatis = " ".join(l.strip() for l in s.sections.get("What is this scheme", "").splitlines() if l.strip())
        if whatis:
            lines.append(whatis[:300])
        top = bullets("Benefits", 3)
        if top:
            lines.append("Key benefits:")
            lines += [f"- {b}" for b in top]
        if s.meta.get("apply"):
            lines.append(f"Apply here: {s.meta['apply']}")

    lines.append("Please confirm on the official portal before applying.")
    return s.title, lines, is_translated


# --- Instant explainer support -------------------------------------------
# Parse a curated KB record straight into the explainer's fields, so English
# answers can be served WITHOUT any LLM call (sub-second). Non-English still
# goes through the LLM for translation.

def _bullets(body: str) -> List[str]:
    """Top-level '- ' bullets from a section body, ignoring sub-bullets and
    stripping the [green]/[yellow]/[red] severity tags."""
    out = []
    for line in body.splitlines():
        s = line.rstrip()
        if s.startswith("- "):
            text = s[2:].strip()
            text = re.sub(r"\s*\[(green|yellow|red)\]\s*$", "", text)
            if text:
                out.append(text)
    return out


def explainer_dict(scheme: "Scheme") -> dict:
    """Build the ExplainerResponse shape directly from the KB (no LLM)."""
    sec = scheme.sections
    docs = _bullets(sec.get("Required Documents", ""))
    docs.append(
        "Note: This list is from official records — your bank, portal, or state "
        "government may ask for extra documents, so confirm on the official portal before applying."
    )

    def para(name: str) -> str:
        lines = []
        for l in sec.get(name, "").splitlines():
            t = l.strip()
            if not t:
                continue
            t = re.sub(r"^[-*]\s+", "", t)   # drop bullet markers
            lines.append(t)
        return " ".join(lines)

    clauses = []
    for name in ("Hidden Conditions & Rules", "Exclusions"):
        clauses.extend(_bullets(sec.get(name, "")))

    return {
        "title": scheme.title,
        "what_is": para("What is this scheme") or para("What is this scheme?"),
        "why_introduced": para("Why it was introduced"),
        "benefits": _bullets(sec.get("Benefits", "")),
        "eligibility": _bullets(sec.get("Eligibility", "")),
        "documents": docs,
        "how_to_apply": para("How to Apply"),
        "deadlines": para("Important Dates") or None,
        "misunderstood_clauses": clauses,
        "source": scheme.meta.get("official", scheme.title),
        "ministry": scheme.meta.get("ministry", "Government of India"),
        "last_updated": "Official records",
        "confidence": "High",
        "disclaimer": "This is AI-generated guidance based on publicly available "
                      "information. Please verify with official government sources before applying.",
    }
