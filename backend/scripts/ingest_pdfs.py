"""
Ingest the scheme PDFs in backend/data/chroma/policies/ into Chroma.

Run standalone:   python scripts/ingest_pdfs.py
Or imported:      called by RAGService.ensure_populated() on startup.
"""
import os
import sys
import json
import logging
import re
import glob

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.rag_service import rag_service

logger = logging.getLogger("janniti.ingest")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "data", "chroma", "policies")
KB_DIR = os.path.join(BASE_DIR, "data", "knowledge_base")  # clean OCR text layer
MD_DIR = os.path.join(BASE_DIR, "data", "knowledge_base_md")  # structured Markdown layer


def filename_to_scheme_name(filename: str) -> str:
    """'kissan samman nidhi.pdf' -> 'Kissan Samman Nidhi'. Single source of
    truth for the real scheme names shown in search/dashboard (bug #6)."""
    base = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ")
    return " ".join(w.capitalize() for w in base.split() if w)


def list_known_schemes() -> list:
    """Scheme names actually available (used by data_service search/dashboard)."""
    man = os.path.join(KB_DIR, "manifest.json")
    if os.path.exists(man):
        try:
            with open(man, encoding="utf-8") as f:
                return sorted(m["scheme"] for m in json.load(f))
        except Exception:
            pass
    if os.path.isdir(KB_DIR) and glob.glob(os.path.join(KB_DIR, "*.txt")):
        return sorted(filename_to_scheme_name(os.path.basename(p)) for p in glob.glob(os.path.join(KB_DIR, "*.txt")))
    if not os.path.exists(PDF_DIR):
        return []
    return sorted(filename_to_scheme_name(f) for f in os.listdir(PDF_DIR) if f.endswith(".pdf"))


def _parse_frontmatter(raw: str):
    meta, body = {}, raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            fm = raw[3:end]
            body = raw[end+4:].lstrip()
            for line in fm.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
    return meta, body


def ingest_markdown_kb() -> dict:
    """Ingest structured Markdown, chunked per `## section` so retrieval lands on
    the right section (benefits/eligibility/etc). Falls back to size-splitting only
    for very long sections. Attaches scheme name + section + tags as metadata."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
    files = sorted(glob.glob(os.path.join(MD_DIR, "*.md")))
    total = 0
    for fp in files:
        raw = open(fp, "r", encoding="utf-8").read()
        meta, body = _parse_frontmatter(raw)
        name = meta.get("scheme_name") or filename_to_scheme_name(os.path.basename(fp))
        tags = meta.get("tags", "")
        source = meta.get("source_pdf", os.path.basename(fp))
        # split into sections on H2 headings
        parts = re.split(r"\n##\s+", body)
        sections = []
        for i, part in enumerate(parts):
            sec = part.strip()
            if not sec:
                continue
            title = "Overview" if i == 0 else sec.splitlines()[0].strip()
            sections.append((title, sec))
        docs, metas, ids = [], [], []
        for si, (title, sec) in enumerate(sections):
            pieces = splitter.split_text(sec) if len(sec) > 1300 else [sec]
            for pi, piece in enumerate(pieces):
                docs.append(f"{name} — {title}\n{piece}")
                metas.append({"source": source, "name": name, "section": title,
                              "tags": tags, "type": "scheme_md"})
                ids.append(f"{os.path.basename(fp)}_{si}_{pi}")
        rag_service.add_documents_batch(documents=docs, metadatas=metas, ids=ids)
        total += len(docs)
        logger.info(f"MD: {len(docs)} chunks for '{name}'")
    logger.info(f"Markdown KB ingest complete: {total} chunks from {len(files)} schemes")
    return {"total_chunks": total, "processed": [], "skipped_scanned": []}


def ingest_text_kb() -> dict:
    """Ingest the clean, OCR-verified text layer in data/knowledge_base/.

    This is the reliable path: text is pre-extracted (with OCR) by
    scripts/build_kb.py, so runtime ingestion never depends on parsing a
    tricky PDF. Each .txt is one scheme; we keep the scheme name from the
    file header so search/citations show the right name.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    files = sorted(glob.glob(os.path.join(KB_DIR, "*.txt")))
    total, processed = 0, []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            raw = f.read()
        name = filename_to_scheme_name(os.path.basename(fp))
        if raw.startswith("SCHEME:"):
            name = raw.split("\n", 1)[0].replace("SCHEME:", "").strip() or name
            body = raw.split("=" * 10, 1)[-1].lstrip("=").strip()
        else:
            body = raw
        chunks = splitter.split_text(body)
        metas = [{"source": os.path.basename(fp), "name": name, "type": "scheme_text"} for _ in chunks]
        ids = [f"{os.path.basename(fp)}_{i}" for i in range(len(chunks))]
        rag_service.add_documents_batch(documents=chunks, metadatas=metas, ids=ids)
        total += len(chunks); processed.append(name)
        logger.info(f"KB: {len(chunks)} chunks for '{name}'")
    logger.info(f"Knowledge-base ingest complete: {total} chunks from {len(files)} schemes")
    return {"total_chunks": total, "processed": processed, "skipped_scanned": []}


