"""
CareSlot — LLM Setup
Initializes Ollama LLM via LangChain for local inference.
"""

from langchain_ollama import ChatOllama
from app.config import get_settings
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


@lru_cache()
def get_llm() -> ChatOllama:
    """
    Get the cached Ollama LLM instance.
    Uses Llama 3.1 8B running locally via Ollama.
    """
    settings = get_settings()

    logger.info(
        f"Initializing Ollama LLM: model={settings.OLLAMA_MODEL}, "
        f"base_url={settings.OLLAMA_BASE_URL}"
    )

    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.3,
        top_p=0.9,
        num_ctx=4096,
        repeat_penalty=1.1,
        timeout=120,  # Allow enough time for cold-start model loading
    )

    return llm


def get_creative_llm() -> ChatOllama:
    """
    Get a more creative LLM instance for conversational responses.
    Higher temperature for more natural dialogue.
    """
    settings = get_settings()

    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.6,
        top_p=0.95,
        num_ctx=4096,
        timeout=120,
    )


async def check_ollama_health() -> bool:
    """Check if Ollama server is running and the model is available."""
    try:
        llm = get_llm()
        response = await llm.ainvoke("Hello")
        return True
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return False
