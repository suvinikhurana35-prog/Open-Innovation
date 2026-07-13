"""
Shared helpers for the JanNiti evaluation framework.

Locates the backend and puts it on sys.path so every eval module can import the
PRODUCTION services (services.rag_service, services.ai_service, services.kb_service,
services.faithfulness) instead of re-implementing them. Also fixes the canonical
output paths and the small IO helpers used across modules.
"""
import os
import sys
import csv
import json

# ---- paths -------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                     # repo root (parent of evaluation/)
BACKEND = os.path.join(ROOT, "backend")
DATASETS = os.path.join(HERE, "datasets")
OUTPUTS = os.path.join(HERE, "outputs")
FIGURES = os.path.join(HERE, "figures")

LANGUAGES = ("en", "hi", "bn", "ta")
LANG_NAME = {"en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil"}

# ---- backend bootstrap -------------------------------------------------
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

# The backend resolves its Chroma index and .env RELATIVE to its own directory
# (CHROMA_PERSIST_DIR defaults to "./data/chroma"). If an eval script is launched
# from evaluation/, those relative paths break and retrieval/LLM silently fall
# back to empty. Force the working directory to backend/ so every stage sees the
# same populated index and .env regardless of where it was launched from.
try:
    os.chdir(BACKEND)
except Exception:
    pass


def ensure_dirs():
    """Create the output directories. Called by each module's __main__, never
    at import time (import must have no side effects)."""
    for d in (DATASETS, OUTPUTS, FIGURES):
        os.makedirs(d, exist_ok=True)


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_csv(path, rows, fieldnames=None):
    """Write a list of dicts to CSV. Raises on an empty list rather than
    silently producing a headerless file."""
    if not rows:
        raise ValueError(f"refusing to write an empty CSV: {path}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    ensure_dirs()
    from services import kb_service
    n = len(kb_service.all_schemes())
    print("repo root       ", ROOT)
    print("backend on path ", BACKEND in sys.path)
    print("curated schemes ", n)
    print("outputs         ", OUTPUTS)
    assert n == 18, f"expected 18 curated schemes, found {n}"
    print("[OK] utils bootstrap works.")
