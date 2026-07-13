"""
Pure metric functions for the JanNiti evaluation. No I/O, no plotting, no
backend imports, no side effects. The caller reduces a ranked result list to a
list of booleans (relevance in rank order) before calling any retrieval metric,
so nothing JanNiti-specific crosses this boundary.
"""
import math
import statistics


def precision_at_k(rel, k):
    if k <= 0:
        raise ValueError("k must be positive")
    return sum(1 for r in rel[:k] if r) / k


def recall_at_k(rel, k, total_relevant):
    if k <= 0:
        raise ValueError("k must be positive")
    if total_relevant <= 0:
        return 0.0
    return sum(1 for r in rel[:k] if r) / total_relevant


def hit_at_k(rel, k):
    if k <= 0:
        raise ValueError("k must be positive")
    return 1.0 if any(rel[:k]) else 0.0


def mrr(rel):
    return next((1.0 / rank for rank, r in enumerate(rel, 1) if r), 0.0)


def ndcg_at_k(rel, k, total_relevant):
    """Binary-gain NDCG. IDCG sums over min(total_relevant, k) ideal positions,
    so a query with fewer relevant items than k still caps NDCG at 1.0."""
    if k <= 0:
        raise ValueError("k must be positive")
    dcg = sum(1.0 / math.log2(i + 2) for i, r in enumerate(rel[:k]) if r)
    ideal = min(total_relevant, k)
    if ideal <= 0:
        return 0.0
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal))
    return dcg / idcg if idcg else 0.0


def rate(count, total):
    """Guarded fraction as a percentage-friendly ratio (0..1)."""
    return (count / total) if total else 0.0


def summarize(values):
    """mean / median / population-std / p95 / n for a list of numbers."""
    if not values:
        return {"mean": 0.0, "median": 0.0, "std": 0.0, "p95": 0.0, "n": 0}
    vals = sorted(values)
    idx = min(len(vals) - 1, int(round(0.95 * (len(vals) - 1))))
    return {
        "mean": statistics.fmean(vals),
        "median": statistics.median(vals),
        "std": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
        "p95": vals[idx],
        "n": len(vals),
    }


def _self_test():
    rel = [False, True, False, True, False]
    assert abs(precision_at_k(rel, 5) - 0.4) < 1e-9
    assert abs(recall_at_k(rel, 5, 2) - 1.0) < 1e-9
    assert hit_at_k(rel, 5) == 1.0
    assert abs(mrr(rel) - 0.5) < 1e-9
    assert abs(ndcg_at_k(rel, 5, 2) - 0.6509) < 1e-3
    assert hit_at_k([False, False], 2) == 0.0
    assert mrr([False, False]) == 0.0
    s = summarize([1, 2, 3, 4])
    assert s["mean"] == 2.5 and s["n"] == 4
    print("[OK] All metric assertions passed.")
    print("Worked example rel=[0,1,0,1,0], R=2:")
    print(f"  P@5={precision_at_k(rel,5):.4f}  R@5={recall_at_k(rel,5,2):.4f}  "
          f"Hit@5={hit_at_k(rel,5):.4f}  MRR={mrr(rel):.4f}  NDCG@5={ndcg_at_k(rel,5,2):.4f}")


if __name__ == "__main__":
    _self_test()
