"""Chat route — now forwards conversation history (fixes 'chat forgets earlier messages')."""
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import ChatMessage, ChatResponse
from services.ai_service import chat_with_ai
from utils.response import success_response, error_response

logger = logging.getLogger("janniti.chat")
router = APIRouter(prefix="/api/chat", tags=["Chat"])


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
