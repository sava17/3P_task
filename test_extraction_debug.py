"""
Test script to generate debug output showing what we extract and embed
Run this to see exactly what content is being processed before embedding
"""

from src.pdf_processing.pdf_extractor import PDFExtractor
from pathlib import Path
import json

def main():
    print("="*80)
    print("EXTRACTION DEBUG TEST")
    print("="*80)
    print()
    print("This script will process BR18 PDFs and save debug output showing:")
    print("  1. Raw extracted content from Gemini Vision")
    print("  2. Structured metadata extracted")
    print("  3. Exact chunks that will be embedded")
    print("  4. Statistics about the chunking process")
    print()

    # Initialize extractor with debug mode enabled
    extractor = PDFExtractor(debug_mode=True, debug_output_dir="debug_extractions")

    # Find all PDF files in example_pdfs directory
    example_pdfs_dir = Path("data/example_pdfs")
    if not example_pdfs_dir.exists():
        print(f"ERROR: {example_pdfs_dir} directory not found")
        print("Please ensure you have some example BR18 PDFs in the data/example_pdfs directory")
        return

    pdf_files = list(example_pdfs_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {example_pdfs_dir}")
        print("Please add some example BR18 documents to test")
        return

    print(f"Found {len(pdf_files)} PDF file(s):\n")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    print()

    # Process each PDF
    results = []
    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")
        print("-"*80)

        try:
            result = extractor.process_br18_example(str(pdf_path))
            results.append({
                "file": pdf_path.name,
                "success": True,
                "chunks": result["chunk_count"],
                "content_words": len(result["content"].split()),
                "metadata": result["metadata"]
            })

            print(f"  ✓ Extracted {len(result['content'].split())} words")
            print(f"  ✓ Created {result['chunk_count']} chunks for embedding")
            print(f"  ✓ Document type: {result['metadata'].get('document_type', 'Unknown')}")

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            results.append({
                "file": pdf_path.name,
                "success": False,
                "error": str(e)
            })

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    successful = sum(1 for r in results if r.get("success"))
    total_chunks = sum(r.get("chunks", 0) for r in results if r.get("success"))
    total_words = sum(r.get("content_words", 0) for r in results if r.get("success"))

    print(f"Processed: {successful}/{len(results)} files successfully")
    print(f"Total chunks created: {total_chunks}")
    print(f"Total words extracted: {total_words}")
    print()
    print(f"Debug output saved to: ./debug_extractions/")
    print()
    print("Check the debug files to see:")
    print("  - *_debug.json    : Structured data with all extraction details")
    print("  - *_content.txt   : Human-readable output showing exact chunks")
    print()

if __name__ == "__main__":
    main()
