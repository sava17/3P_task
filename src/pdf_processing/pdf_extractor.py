import httpx
from google import genai
from google.genai import types
from pathlib import Path
from typing import Dict, List, Optional
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
import PyPDF2
import json
from datetime import datetime

class PDFExtractor:
    """Extract and parse content from BR18 PDF documents"""

    def __init__(self, debug_mode: bool = True, debug_output_dir: str = "debug_extractions"):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.debug_mode = debug_mode
        self.debug_output_dir = Path(debug_output_dir)
        if self.debug_mode:
            self.debug_output_dir.mkdir(parents=True, exist_ok=True)

    def extract_text_pypdf(self, pdf_path: str) -> str:
        """
        Extract text using PyPDF2 (fallback method)

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content
        """
        text_content = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
        return text_content

    def extract_with_gemini(self, pdf_path: str, extraction_prompt: Optional[str] = None) -> str:
        """
        Extract structured content from PDF using Gemini Vision

        Args:
            pdf_path: Path to PDF file
            extraction_prompt: Custom prompt for extraction (optional)

        Returns:
            Extracted and structured content
        """
        if extraction_prompt is None:
            extraction_prompt = """Extract all text content from this BR18 fire safety document.
Preserve the structure including:
- Section headings
- Paragraph numbers (e.g., BR18 §508)
- Tables and lists
- Building specifications (area, floors, fire classification)
- Any references to regulations or other documents

Format the output as structured text."""

        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=pdf_data,
                    mime_type='application/pdf',
                ),
                extraction_prompt
            ]
        )

        return response.text

    def extract_br18_metadata(self, pdf_path: str) -> Dict:
        """
        Extract specific BR18 metadata from document using Gemini

        Args:
            pdf_path: Path to BR18 document

        Returns:
            Dictionary with extracted metadata
        """
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        metadata_prompt = """Analyze this BR18 fire safety document and extract the following information in JSON format:

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
  "br18_references": ["list of BR18 paragraph references like §508"],
  "key_requirements": ["list of key fire safety requirements mentioned"]
}

If any field is not found, use null. Return ONLY the JSON object, no other text."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=pdf_data,
                    mime_type='application/pdf',
                ),
                metadata_prompt
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,  # Very low for factual extraction
            )
        )

        import json
        try:
            # Extract JSON from response
            text = response.text.strip()
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Fallback to raw text if JSON parsing fails
            return {"raw_response": response.text, "error": "Failed to parse JSON"}

    def chunk_document(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split document into chunks for RAG system

        Args:
            text: Document text
            chunk_size: Target chunk size in words
            overlap: Overlap between chunks in words

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []

        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            start = end - overlap

        return chunks

    def save_debug_output(self, pdf_path: str, content: str, metadata: Dict, chunks: List[str]):
        """
        Save extraction debug output for analysis

        Args:
            pdf_path: Original PDF path
            content: Extracted content
            metadata: Extracted metadata
            chunks: Generated chunks
        """
        if not self.debug_mode:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_name = Path(pdf_path).stem
        debug_file = self.debug_output_dir / f"{pdf_name}_{timestamp}_debug.json"

        debug_data = {
            "timestamp": datetime.now().isoformat(),
            "source_pdf": str(pdf_path),
            "extraction_technique": "Gemini Vision + LLM",
            "chunking_technique": "Word-based with overlap (500 words/chunk, 50 word overlap)",
            "metadata": metadata,
            "full_extracted_content": content,
            "total_content_length": len(content),
            "total_content_words": len(content.split()),
            "chunks": [
                {
                    "chunk_index": i,
                    "content": chunk,
                    "word_count": len(chunk.split()),
                    "char_count": len(chunk)
                }
                for i, chunk in enumerate(chunks)
            ],
            "chunk_count": len(chunks),
            "chunking_stats": {
                "total_chunks": len(chunks),
                "avg_words_per_chunk": sum(len(c.split()) for c in chunks) / len(chunks) if chunks else 0,
                "avg_chars_per_chunk": sum(len(c) for c in chunks) / len(chunks) if chunks else 0
            }
        }

        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2)

        # Also save human-readable text version
        text_file = self.debug_output_dir / f"{pdf_name}_{timestamp}_content.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"EXTRACTION DEBUG OUTPUT\n")
            f.write(f"Source: {pdf_path}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("="*80 + "\n\n")

            f.write("METADATA:\n")
            f.write("-"*80 + "\n")
            f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
            f.write("\n\n")

            f.write("FULL EXTRACTED CONTENT:\n")
            f.write("-"*80 + "\n")
            f.write(content)
            f.write("\n\n")

            f.write("CHUNKS (for embedding):\n")
            f.write("="*80 + "\n")
            for i, chunk in enumerate(chunks):
                f.write(f"\n--- CHUNK {i+1}/{len(chunks)} ---\n")
                f.write(f"Words: {len(chunk.split())} | Chars: {len(chunk)}\n")
                f.write("-"*80 + "\n")
                f.write(chunk)
                f.write("\n")

        print(f"✓ Debug output saved to: {debug_file}")
        print(f"✓ Human-readable output saved to: {text_file}")

    def extract_dbk_insights(self, pdf_path: str) -> Dict:
        """
        Extract DBK-specific insights: Hvilke formuleringer godkendes?

        Focuses on approved phrasing, technical specifications, and compliant language.

        Args:
            pdf_path: Path to DBK document

        Returns:
            Dictionary with DBK-specific insights
        """
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        dbk_prompt = """Analyze this DBK (Dokumentation for brandtekniske installationer) document.

