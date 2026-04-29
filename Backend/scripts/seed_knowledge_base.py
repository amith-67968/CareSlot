"""
CareSlot — Seed Knowledge Base
Populates ChromaDB with medical knowledge from JSON files.
Run: python -m scripts.seed_knowledge_base
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.ai.rag import ingest_knowledge, get_collection_stats


def main():
    print("=" * 50)
    print("CareSlot — Knowledge Base Seeder")
    print("=" * 50)

    # Check current state
    stats = get_collection_stats()
    print(f"\nCurrent documents in ChromaDB: {stats['total_documents']}")

    # Ingest knowledge
    print("\nIngesting medical knowledge base...")
    count = ingest_knowledge()
    print(f"[OK] Successfully ingested {count} documents")

    # Verify
    stats = get_collection_stats()
    print(f"\nTotal documents now: {stats['total_documents']}")
    print("\n[DONE] Knowledge base is ready!")


if __name__ == "__main__":
    main()
