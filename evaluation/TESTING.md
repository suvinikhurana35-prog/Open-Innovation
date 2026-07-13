# JanNiti Evaluation Framework

Reproducible evaluation for the JanNiti platform. Every module imports the
**production** backend (`services.*`) read-only and writes results to
`outputs/` (CSV, LaTeX, Excel) and figures to `figures/` (PNG + PDF, 300 DPI).

## Requirements

From the repo's `backend/` (with your venv/interpreter that runs the backend):

```
pip install -r ../backend/requirements.txt
pip install rank_bm25 matplotlib scikit-learn openpyxl
```

The **retrieval** and **ablation-retrieval** stages need the vector index built:

```
cd ../backend
python main.py        # wait for "Vector store ready: 780 documents", then Ctrl+C
```

Everything else (grounding, multilingual, latency, functional, recommendation)
runs from the curated KB and needs no vector index. The **ungrounded** arm of the
grounding stage needs a working LLM key in `backend/.env`.

## Run everything

```
cd evaluation
python run_all.py
```

This runs all stages in order, then builds figures and tables, and prints:

```
=====================================
  Evaluation Complete
  Total Queries:  183
  Total Schemes:  18
  Total Runtime:  ...
  Output Folder:  .../evaluation/outputs
  Figures:        ... files
  Tables:         ... LaTeX tables
=====================================
```

## Run modules individually (each is standalone)

```
python utils.py                 # bootstrap check -> "curated schemes 18"
python metrics.py               # pure-metric assertions
python benchmark.py --verify    # corpus integrity (writes nothing)
python benchmark.py             # build datasets/benchmark.json + summary + figure
python retrieval_eval.py        # BM25 / Dense / Hybrid / JanNiti  (needs index)
python grounding_eval.py        # grounded vs ungrounded faithfulness
python multilingual_eval.py     # script correctness + numeric fidelity
python recommendation_eval.py   # Top-1 / Top-3 (Copeland over 153 pairs/profile)
python latency_eval.py          # avg / median / p95 / std per operation
python functional_eval.py       # per-feature pass rate
python ablation_eval.py         # assembles ablation table (run retrieval+grounding first)
python plotting.py              # figures from the metric CSVs
python tables.py                # Table I-VII as CSV + LaTeX + xlsx
```

## Outputs

`outputs/`: `retrieval_results.csv`, `retrieval_metrics.csv`,
`grounding_metrics.csv`, `multilingual_metrics.csv`, `recommendation_metrics.csv`,
`latency_metrics.csv`, `functional_metrics.csv`, `ablation_metrics.csv`,
`final_metrics.xlsx`, and `tableN_*.{csv,tex}`.

`figures/`: `retrieval_{precision,recall,mrr,ndcg,hit5}`, `multilingual`,
`recommendation`, `grounding`, `latency`, `ablation`, `overall_summary`,
`benchmark_distribution` — each as `.png` and `.pdf`.

## Metric definitions (for the paper)

- **Retrieval relevance is scheme-level**: a retrieved chunk is relevant iff its
  scheme is one of the query's `expected_schemes`. `total_relevant` is the number
  of corpus chunks belonging to those schemes. Report **Hit@5, MRR, NDCG@5**
  first; Precision@5 is bounded because each scheme has many chunks — state this.
- **BM25 and Hybrid are evaluation-only baselines** implemented in
  `retrieval_eval.py`; they are not JanNiti components. Dense = production
  `rag_service.search`; JanNiti = production `ai_service._retrieve_scheme_context`.
- **Faithfulness** uses the production inference-time scorer (token overlap with
  numeric-consistency penalty; support threshold 0.45).
- **Script correctness**: fraction of alphabetic characters in the target script
  (Devanagari/Bengali/Tamil), threshold 0.6. **Numeric fidelity**: fraction of the
  English answer's numeric facts preserved in the translated answer.
- **Recommendation** ranks all 18 schemes per profile by Copeland score over the
  pairwise `recommend_for_profile`; Top-1/Top-3 against a labelled acceptable set
  (`datasets/profiles.json`). Deterministic, no API cost.

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| `curated schemes 0` | `backend/data/kb/` missing | restore the 18 `.md` files |
| retrieval stage `RAG unavailable` | chromadb/embedder missing or index empty | full install + `python main.py` once |
| grounding shows only grounded row | no reachable LLM | put a valid key in `backend/.env` |
| `int has no len()` on ingest | stale Chroma index vs pinned chromadb | delete `backend/data/chroma` and rebuild |
| retrieval P@5 looks low | many chunks per scheme | lead with Hit@5/NDCG@5; note the ceiling |
