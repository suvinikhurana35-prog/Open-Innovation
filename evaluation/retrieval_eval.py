"""
Retrieval evaluation: BM25, Dense, Hybrid (RRF), and JanNiti (section-aware),
scored with Precision@5, Recall@5, MRR, NDCG@5, Hit@5.

Relevance is scheme-level (as approved): a retrieved chunk is relevant iff its
scheme matches ANY scheme in the query's `expected_schemes`. total_relevant is
the number of chunks in the corpus belonging to those schemes, counted once up
front from the ChromaDB metadata.

BM25 and Hybrid are evaluation-only baselines implemented here; they are NOT
JanNiti components. Dense = production rag_service.search; JanNiti =
production ai_service._retrieve_scheme_context.

  python retrieval_eval.py
Requires chromadb + sentence-transformers installed and the index populated
(python main.py once -> "Vector store ready: 780 documents").
"""
import re
import sys
from collections import Counter, defaultdict

from utils import DATASETS, OUTPUTS, ensure_dirs, read_json, write_csv
import metrics
from services.rag_service import rag_service
from services import ai_service

K = 5


def normalize(name):
    return re.sub(r"\s*\([^)]*\)\s*$", "", name or "").strip().lower()


def _load_corpus():
    """Pull every chunk (text + scheme name) from the live collection."""
    got = rag_service.collection.get(include=["documents", "metadatas"])
    docs = got["documents"]
    metas = got["metadatas"]
    schemes = [normalize((m or {}).get("name", "")) for m in metas]
    return docs, schemes


def _tokens(text):
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _bm25_ranker(docs):
    from rank_bm25 import BM25Okapi
    corpus_tokens = [_tokens(d) for d in docs]
    bm25 = BM25Okapi(corpus_tokens)

    def rank(query, k):
        scores = bm25.get_scores(_tokens(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return order[:k]
    return rank


def _dense_rank(query, k):
    """Return corpus-independent chunk identities as (scheme, text-prefix)."""
    res = rag_service.search(query, top_k=k)
    return [(normalize((r.get("metadata") or {}).get("name", "")), (r.get("text") or "")[:80]) for r in res]


def _janniti_rank(query, k):
    res = ai_service._retrieve_scheme_context(query)[:k]
    return [(normalize((r.get("metadata") or {}).get("name", "")), (r.get("text") or "")[:80]) for r in res]


def _rrf(rank_lists, k, c=60):
    """Reciprocal-rank fusion of several ranked identity lists."""
    score = defaultdict(float)
    for lst in rank_lists:
        for rank, item in enumerate(lst, 1):
            score[item] += 1.0 / (c + rank)
    fused = sorted(score, key=lambda x: score[x], reverse=True)
    return fused[:k]


def evaluate():
    ensure_dirs()
    bench = read_json(f"{DATASETS}/benchmark.json")
    print(f"[INFO] Loaded {len(bench)} benchmark queries.")
    print("[INFO] Loading corpus from ChromaDB...")
    docs, doc_schemes = _load_corpus()
    if not docs:
        sys.exit("[ERROR] Corpus is empty. Run `python main.py` once to build the index.")
    print(f"[INFO] Corpus: {len(docs)} chunks.")
    scheme_chunk_counts = Counter(doc_schemes)

    print("[INFO] Building BM25 index...")
    bm25_rank = _bm25_ranker(docs)
    # BM25 returns corpus indices -> convert to (scheme, text-prefix) identity
    bm25_id = [(doc_schemes[i], docs[i][:80]) for i in range(len(docs))]

    per_query_rows, agg = [], defaultdict(lambda: defaultdict(list))
    systems = ["BM25", "Dense", "Hybrid", "JanNiti"]

    for q in bench:
        gold = {normalize(s) for s in q["expected_schemes"]}
        total_rel = sum(scheme_chunk_counts.get(g, 0) for g in gold)
        if total_rel == 0:
            continue

        bm_idx = bm25_rank(q["query"], K)
        bm_ids = [bm25_id[i] for i in bm_idx]
        dn_ids = _dense_rank(q["query"], K)
        jn_ids = _janniti_rank(q["query"], K)
        hy_ids = _rrf([[bm25_id[i] for i in bm25_rank(q["query"], 20)], _dense_rank(q["query"], 20)], K)

        ranked = {"BM25": bm_ids, "Dense": dn_ids, "Hybrid": hy_ids, "JanNiti": jn_ids}
        for sysname in systems:
            rel = [1 if ident[0] in gold else 0 for ident in ranked[sysname]]
            row = {
                "id": q["id"], "intent": q["intent"], "system": sysname,
                "precision@5": round(metrics.precision_at_k(rel, K), 4),
                "recall@5": round(metrics.recall_at_k(rel, K, total_rel), 4),
                "mrr": round(metrics.mrr(rel), 4),
                "ndcg@5": round(metrics.ndcg_at_k(rel, K, total_rel), 4),
                "hit@5": round(metrics.hit_at_k(rel, K), 4),
            }
            per_query_rows.append(row)
            for m in ("precision@5", "recall@5", "mrr", "ndcg@5", "hit@5"):
                agg[sysname][m].append(row[m])
                agg[f"{sysname}|{q['intent']}"][m].append(row[m])

    write_csv(f"{OUTPUTS}/retrieval_results.csv", per_query_rows)
    print(f"[INFO] Wrote {len(per_query_rows)} rows to outputs/retrieval_results.csv")

    metric_rows = []
    for sysname in systems:
        r = {"system": sysname, "scope": "overall"}
        for m in ("precision@5", "recall@5", "mrr", "ndcg@5", "hit@5"):
            vals = agg[sysname][m]
            r[m] = round(sum(vals) / len(vals), 4) if vals else 0.0
        metric_rows.append(r)
    # per-intent
    intents = sorted({q["intent"] for q in bench})
    for sysname in systems:
        for intent in intents:
            key = f"{sysname}|{intent}"
            if not agg[key]["hit@5"]:
                continue
            r = {"system": sysname, "scope": intent}
            for m in ("precision@5", "recall@5", "mrr", "ndcg@5", "hit@5"):
                vals = agg[key][m]
                r[m] = round(sum(vals) / len(vals), 4) if vals else 0.0
            metric_rows.append(r)
    write_csv(f"{OUTPUTS}/retrieval_metrics.csv", metric_rows)
    print("[INFO] Wrote outputs/retrieval_metrics.csv")

    print("\n[RESULT] Overall retrieval (mean over queries):")
    print(f"  {'system':10s} {'P@5':>7s} {'R@5':>7s} {'MRR':>7s} {'NDCG@5':>7s} {'Hit@5':>7s}")
    for r in metric_rows:
        if r["scope"] == "overall":
            print(f"  {r['system']:10s} {r['precision@5']:7.3f} {r['recall@5']:7.3f} "
                  f"{r['mrr']:7.3f} {r['ndcg@5']:7.3f} {r['hit@5']:7.3f}")
    print("[INFO] Retrieval evaluation done.")


if __name__ == "__main__":
    if not rag_service.available:
        sys.exit("[ERROR] RAG unavailable. Install chromadb + sentence-transformers "
                 "and run `python main.py` once to populate the index.")
    evaluate()
