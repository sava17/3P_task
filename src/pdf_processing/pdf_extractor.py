import httpx
from google import genai
from google.genai import types
from pathlib import Path
from typing import Dict, List, Optional
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
import PyPDF2

class PDFExtractor:
    """Extract and parse content from BR18 PDF documents"""

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

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
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        if extraction_prompt is None:
            extraction_prompt = """Extract all text content from this BR18 fire safety document.
Preserve the structure including:
- Section headings
- Paragraph numbers (e.g., BR18 §508)
- Tables and lists
- Building specifications (area, floors, fire classification)
- Any references to regulations or other documents

Format the output as structured text."""

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

    def process_br18_example(self, pdf_path: str) -> Dict:
        """
        Complete processing pipeline for a BR18 example document

        Args:
            pdf_path: Path to BR18 PDF

        Returns:
            Dictionary with extracted content, metadata, and chunks
        """
        print(f"Processing: {pdf_path}")

        # Extract full content
        content = self.extract_with_gemini(pdf_path)

        # Extract metadata
        metadata = self.extract_br18_metadata(pdf_path)

        # Create chunks for RAG
        chunks = self.chunk_document(content)

        return {
            "pdf_path": pdf_path,
            "content": content,
            "metadata": metadata,
            "chunks": chunks,
            "chunk_count": len(chunks)
        }
