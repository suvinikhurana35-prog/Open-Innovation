"""
Transliteration proxy router.
Accepts { text: str, language: "hi" | "bn" | "ta" } and returns
{ suggestions: list[str] } using Google Input Tools (no key needed).
"""
from fastapi import APIRouter
from pydantic import BaseModel
import httpx
import logging

logger = logging.getLogger("janniti.transliterate")

router = APIRouter()

# Google Input Tools language codes
LANG_MAP = {
    "hi": "hi",   # Hindi
    "bn": "bn",   # Bengali
    "ta": "ta",   # Tamil
    "en": "en",
}


class TransliterateRequest(BaseModel):
    text: str
    language: str = "hi"


class TransliterateResponse(BaseModel):
    suggestions: list[str]


@router.post("/api/transliterate", response_model=TransliterateResponse)
async def transliterate(req: TransliterateRequest):
    lang = LANG_MAP.get(req.language, "hi")
    text = req.text.strip()

    if not text or lang == "en":
        return TransliterateResponse(suggestions=[])

    try:
        # Google Input Tools endpoint (public, no auth)
        url = (
            "https://inputtools.google.com/request"
            f"?text={text}&itc={lang}-t-i0-und&num=5&cp=0&cs=1&ie=utf-8&oe=utf-8&app=demopage"
        )
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            # Response format: ["SUCCESS", [[word, [candidates]]]]
            if data and data[0] == "SUCCESS" and data[1]:
                candidates = data[1][0][1]
                return TransliterateResponse(suggestions=candidates[:6])
    except Exception as exc:
        logger.warning("Transliteration failed: %s", exc)

    return TransliterateResponse(suggestions=[])
