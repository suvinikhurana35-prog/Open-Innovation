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

from services import translation_cache, kb_i18n

logger = logging.getLogger("janniti.kb")

_KB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "kb")
_TRANS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "translations")

# Words that appear across MANY scheme names in each language -> not distinctive,
# so they must not be used to match a scheme (they'd cause false matches).
_NATIVE_STOP = {
    # Hindi
    "प्रधानमंत्री", "प्रधान", "मंत्री", "योजना", "राष्ट्रीय", "भारत", "के", "लिए", "और", "में",
    "छात्रवृत्ति", "बीमा", "ऋण", "कार्ड",
    # Bengali
    "প্রধানমন্ত্রী", "প্রধান", "মন্ত্রী", "যোজনা", "প্রকল্প", "জাতীয়", "ভারত", "বৃত্তি", "বিমা", "ঋণ",
    # Tamil
    "பிரதமர்", "திட்டம்", "தேசிய", "இந்திய", "உதவித்தொகை", "கடன்", "காப்பீடு",
    # Latin generics
    "yojana", "scheme", "pradhan", "mantri", "national", "the", "for", "of", "and",
    "bima", "loan", "card", "scholarship",
}

_NATIVE_INDEX = None  # native-script alias/token (lower) -> slug

# Curated native-script names for each scheme, covering how people actually type
# them in Hindi / Bengali / Tamil. Needed because some cached titles keep brand
# words in Latin (e.g. "MUDRA"), so the auto-index alone misses them. Phrases are
# matched as substrings, so multi-word entries stay distinctive.
_NATIVE_ALIASES_EXTRA = {
    "pm-kisan": ["किसान सम्मान", "সম্মান নিধি", "கிசான் சம்மான்", "किसान निधि"],
    "kisan-credit-card": ["किसान क्रेडिट", "क्रेडिट कार्ड", "কিসান ক্রেডিট", "கிசான் கிரெடிட்"],
    "fasal-bima": ["फसल बीमा", "ফসল বিমা", "பயிர் காப்பீடு", "फसल"],
    "atal-pension": ["अटल पेंशन", "অটল পেনশন", "அடல் ஓய்வூதியம்", "अटल"],
    "jeevan-jyoti-bima": ["जीवन ज्योति", "জীবন জ্যোতি", "ஜீவன் ஜோதி"],
    "suraksha-bima": ["सुरक्षा बीमा", "সুরক্ষা বিমা", "சுரக்ஷா காப்பீடு", "सुरक्षा बीमा योजना"],
    "jan-dhan": ["जन धन", "জন ধন", "ஜன் தன்", "जनधन", "জনধন"],
    "garib-kalyan-anna": ["गरीब कल्याण", "গরিব কল্যাণ", "கரீப் கல்யாண்"],
    "mudra": ["मुद्रा", "মুদ্রা", "முத்ரா", "मुद्रा लोन", "মুদ্রা লোন"],
    "stand-up-india": ["स्टैंड अप", "স্ট্যান্ড আপ", "ஸ்டாண்ட் அப்", "स्टैंड-अप"],
    "viksit-bharat-rozgar": ["विकसित भारत रोजगार", "বিকশিত ভারত", "விக்சித் பாரத்"],
    "kaushal-vikas": ["कौशल विकास", "কৌশল বিকাশ", "கௌஷல் விகாஸ்"],
    "skill-loan": ["स्किल लोन", "কৌশল ঋণ", "ஸ்கில் லோன்", "कौशल ऋण"],
    "cbse-single-girl-child": ["एकल बालिका", "একক বালিকা", "ஒற்றை பெண்", "सीबीएसई बालिका"],
    "pg-indira-gandhi-sgc": ["इंदिरा गांधी", "ইন্দিরা গান্ধী", "இந்திரா காந்தி"],
    "national-pg-scholarship": ["स्नातकोत्तर छात्रवृत्ति", "স্নাতকোত্তর বৃত্তি", "முதுகலை உதவித்தொகை"],
    "icar-national-talent": ["प्रतिभा छात्रवृत्ति", "ট্যালেন্ট বৃত্তি", "தேசிய திறமை"],
    "ugc-jrf-engineering": ["जूनियर रिसर्च", "জুনিয়র রিসার্চ", "ஜூனியர் ஆராய்ச்சி", "अनुसंधान फेलोशिप"],
}

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


def _by_slug(slug: str) -> Optional["Scheme"]:
    for s in _load():
        if s.slug == slug:
            return s
    return None