Extract and identify:

1. **Godkendte Formuleringer** (Approved Phrasing):
   - Exact phrasing used for fire system descriptions
   - Technical terminology that was accepted
   - How compliance is expressed

2. **Tekniske Specifikationer** (Technical Specifications):
   - Fire resistance classes (e.g., REI 60, EI 30-C)
   - Material classifications (e.g., K1 10/B-s1,d0, A2-s1,d0)
   - Distance requirements (e.g., "30 meter til udgang")
   - Evacuation route specifications

3. **BR18 Paragraph References**:
   - Which specific BR18 paragraphs are cited (e.g., §508, §509)
   - How they are referenced and applied

4. **Successful Patterns**:
   - Structure and organization of the document
   - How fire safety measures are documented
   - How compliance is demonstrated

Return as JSON:
{
  "document_type": "DBK",
  "approved_phrasing": ["list of exact phrases that express compliance well"],
  "technical_specs": {
    "fire_resistance_classes": ["REI 60", etc.],
    "material_classes": ["K1 10/B-s1,d0", etc.],
    "distances": ["30 meter til udgang", etc.]
  },
  "br18_references": ["§508", "§509", etc.],
  "structural_patterns": ["how sections are organized"],
  "key_insights": ["what makes this document successful"]
}

Return ONLY valid JSON."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                dbk_prompt
            ],
            config=types.GenerateContentConfig(temperature=0.1)
        )

        return self._parse_json_response(response.text)

    def extract_start_insights(self, pdf_path: str) -> Dict:
        """
        Extract START-specific insights: Typiske certificeringsforhold

        Focuses on certification patterns, declaration language, and approval context.

        Args:
            pdf_path: Path to START document

        Returns:
            Dictionary with START-specific insights
        """
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        start_prompt = """Analyze this START (Starterklæring) document.

Extract and identify:

1. **Certificeringsforhold** (Certification Context):
   - Consultant certification details
   - How certification is referenced
   - Authority and credibility language

2. **Declaration Language**:
   - How compliance is declared ("Dette projekt overholder...")
   - Phrasing for adherence to BR18
   - Language that establishes authority

3. **Project Description Patterns**:
   - How building type is described
   - How fire classification is stated
   - How scope of work is defined

4. **BR18 Compliance Statements**:
   - How BR18 adherence is expressed
   - Which paragraphs are typically cited in declarations
   - Format of compliance statements

Return as JSON:
{
  "document_type": "START",
  "certification_patterns": ["how consultant credentials are presented"],
  "declaration_phrases": ["exact phrases declaring compliance"],
  "project_description_format": ["how projects are described"],
  "br18_compliance_language": ["how BR18 adherence is stated"],
  "scope_definition": ["how work scope is defined"],
  "key_insights": ["what makes this declaration effective"]
}

Return ONLY valid JSON."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                start_prompt
            ],
            config=types.GenerateContentConfig(temperature=0.1)
        )

        return self._parse_json_response(response.text)

    def extract_bsr_insights(self, pdf_path: str) -> Dict:
        """
        Extract BSR-specific insights: Succesfulde brandstrategier

        Focuses on successful fire strategy patterns and approaches.

        Args:
            pdf_path: Path to BSR document

        Returns:
            Dictionary with BSR-specific insights
        """
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        bsr_prompt = """Analyze this BSR (Brandsikringsredegørelse) document.

Extract and identify:

1. **Successful Fire Strategies**:
   - Overall approach to fire safety
   - How fire scenarios are analyzed
   - Risk assessment methodology

