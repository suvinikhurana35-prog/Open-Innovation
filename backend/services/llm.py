"""
Unified LLM access layer.

Replaces the old local Ollama client (which doesn't exist on a cloud server —
the #1 "the bot feels dead" bug) with a hosted provider. One function,
``llm_chat``, is used by every feature (explainer, conditions, ELI5, compare,
chat), so chat and voice no longer disagree about which model to use.

Provider is chosen by config.LLM_PROVIDER:
  * "anthropic" -> Claude (ANTHROPIC_API_KEY)
  * "openai"    -> GPT (OPENAI_API_KEY)

Failures are logged loudly (no more silent swallowing) and return a clear
sentinel so callers can distinguish "model unavailable" from real content.
"""
import json
import logging
from typing import List, Optional

import config

logger = logging.getLogger("janniti.llm")

# Sentinel returned when the model can't be reached, so callers don't mistake
# an outage for a real (empty) answer.
LLM_UNAVAILABLE = "__LLM_UNAVAILABLE__"

_client = None
_client_kind = None


def _get_client():
    """Lazily build the provider client once."""
    global _client, _client_kind
    if _client is not None:
        return _client, _client_kind

    if config.LLM_PROVIDER == "anthropic":
        if not config.ANTHROPIC_API_KEY:
            logger.warning("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set.")
            return None, None
        try:
            from anthropic import Anthropic
        except ImportError:
            logger.error("LLM_PROVIDER=anthropic but the 'anthropic' package is not installed. Run: pip install anthropic")
            return None, None
        _client = Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=config.LLM_TIMEOUT)
        _client_kind = "anthropic"
    elif config.LLM_PROVIDER == "openai":
        if not config.llm_configured():
            logger.warning("LLM_PROVIDER=openai but OPENAI_API_KEY is missing/placeholder.")
            return None, None
        try:
            from openai import OpenAI
        except ImportError:
            logger.error("LLM_PROVIDER=openai but the 'openai' package is not installed. Run: pip install openai")
            return None, None
        _client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.LLM_TIMEOUT)
        _client_kind = "openai"
    else:
        logger.error(f"Unknown LLM_PROVIDER: {config.LLM_PROVIDER!r}")
        return None, None
    return _client, _client_kind


def llm_chat(messages: List[dict], json_mode: bool = False) -> str:
    """Send chat messages to the configured provider and return text.

    ``messages`` use the OpenAI-style [{"role","content"}] shape. For Anthropic
    we split out the system message and translate the rest.
    Returns ``LLM_UNAVAILABLE`` on any failure.
    """
    client, kind = _get_client()
    if client is None:
        return LLM_UNAVAILABLE

    try:
        if kind == "anthropic":
            system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
            convo = [m for m in messages if m["role"] in ("user", "assistant")]
            if json_mode:
                system += "\n\nRespond with a single valid JSON object and nothing else."
            resp = client.messages.create(
                model=config.ANTHROPIC_MODEL,
                max_tokens=config.LLM_MAX_TOKENS,
                system=system or "You are a helpful assistant.",
                messages=convo or [{"role": "user", "content": ""}],
            )
            text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
        else:  # openai
            kwargs = dict(model=config.OPENAI_MODEL, messages=messages,
                          max_tokens=config.LLM_MAX_TOKENS)
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            text = (resp.choices[0].message.content or "").strip()

        if json_mode:
            text = _strip_code_fence(text)
        return text or LLM_UNAVAILABLE
    except Exception as e:
        logger.error(f"LLM call failed ({config.LLM_PROVIDER}): {e}", exc_info=True)
        return LLM_UNAVAILABLE


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1] if "\n" in t else t
        if t.endswith("```"):
            t = t[: t.rfind("```")]
    return t.strip()


def parse_json_or_none(content: str) -> Optional[dict]:
    """Parse JSON content, returning None for the unavailable sentinel or bad JSON."""
    if not content or content == LLM_UNAVAILABLE:
        return None
    try:
        data = json.loads(_strip_code_fence(content))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, ValueError):
        return None
