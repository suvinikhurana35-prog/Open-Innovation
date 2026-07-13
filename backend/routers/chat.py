"""Chat route — now forwards conversation history (fixes 'chat forgets earlier messages')."""
import logging
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from models.schemas import ChatMessage, ChatResponse
from services.ai_service import chat_with_ai, translate_texts
from utils.response import success_response, error_response

logger = logging.getLogger("janniti.chat")
router = APIRouter(prefix="/api/chat", tags=["Chat"])


class TranslateRequest(BaseModel):
    texts: List[str]
    language: str = "en"


@router.post("/translate")
async def translate(req: TranslateRequest):
    """Re-render existing chat messages in the selected language (used when the
    user switches language and wants the previous conversation translated)."""
    try:
        if not req.texts:
            return success_response({"texts": []})
        out = translate_texts(req.texts, req.language)
        return success_response({"texts": out})
    except Exception as e:
        logger.error(f"Translate failed: {e}", exc_info=True)
        return error_response("Translation failed. Please try again.")


@router.post("/message")
async def chat(message: ChatMessage):
    try:
        result = chat_with_ai(
            message=message.message,
            conversation_history=message.conversation_history,
            language=message.language,
            profile=message.profile,
        )
        return success_response(ChatResponse(**result))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        return error_response("Chat request failed. Please try again.")
