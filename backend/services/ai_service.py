"""
AI feature layer: explainer, hidden-conditions, ELI5, compare, chat.

v2.0 changes:
  * STRUCTURED KB FIRST: queries that match one of the 18 schemes now use the
    curated markdown in backend/data/kb/ (built from the official PDFs) as the
    LLM context — complete sections, no chunk fragments, no cross-scheme
    leakage, no more "not available in the loaded records" for content that
    exists. Chroma RAG remains the fallback for free-form questions.
  * 15 languages supported in _lang() (MyScheme parity).
  * Confidence is High when the answer is grounded in the curated KB.
"""
import json
import re
import logging
import time
from datetime import datetime
from typing import List, Optional

import config
from services.rag_service import rag_service
from services import kb_service
from services import kb_i18n
from services import translation_cache
from services.llm import llm_chat, parse_json_or_none, LLM_UNAVAILABLE
from services import faithfulness
from services import extractive
from models.schemas import ExplainerResponse, ELI5Response

logger = logging.getLogger("janniti.ai")


def _now() -> float:
    return time.perf_counter()


def _log_explainer(lang: str, kb_s: float, llm_s, cache: str, total: float) -> None:
    logger.info("[explainer] lang=%-3s kb=%.3fs  llm=%-8s cache=%-5s total=%.2fs",
                lang, kb_s, str(llm_s), cache, total)

SYSTEM_PROMPT = """You are JanNiti, India's Policy Literacy AI. You help Indian citizens understand government schemes in simple language.
Rules:
1. Explain at a Grade 6-8 reading level with everyday Indian analogies.
2. Use ONLY the official context provided. If the answer isn't there, say it isn't available in the loaded records.
3. Always cite the scheme/source. Be honest about confidence.
4. Add a disclaimer that this is AI guidance, not an official notification.
5. Never give legal advice; recommend official sources for final decisions.
6. Answer in the language requested."""

_RECENT_YEARS = {str(datetime.now().year), str(datetime.now().year - 1)}

_LANG_NAMES = {
    "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil",
    "te": "Telugu", "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada",
    "ml": "Malayalam", "pa": "Punjabi", "or": "Odia", "as": "Assamese",
    "ur": "Urdu", "mai": "Maithili", "ks": "Kashmiri",
}


def _lang(language: str) -> str:
    name = _LANG_NAMES.get(language, language if language else "English")
    if name == "English":
        return "Respond entirely in English."
    # Strong lock: weaker models tend to drift to Hindi for Indian-scheme
    # content, so be explicit that ONLY the requested language is allowed.
    return (
        f"Respond ENTIRELY in {name}. Write every sentence in {name} only. "
        f"Do NOT answer in English, Hindi, or any language other than {name} "
        f"(unless {name} itself is that language). Only figures (e.g. Rs. 6,000), "
        f"dates, percentages, URLs and acronyms (PM-KISAN, PMFBY, DBT, NSP) may "
        f"stay in Latin script."
    )


def _confidence(has_source: bool, has_recent: bool, n: int) -> str:
    if has_source and has_recent and n >= 3:
        return "High"
    if has_source and n >= 1:
        return "Medium"
    return "Low"


def _fallback_explainer(query: str, msg: str) -> ExplainerResponse:
    return ExplainerResponse(
        title=query, what_is=msg, why_introduced="Information unavailable.",
        benefits=[], eligibility=[], documents=[], how_to_apply="Not available.",
        deadlines=None, misunderstood_clauses=[], source="Official records not found",
        ministry="Unknown", last_updated="N/A", confidence="Low",
        disclaimer="This is AI-generated guidance. Please verify with official government sources before applying.",
    )


# --- Section-targeted retrieval (RAG fallback path) ------------------------
_SECTION_QUERIES = [
    "benefits amount financial assistance",
    "eligibility who can apply criteria",
    "documents required checklist",
    "how to apply application process steps",
    "deadline last date application period renewal",
    "conditions exclusions rules penalties misunderstood",
]


def _retrieve_scheme_context(query: str, language: str = "en",
                             per_section: int = 3, cap: int = 18) -> list:
    """Multi-query retrieval: base query + one query per explainer section.
    Chunks are deduped and, once the scheme is identified from the first
    pass, restricted to that scheme so sections don't mix schemes up."""
    first = rag_service.search(query, top_k=6, language=language)
    if not first:
        return []
    scheme_name = (first[0].get("metadata", {}).get("name") or "").lower().strip()

    seen, out = set(), []

    def add(results):
        for r in results:
            meta = r.get("metadata", {}) or {}
            key = (meta.get("source", ""), (r.get("text") or "")[:100])
            if key in seen:
                continue
            nm = (meta.get("name") or "").lower().strip()
            if scheme_name and nm and nm != scheme_name:
                continue  # keep the context on one scheme
            seen.add(key)
            out.append(r)

    add(first)
    for sq in _SECTION_QUERIES:
        if len(out) >= cap:
            break
        add(rag_service.search(f"{query} {sq}", top_k=per_section, language=language))
    return out[:cap]


