import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.orchestrator import orchestrator


def main():
    print("=" * 60)
    print("PHASE 3: MULTI-AGENT SYSTEM TEST")
    print("=" * 60)

    test_queries = [
        "What are the penalties for data breach under DPDPA?",
        "What are the requirements for board meetings under Companies Act?",
        "Is my company compliant with IT Act if we process user data?"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)

        result = orchestrator.process_query(query)

        print(f"Intent: {result['intent']}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Citations Valid: {result['citation_validation']['is_valid']}")
        print(f"\nAnswer Preview: {result['answer'][:300]}...")
        print("\n" + "=" * 50)


if __name__ == "__main__":
    main()