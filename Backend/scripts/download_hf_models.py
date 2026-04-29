"""
CareSlot — Download & Cache HuggingFace Models
================================================

Pre-downloads the HuggingFace model used for PCOD/PCOS risk assessment
so it's cached locally before the first API request.

Models downloaded:
    - facebook/bart-large-mnli (zero-shot classification, ~1.6 GB)

Usage:
    cd Backend
    python scripts/download_hf_models.py
"""

import sys
import os


def main():
    print("=" * 60)
    print("CareSlot -- Downloading HuggingFace Models")
    print("=" * 60)

    # -- 1. Download BART-MNLI for zero-shot classification ----------
    print("\n[1/2] Downloading facebook/bart-large-mnli (~1.6 GB)...")
    print("      This is used for PCOD/PCOS risk assessment.")
    print("      First download may take several minutes.\n")

    try:
        from transformers import pipeline

        classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1,  # CPU
        )

        # Quick test to verify it works
        test_result = classifier(
            "Patient has irregular periods and weight gain",
            candidate_labels=["PCOS", "PCOD", "Normal"],
            multi_label=True,
        )

        print("[OK] facebook/bart-large-mnli downloaded and verified!")
        print(f"     Test result: {test_result['labels'][0]} ({test_result['scores'][0]:.3f})")

    except Exception as e:
        print(f"[FAIL] Failed to download BART model: {e}")
        print("       You may need to install: pip install transformers torch")
        return False

    # -- 2. Download sentence-transformers for embeddings ------------
    print("\n[2/2] Downloading sentence-transformers/all-MiniLM-L6-v2 (~90 MB)...")
    print("      This is used for ChromaDB embeddings (RAG pipeline).\n")

    try:
        from sentence_transformers import SentenceTransformer

        embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        # Quick test
        test_embedding = embed_model.encode(["test sentence"])
        print(f"[OK] all-MiniLM-L6-v2 downloaded and verified!")
        print(f"     Embedding dimension: {test_embedding.shape[1]}")

    except Exception as e:
        print(f"[FAIL] Failed to download embedding model: {e}")
        print("       You may need to install: pip install sentence-transformers")
        return False

    print("\n" + "=" * 60)
    print("[DONE] All models downloaded and cached successfully!")
    print("       Models are stored in: ~/.cache/huggingface/")
    print("       Subsequent loads will be instant (from cache).")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