def _grounding(query: str, language: str, cap: int = 18):
    """Return (context, rag_results, kb_scheme). Curated KB wins when the
    query maps to a known scheme; RAG chunks are the fallback.

    SPEED: when the KB matches, vector retrieval is skipped entirely (the KB
    file comes from an in-memory cache), cutting ~7 Chroma searches per
    explainer request. RAG is fetched lazily only if the LLM fails and the
    extractive fallback needs chunks."""
    kb = kb_service.match(query)
    if kb is not None:
        return kb.raw, [], kb
    rag_results = _retrieve_scheme_context(query, language, cap=cap)
    return "\n\n".join(r["text"] for r in rag_results), rag_results, None


def _rag_for_fallback(query: str, language: str, rag_results: list) -> list:
    """Fetch chunks only when the extractive fallback actually needs them."""
    return rag_results or _retrieve_scheme_context(query, language)


_TRANSLATABLE_SCALARS = ("title", "what_is", "why_introduced", "how_to_apply",
                         "deadlines", "disclaimer")
_TRANSLATABLE_ARRAYS = ("benefits", "eligibility", "documents", "misunderstood_clauses")


def translate_texts(texts: List[str], language: str, batch: int = 10) -> List[str]:
    """Translate arbitrary UI text (e.g. whole chat messages) into ANY target
    language, English included. Unlike _translate_strings (which is keyed on an
    English source and short-circuits for en), this re-renders existing text in
    the selected language regardless of its current language — used when the
    user switches languages and wants the previous conversation re-rendered."""
    if not texts:
        return []
    lang_name = _LANG_NAMES.get(language, "English")
    out = list(texts)
    for start in range(0, len(texts), batch):
        chunk = texts[start:start + batch]
        numbered = "\n".join(f"{j + 1}. {s}" for j, s in enumerate(chunk))
        prompt = (
            f"Translate each numbered line below into {lang_name}. Write ONLY in "
            f"{lang_name}. Keep figures (Rs. 6,000), dates, percentages, URLs and "
            f"acronyms (PM-KISAN, PMFBY, RuPay, SIDBI) unchanged. Return EXACTLY the "
            f"same numbering, one item per line as 'N. <translation>', with the same "
            f"number of lines.\n\n{numbered}"
        )
        raw = llm_chat(messages=[
            {"role": "system", "content": f"You are a precise translator into {lang_name}."},
            {"role": "user", "content": prompt}])
        if raw == LLM_UNAVAILABLE or not raw:
            continue
        parsed = {}
        for line in raw.splitlines():
            m = re.match(r"\s*(\d+)[.)]\s*(.+)", line)
            if m:
                parsed[int(m.group(1))] = m.group(2).strip()
        for j in range(len(chunk)):
            if (j + 1) in parsed and parsed[j + 1]:
                out[start + j] = parsed[j + 1]
    return out
    """Shared translation layer used by BOTH the explainer and the chatbot.
    Returns (list, ok).

    - Checks the content-hash cache first; only strings never seen before are
      sent to the AI, so repeated phrases (across schemes and chat) are instant.
    - Uses a NUMBERED-LIST prompt in small batches so the AI reply can't be
      truncated or malformed.
    - On any AI failure the original English is kept for that item and ok=False,
      so callers won't cache an incomplete result.
    """
    if not strings:
        return [], True
    if (language or "en") == "en":
        return list(strings), True

    out = list(strings)
    ok = True

    # 1) fill from the shared content cache
    todo_idx = []
    for i, s in enumerate(strings):
        cached = translation_cache.line_get(s, language)
        if cached is not None:
            out[i] = cached
        else:
            todo_idx.append(i)

    # 2) translate the rest in safe batches
    lang_name = _LANG_NAMES.get(language, language)
    new_pairs = []
    for start in range(0, len(todo_idx), batch):
        idx_chunk = todo_idx[start:start + batch]
        chunk = [strings[i] for i in idx_chunk]
        numbered = "\n".join(f"{j + 1}. {s}" for j, s in enumerate(chunk))
        prompt = (
            f"Translate the following numbered lines into {lang_name} language "
            f"(language code '{language}').\n"
            f"Write the translations ONLY in {lang_name}. Do NOT answer in English, "
            f"Hindi, or any language other than {lang_name}. The ONLY things that may "
            f"stay in English/digits are figures (e.g. Rs. 6,000), dates, percentages, "
            f"URLs, and acronyms (PM-KISAN, PMFBY, DBT, NSP).\n"
            "Return EXACTLY the same numbers, one item per line, in the format "
            "'N. <translation>'. Keep the same number of lines; do NOT merge, drop, "
            "add or reorder lines.\n\n"
            f"{numbered}"
        )
        raw = llm_chat(
            messages=[{"role": "system", "content":
                       f"You are a precise translator. You translate Indian government scheme "
                       f"information into {lang_name} and never into any other language."},
                      {"role": "user", "content": prompt}],
            json_mode=False,
        )
        if raw == LLM_UNAVAILABLE or not raw:
            ok = False
            continue
        got = 0
        for line in raw.splitlines():
            m = re.match(r"\s*(\d+)[.)]\s*(.+)", line)
            if not m:
                continue
            j = int(m.group(1)) - 1
            if 0 <= j < len(idx_chunk):
                translation = m.group(2).strip()
                out[idx_chunk[j]] = translation
                new_pairs.append((chunk[j], translation))
                got += 1
        if got < len(idx_chunk):
            ok = False

    if new_pairs:
        translation_cache.line_put_many(new_pairs, language)
    return out, ok