def _native_index() -> dict:
    """Build a native-script (Hindi/Bengali/Tamil) name -> slug index from the
    pre-translated scheme titles, so users can name a scheme in their own script
    (e.g. 'मुद्रा', 'মুদ্রা', 'முத்ரா') and still get a grounded answer instead of
    the not-found fallback. Only tokens UNIQUE to one scheme are used, so shared
    words like 'योजना'/'बीमा' never cause a wrong match."""
    global _NATIVE_INDEX
    if _NATIVE_INDEX is not None:
        return _NATIVE_INDEX
    import json
    idx, token_owners, phrases = {}, {}, {}
    for s in _load():
        for lang in ("hi", "bn", "ta"):
            p = os.path.join(_TRANS_DIR, f"{s.slug}__{lang}.json")
            if not os.path.exists(p):
                continue
            try:
                title = (json.load(open(p, encoding="utf-8")).get("title") or "")
            except Exception:
                continue
            title = re.sub(r"\(.*?\)", "", title).strip().lower()
            if not title:
                continue
            phrases[title] = s.slug  # full translated title (exact-phrase match)
            for tok in re.split(r"[^\w]+", title, flags=re.UNICODE):
                tok = tok.strip()
                if len(tok) < 2 or tok in _NATIVE_STOP or tok.isdigit():
                    continue
                token_owners.setdefault(tok, set()).add(s.slug)
    for tok, owners in token_owners.items():
        if len(owners) == 1:                 # unique token -> safe alias
            idx[tok] = next(iter(owners))
    idx.update(phrases)                       # full-title phrases too
    for slug, aliases in _NATIVE_ALIASES_EXTRA.items():   # curated brand names
        for a in aliases:
            a = a.strip().lower()
            if a:
                idx[a] = slug
    _NATIVE_INDEX = idx
    return idx


def match(query: str) -> Optional[Scheme]:
    """Match a query to a scheme. Alias substring match wins outright;
    otherwise score by title-token overlap and require a solid majority.
    Also recognises scheme names written in Hindi/Bengali/Tamil script."""
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

    # 1b) native-script name match (Hindi/Bengali/Tamil) -> longest wins
    best_n, best_ns = "", None
    for alias, slug in _native_index().items():
        if alias in q and len(alias) > len(best_n):
            best_n, best_ns = alias, slug
    if best_ns:
        return _by_slug(best_ns)

    # 1c) suffix-tolerant native match: Tamil/Bengali/Hindi attach grammatical
    # case endings straight onto a word (e.g. "ஓய்வூதியம்" -> "ஓய்வூதியத்தில்"
    # for "in the pension"), so a plain substring check above can miss a
    # scheme name that's clearly present except for its last 1-2 characters.
    # Try longer aliases first, truncated by 1 then 2 characters.
    best_f, best_fs = "", None
    for alias, slug in _native_index().items():
        if len(alias) < 6:
            continue
        for cut in (1, 2):
            stem = alias[:-cut]
            if len(stem) >= 4 and stem in q and len(alias) > len(best_f):
                best_f, best_fs = alias, slug
                break
    if best_fs:
        return _by_slug(best_fs)

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


def scheme_names(lang: str = "en") -> List[str]:
    """Scheme titles. For hi/bn/ta, use the pre-translated title from the cache
    so the chatbot's fallback list renders consistently in the selected
    language (not a mix of English and translated names)."""
    if not lang or lang == "en":
        return [s.title for s in _load()]
    import json
    out = []
    for s in _load():
        p = os.path.join(_TRANS_DIR, f"{s.slug}__{lang}.json")
        title = s.title
        if os.path.exists(p):
            try:
                title = json.load(open(p, encoding="utf-8")).get("title") or s.title
            except Exception:
                pass
        out.append(title)
    return out


# --- Grounded chatbot answer (point-to-point, no hallucination) ----------
# Keywords include Hindi/Bengali/Tamil terms too, so intent detection works
# correctly even when the user types the whole question in their own script
# (not just when they mix in English words).
_INTENTS = [
    ("eligibility", (
        "eligib", "qualify", "who can", "am i", "can i get", "eligible", "apply for it",
        "पात्र", "पात्रता", "योग्य",
        "যোগ্য", "যোগ্যতা",
        "தகுதி",
    )),
    ("Required Documents", (
        "document", "paper", "proof", "kyc", "certificate", "id ",
        "दस्तावेज़", "दस्तावेज", "कागजात", "काग़ज़ात",
        "নথি", "কাগজপত্র", "প্রমাণ",
        "ஆவணங்கள்", "ஆவணம்",
    )),
    ("How to Apply", (
        "how to apply", "apply", "register", "process", "where to", "link", "portal", "website",
        "आवेदन कैसे", "आवेदन", "रजिस्टर", "पंजीकरण", "कैसे करें",
        "আবেদন", "নিবন্ধন", "কীভাবে",
        "விண்ணப்பிக்க", "பதிவு", "எப்படி",
    )),
    ("Benefits", (
        "benefit", "amount", "money", "how much", "get", "subsidy", "pension", "loan", "cover",
        "लाभ", "फायदा", "कितना पैसा", "राशि", "कितना मिलेगा",
        "সুবিধা", "কত টাকা", "উপকার",
        "பலன்கள்", "நன்மைகள்", "எவ்வளவு",
    )),
    ("Important Dates", (
        "date", "deadline", "last date", "when", "renew",
        "तारीख", "समय सीमा", "समय-सीमा", "अंतिम तिथि",
        "তারিখ", "শেষ তারিখ", "সময়সীমা",
        "தேதி", "கடைசி தேதி", "காலக்கெடு",
    )),
    ("Hidden Conditions & Rules", (
        "condition", "rule", "catch", "exclusion", "penalty", "hidden",
        "पेंच", "शर्त", "नियम", "छिपा", "छिपा दंड",
        "শর্ত", "ফাঁক", "লুকানো",
        "நிபந்தனை", "சிக்கல்", "மறைமுக",
    )),
]


