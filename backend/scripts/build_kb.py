"""
Build the JanNiti knowledge base: a clean, OCR-readable text layer that sits
between the scheme PDFs and the LLM.

For every PDF:
  1. Extract text with pdfplumber (fast, accurate for digital PDFs).
  2. For any page that yields no/▏thin text (scanned/image page), fall back to
     OCR (pdftoppm -> tesseract) so nothing is silently lost.
  3. Normalise whitespace, de-hyphenate line breaks.
Duplicate files (e.g. "scheme.pdf" and "scheme_1.pdf") are detected by content
and written once. Output: one clean .txt per scheme + a manifest.json.

This is what makes retrieval reliable: the app ingests these .txt files, so a
PDF that won't parse at runtime can never break the search again.
"""
import os, re, sys, json, hashlib, subprocess, tempfile, glob

import pdfplumber

OCR_MIN_CHARS = 40  # below this on a page -> treat as scanned, OCR it


def _ocr_page(pdf_path: str, page_index: int) -> str:
    """Render one page to an image and OCR it with tesseract."""
    try:
        with tempfile.TemporaryDirectory() as td:
            base = os.path.join(td, "pg")
            subprocess.run(["pdftoppm", "-png", "-r", "300", "-f", str(page_index + 1),
                            "-l", str(page_index + 1), pdf_path, base],
                           check=True, capture_output=True, timeout=120)
            imgs = sorted(glob.glob(base + "*"))
            if not imgs:
                return ""
            out = subprocess.run(["tesseract", imgs[0], "stdout", "-l", "eng"],
                                 capture_output=True, text=True, timeout=120)
            return out.stdout or ""
    except Exception as e:
        print(f"    [ocr] page {page_index+1} failed: {e}")
        return ""


def _clean(text: str) -> str:
    text = re.sub(r"\(cid:\d+\)", "", text)       # drop any residual undecodable glyphs
    text = text.replace("\u00ad", "")            # soft hyphens
    text = re.sub(r"-\n(\w)", r"\1", text)        # de-hyphenate across line breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _garbled(t: str) -> bool:
    """True if the page text is dominated by undecodable (cid:N) glyphs."""
    return t.count("(cid:") >= 5


def extract_pdf(pdf_path: str) -> str:
    parts, ocr_pages = [], 0
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            t = page.extract_text() or ""
            if len(t.strip()) < OCR_MIN_CHARS or _garbled(t):   # scanned OR garbled -> OCR
                ocr = _ocr_page(pdf_path, i)
                if len(ocr.strip()) > 40 and ocr.count("(cid:") == 0:
                    t = ocr
                    ocr_pages += 1
            parts.append(t)
    if ocr_pages:
        print(f"    [ocr] recovered {ocr_pages} scanned/garbled page(s)")
    return _clean("\n".join(parts))


def scheme_name(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename))[0]
    base = re.sub(r"_\d+$", "", base)             # drop _1 duplicate suffix
    base = base.replace("_", " ").replace("-", " ")
    return " ".join(w.capitalize() for w in base.split())


def build(src_dir: str, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    pdfs = sorted(glob.glob(os.path.join(src_dir, "*.pdf")))
    seen_hashes, manifest = {}, []
    for p in pdfs:
        name = scheme_name(p)
        print(f"- {os.path.basename(p)}  ->  {name}")
        text = extract_pdf(p)
        h = hashlib.md5(text.encode()).hexdigest()
        if h in seen_hashes:
            print(f"    duplicate of '{seen_hashes[h]}', skipped")
            continue
        seen_hashes[h] = name
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        out_path = os.path.join(out_dir, slug + ".txt")
        header = f"SCHEME: {name}\nSOURCE FILE: {os.path.basename(p)}\n{'='*60}\n\n"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(header + text + "\n")
        manifest.append({"scheme": name, "slug": slug, "file": slug + ".txt",
                         "chars": len(text), "source_pdf": os.path.basename(p)})
        print(f"    wrote {slug}.txt ({len(text)} chars)")
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\nKnowledge base: {len(manifest)} unique schemes -> {out_dir}")
    return {"schemes": manifest, "count": len(manifest)}


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "."
    out = sys.argv[2] if len(sys.argv) > 2 else "knowledge_base"
    build(src, out)