def translate_lines(strings: List[str], language: str):
    """Public entry point for the shared translation layer (used by chatbot)."""
    return _translate_strings(strings, language)


def _translate_explainer_dict(base: dict, language: str):
    """Translate the human-readable fields of an English explainer dict into
    `language`. Returns (dict, ok). Robust: flattens everything into one string
    list, translates in safe batches, then reassembles. ok=False means the
    result is partly English and should NOT be cached."""
    flat: List[str] = []
    slots: List = []  # (kind, key, index)

    for k in _TRANSLATABLE_SCALARS:
        v = base.get(k)
        if isinstance(v, str) and v.strip():
            slots.append(("scalar", k, None))
            flat.append(v)

    for k in _TRANSLATABLE_ARRAYS:
        for i, item in enumerate(base.get(k) or []):
            if isinstance(item, str) and item.strip():
                slots.append(("array", k, i))
                flat.append(item)

    if not flat:
        return base, True

    translated, ok = _translate_strings(flat, language)

    out = dict(base)
    arr_copy = {k: list(base.get(k) or []) for k in _TRANSLATABLE_ARRAYS}
    for (kind, key, idx), tv in zip(slots, translated):
        if kind == "scalar":
            out[key] = tv
        else:
            arr_copy[key][idx] = tv
    for k in _TRANSLATABLE_ARRAYS:
        out[k] = arr_copy[k]
    return out, ok


