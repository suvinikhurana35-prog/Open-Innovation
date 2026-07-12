import os
import logging
from gtts import gTTS
import tempfile
import base64

logger = logging.getLogger("janniti.voice")

LANGUAGE_MAP = {
    "en": "en",
    "hi": "hi",
    "bn": "bn",
    "te": "te",
    "ta": "ta",
    "mr": "mr",
    "gu": "gu",
    "kn": "kn",
    "ml": "ml",
    "pa": "pa",
    "or": "or",
    "as": "as",
}

# Try to set up OpenAI client only if key is available
_openai_client = None
_openai_available = False
try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "sk-placeholder" and not api_key.startswith("sk-your"):
        _openai_client = OpenAI(api_key=api_key)
        _openai_available = True
    else:
        logger.warning("No valid OPENAI_API_KEY found, falling back to gTTS for voice")
except ImportError:
    logger.warning("openai package not installed, falling back to gTTS for voice")

async def speech_to_text(audio_bytes: bytes, language: str = "en") -> str:
    if not _openai_client:
        raise RuntimeError("Speech-to-text unavailable: no OpenAI API key configured and no fallback available.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = _openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language if language in LANGUAGE_MAP else "en",
                response_format="text"
            )
        return transcript
    finally:
        os.unlink(tmp_path)


async def text_to_speech(text: str, language: str = "en") -> str:
    lang_code = LANGUAGE_MAP.get(language, "en")

    # Try OpenAI TTS first if available
    if _openai_client:
        try:
            response = _openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text,
                speed=0.9
            )
            audio_bytes = response.content
            return base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            logger.warning(f"OpenAI TTS failed, falling back to gTTS: {e}")

    # Fallback to gTTS
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tts = gTTS(text=text, lang=lang_code, slow=False)
            tts.save(tmp.name)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        os.unlink(tmp_path)
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        logger.error(f"gTTS failed: {e}", exc_info=True)
        return ""
