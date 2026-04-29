"""
CareSlot — RAG Pipeline
ChromaDB vector store for medical knowledge retrieval-augmented generation.
"""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.ai.embeddings import get_embeddings
from app.config import get_settings
from typing import List, Optional
import json
import os
import logging

logger = logging.getLogger(__name__)

# Singleton ChromaDB vector store
_vector_store: Optional[Chroma] = None


def get_vector_store() -> Chroma:
    """Get or create the ChromaDB vector store."""
    global _vector_store

    if _vector_store is None:
        settings = get_settings()
        embeddings = get_embeddings()

        persist_dir = os.path.abspath(settings.CHROMA_PERSIST_DIR)
        os.makedirs(persist_dir, exist_ok=True)

        logger.info(f"Initializing ChromaDB at: {persist_dir}")

        _vector_store = Chroma(
            collection_name="medical_knowledge",
            embedding_function=embeddings,
            persist_directory=persist_dir,
        )

    return _vector_store


def get_retriever(k: int = 5):
    """
    Get a similarity search retriever from the vector store.

    Args:
        k: Number of top results to retrieve.

    Returns:
        A LangChain retriever for use in chains.
    """
    store = get_vector_store()
    return store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


def ingest_knowledge(knowledge_dir: str = None) -> int:
    """
    Ingest medical knowledge base documents into ChromaDB.

    Args:
        knowledge_dir: Path to directory containing JSON knowledge files.

    Returns:
        Number of documents ingested.
    """
    if knowledge_dir is None:
        knowledge_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "knowledge",
        )

    store = get_vector_store()
    documents: List[Document] = []

    # Process each knowledge file
    knowledge_files = [
        "symptoms.json",
        "diseases.json",
        "precautions.json",
        "specialists.json",
    ]

    for filename in knowledge_files:
        filepath = os.path.join(knowledge_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Knowledge file not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        category = filename.replace(".json", "")

        if isinstance(data, list):
            for item in data:
                content = _format_knowledge_item(item)
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": filename,
                        "category": category,
                        "name": item.get("name", item.get("condition", "")),
                    },
                )
                documents.append(doc)
        elif isinstance(data, dict):
            for key, value in data.items():
                content = f"{key}: {json.dumps(value) if isinstance(value, (dict, list)) else value}"
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": filename,
                        "category": category,
                        "name": key,
                    },
                )
                documents.append(doc)

    if documents:
        store.add_documents(documents)
        logger.info(f"Ingested {len(documents)} documents into ChromaDB")
    else:
        logger.warning("No documents found to ingest")

    return len(documents)


def _format_knowledge_item(item: dict) -> str:
    """Format a knowledge item into a searchable text block."""
    parts = []

    for key, value in item.items():
        if isinstance(value, list):
            parts.append(f"{key}: {', '.join(str(v) for v in value)}")
        elif isinstance(value, dict):
            parts.append(f"{key}: {json.dumps(value)}")
        else:
            parts.append(f"{key}: {value}")

    return "\n".join(parts)


def similarity_search(query: str, k: int = 5) -> List[Document]:
    """
    Direct similarity search on the vector store.

    Args:
        query: The search query.
        k: Number of results.

    Returns:
        List of matching documents.
    """
    store = get_vector_store()
    return store.similarity_search(query, k=k)


def get_collection_stats() -> dict:
    """Get statistics about the ChromaDB collection."""
    store = get_vector_store()
    collection = store._collection
    return {
        "total_documents": collection.count(),
        "name": collection.name,
    }
