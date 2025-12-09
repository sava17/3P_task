"""
Demo script for parsing municipal responses (Afslag/Godkendelse)

Shows how to upload rejection and approval documents to create
negative constraints and golden records.
"""

from src.municipal_response_parser import MunicipalResponseParser
from src.rag_system.vector_store import VectorStore

def demo_municipal_response_parsing():
    """Demonstrate parsing of Afslag and Godkendelse"""

    parser = MunicipalResponseParser()
    vector_store = VectorStore()

    print("=" * 80)
    print("MUNICIPAL RESPONSE PARSING DEMO")
    print("=" * 80)
    print()

    # Check initial state
    stats_before = vector_store.get_stats()
    print(f"Knowledge base BEFORE: {stats_before['total_chunks']} chunks")
    print(f"  - Golden records: {stats_before.get('golden_records', 0)}")
    print(f"  - Negative constraints: {stats_before.get('negative_constraints', 0)}")
    print()

    # Parse REJECTION
    print("=" * 80)
    print("PARSING REJECTION (Afslag)")
    print("=" * 80)

    rejection_file = "data/example_pdfs/synthetic_examples/municipal_responses/AFSLAG_Koebenhavn_Kontorbygning.txt"

    try:
        rejection_data = parser.parse_rejection(rejection_file)

        print(f"\n✅ Extracted from rejection:")
        print(f"   Municipality: {rejection_data.get('municipality')}")
        print(f"   Rejection reasons: {len(rejection_data.get('rejection_reasons', []))}")
        print(f"   Negative constraints: {len(rejection_data.get('negative_constraints', []))}")

        # Create knowledge chunks from rejection
        neg_chunks = parser.create_knowledge_chunks_from_rejection(rejection_data)

        # Add to vector store
        vector_store.add_chunks_batch(neg_chunks)

        print(f"\n✅ Added {len(neg_chunks)} negative constraint chunks to knowledge base")

        # Show examples
        print("\nExample negative constraints:")
        for i, chunk in enumerate(neg_chunks[:3], 1):
            print(f"\n{i}. {chunk.content[:150]}...")
            print(f"   Confidence: {chunk.metadata.get('confidence_score')}")
            print(f"   Status: {chunk.metadata.get('approval_status')}")

    except Exception as e:
        print(f"❌ Error parsing rejection: {e}")

    print()

    # Parse APPROVAL
    print("=" * 80)
    print("PARSING APPROVAL (Godkendelse)")
    print("=" * 80)

    approval_file = "data/example_pdfs/synthetic_examples/municipal_responses/GODKENDELSE_Aarhus_Lagerhal.txt"

    try:
        approval_data = parser.parse_approval(approval_file)

        print(f"\n✅ Extracted from approval:")
        print(f"   Municipality: {approval_data.get('municipality')}")
        print(f"   Successful elements: {len(approval_data.get('successful_elements', []))}")
        print(f"   Golden patterns: {len(approval_data.get('golden_patterns', []))}")

        # Create knowledge chunks from approval
        golden_chunks = parser.create_knowledge_chunks_from_approval(approval_data)

        # Add to vector store
        vector_store.add_chunks_batch(golden_chunks)

        print(f"\n✅ Added {len(golden_chunks)} golden record chunks to knowledge base")

        # Show examples
        print("\nExample golden records:")
        for i, chunk in enumerate(golden_chunks[:3], 1):
            print(f"\n{i}. {chunk.content[:150]}...")
            print(f"   Confidence: {chunk.metadata.get('confidence_score')}")
            print(f"   Status: {chunk.metadata.get('approval_status')}")

    except Exception as e:
        print(f"❌ Error parsing approval: {e}")

    print()

    # Check final state
    stats_after = vector_store.get_stats()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Knowledge base AFTER: {stats_after['total_chunks']} chunks")
    print(f"  - Golden records: {stats_after.get('golden_records', 0)}")
    print(f"  - Negative constraints: {stats_after.get('negative_constraints', 0)}")
    print()

    print(f"📈 GROWTH:")
    print(f"  - Total chunks: {stats_before['total_chunks']} → {stats_after['total_chunks']}")
    print(f"  - Golden records: {stats_before.get('golden_records', 0)} → {stats_after.get('golden_records', 0)}")
    print(f"  - Negative constraints: {stats_before.get('negative_constraints', 0)} → {stats_after.get('negative_constraints', 0)}")
    print()

    # Show how they're used
    print("=" * 80)
    print("HOW THESE ARE USED IN DOCUMENT GENERATION")
    print("=" * 80)
    print()

    print("When generating a document for København:")
    neg_ko = vector_store.get_negative_constraints(municipality="København")
    if neg_ko:
        print(f"  ⚠️ System will AVOID {len(neg_ko)} rejected patterns")
        print(f"     Example: {neg_ko[0].content[:100]}...")
    else:
        print("  (No København-specific constraints yet)")

    print()

    print("When generating a document for Aarhus:")
    golden_aarhus = vector_store.get_golden_records(municipality="Aarhus")
    if golden_aarhus:
        print(f"  ✅ System will PRIORITIZE {len(golden_aarhus)} approved patterns")
        print(f"     Example: {golden_aarhus[0].content[:100]}...")
    else:
        print("  (No Aarhus-specific golden records yet)")

    print()
    print("=" * 80)
    print("DEMO COMPLETE! 🎉")
    print("=" * 80)
    print()
    print("This demonstrates 'Juster fremtidige anbefalinger':")
    print("  - Rejections create negative constraints (avoid these)")
    print("  - Approvals create golden records (do this)")
    print("  - Future documents use this institutional memory")


if __name__ == "__main__":
    demo_municipal_response_parsing()
