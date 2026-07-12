"""
Lightweight RAG stub for deployment (free-tier friendly).

The real rag_service loads a ~400MB sentence-transformer model + ChromaDB,
which exceeds free-tier memory (512MB). Since JanNiti now serves every scheme
from the curated knowledge base (backend/data/kb/*.md), RAG is only a rarely-used
fallback. This stub provides the same interface but returns no results, so the
app runs on a small server with no ML dependencies.

Enabled by setting  DISABLE_RAG=1  in the environment (see rag_service.py).
"""
import logging

logger = logging.getLogger("janniti.rag")


class _NoRAG:
    """Same interface as RAGService, but does nothing."""

    available = False

    def search(self, query, top_k=5, language="en"):
        return []

    def add_document(self, *args, **kwargs):
        return None

    def count_documents(self):
        return 0

    def ensure_populated(self):
        logger.info("RAG disabled (lite mode) — serving from curated KB only.")
        return 0
