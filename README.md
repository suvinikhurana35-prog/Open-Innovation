# JanNiti — AI Policy Literacy Assistant for Indian Government Schemes

JanNiti explains 18 Indian government welfare schemes in plain language, in four
languages (English, Hindi, Bengali, Tamil). It combines a curated knowledge base
with an LLM to give grounded, non-hallucinated answers.

## Features
- **Scheme Explainer** — what it is, benefits, eligibility, required documents,
  how to apply, deadlines, and hidden conditions for each scheme
- **AI Chatbot** — grounded, point-to-point answers drawn only from official records
- **Compare** — side-by-side comparison of any two schemes
- **Accessibility panel** (Ctrl+F2) — text size, spacing, dyslexia mode, ADHD mode,
  invert colours, and more
- **4 languages** with a translation cache for fast responses

## Architecture
```
frontend/   Next.js 14 (React, Tailwind)  ->  deployed on Vercel
backend/    FastAPI (Python 3.11)         ->  deployed on Render
            services/kb_service.py        curated knowledge base (18 .md files)
            services/rag_service.py       ChromaDB + sentence-transformers (RAG)
            services/ai_service.py        LLM orchestration + translation layer
            data/kb/                      the 18 curated scheme records
            data/translations/            translation + comparison cache
            data/chroma/                  vector store for RAG
```

### How answers are produced (grounding)
1. The query is matched to one of the 18 schemes (`kb_service`).
2. If matched, the answer is built **directly from the curated record** — no
   vector search, no hallucination, instant.
3. If not matched, it falls back to **RAG** (vector search over the source PDFs).
4. Non-English answers are translated once, then cached.

## Running locally (full version, RAG enabled)

Backend:
```bash
cd backend
pip install -r requirements.txt
# create backend/.env  (see .env.example) with your ANTHROPIC_API_KEY
uvicorn main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:3000

### Optional: make every language instant
```bash
cd backend
python -m scripts.precache_all
```
Pre-translates all schemes and common comparisons into the cache.

## Deployment (free tier)
See `DEPLOY_GUIDE.md`.

**Lite mode:** the deployed backend sets `DISABLE_RAG=1` and installs
`requirements-lite.txt`. This skips the ~450MB embedding model (which does not
fit in a 512MB free instance). All 18 schemes are still served in full from the
curated knowledge base — the app behaves identically and is in fact faster.

RAG remains fully available when running locally, which is where model
evaluation should be performed.

## Research / evaluation notes
- **Do not benchmark latency against the free-tier live link.** Render's free
  instances sleep after ~15 minutes of inactivity; the next request takes ~50s
  to wake. Benchmark locally.
- **RAG evaluation must be done locally** (`DISABLE_RAG` unset, full
  `requirements.txt`), because the deployed instance runs KB-only.
- The translation and comparison caches live in `backend/data/translations/`.
  Delete that folder to measure uncached (cold) response times.

## Disclaimer
JanNiti provides AI-generated guidance based on publicly available government
records. It is not an official government service. Always verify details on the
official scheme portal before applying.