def ingest_pdfs() -> dict:
    """Returns {'total_chunks', 'processed', 'skipped_scanned'}.

    LayoutLMv3 note: files with no extractable text (scanned/image PDFs) are
    tracked in 'skipped_scanned' rather than silently dropped — that list being
    non-empty is the real trigger for adding OCR/LayoutLMv3. All 18 current PDFs
    extract fine, so there's nothing for it to do yet.
    """
    # Prefer structured Markdown layer (section-aware) > clean text > PDFs.
    if os.path.isdir(MD_DIR) and glob.glob(os.path.join(MD_DIR, "*.md")):
        logger.info("Using structured Markdown knowledge base for ingestion.")
        return ingest_markdown_kb()
    if os.path.isdir(KB_DIR) and glob.glob(os.path.join(KB_DIR, "*.txt")):
        logger.info("Using clean knowledge-base text layer for ingestion.")
        return ingest_text_kb()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    total_chunks, processed, skipped = 0, [], []

    if not os.path.exists(PDF_DIR):
        logger.error(f"PDF folder not found: {PDF_DIR}")
        return {"total_chunks": 0, "processed": [], "skipped_scanned": []}

    pdf_files = sorted(f for f in os.listdir(PDF_DIR) if f.endswith(".pdf"))
    if not pdf_files:
        logger.warning(f"No PDFs in {PDF_DIR}.")
        return {"total_chunks": 0, "processed": [], "skipped_scanned": []}

    logger.info(f"Found {len(pdf_files)} PDFs in {PDF_DIR}")
    for pdf_file in pdf_files:
        path = os.path.join(PDF_DIR, pdf_file)
        name = filename_to_scheme_name(pdf_file)
        try:
            reader = PdfReader(path)
            text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
            if not text.strip():
                logger.warning(f"Skipping {pdf_file}: no extractable text (needs OCR/LayoutLMv3).")
                skipped.append(pdf_file)
                continue
            chunks = splitter.split_text(text)
            metas = [{"source": pdf_file, "name": name, "type": "policy_pdf"} for _ in chunks]
            ids = [f"{pdf_file}_{i}" for i in range(len(chunks))]
            rag_service.add_documents_batch(documents=chunks, metadatas=metas, ids=ids)
            total_chunks += len(chunks)
            processed.append(pdf_file)
            logger.info(f"Added {len(chunks)} chunks for {pdf_file} ('{name}')")
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {e}", exc_info=True)

    logger.info(f"Ingestion complete: {total_chunks} chunks, total docs now "
                f"{rag_service.count_documents()}")
    if skipped:
        logger.warning(f"{len(skipped)} file(s) skipped as likely scanned: {skipped}")
    return {"total_chunks": total_chunks, "processed": processed, "skipped_scanned": skipped}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    ingest_pdfs()
