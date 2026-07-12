"""
Translation cache — JanNiti v2.0.

Non-English explainers are expensive because each one is an LLM call. This
module caches the translated result on disk (backend/data/translations/), keyed
by scheme slug + language, so:

  * first view of a scheme in a language  -> 1 LLM call, then cached
  * every later view (any user)           -> instant, read from disk

The English explainer never hits the LLM at all (built straight from the KB),
so English is always sub-second. This cache makes the OTHER 14 languages
sub-second too, after their first view.

Cache entries are plain JSON (the ExplainerResponse dict). Safe to delete the
folder any time to force re-translation.
"""
import json
import logging
import os
import threading

logger = logging.getLogger("janniti.tcache")

_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "translations")
_lock = threading.Lock()


def _path(slug: str, language: str) -> str:
    safe = "".join(c for c in f"{slug}__{language}" if c.isalnum() or c in "-_")
    return os.path.join(_DIR, f"{safe}.json")


def get(slug: str, language: str):
    """Return the cached dict for this scheme+language, or None."""
    p = _path(slug, language)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("translation cache read failed %s: %s", p, e)
        return None


def put(slug: str, language: str, data: dict) -> None:
    """Store the translated dict for this scheme+language."""
    try:
        with _lock:
            os.makedirs(_DIR, exist_ok=True)
            tmp = _path(slug, language) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, _path(slug, language))
    except OSError as e:
        logger.warning("translation cache write failed: %s", e)


def clear() -> int:
    """Delete all cached translations. Returns count removed."""
    if not os.path.isdir(_DIR):
        return 0
    n = 0
    for name in os.listdir(_DIR):
        if name.endswith(".json"):
            try:
                os.remove(os.path.join(_DIR, name)); n += 1
            except OSError:
                pass
    return n


# ---- Content-hash line cache (shared translation layer) -----------------
# Caches translations keyed by a hash of the source text + language, so any
# string translated once (in the explainer OR the chatbot) is instant forever
# after. Stored in one JSON file per language for compactness.
import hashlib  # noqa: E402
import json as _json  # noqa: E402

_LINE_DIR = os.path.join(_DIR, "_lines")


def _line_path(language: str) -> str:
    safe = "".join(c for c in language if c.isalnum() or c in "-_") or "xx"
    return os.path.join(_LINE_DIR, f"{safe}.json")


_line_cache = {}  # language -> {hash: translation}


def _load_lines(language: str) -> dict:
    if language in _line_cache:
        return _line_cache[language]
    d = {}
    p = _line_path(language)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                d = _json.load(f)
        except (OSError, ValueError):
            d = {}
    _line_cache[language] = d
    return d


def line_get(text: str, language: str):
    d = _load_lines(language)
    return d.get(hashlib.sha1(text.encode("utf-8")).hexdigest())


def line_put_many(pairs, language: str) -> None:
    """pairs: iterable of (source_text, translation)."""
    d = _load_lines(language)
    for src, tr in pairs:
        d[hashlib.sha1(src.encode("utf-8")).hexdigest()] = tr
    try:
        with _lock:
            os.makedirs(_LINE_DIR, exist_ok=True)
            tmp = _line_path(language) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                _json.dump(d, f, ensure_ascii=False)
            os.replace(tmp, _line_path(language))
    except OSError as e:
        logger.warning("line cache write failed: %s", e)
