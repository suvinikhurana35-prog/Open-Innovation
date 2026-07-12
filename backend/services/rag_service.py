"""
Retrieval layer over ChromaDB.

Fixes from the review:
  * bug #4 ($contains): Chroma's metadata `where` filter does NOT support
    `$contains` (that operator only works in `where_document` over the body).
    The old get_policy_context used it on a metadata field and errored/returned
    nothing. We now retrieve broadly and filter for the name substring in
    Python.
  * bug #7 (silent errors): replaced bare print with structured logging.
  * bug #5 (fragile pre-built DB): added ensure_populated() so the server can
    rebuild the index on startup if the persisted collection is empty.
"""
import os
import hashlib
import logging
from typing import List, Optional

import config

logger = logging.getLogger("janniti.rag")

# ---------------------------------------------------------------------------
# LITE MODE (for free-tier deployment)
# Set DISABLE_RAG=1 to skip the ~400MB ML model + ChromaDB entirely. The app
# then serves every scheme from the curated KB (backend/data/kb/*.md), which is
# what it already does for all 18 schemes. Also auto-falls back if the heavy
# packages aren't installed, so the same code runs locally and on a small host.
# ---------------------------------------------------------------------------
_DISABLE_RAG = os.getenv("DISABLE_RAG", "").strip().lower() in ("1", "true", "yes")

_HEAVY_OK = False
if not _DISABLE_RAG:
    try:
        import chromadb
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer
        _HEAVY_OK = True
    except Exception as _e:  # missing packages / no memory
        logger.warning("RAG dependencies unavailable (%s) — running in lite mode.", _e)

if _DISABLE_RAG or not _HEAVY_OK:
    from services.rag_stub import _NoRAG
    rag_service = _NoRAG()
    logger.info("RAG lite mode: serving from curated KB only.")
else:
    pass  # real RAGService is defined below and instantiated at the bottom


class RAGService:
    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or config.CHROMA_PERSIST_DIR
        self._available = False
        self.collection = None
        self.embedder = None
        self.collection_name = "janNiti_policies"
        try:
            os.makedirs(self.persist_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            self.embedder = SentenceTransformer(config.EMBED_MODEL)
            self.collection = self._get_or_create_collection()
            self._available = True
            logger.info(f"RAGService ready (dir={self.persist_dir}, docs={self.count_documents()})")
        except Exception as e:
            logger.error(f"Failed to initialize RAGService: {e}. Running degraded.", exc_info=True)

    def _get_or_create_collection(self):
        try:
            return self.client.get_collection(self.collection_name)
        except Exception:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    @property
    def available(self) -> bool:
        return self._available

    def add_document(self, text: str, metadata: dict, doc_id: Optional[str] = None):
        if not self._available:
            return None
        if doc_id is None:
            doc_id = hashlib.md5(text.encode()).hexdigest()
        embedding = self.embedder.encode(text).tolist()
        self.collection.add(embeddings=[embedding], documents=[text],
                            metadatas=[metadata], ids=[doc_id])
        return doc_id

    def add_documents_batch(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        if not self._available:
            return
        embeddings = self.embedder.encode(documents).tolist()
        self.collection.add(embeddings=embeddings, documents=documents,
                            metadatas=metadatas, ids=ids)

    def search(self, query: str, top_k: int = 5, language: str = "en") -> List[dict]:
        if not self._available:
            return []
        try:
            query_embedding = self.embedder.encode(query).tolist()
            results = self.collection.query(query_embeddings=[query_embedding], n_results=top_k)
        except Exception as e:
            logger.error(f"search failed: {e}", exc_info=True)
            return []
        documents = []
        if results.get("documents") and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                documents.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0,
                })
        return documents

    def get_policy_context(self, policy_name: str) -> Optional[dict]:
        """Find the chunk whose `name` metadata best matches policy_name.

        FIX (bug #4): retrieve top vector matches, then filter by substring on
        the name field in Python — Chroma's metadata `where` can't do substring.
        """
        if not self._available:
            return None
        try:
            query_embedding = self.embedder.encode(policy_name).tolist()
            results = self.collection.query(query_embeddings=[query_embedding], n_results=10)
        except Exception as e:
            logger.error(f"get_policy_context failed: {e}", exc_info=True)
            return None
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
        needle = policy_name.lower().strip()
        # 1) exact/substring match on name metadata
        for i, doc in enumerate(docs):
            name = (metas[i].get("name", "") if i < len(metas) else "").lower()
            if needle and (needle in name or name in needle):
                return {"text": doc, "metadata": metas[i] if i < len(metas) else {}}
        # 2) otherwise fall back to the closest vector match
        if docs:
            return {"text": docs[0], "metadata": metas[0] if metas else {}}
        return None

    def count_documents(self) -> int:
        if not self._available:
            return 0
        try:
            return self.collection.count()
        except Exception:
            return 0

    def ensure_populated(self) -> int:
        """Rebuild the index from the PDFs if the collection is empty.

        Returns the document count after the check. Safe to call on every
        startup — it only ingests when count == 0.
        """
        if not self._available:
            logger.warning("ensure_populated: RAG unavailable, skipping.")
            return 0
        count = self.count_documents()
        if count > 0:
            logger.info(f"ensure_populated: collection already has {count} docs.")
            return count
        logger.info("ensure_populated: collection empty -> ingesting PDFs.")
        try:
            from scripts.ingest_pdfs import ingest_pdfs
            report = ingest_pdfs()
            logger.info(f"ensure_populated: ingested {report.get('total_chunks', 0)} chunks.")
        except Exception as e:
            logger.error(f"ensure_populated: ingest failed: {e}", exc_info=True)
        return self.count_documents()

    def delete_collection(self):
        if not self._available:
            return
        self.client.delete_collection(self.collection_name)
        self.collection = self._get_or_create_collection()


# Only build the real RAG when the heavy deps are present and not disabled.
# (In lite mode, rag_service was already set to the no-op stub above.)
if not _DISABLE_RAG and _HEAVY_OK:
    rag_service = RAGService()