def generate_explainer(query: str, language: str = "en", state: Optional[str] = None) -> ExplainerResponse:
    """Explainer with per-request timing logs.

    Log line format (watch the backend terminal):
        [explainer] lang=en  kb=0.003s  llm=SKIPPED  cache=-       total=0.01s
        [explainer] lang=hi  kb=0.002s  llm=5.9s     cache=MISS    total=5.9s
        [explainer] lang=hi  kb=0.002s  llm=SKIPPED  cache=HIT     total=0.01s
    """
    t0 = _now()
    lang = language or "en"

    # 1) KB match (milliseconds)
    tk = _now()
    kb_fast = kb_service.match(query)
    kb_ms = _now() - tk

    if kb_fast is not None:
        # English -> build straight from KB, no LLM, no cache needed.
        if lang == "en":
            try:
                resp = ExplainerResponse(**kb_service.explainer_dict(kb_fast))
                _log_explainer(lang, kb_ms, llm_s="SKIPPED", cache="-", total=_now() - t0)
                return resp
            except Exception as e:
                logger.error(f"KB fast-path failed, falling back to LLM: {e}")

        # Non-English -> FIRST try a pre-built translated .md file (instant).
        if lang != "en":
            tsch = kb_service.translated_scheme(kb_fast.slug, lang)
            if tsch is not None:
                try:
                    d = kb_service.explainer_dict(tsch)
                    # keep authoritative English apply/official links + ministry
                    d["source"] = kb_fast.meta.get("official", d.get("source"))
                    d["ministry"] = kb_fast.meta.get("ministry", d.get("ministry"))
                    resp = ExplainerResponse(**d)
                    _log_explainer(lang, kb_ms, llm_s="SKIPPED", cache="MD", total=_now() - t0)
                    return resp
                except Exception as e:
                    logger.error(f"Translated-md path failed: {e}")

        # Non-English -> check the on-disk translation cache first.
        cached = translation_cache.get(kb_fast.slug, lang)
        if cached:
            try:
                resp = ExplainerResponse(**cached)
                _log_explainer(lang, kb_ms, llm_s="SKIPPED", cache="HIT", total=_now() - t0)
                return resp
            except Exception:
                pass  # corrupted entry -> re-translate below

        # Cache miss -> translate the English KB dict, cache only if complete.
        base = kb_service.explainer_dict(kb_fast)
        tl = _now()
        translated, ok = _translate_explainer_dict(base, lang)
        llm_s = _now() - tl
        try:
            resp = ExplainerResponse(**translated)
            if ok:
                translation_cache.put(kb_fast.slug, lang, translated)
            _log_explainer(lang, kb_ms, llm_s=f"{llm_s:.1f}s",
                           cache="MISS" if ok else "PARTIAL", total=_now() - t0)
            return resp
        except Exception as e:
            logger.error(f"Translated explainer schema error: {e}")
            # fall through to the generic path

    # 2) No KB match -> RAG + LLM (free-form path, unchanged)
    context, rag_results, kb = _grounding(query, language)
    if not context:
        _log_explainer(lang, kb_ms, llm_s="-", cache="-", total=_now() - t0)
        return _fallback_explainer(query, "This information is not in the official records currently loaded into JanNiti.")

    prompt = f"""{_lang(language)}

Based ONLY on the official context below, explain this scheme simply (Grade 6-8).
Fill EVERY field from the context — the context is the complete official record for this scheme.
Each benefits/eligibility/documents item must be a COMPLETE sentence or phrase (never a fragment).

Context:
{context}

User query: {query}
{f"State: {state}" if state else ""}

As the LAST item of the documents array, add one short note in the SAME response language meaning:
"Note: this list is from official records — your bank/portal or state may ask for extra documents, so confirm on the official portal before applying."

Return JSON with keys: title, what_is, why_introduced, benefits (array), eligibility (array),
documents (array), how_to_apply (string), deadlines (string or null), misunderstood_clauses (array),
source, ministry, last_updated, confidence (High/Medium/Low),
disclaimer ("This is AI-generated guidance based on publicly available information. Please verify with official government sources before applying.")."""

    tl = _now()
    content = llm_chat(
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
        json_mode=True,
    )
    llm_s = _now() - tl
    data = parse_json_or_none(content)
    if data is None:
        _log_explainer(lang, kb_ms, llm_s=f"{llm_s:.1f}s", cache="n/a", total=_now() - t0)
        # LLM down/out of credit -> show the real official text from retrieval
        return ExplainerResponse(**extractive.build_explainer(query, _rag_for_fallback(query, language, rag_results), language))

    for k in ("how_to_apply", "why_introduced"):
        if isinstance(data.get(k), list):
            data[k] = "\n".join(str(x) for x in data[k])
    if isinstance(data.get("deadlines"), list):
        data["deadlines"] = "\n".join(data["deadlines"]) if data["deadlines"] else None

    if kb is not None:
        # curated-KB grounding: authoritative source/ministry + High confidence
        data.setdefault("title", kb.title)
        if not data.get("ministry") or data.get("ministry") == "Unknown":
            data["ministry"] = kb.meta.get("ministry", data.get("ministry", "Unknown"))
        data["source"] = kb.meta.get("official", data.get("source") or kb.title)
        data["confidence"] = "High"
    else:
        has_recent = any(y in str(data.get("last_updated", "")) for y in _RECENT_YEARS)
        data["confidence"] = _confidence(
            bool(data.get("source") and data["source"] != "General knowledge"),
            has_recent, len(rag_results),
        )
    _log_explainer(lang, kb_ms, llm_s=f"{llm_s:.1f}s", cache="n/a", total=_now() - t0)
    try:
        return ExplainerResponse(**data)
    except Exception as e:
        logger.error(f"Explainer schema error: {e}; data keys={list(data.keys())}")
        return ExplainerResponse(**extractive.build_explainer(query, _rag_for_fallback(query, language, rag_results), language))


def detect_conditions(query: str, language: str = "en") -> dict:
    lang = language or "en"

    # FAST PATH: build straight from the (possibly translated) .md "Hidden
    # Conditions & Rules" + "Exclusions" sections — instant, no AI, already in
    # the selected language when a translated .md exists.
    sch, is_translated = kb_service.match_localized(query, lang)
    if sch is not None:
        conditions = []
        for section, default_sev in (("Hidden Conditions & Rules", None), ("Exclusions", "red")):
            body = sch.sections.get(section, "")
            for raw in body.splitlines():
                s = raw.strip()
                if not s.startswith("- "):
                    continue
                text = s[2:].strip()
                sev = default_sev or "yellow"
                m = re.search(r"\[(green|yellow|red)\]\s*$", text)
                if m:
                    sev = m.group(1)
                    text = text[: m.start()].strip()
                if text:
                    conditions.append({"text": text, "severity": sev, "explanation": ""})
        if conditions:
            # LANGUAGE (hidden conditions): the KB sections are English. The
            # explainer's "misunderstood_clauses" are these SAME clauses (Hidden
            # Conditions & Rules + Exclusions, same order) and are already
            # translated per scheme in the cache. Reuse them so conditions render
            # in the selected language with NO live LLM call; severity is kept.
            if lang != "en" and not is_translated:
                cached = translation_cache.get(sch.slug, lang)
                tclauses = (cached or {}).get("misunderstood_clauses") if cached else None
                if tclauses and len(tclauses) >= len(conditions):
                    for c, tv in zip(conditions, tclauses):
                        c["text"] = tv
                else:
                    # last resort: live translation (works only if LLM is up)
                    texts = [c["text"] for c in conditions]
                    translated, _ok = _translate_strings(texts, lang)
                    for c, tv in zip(conditions, translated):
                        c["text"] = tv
            return {"conditions": conditions, "summary": ""}

    # fallback: AI path (only if no KB/.md match)
    context, rag_results, kb = _grounding(query, language, cap=16)
    prompt = f"""{_lang(language)}

From the scheme text below, list hidden conditions, exclusions, obligations, and penalties.
The "Hidden Conditions & Rules" section (if present) already marks severity as [green]/[yellow]/[red] — use those.
Also include items from "Exclusions". Every item must be a complete, self-contained sentence.

Scheme text:
{context if context else query}

Return JSON: {{"conditions": [{{"text","severity"(green|yellow|red),"explanation"}}], "summary": "..."}}.
green=general info, yellow=read carefully, red=penalties/exclusions/disqualification."""
    data = parse_json_or_none(llm_chat(
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
        json_mode=True))
    if data is None:
        return extractive.build_conditions(_rag_for_fallback(query, language, rag_results))
    data.setdefault("conditions", [])
    data.setdefault("summary", "")
    return data


