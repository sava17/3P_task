"""
Simple script to query the knowledge base and demonstrate RAG retrieval

Shows that municipality-specific patterns are stored and retrievable.
"""

from src.rag_system.vector_store import VectorStore

def query_knowledge_base():
    """Interactive knowledge base query"""

    # Initialize vector store
    vector_store = VectorStore()

    # Get stats
    stats = vector_store.get_stats()
    print("=" * 80)
    print("KNOWLEDGE BASE STATUS")
    print("=" * 80)
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Municipalities: {list(stats['by_municipality'].keys())}")
    print()

    # Example queries demonstrating municipality-specific learning
    queries = [
        ("Hvad kræver København for redningsåbninger?", "København"),
        ("Hvad siger Aarhus om brandventilation?", "Aarhus"),
        ("Kan vi bruge synligt træ i Odense institution?", "Odense"),
        ("Hvad er kravene til flugtafstande?", None),  # General query
    ]

    for query, municipality in queries:
        print("=" * 80)
        print(f"QUERY: {query}")
        if municipality:
            print(f"FILTERED BY: {municipality} Kommune")
        print("=" * 80)

        # Search knowledge base
        chunks = vector_store.search_with_confidence(
            query=query,
            municipality=municipality,
            top_k=3,
            exclude_rejected=True,
            prioritize_approved=True
        )

        if chunks:
            print(f"\nFound {len(chunks)} relevant knowledge chunks:\n")
            for i, chunk in enumerate(chunks, 1):
                print(f"--- RESULT {i} ---")
                print(f"Source: {chunk.source_type}")
                if chunk.municipality:
                    print(f"Municipality: {chunk.municipality}")
                print(f"Confidence: {chunk.metadata.get('confidence_score', 'N/A')}")
                print(f"Content:\n{chunk.content[:300]}...")
                print()
        else:
            print("❌ No results found. Knowledge base might be empty.")

        print()

    # Show golden records
    print("=" * 80)
    print("GOLDEN RECORDS (Best Practices)")
    print("=" * 80)
    golden = vector_store.get_golden_records(min_confidence=0.8)
    if golden:
        for i, chunk in enumerate(golden[:5], 1):
            print(f"\n{i}. [{chunk.municipality or 'General'}] (confidence: {chunk.metadata.get('confidence_score')})")
            print(f"   {chunk.content[:200]}...")
    else:
        print("No golden records yet. Upload approved documents to create them.")

    print()

    # Show negative constraints
    print("=" * 80)
    print("NEGATIVE CONSTRAINTS (What to Avoid)")
    print("=" * 80)
    negative = vector_store.get_negative_constraints()
    if negative:
        for i, chunk in enumerate(negative[:5], 1):
            print(f"\n{i}. [{chunk.municipality or 'General'}] (confidence: {chunk.metadata.get('confidence_score')})")
            print(f"   {chunk.content[:200]}...")
    else:
        print("No negative constraints yet. Upload rejection documents to create them.")


if __name__ == "__main__":
    query_knowledge_base()