2. **Strategy Communication**:
   - How strategies are explained to authorities
   - Language that demonstrates thoroughness
   - How alternatives are evaluated

3. **Technical Solutions**:
   - Fire protection systems chosen
   - Evacuation strategies
   - Compartmentation approach

4. **Justification Patterns**:
   - How design choices are justified
   - How compliance is demonstrated
   - How safety equivalence is argued (if applicable)

Return as JSON:
{
  "document_type": "BSR",
  "strategy_approaches": ["overall fire safety strategies used"],
  "risk_analysis_methods": ["how fire risks are analyzed"],
  "technical_solutions": ["fire protection systems and approaches"],
  "justification_language": ["how choices are justified to authorities"],
  "scenario_analysis": ["how fire scenarios are presented"],
  "key_insights": ["what makes this strategy successful"]
}

Return ONLY valid JSON."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                bsr_prompt
            ],
            config=types.GenerateContentConfig(temperature=0.1)
        )

        return self._parse_json_response(response.text)

    def extract_document_type_insights(self, pdf_path: str, doc_type: str) -> Dict:
        """
        Route to appropriate document-type-specific extraction

        Args:
            pdf_path: Path to PDF
            doc_type: Document type (START, DBK, BSR, etc.)

        Returns:
            Document-type-specific insights
        """
        doc_type_upper = doc_type.upper()

        if doc_type_upper == "DBK":
            return self.extract_dbk_insights(pdf_path)
        elif doc_type_upper == "START":
            return self.extract_start_insights(pdf_path)
        elif doc_type_upper == "BSR":
            return self.extract_bsr_insights(pdf_path)
        else:
            # Fallback to generic metadata extraction
            return self.extract_br18_metadata(pdf_path)

    def _parse_json_response(self, response_text: str) -> Dict:
        """Parse JSON from Gemini response, handling markdown code blocks"""
        text = response_text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print(f"Raw response: {response_text[:500]}...")
            return {"raw_response": response_text, "error": f"Failed to parse JSON: {e}"}

    def process_br18_example(self, pdf_path: str, extract_insights: bool = True) -> Dict:
        """
        Complete processing pipeline for a BR18 example document with document-type-specific insights

        Args:
            pdf_path: Path to BR18 PDF
            extract_insights: Whether to extract document-type-specific insights

        Returns:
            Dictionary with extracted content, metadata, chunks, and insights
        """
        print(f"\n{'='*80}")
        print(f"📄 Processing BR18 Document: {Path(pdf_path).name}")
        print(f"{'='*80}\n")

        # Extract full content
        print("📖 Extracting full content with Gemini...")
        content = self.extract_with_gemini(pdf_path)
        print(f"✅ Extracted {len(content)} characters, {len(content.split())} words\n")

        # Extract metadata
        print("🔍 Extracting metadata...")
        metadata = self.extract_br18_metadata(pdf_path)
        print(f"✅ Metadata extracted: {metadata.get('document_type', 'Unknown type')}\n")

        # Extract document-type-specific insights
        insights = None
        if extract_insights and metadata.get('document_type'):
            doc_type = metadata.get('document_type')
            print(f"🧠 Extracting {doc_type}-specific insights...")
            insights = self.extract_document_type_insights(pdf_path, doc_type)
            print(f"✅ Insights extracted for {doc_type}\n")

        # Create chunks for RAG
        print("✂️  Creating chunks for RAG system...")
        chunks = self.chunk_document(content)
        print(f"✅ Created {len(chunks)} chunks\n")

        # Save debug output if enabled
        if self.debug_mode:
            print("💾 Saving debug output...")
            self.save_debug_output(pdf_path, content, metadata, chunks)

            # Also save insights to debug output
            if insights:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_name = Path(pdf_path).stem
                insights_file = self.debug_output_dir / f"{pdf_name}_{timestamp}_insights.json"
                with open(insights_file, 'w', encoding='utf-8') as f:
                    json.dump(insights, f, ensure_ascii=False, indent=2)
                print(f"✅ Insights saved to: {insights_file}\n")

        result = {
            "pdf_path": pdf_path,
            "content": content,
            "metadata": metadata,
            "insights": insights,  # NEW: Document-type-specific insights
            "chunks": chunks,
            "chunk_count": len(chunks)
        }

        print(f"{'='*80}")
        print(f"✅ Processing complete for {Path(pdf_path).name}")
        print(f"   Content: {len(content)} chars")
        print(f"   Chunks: {len(chunks)}")
        print(f"   Insights: {'Yes' if insights else 'No'}")
        print(f"{'='*80}\n")

        return result