_ELI5_FIELDS = ("story", "simple_explanation", "everyday_example", "key_takeaway")


def _localized_fields(scheme, lang: str) -> dict:
    """Return the scheme's explainer fields in `lang`.

    English is built from the KB; hi/bn/ta come from the pre-built per-scheme
    translation cache (data/translations/<slug>__<lang>.json). This is what lets
    Simple Story / Compare render fully translated with NO live LLM call."""
    if lang == "en":
        return kb_service.explainer_dict(scheme)
    cached = translation_cache.get(scheme.slug, lang)
    if cached:
        return cached
    return kb_service.explainer_dict(scheme)  # graceful English fallback


def _kb_eli5(scheme, lang: str = "en") -> dict:
    """Build the 'Simple Story' straight from the (translated) KB — no LLM.

    Accurate, instant, fully multilingual, and can never show an
    'AI unavailable' message."""
    f = _localized_fields(scheme, lang)
    ui = kb_i18n.ui(lang)
    title = f.get("title") or scheme.title
    benefits = f.get("benefits") or []
    elig = f.get("eligibility") or []
    whatis = f.get("what_is") or title
    nm = kb_i18n.name(scheme.slug)
    rl = kb_i18n.role(lang, scheme.slug)
    b1 = benefits[0] if benefits else ""

    story = " ".join(x for x in [
        ui["story_intro"].format(name=nm, role=rl),
        ui["story_learn"].format(name=nm, title=title),
        (ui["story_benefit"].format(benefit=b1) if b1 else ""),
        ui["story_end"].format(name=nm),
    ] if x)

    simple = whatis
    if benefits:
        simple += " " + ui["in_short"] + " " + "; ".join(benefits[:3]).rstrip(".") + "."

    example = ui["example"].format(title=title)

    takeaway = ""
    if elig:
        takeaway += ui["eligible_if"] + " " + "; ".join(elig[:2]).rstrip(".") + ". "
    takeaway += ui["disclaimer"]

    return {"story": story, "simple_explanation": simple,
            "everyday_example": example, "key_takeaway": takeaway}


def generate_eli5(query: str, language: str = "en") -> ELI5Response:
    """Simple Story, built from the curated 18-scheme KB in the selected
    language. Deterministic, instant, no LLM, never an error fallback."""
    lang = language or "en"
    kb = kb_service.match(query)
    if kb is None:
        ui = kb_i18n.ui(lang)
        names = ", ".join(kb_service.scheme_names()[:6])
        return ELI5Response(
            story=ui["no_scheme_story"],
            simple_explanation=f"{ui['reco_ask_name']} ({names} …)",
            everyday_example=ui["no_scheme_story"],
            key_takeaway=ui["no_scheme_story"])
    return ELI5Response(**_kb_eli5(kb, lang))


def _scheme_context(name: str, language: str) -> str:
    kb = kb_service.match(name)
    if kb is not None:
        return kb.raw
    return "\n\n".join(r["text"] for r in rag_service.search(name, top_k=5, language=language))


