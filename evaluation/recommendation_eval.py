"""
Recommendation evaluation.

The production recommend_for_profile is a pairwise chooser (better of two
schemes for a profile). We compose it over all C(18,2) pairs per profile and
rank the 18 schemes by Copeland score (number of pairwise wins), giving a full
ranking without any new backend endpoint. From that ranking we report Top-1 and
Top-3 accuracy, plus precision/recall against the labelled acceptable set.

  python recommendation_eval.py
Deterministic (the recommender is rule-based), so no API budget is required.
"""
import itertools
from collections import defaultdict

from utils import HERE, OUTPUTS, ensure_dirs, read_json, write_csv
from services import ai_service, kb_service

PROFILES = f"{HERE}/datasets/profiles.json"


def _title_to_slug():
    return {s.title: s.slug for s in kb_service.all_schemes()}


def copeland_rank(profile, titles, t2s):
    wins = defaultdict(int)
    for a, b in itertools.combinations(titles, 2):
        rec = ai_service.recommend_for_profile(a, b, profile, "en")
        chosen = rec.get("recommended_scheme", "")
        # map chosen title -> slug (chosen is a localized/plain title)
        if chosen == a:
            wins[t2s[a]] += 1
        elif chosen == b:
            wins[t2s[b]] += 1
        else:
            # fall back: match by containment
            cs = chosen.lower()
            if a.lower() in cs or cs in a.lower():
                wins[t2s[a]] += 1
            elif b.lower() in cs or cs in b.lower():
                wins[t2s[b]] += 1
    return [slug for slug, _ in sorted(wins.items(), key=lambda x: -x[1])]


def evaluate():
    ensure_dirs()
    profiles = read_json(PROFILES)
    schemes = kb_service.all_schemes()
    titles = [s.title for s in schemes]
    t2s = _title_to_slug()
    print(f"[INFO] Recommendation evaluation over {len(profiles)} profiles "
          f"({len(titles)} schemes, {len(titles)*(len(titles)-1)//2} pairs each).")

    rows = []
    top1 = top3 = prec_num = prec_den = rec_num = rec_den = 0
    for p in profiles:
        ranking = copeland_rank(p["profile"], titles, t2s)
        top = ranking[:3]
        acc = set(p["acceptable"])
        is_top1 = ranking[0] in acc if ranking else False
        is_top3 = p["gold"] in top
        top1 += int(is_top1)
        top3 += int(is_top3)
        # precision@3 / recall@3 against acceptable set
        hit = len(set(top) & acc)
        prec_num += hit; prec_den += 3
        rec_num += hit; rec_den += len(acc)
        rows.append({"profile": p["id"], "gold": p["gold"],
                     "top1": ranking[0] if ranking else "",
                     "top3": ",".join(top),
                     "top1_correct": int(is_top1), "top3_correct": int(is_top3)})

    write_csv(f"{OUTPUTS}/recommendation_results.csv", rows)
    n = len(profiles)
    metric_rows = [{
        "metric": "Top-1 accuracy", "value": round(100 * top1 / n, 2),
    }, {
        "metric": "Top-3 accuracy", "value": round(100 * top3 / n, 2),
    }, {
        "metric": "Precision@3", "value": round(100 * prec_num / prec_den, 2),
    }, {
        "metric": "Recall@3", "value": round(100 * rec_num / rec_den, 2),
    }]
    write_csv(f"{OUTPUTS}/recommendation_metrics.csv", metric_rows)

    print("\n[RESULT] Recommendation:")
    for r in metric_rows:
        print(f"  {r['metric']:16s} {r['value']:.1f}%")
    print("[INFO] Recommendation evaluation done.")


if __name__ == "__main__":
    evaluate()
