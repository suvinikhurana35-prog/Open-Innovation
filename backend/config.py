"""
Central configuration for the JanNiti backend.

Everything that used to be hard-coded (the LLM provider, model name, request
timeout, CORS origins, the Chroma directory) is now read from the environment
with sensible defaults, so the same code runs locally and on a cloud host
without edits. See .env.example for the full list.
"""
import os

# Load backend/.env for EVERY entry point (server, eval scripts, tools), not
# just main.py. Without this, importing config directly (e.g. from an
# evaluation script) silently falls back to the built-in defaults and reads the
# wrong provider/key. We locate .env next to this file so the working directory
# doesn't matter.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass  # python-dotenv absent -> rely on real environment variables


def _csv(name: str, default: str) -> list:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# ---- LLM provider -----------------------------------------------------
# "openai" (uses OPENAI_API_KEY) or "anthropic" (uses ANTHROPIC_API_KEY).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Generous timeout so cloud cold-starts don't trip the old 5s limit.
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# ---- RAG / data -------------------------------------------------------
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
EMBED_MODEL = os.getenv("EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

# Rebuild the vector index on startup if the collection is empty.
AUTO_INGEST_ON_START = os.getenv("AUTO_INGEST_ON_START", "true").lower() == "true"

# ---- research feature flags ------------------------------------------
ENABLE_FAITHFULNESS = os.getenv("ENABLE_FAITHFULNESS", "true").lower() == "true"
ENABLE_SELECTIVE_RETRIEVAL = os.getenv("ENABLE_SELECTIVE_RETRIEVAL", "true").lower() == "true"

# ---- CORS -------------------------------------------------------------
CORS_ORIGINS = _csv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,https://janniti.vercel.app",
)

# ---- external ---------------------------------------------------------
DATAGOV_API_KEY = os.getenv("DATAGOV_API_KEY", "")


def llm_configured() -> bool:
    if LLM_PROVIDER == "anthropic":
        return bool(ANTHROPIC_API_KEY)
    if LLM_PROVIDER == "openai":
        return bool(OPENAI_API_KEY) and not OPENAI_API_KEY.startswith("sk-your")
    return False