def compare_schemes(scheme1: str, scheme2: str, language: str = "en") -> dict:
    """Side-by-side comparison built directly from the curated KB.

    Deterministic and fully multilingual (via the per-scheme translation cache),
    so it never returns 'unavailable' and never hallucinates. Only schemes in
    the 18-scheme KB can be compared."""
    lang = language or "en"
    ui = kb_i18n.ui(lang)
    s1 = kb_service.match(scheme1)
    s2 = kb_service.match(scheme2)
    if s1 is None or s2 is None:
        return {"scheme1_name": scheme1, "scheme2_name": scheme2,
                "comparisons": [], "recommendation": ui["cmp_unknown"]}

    f1 = _localized_fields(s1, lang)
    f2 = _localized_fields(s2, lang)

    def as_text(v):
        if isinstance(v, list):
            return "; ".join(str(x) for x in v) if v else "—"
        return str(v) if v else "—"

    rows = [
        {"aspect": ui["asp_what"], "scheme1_value": as_text(f1.get("what_is")), "scheme2_value": as_text(f2.get("what_is"))},
        {"aspect": ui["asp_benefits"], "scheme1_value": as_text(f1.get("benefits")), "scheme2_value": as_text(f2.get("benefits"))},
        {"aspect": ui["asp_eligibility"], "scheme1_value": as_text(f1.get("eligibility")), "scheme2_value": as_text(f2.get("eligibility"))},
        {"aspect": ui["asp_documents"], "scheme1_value": as_text(f1.get("documents")), "scheme2_value": as_text(f2.get("documents"))},
        {"aspect": ui["asp_apply"], "scheme1_value": as_text(f1.get("how_to_apply")), "scheme2_value": as_text(f2.get("how_to_apply"))},
        {"aspect": ui["asp_deadline"], "scheme1_value": as_text(f1.get("deadlines")), "scheme2_value": as_text(f2.get("deadlines"))},
    ]
    return {
        "scheme1_name": f1.get("title") or s1.title,
        "scheme2_name": f2.get("title") or s2.title,
        "comparisons": rows,
        "recommendation": ui["cmp_pick_help"],
    }


def profile_fit_score(slug: str, profile: dict) -> float:
    """A principled, deterministic fit score between a citizen profile and a
    scheme, using the same eligibility signals as the chatbot recommender
    (occupation/flags -> category, age windows, girl-child, income). Higher is
    a better fit. Used to rank/choose schemes without an LLM."""
    profile = profile or {}
    occ = (profile.get("occupation") or "").lower()
    age = profile.get("age")
    gender = (profile.get("gender") or "").lower()
    income = profile.get("annualIncome")
    is_farmer = profile.get("isFarmer")
    is_student = profile.get("isStudent")
    cat = kb_i18n.SCHEME_CAT.get(slug, "general")
    score = 0.0

    # occupation / flag -> category alignment
    if cat == "farmer" and (is_farmer or "farm" in occ):
        score += 3
    if cat == "business" and any(w in occ for w in ("self", "business", "shop", "entrepreneur")):
        score += 3
    if cat == "youth" and any(w in occ for w in ("unemploy", "job", "fresher", "graduate", "seeker")):
        score += 3
    if cat == "student" and (is_student or "student" in occ):
        score += 3
    if cat in ("worker", "household") and any(w in occ for w in ("worker", "wage", "labour", "unorganised", "daily")):
        score += 2
    if cat == "household" and isinstance(income, (int, float)) and income and income <= 250000:
        score += 2

    # age windows (age-gated schemes)
    if slug in _AGE_WINDOWS and isinstance(age, (int, float)) and age:
        lo, hi = _AGE_WINDOWS[slug]
        score += 2 if lo <= age <= hi else -3

    # girl-child schemes
    if slug in _GIRL_CHILD_SCHEMES:
        score += 2 if gender == "female" else -5

    return score


def recommend_for_profile(scheme1: str, scheme2: str, profile: dict, language: str = "en") -> dict:
    """Given two schemes and a citizen's profile, pick which fits better —
    grounded in the KB, deterministic, multilingual, no LLM."""
    lang = language or "en"
    ui = kb_i18n.ui(lang)
    s1 = kb_service.match(scheme1)
    s2 = kb_service.match(scheme2)
    if s1 is None or s2 is None:
        return {"recommended_scheme": "", "reasoning": ui["cmp_unknown"]}

    # choose by principled profile-fit score (tie-break: keep scheme1)
    sc1 = profile_fit_score(s1.slug, profile)
    sc2 = profile_fit_score(s2.slug, profile)
    winner = s2 if sc2 > sc1 else s1
    f = _localized_fields(winner, lang)
    picked = f.get("title") or winner.title
    return {"recommended_scheme": picked,
            "reasoning": f"{ui['reco_prefix']} {picked}. {ui['cmp_pick_help']}"}


# --- Smart KB-only chatbot helpers --------------------------------------
# Map broad intents to the relevant schemes so a question that doesn't name a
# scheme ("which scheme helps farmers?") still gets a grounded, accurate answer
# from the 18-scheme KB — no LLM, no hallucination.
_CATEGORY_KEYWORDS = {
    "farmer": (["farmer", "kisan", "crop", "farming", "agricultur", "cultivat", "harvest"],
               ["pm-kisan", "kisan-credit-card", "fasal-bima"]),
    "pension": (["pension", "old age", "retirement", "retire", "senior citizen"],
                ["atal-pension"]),
    "insurance": (["insurance", "bima", "life cover", "accident", "death cover", "disability cover"],
                  ["jeevan-jyoti-bima", "suraksha-bima"]),
    "bank": (["bank account", "jan dhan", "jandhan", "savings account", "open account",
              "no bank", "zero balance"], ["jan-dhan"]),
    "food": (["ration", "free food", "anna", "grain", "foodgrain", "food security"],
             ["garib-kalyan-anna"]),
    "business": (["business", "startup", "enterprise", "mudra", "shop", "self employ",
                  "self-employ", "small business"], ["mudra", "stand-up-india"]),
    "job": (["job", "employment", "rozgar", "hiring", "first job", "new employee"],
            ["viksit-bharat-rozgar"]),
    "skill": (["skill", "training", "upskill", "vocational", "certificate course"],
              ["kaushal-vikas", "skill-loan"]),
    "scholarship": (["scholarship", "student", "study", "education", "fellowship",
                     "girl child", "research", "college", "school fee"],
                    ["cbse-single-girl-child", "pg-indira-gandhi-sgc",
                     "national-pg-scholarship", "icar-national-talent", "ugc-jrf-engineering"]),
}

