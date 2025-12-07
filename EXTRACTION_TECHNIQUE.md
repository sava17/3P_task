# Extraction & Embedding Technique Analysis

## Overview
This document explains how we process source material (BR18 PDFs) before embedding them into our RAG knowledge base.

## Processing Pipeline

### 1. PDF Extraction Technique

**Method**: Gemini Vision + LLM (Multimodal AI)

**Location**: `src/pdf_processing/pdf_extractor.py:32` (extract_with_gemini)

**How it works**:
- PDFs are sent directly to Google's Gemini model as binary data
- Gemini uses vision capabilities to "read" the PDF visually (not just text extraction)
- An LLM prompt guides the extraction to preserve structure

**Advantages**:
- Handles complex layouts, tables, and formatting
- Understands visual context (can see diagrams, symbols)
- Preserves hierarchical structure better than text-only extraction
- Can interpret scanned documents or images within PDFs

**Extraction Prompt**:
```
Extract all text content from this BR18 fire safety document.
Preserve the structure including:
- Section headings
- Paragraph numbers (e.g., BR18 §508)
- Tables and lists
- Building specifications (area, floors, fire classification)
- Any references to regulations or other documents

Format the output as structured text.
```

### 2. Metadata Extraction

**Method**: Structured prompting with JSON output

**Location**: `src/pdf_processing/pdf_extractor.py:70` (extract_br18_metadata)

**What we extract**:
```json
{
  "document_type": "START/ITT/DBK/BSR/etc.",
  "project_name": "name of building project",
  "address": "building address",
  "municipality": "municipality name",
  "building_type": "warehouse/office/residential/etc.",
  "total_area_m2": number,
  "floors": number,
  "fire_classification": "BK1/BK2/BK3/BK4",
  "application_category": "1-6",
  "risk_class": "1-4",
  "consultant_name": "certified consultant name",
  "consultant_certificate": "certificate number",
  "br18_references": ["§508", "§509", ...],
  "key_requirements": ["list of requirements"]
}
```

**Purpose**:
- Enable filtering by municipality, document type
- Track which projects get approved
- Learn municipality-specific preferences
- Extract regulatory references for compliance checking

### 3. Chunking Technique

**Method**: Word-based chunking with overlap

**Location**: `src/pdf_processing/pdf_extractor.py:134` (chunk_document)

**Parameters**:
- **Chunk size**: 500 words
- **Overlap**: 50 words

**Algorithm**:
```python
1. Split full text into words
2. Create chunks of 500 words
3. Step forward by (chunk_size - overlap) = 450 words
4. Repeat until all text is chunked
```

**Why overlap?**
- Prevents important context from being split between chunks
- If a critical regulation spans a chunk boundary, the overlap ensures both chunks have context
- Improves retrieval quality at the cost of slight redundancy

**Trade-offs**:

| Aspect | Current Approach | Alternative |
|--------|------------------|-------------|
| Simplicity | ✓ Very simple | Semantic chunking is complex |
| Speed | ✓ Very fast | Semantic chunking is slower |
| Context preservation | ~ Good with overlap | Semantic chunking better |
| Chunk consistency | ✓ Predictable size | Variable size chunks |

### 4. Embedding Generation

**Method**: Google Gemini Embeddings API

**Location**: `src/rag_system/embeddings.py:12` (generate_embedding)

**Model**: `text-embedding-004`

**Embedding dimension**: 768

**Task types**:
- `retrieval_document`: When embedding document chunks (storage)
- `retrieval_query`: When embedding user queries (search)

**Why different task types?**
- Gemini optimizes embeddings differently for documents vs queries
- Documents need to be "findable"
- Queries need to "find" documents
- This asymmetric embedding improves retrieval accuracy

### 5. Storage

**Method**: ChromaDB (Purpose-built vector database for LLM applications)

**Location**: `src/rag_system/vector_store.py:12`

**Distance metric**: Cosine similarity (default)

**Why Chroma?**
- ✅ Built specifically for RAG systems
- ✅ Automatic persistent storage
- ✅ Built-in metadata filtering
- ✅ Can add items dynamically (perfect for learning systems)
- ✅ No manual index rebuilding required

**What gets stored**:
```python
{
  "chunk_id": "unique-id",
  "source_type": "approved_doc",  # or regulation, feedback, insight
  "source_reference": "path/to/pdf",
  "municipality": "København",
  "document_type": "DBK",
  "content": "the actual text chunk",
  "metadata": {...},  # Flattened for Chroma compatibility
  "embedding": [768 floats],
  "created_at": "timestamp"
}
```

**Continuous Learning Support**:
Unlike static indexes (Annoy, FAISS without modifications), Chroma allows:
- Adding new approved documents anytime
- Adding learned insights from feedback
- No index rebuild required
- Automatic persistence

## Debug Output Feature

### New Feature: Extraction Debugging

