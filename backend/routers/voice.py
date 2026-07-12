import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from services.voice_service import speech_to_text, text_to_speech
from pydantic import BaseModel
from utils.response import success_response, error_response

logger = logging.getLogger("janniti.voice")
router = APIRouter(prefix="/api/voice", tags=["Voice"])

class TTSRequest(BaseModel):
    text: str
    language: str = "en"

@router.post("/stt")
async def stt(audio: UploadFile = File(...), language: str = Form("en")):
    try:
        audio_bytes = await audio.read()
        text = await speech_to_text(audio_bytes, language)
        return success_response({"text": text})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT failed: {e}", exc_info=True)
        return error_response("Speech to text conversion failed.")

@router.post("/tts")
async def tts(request: TTSRequest):
    try:
        audio_b64 = await text_to_speech(request.text, request.language)
        if audio_b64:
            return success_response({"audio": audio_b64, "format": "mp3"})
        return error_response("TTS generation failed.", status_code=500)
    except Exception as e:
        logger.error(f"TTS failed: {e}", exc_info=True)
        return error_response("Text to speech conversion failed.")
