"""
CareSlot — Embedding Model
Shared HuggingFace embedding model for ChromaDB vector operations.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from app.config import get_settings
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


@lru_cache()
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Get the cached HuggingFace embeddings model.
    Uses all-MiniLM-L6-v2 for efficient sentence embeddings.
    """
    settings = get_settings()

    logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")

    embeddings = HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    return embeddings