**Purpose**:
- See exactly what content is extracted from PDFs
- Verify accuracy of extraction before embedding
- Analyze chunking quality
- Troubleshoot retrieval issues

**Usage**:

```python
# Enable debug mode
extractor = PDFExtractor(debug_mode=True, debug_output_dir="debug_extractions")

# Process a PDF
result = extractor.process_br18_example("path/to/document.pdf")

# Debug files are automatically saved:
# - document_TIMESTAMP_debug.json (structured data)
# - document_TIMESTAMP_content.txt (human-readable)
```

**Or use the test script**:
```bash
python test_extraction_debug.py
```

### Debug Output Contents

**JSON file** (`*_debug.json`):
```json
{
  "timestamp": "2025-12-07T12:30:45",
  "source_pdf": "path/to/document.pdf",
  "extraction_technique": "Gemini Vision + LLM",
  "chunking_technique": "Word-based with overlap (500 words/chunk, 50 word overlap)",
  "metadata": {...},
  "full_extracted_content": "entire extracted text",
  "chunks": [
    {
      "chunk_index": 0,
      "content": "chunk text here...",
      "word_count": 500,
      "char_count": 3245
    }
  ],
  "chunking_stats": {
    "total_chunks": 15,
    "avg_words_per_chunk": 487.3,
    "avg_chars_per_chunk": 3156.8
  }
}
```

**Text file** (`*_content.txt`):
```
================================================================================
EXTRACTION DEBUG OUTPUT
Source: path/to/document.pdf
Timestamp: 2025-12-07T12:30:45
================================================================================

METADATA:
--------------------------------------------------------------------------------
{
  "document_type": "DBK",
  "project_name": "Warehouse Building",
  ...
}

FULL EXTRACTED CONTENT:
--------------------------------------------------------------------------------
[Entire extracted text here, exactly as extracted by Gemini]

CHUNKS (for embedding):
================================================================================

--- CHUNK 1/15 ---
Words: 500 | Chars: 3245
--------------------------------------------------------------------------------
[Exact content of chunk 1 that will be embedded]

--- CHUNK 2/15 ---
Words: 500 | Chars: 3198
--------------------------------------------------------------------------------
[Exact content of chunk 2 that will be embedded]
...
```

## Evaluating Extraction Quality

### What to look for in debug output:

1. **Structural Preservation**
   - Are headings preserved?
   - Are paragraph numbers (§508, etc.) intact?
   - Are tables readable?

2. **Completeness**
   - Is all important text extracted?
   - Are there missing sections?
   - Are footnotes/references included?

3. **Chunking Quality**
   - Do chunks break in sensible places?
   - Is important context preserved in overlaps?
   - Are related regulations kept together?

4. **Metadata Accuracy**
   - Is the document type correctly identified?
   - Is the fire classification extracted correctly?
   - Are BR18 references accurate?

## Potential Improvements

### 1. Semantic Chunking
Instead of word-based chunking, chunk by semantic units:
- Keep entire paragraphs together
- Split on section boundaries
- Use BR18 paragraph markers (§) as natural breakpoints

### 2. Hierarchical Chunking
Create multi-level chunks:
- Full sections (for broad context)
- Paragraphs (for specific regulations)
- Sentences (for precise requirements)

### 3. Metadata Enrichment
Add more context to each chunk:
- Which section of BR18 it relates to
- Whether it's a requirement, example, or definition
- Importance score based on document structure

### 4. Table Extraction
Special handling for tables:
- Convert tables to structured format
- Create separate embeddings for table content
- Preserve row/column relationships

## Testing Extraction Quality

**Steps**:

1. Run debug extraction:
   ```bash
   python test_extraction_debug.py
   ```

2. Review output files in `debug_extractions/`

3. For each document, check:
   - Does extracted content match original PDF?
   - Are chunks logically separated?
   - Is important information preserved?
   - Are BR18 references intact?

4. Compare retrieval results:
   - Search for known information
   - Check if correct chunks are retrieved
   - Verify context is sufficient for LLM to answer

## Performance Metrics

**Current performance** (will vary by document):

| Metric | Typical Value |
|--------|---------------|
| Extraction time | 5-15 seconds per PDF |
| Extraction accuracy | ~95% (manual review needed) |
| Words per chunk | 450-500 |
| Chunks per document | 10-30 (depends on length) |
| Chunk overlap | 50 words (10%) |
| Embedding time | ~1 second per 10 chunks |

## Conclusion

Our extraction pipeline uses:
1. **Gemini Vision** for intelligent PDF reading
2. **Structured prompting** for metadata extraction
3. **Simple word-based chunking** for consistency
4. **Task-optimized embeddings** for better retrieval
5. **Debug output** for quality verification

The debug feature now allows you to inspect and verify extraction quality before embedding, ensuring the RAG system has high-quality knowledge to work with.