# Deterministic eligibility windows used to give profile-aware hints.
_AGE_WINDOWS = {"atal-pension": (18, 40), "jeevan-jyoti-bima": (18, 50), "suraksha-bima": (18, 70)}
_FARMER_SCHEMES = {"pm-kisan", "kisan-credit-card", "fasal-bima"}
_GIRL_CHILD_SCHEMES = {"cbse-single-girl-child", "pg-indira-gandhi-sgc"}


def _kb_suggest(message: str):
    """If the question names a category (not a single scheme), return grounded
    one-liners for the relevant schemes. Returns list[str] or None."""
    q = (message or "").lower()
    schemes = {s.slug: s for s in kb_service.all_schemes()}
    for _cat, (kws, slugs) in _CATEGORY_KEYWORDS.items():
        if any(k in q for k in kws):
            picks = [schemes[sl] for sl in slugs if sl in schemes]
            if picks:
                lines = ["Here are the schemes that can help:"]
                for s in picks:
                    wi = " ".join(l.strip() for l in s.sections.get("What is this scheme", "").splitlines() if l.strip())
                    lines.append(f"- {s.title}: {wi[:110].rstrip()}...")
                lines.append("Ask me about any one by name for full details.")
                return lines
    return None


def _profile_note(scheme, profile: dict) -> str:
    """A short, deterministic personalisation using the user's saved profile —
    so the bot uses their details instead of asking questions."""
    if not scheme or not profile:
        return ""
    slug = scheme.slug
    age = profile.get("age")
    occ = (profile.get("occupation") or "").lower()
    gender = (profile.get("gender") or "").lower()
    is_farmer = profile.get("isFarmer")
    bits = []

    if slug in _FARMER_SCHEMES and (is_farmer or "farm" in occ):
        bits.append("you're registered as a farmer, so you likely meet the core occupation requirement")
    if slug in _AGE_WINDOWS and isinstance(age, (int, float)) and age:
        lo, hi = _AGE_WINDOWS[slug]
        if lo <= age <= hi:
            bits.append(f"at age {int(age)} you fall within the required {lo}-{hi} age range")
        else:
            bits.append(f"this scheme needs age {lo}-{hi}, and your profile shows {int(age)}")
    if slug in _GIRL_CHILD_SCHEMES and gender == "female":
        bits.append("it is for a single girl child, and your profile's gender fits that criterion")

    if not bits:
        return ""
    return "Based on your profile, " + "; ".join(bits) + "."


_RECO_TRIGGERS = ("which scheme", "recommend", "suggest a scheme", "suggest scheme",
                  "should i apply", "should i go for", "what can i apply", "what should i apply",
                  "am i eligible for", "eligible for anything", "best scheme for me",
                  "help me find", "which one should i", "what schemes can i")


def _is_reco_intent(message: str) -> bool:
    q = (message or "").lower()
    return any(t in q for t in _RECO_TRIGGERS)


def _kb_recommend(profile: dict, lang: str):
    """Pick the most relevant schemes for this user's profile, grounded in the
    18-scheme KB. Uses profile fields instead of asking questions."""
    profile = profile or {}
    schemes = {s.slug: s for s in kb_service.all_schemes()}
    picks: list = []

    def add(slugs):
        for sl in slugs:
            if sl in schemes and sl not in picks:
                picks.append(sl)

    occ = (profile.get("occupation") or "").lower()
    age = profile.get("age")
    income = profile.get("annualIncome")
    is_farmer = profile.get("isFarmer")
    is_student = profile.get("isStudent")
    gender = (profile.get("gender") or "").lower()

    if is_farmer or "farm" in occ:
        add(["pm-kisan", "kisan-credit-card", "fasal-bima"])
    if is_student or "student" in occ:
        add(["cbse-single-girl-child", "national-pg-scholarship", "skill-loan"])
        if gender == "female":
            add(["pg-indira-gandhi-sgc"])
    if any(w in occ for w in ("self", "business", "shop", "entrepreneur")):
        add(["mudra", "stand-up-india"])
    if any(w in occ for w in ("unemploy", "job", "fresher", "graduate")):
        add(["viksit-bharat-rozgar", "kaushal-vikas"])
    if isinstance(age, (int, float)) and age:
        if 18 <= age <= 40:
            add(["atal-pension"])
        if 18 <= age <= 50:
            add(["jeevan-jyoti-bima"])
        if 18 <= age <= 70:
            add(["suraksha-bima"])
    if isinstance(income, (int, float)) and income and income <= 250000:
        add(["jan-dhan", "garib-kalyan-anna"])

    ui = kb_i18n.ui(lang)
    if not picks:
        return None  # no profile signal -> caller returns reco_none
    lines = [ui["reco_prefix"]]
    for sl in picks[:6]:
        f = _localized_fields(schemes[sl], lang)
        lines.append(f"- {f.get('title') or schemes[sl].title}")
    lines.append(ui["reco_ask_name"])
    return lines


