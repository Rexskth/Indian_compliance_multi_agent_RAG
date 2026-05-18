import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.retrieval.hybrid_retriever import HybridRetriever


def main():
    print("=" * 60)
    print("PHASE 2: RAG CORE - HYBRID RETRIEVAL TEST")
    print("=" * 60)

    retriever = HybridRetriever()

    test_queries = [
        "data protection rights under DPDPA",
        "penalty for unauthorized access under IT Act",
        "board meeting requirements Companies Act"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)

        results = retriever.retrieve(query, top_k=3)

        for r in results:
            print(f"Rank {r.rank}: [{r.source}] Score: {r.score:.4f}")
            print(f"  Section: {r.section_number or 'N/A'}, Page: {r.page_number}")
            print(f"  Text: {r.text[:150]}...")
            print()


if __name__ == "__main__":
    main()