def chat_lines(query: str, lang: str = "en"):
    """Return (scheme_title, lines[], is_translated) — a short, point-to-point
    answer built ONLY from the matched scheme's KB record, so it cannot
    hallucinate.

    For non-English languages this reads the scheme's pre-built translation
    JSON (backend/data/translations/<slug>__<lang>.json — the SAME file the
    explainer already uses), so the answer is the real, human-reviewed
    translation of the official scheme data: instant, deterministic, and with
    zero dependency on a live LLM call. Falls back to the English KB record
    (with is_translated=False, so the caller can still try a live translation)
    only when no cached translation exists for that scheme+language yet.
    Returns (None, None, False) if no scheme matches."""
    s = match(query)
    if s is None:
        return None, None, False

    loc = translation_cache.get(s.slug, lang) if lang and lang != "en" else None
    is_translated = loc is not None
    ui = kb_i18n.ui(lang)
    q = (query or "").lower()

    def bullets(section: str, limit: int = 6):
        return _bullets(s.sections.get(section, ""))[:limit]

    def loc_bullets(key: str, section: str, limit: int = 6):
        """Localized bullet list when a translation cache entry exists,
        otherwise the raw English KB bullets."""
        if loc and loc.get(key):
            return list(loc[key])[:limit]
        return bullets(section, limit)

    def loc_text(key: str, section: str, limit: int = 400):
        if loc and loc.get(key):
            return str(loc[key])[:limit]
        return " ".join(l.strip() for l in s.sections.get(section, "").splitlines() if l.strip())[:limit]

    # pick the section the user asked about
    chosen = None
    for section, kws in _INTENTS:
        if any(k in q for k in kws):
            chosen = section
            break

    lines: List[str] = []
    if chosen == "eligibility":
        lines.append(ui["chat_label_eligibility"])
        lines += [f"- {b}" for b in loc_bullets("eligibility", "Eligibility")]
    elif chosen == "Required Documents":
        lines.append(ui["chat_label_documents"])
        lines += [f"- {b}" for b in loc_bullets("documents", "Required Documents")]
    elif chosen == "How to Apply":
        how = loc_text("how_to_apply", "How to Apply")
        lines.append(ui["chat_label_apply"])
        if how:
            lines.append(how)
        if s.meta.get("apply"):
            lines.append(f"{ui['chat_label_apply_here']} {s.meta['apply']}")
    elif chosen == "Benefits":
        lines.append(ui["chat_label_benefits"])
        lines += [f"- {b}" for b in loc_bullets("benefits", "Benefits")]
    elif chosen == "Important Dates":
        dt = loc_text("deadlines", "Important Dates", limit=300)
        lines.append(ui["chat_label_dates"])
        lines.append(dt if dt else ui["chat_label_no_deadline"])
    elif chosen == "Hidden Conditions & Rules":
        lines.append(ui["chat_label_rules"])
        rules = loc_bullets("misunderstood_clauses", "Hidden Conditions & Rules")
        if not rules:
            rules = bullets("Hidden Conditions & Rules")
        lines += [f"- {b}" for b in rules]
    else:
        # general summary
        whatis = loc_text("what_is", "What is this scheme", limit=300)
        if whatis:
            lines.append(whatis)
        top = loc_bullets("benefits", "Benefits", 3)
        if top:
            lines.append(ui["chat_label_key_benefits"])
            lines += [f"- {b}" for b in top]
        if s.meta.get("apply"):
            lines.append(f"{ui['chat_label_apply_here']} {s.meta['apply']}")

    lines.append(ui["chat_label_confirm"])
    title = (loc.get("title") if loc and loc.get("title") else s.title)
    return title, lines, is_translated


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
