"""
Pre-cache EVERYTHING for instant fetching — explainer + comparisons.

Run this once (with your AI key set). After it finishes:
  * Every scheme in every language loads instantly in the EXPLAINER (and chat).
  * Common scheme-vs-scheme COMPARISONS load instantly in every language.

Run from the backend folder:
    cd backend
    py -3.11 -m scripts.precache_all         (or: python -m scripts.precache_all)

Options:
    --langs en hi bn ta      languages to cover (default: your 4)
    --compare-all            compare EVERY pair (18x18) — slow/expensive.
                             Default only compares each scheme with PM-KISAN +
                             a few common pairs (fast, covers typical use).
    --force                  redo even if already cached.

Safe to re-run: already-cached items are skipped.
"""
import argparse
import itertools
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import kb_service, translation_cache          # noqa: E402
from services.ai_service import _translate_explainer_dict, compare_schemes  # noqa: E402

# your 4 languages (English needs no translation but we still 'touch' it)
DEFAULT_LANGS = ["hi", "bn", "ta"]


def precache_explainer(langs, force):
    schemes = kb_service.all_schemes()
    total = len(schemes) * len(langs)
    done = ok = skip = fail = 0
    print(f"\n== EXPLAINER: {len(schemes)} schemes x {len(langs)} languages ==")
    for s in schemes:
        base = kb_service.explainer_dict(s)
        for lang in langs:
            done += 1
            if not force and translation_cache.get(s.slug, lang):
                skip += 1
                print(f"[{done}/{total}] skip  {s.slug}/{lang}")
                continue
            data, good = _translate_explainer_dict(base, lang)
            if good:
                translation_cache.put(s.slug, lang, data)
                ok += 1
                print(f"[{done}/{total}] OK    {s.slug}/{lang}")
            else:
                fail += 1
                print(f"[{done}/{total}] FAIL  {s.slug}/{lang}")
    print(f"Explainer: translated={ok} skipped={skip} failed={fail}")


def precache_compare(langs, compare_all, force):
    schemes = kb_service.all_schemes()
    names = [s.title for s in schemes]
    if compare_all:
        pairs = list(itertools.combinations(names, 2))
    else:
        # each scheme vs PM-KISAN + a few common cross-pairs
        anchor = next((s.title for s in schemes if s.slug == "pm-kisan"), names[0])
        pairs = [(anchor, n) for n in names if n != anchor]
        commons = [("kisan-credit-card", "mudra"), ("jeevan-jyoti-bima", "suraksha-bima"),
                   ("atal-pension", "jan-dhan"), ("skill-loan", "kaushal-vikas")]
        slug2title = {s.slug: s.title for s in schemes}
        for a, b in commons:
            if a in slug2title and b in slug2title:
                pairs.append((slug2title[a], slug2title[b]))
    # english + the languages
    all_langs = ["en"] + [l for l in langs if l != "en"]
    total = len(pairs) * len(all_langs)
    done = ok = skip = fail = 0
    print(f"\n== COMPARE: {len(pairs)} pairs x {len(all_langs)} languages ==")
    for s1, s2 in pairs:
        for lang in all_langs:
            done += 1
            # compare_schemes caches internally; force clears would need cache edit,
            # so we just call it — it returns cached instantly if present.
            try:
                res = compare_schemes(s1, s2, lang)
                if res and res.get("comparisons"):
                    ok += 1
                    print(f"[{done}/{total}] OK    {s1[:18]} vs {s2[:18]} / {lang}")
                else:
                    fail += 1
                    print(f"[{done}/{total}] FAIL  {s1[:18]} vs {s2[:18]} / {lang}")
            except Exception as e:
                fail += 1
                print(f"[{done}/{total}] ERR   {s1[:18]} vs {s2[:18]} / {lang}: {e}")
    print(f"Compare: ok={ok} failed={fail}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", nargs="*", default=DEFAULT_LANGS)
    ap.add_argument("--compare-all", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--skip-explainer", action="store_true")
    ap.add_argument("--skip-compare", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    if not args.skip_explainer:
        precache_explainer(args.langs, args.force)
    if not args.skip_compare:
        precache_compare(args.langs, args.compare_all, args.force)
    print(f"\nAll done in {time.time() - t0:.0f}s. Explainer + compare are now fast in all languages.")
    print("Re-run this anytime to fill anything that failed (usually rate limits).")


if __name__ == "__main__":
    main()