def chat_with_ai(message: str, conversation_history: Optional[List[dict]] = None,
                 language: str = "en", profile: Optional[dict] = None) -> dict:
    """Fully KB-grounded chatbot.

    Answers ONLY from the curated 18-scheme knowledge base, so it gives
    point-to-point information, never hallucinates, and never interrogates the
    user. If the user has a saved profile, a short deterministic eligibility
    hint is added instead of asking questions. Works even when the LLM is
    unavailable (non-English text is served from the translation cache)."""
    lang = language or "en"
    profile = profile or {}

    # ---- 1) Question maps to a known scheme -> point-to-point KB answer ----
    title, lines, is_translated = kb_service.chat_lines(message, lang)
    if title and lines:
        sch = kb_service.match(message)
        note = _profile_note(sch, profile) if sch else ""

        if lang == "en":
            out_lines = ([note, ""] + lines) if note else lines
            reply = "\n".join(out_lines)
            src_title = title
        elif is_translated:
            # `lines` are already the real, human-reviewed translation for this
            # scheme+language (from the translation cache) — never re-run them
            # through the LLM. Only the (English) profile note needs translating.
            if note:
                note_t, _ = _translate_strings([note], lang)
                reply = note_t[0] + "\n\n" + "\n".join(lines)
            else:
                reply = "\n".join(lines)
            src_title = title
        else:
            # No cached translation for this scheme+language yet -> best-effort
            # live LLM translation of the (English) KB lines + the note.
            base = ([note, ""] + lines) if note else list(lines)
            translated, _ = _translate_strings([x for x in base if x != ""], lang)
            # re-insert the blank spacer after the note if present
            reply = ("\n\n".join(translated[:1]) + "\n\n" + "\n".join(translated[1:])) if note \
                else "\n".join(translated)
            src_title = _translate_strings([title], lang)[0][0]
        return {"reply": reply, "sources": [src_title], "confidence": "High",
                "faithfulness": 1.0, "grounded": True}

    # ---- 2) Recommendation intent ("which scheme should I apply for?") ----
    if _is_reco_intent(message):
        rec = _kb_recommend(profile, lang)
        ui = kb_i18n.ui(lang)
        reply = "\n".join(rec) if rec else ui["reco_none"]
        return {"reply": reply, "sources": ["JanNiti scheme list"],
                "confidence": "Medium" if rec else "Low",
                "faithfulness": 1.0 if rec else None, "grounded": bool(rec)}

    # ---- 3) Category question ("which scheme helps farmers?") -------------
    sugg = _kb_suggest(message)
    if sugg:
        ui = kb_i18n.ui(lang)
        # The connector lines ("Here are the schemes that can help:" / "Ask me
        # about any one by name...") are static -> always render instantly and
        # correctly from kb_i18n, with zero dependency on a live LLM call. Only
        # the middle, scheme-specific snippet lines (pulled straight from the
        # English KB) need best-effort translation when the LLM is reachable.
        middle = sugg[1:-1]
        if lang != "en" and middle:
            middle, _ = _translate_strings(middle, lang)
        out_lines = [ui["chat_cat_intro"]] + middle + [ui["chat_cat_outro"]]
        return {"reply": "\n".join(out_lines), "sources": ["JanNiti scheme list"],
                "confidence": "Medium", "faithfulness": 1.0, "grounded": True}

    # ---- 4) Outside the 18 schemes -> honest answer, list what IS covered --
    # Fully static + deterministic: scheme names come from the pre-translated
    # KB (kb_service.scheme_names) and the intro/outro connector lines come
    # from kb_i18n, so this NEVER falls back to English just because the live
    # LLM/translation call is unavailable or slow.
    names = kb_service.scheme_names(lang)   # already in the selected language
    ui = kb_i18n.ui(lang)
    fb = [ui["chat_no_match_intro"]] + [f"- {n}" for n in names] + [ui["chat_no_match_outro"]]
    return {"reply": "\n".join(fb), "sources": ["JanNiti scheme list"],
            "confidence": "Low", "faithfulness": None, "grounded": False}
