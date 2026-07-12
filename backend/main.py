import logging
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("janniti")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routers import explainer, chat, compare, dashboard, voice, transliterate

app = FastAPI(
    title="JanNiti - India's Policy Literacy Platform",
    description="AI-powered platform explaining Indian government schemes in simple language",
    version="1.1.0",
    docs_url="/docs", redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,      # env-driven (bug #8)
    allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(explainer.router)
app.include_router(chat.router)
app.include_router(compare.router)
app.include_router(dashboard.router)
app.include_router(voice.router)
app.include_router(transliterate.router)


@app.on_event("startup")
async def _startup():
    logger.info(f"LLM provider: {config.LLM_PROVIDER} | configured: {config.llm_configured()}")
    if not config.llm_configured():
        logger.warning("No LLM key configured — chat/explainer will return a clear "
                       "'AI unavailable' message until a key is set.")
    if config.AUTO_INGEST_ON_START:
        try:
            from services.rag_service import rag_service
            count = rag_service.ensure_populated()   # rebuild index if empty (bug #5)
            logger.info(f"Vector store ready: {count} documents.")
        except Exception as e:
            logger.error(f"Startup ingest failed: {e}", exc_info=True)


@app.get("/")
async def root():
    return {"name": "JanNiti API", "version": "1.1.0", "status": "running"}


@app.get("/health")
async def health():
    from services.rag_service import rag_service
    return {
        "status": "healthy",
        "llm_provider": config.LLM_PROVIDER,
        "llm_configured": config.llm_configured(),
        "documents_indexed": rag_service.count_documents(),
        "rag_available": rag_service.available,
    }


@app.get("/health/llm")
async def health_llm():
    """Live LLM self-test. Makes ONE tiny real call and reports the exact
    result/error, so you can tell a bad key/model from an outage — and quickly
    verify a new model string when testing different providers.

    Note: every core feature (explainer, simple story, hidden conditions,
    compare, chat) works from the curated KB WITHOUT the LLM, so a failure here
    does not break the app; it only affects live free-form generation."""
    from services.llm import llm_chat, LLM_UNAVAILABLE
    model = config.ANTHROPIC_MODEL if config.LLM_PROVIDER == "anthropic" else config.OPENAI_MODEL
    try:
        reply = llm_chat(messages=[{"role": "user", "content": "Reply with the word OK."}])
        ok = reply != LLM_UNAVAILABLE
        return {
            "provider": config.LLM_PROVIDER,
            "model": model,
            "configured": config.llm_configured(),
            "live_call_ok": ok,
            "sample_reply": (reply[:120] if ok else None),
            "hint": None if ok else "Live call failed — check the API key, that the model name is valid for your account, and remaining credits. See the server log for the exact provider error.",
        }
    except Exception as e:
        return {"provider": config.LLM_PROVIDER, "model": model,
                "configured": config.llm_configured(), "live_call_ok": False,
                "error": str(e)}


if __name__ == "__main__":
    import os, uvicorn
    logger.info("Starting JanNiti backend server...")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
