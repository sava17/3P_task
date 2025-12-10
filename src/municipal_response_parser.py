"""
Municipal Response Parser - Parse Afslag (Rejection) and Godkendelse (Approval) documents

This module implements Del 2: Myndighedsfeedback Integration
- Parse afslag og godkendelser
- Juster fremtidige anbefalinger

Extracts structured feedback from municipal authority response documents to create:
- Negative Constraints: What NOT to do (from rejections)
- Golden Records: Best practices (from approvals)
"""

import os
from google import genai
from google.genai import types
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from src.models import KnowledgeChunk
from src.learning_engine.confidence_scorer import ConfidenceScorer


class MunicipalResponseParser:
    """Parse municipal approval and rejection documents to extract learning insights"""

    def __init__(self):
        """Initialize the parser with Gemini API"""
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.confidence_scorer = ConfidenceScorer()
        self.model = GEMINI_MODEL

    def parse_rejection(self, pdf_path: str) -> Dict:
        """
        Parse an Afslag (Rejection) document from municipality

        Extracts:
        - Specific reasons for rejection
        - Which clauses/designs were problematic
        - Municipality-specific requirements mentioned
        - Suggestions for correction

        Args:
            pdf_path: Path to rejection PDF

        Returns:
            Dictionary with structured rejection data
        """
        print(f"\n🔴 Parsing REJECTION document: {Path(pdf_path).name}")
        print("=" * 80)

        # Detect file type
        file_extension = Path(pdf_path).suffix.lower()
        is_text_file = file_extension in ['.txt', '.text']

        rejection_prompt = """Analyze this municipal REJECTION (Afslag) document for a BR18 fire safety submission.

Extract the following information in JSON format:

{
  "response_type": "rejection",
  "municipality": "which municipality issued this rejection",
  "project_name": "building project name",
  "rejection_date": "date of rejection (if available)",
  "document_types_rejected": ["which BR18 documents were rejected, e.g., START, DBK"],

  "rejection_reasons": [
    {
      "category": "technical/procedural/compliance",
      "specific_issue": "exact description of what was wrong",
      "br18_reference": "BR18 paragraph if mentioned",
      "municipality_requirement": "specific local requirement if mentioned",
      "severity": "critical/major/minor"
    }
  ],

  "negative_constraints": [
    "Specific design choices or phrasings to AVOID in future submissions",
    "Methods/approaches that this municipality does not accept"
  ],

  "required_corrections": [
    "What must be changed/added for approval"
  ],

  "key_insights": [
    "Municipality-specific patterns revealed by this rejection"
  ]
}

Return ONLY valid JSON. Be very specific about what was rejected and why."""

        if is_text_file:
            # Read as text
            with open(pdf_path, 'r', encoding='utf-8') as f:
                text_content = f.read()

            # Send as text prompt
            response = self.client.models.generate_content(
                model=self.model,
                contents=[rejection_prompt + f"\n\nDocument content:\n{text_content}"],
                config=types.GenerateContentConfig(temperature=0.1)
            )
        else:
            # Read as binary (PDF)
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()

            # Send as PDF
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                    rejection_prompt
                ],
                config=types.GenerateContentConfig(temperature=0.1)
            )

        parsed_data = self._parse_json_response(response.text)
        parsed_data["source_pdf"] = str(pdf_path)

        print(f"\n✅ Rejection parsed:")
        print(f"   Municipality: {parsed_data.get('municipality')}")
        print(f"   Rejection Reasons: {len(parsed_data.get('rejection_reasons', []))}")
        print(f"   Negative Constraints: {len(parsed_data.get('negative_constraints', []))}")
        print("=" * 80 + "\n")

        return parsed_data

    def parse_approval(self, pdf_path: str) -> Dict:
        """
        Parse a Godkendelse (Approval) document from municipality

        Extracts:
        - What was approved
        - Which approaches/phrasings were successful
        - Any commendations or notes
        - Speed of approval (if indicated)

        Args:
            pdf_path: Path to approval PDF

        Returns:
            Dictionary with structured approval data
        """
        print(f"\n🟢 Parsing APPROVAL document: {Path(pdf_path).name}")
        print("=" * 80)

        # Detect file type
        file_extension = Path(pdf_path).suffix.lower()
        is_text_file = file_extension in ['.txt', '.text']

        approval_prompt = """Analyze this municipal APPROVAL (Godkendelse) document for a BR18 fire safety submission.

Extract the following information in JSON format:

{
  "response_type": "approval",
  "municipality": "which municipality issued this approval",
  "project_name": "building project name",
  "approval_date": "date of approval (if available)",
  "document_types_approved": ["which BR18 documents were approved, e.g., START, DBK"],

  "approval_notes": [
    "Any specific comments or commendations from the municipality"
  ],

  "successful_elements": [
    {
      "aspect": "what was particularly well done",
      "reason": "why this impressed the municipality",
      "replicable": true/false
    }
  ],

  "golden_patterns": [
    "Specific approaches, phrasings, or methods that led to smooth approval",
    "Design choices that this municipality appreciates"
  ],

  "approval_speed": "fast/standard/slow/unknown (based on processing time mentioned in document - 'fast' if <2 weeks, 'standard' if 2-4 weeks, 'slow' if >4 weeks, 'unknown' if not mentioned)",

  "key_insights": [
    "What this approval teaches us about this municipality's preferences"
  ]
}

Return ONLY valid JSON. Focus on what made this submission successful."""

        if is_text_file:
            # Read as text
            with open(pdf_path, 'r', encoding='utf-8') as f:
                text_content = f.read()

            # Send as text prompt
            response = self.client.models.generate_content(
                model=self.model,
                contents=[approval_prompt + f"\n\nDocument content:\n{text_content}"],
                config=types.GenerateContentConfig(temperature=0.1)
            )
        else:
            # Read as binary (PDF)
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()

            # Send as PDF
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                    approval_prompt
                ],
                config=types.GenerateContentConfig(temperature=0.1)
            )

        parsed_data = self._parse_json_response(response.text)
        parsed_data["source_pdf"] = str(pdf_path)

        print(f"\n✅ Approval parsed:")
        print(f"   Municipality: {parsed_data.get('municipality')}")
        print(f"   Successful Elements: {len(parsed_data.get('successful_elements', []))}")
        print(f"   Golden Patterns: {len(parsed_data.get('golden_patterns', []))}")
        print("=" * 80 + "\n")

        return parsed_data

    def create_knowledge_chunks_from_rejection(
        self,
        rejection_data: Dict
    ) -> List[KnowledgeChunk]:
        """
        Convert rejection data into knowledge chunks for vector store

        Creates chunks with:
        - approval_status = "rejected"
        - confidence_score = 0.0 (to avoid using these patterns)
        - municipality-specific metadata

        Args:
            rejection_data: Parsed rejection data

        Returns:
            List of KnowledgeChunk objects
        """
        chunks = []
        municipality = rejection_data.get('municipality', 'Unknown')
        project = rejection_data.get('project_name', 'Unknown Project')

        # Create chunks for each negative constraint
        for idx, constraint in enumerate(rejection_data.get('negative_constraints', [])):
            chunk = KnowledgeChunk(
                chunk_id=f"rejection_{municipality}_{idx}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                source_type="feedback",
                source_reference=rejection_data.get('source_pdf', 'unknown'),
                municipality=municipality,
                document_type=None,
                content=f"⚠️ AVOID (Rejected by {municipality}): {constraint}",
                metadata={
                    "approval_status": "rejected",
                    "confidence_score": 0.0,  # Don't use this pattern!
                    "response_type": "rejection",
                    "project_name": project,
                    "rejection_date": rejection_data.get('rejection_date')
                }
            )
            chunks.append(chunk)

        # Create chunks for rejection reasons (to understand why things fail)
        for idx, reason in enumerate(rejection_data.get('rejection_reasons', [])):
            content = f"Rejection Reason ({municipality}): {reason.get('specific_issue')}"
            if reason.get('municipality_requirement'):
                content += f" | Requirement: {reason.get('municipality_requirement')}"

            chunk = KnowledgeChunk(
                chunk_id=f"rejection_reason_{municipality}_{idx}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                source_type="feedback",
                source_reference=rejection_data.get('source_pdf', 'unknown'),
                municipality=municipality,
                document_type=None,
                content=content,
                metadata={
                    "approval_status": "rejected",
                    "confidence_score": 0.0,
                    "response_type": "rejection",
                    "severity": reason.get('severity', 'unknown'),
                    "category": reason.get('category', 'unknown')
                }
            )
            chunks.append(chunk)

        print(f"✅ Created {len(chunks)} negative constraint chunks from rejection")
        return chunks

    def create_knowledge_chunks_from_approval(
        self,
        approval_data: Dict
    ) -> List[KnowledgeChunk]:
        """
        Convert approval data into knowledge chunks for vector store

        Creates chunks with:
        - approval_status = "approved"
        - confidence_score = DYNAMIC (0.75-0.93 based on context)
        - municipality-specific metadata

        Args:
            approval_data: Parsed approval data

        Returns:
            List of KnowledgeChunk objects
        """
        chunks = []
        municipality = approval_data.get('municipality', 'Unknown')
        project = approval_data.get('project_name', 'Unknown Project')

        # Create chunks for each golden pattern
        for idx, pattern in enumerate(approval_data.get('golden_patterns', [])):
            # Calculate dynamic confidence based on approval context
            confidence, breakdown = self.confidence_scorer.calculate_approval_pattern_confidence(
                approval_data=approval_data,
                municipality=municipality,
                pattern_type="recommended_pattern"
            )

            chunk = KnowledgeChunk(
                chunk_id=f"approval_{municipality}_{idx}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                source_type="feedback",
                source_reference=approval_data.get('source_pdf', 'unknown'),
                municipality=municipality,
                document_type=None,
                content=f"✅ RECOMMENDED ({municipality}): {pattern}",
                metadata={
                    "approval_status": "approved",
                    "confidence_score": round(confidence, 2),  # Round to 2 decimals
                    "confidence_breakdown": breakdown,  # Store calculation details
                    "response_type": "approval",
                    "project_name": project,
                    "approval_date": approval_data.get('approval_date'),
                    "approval_speed": approval_data.get('approval_speed', 'unknown')
                }
            )
            chunks.append(chunk)

        # Create chunks for successful elements
        for idx, element in enumerate(approval_data.get('successful_elements', [])):
            content = f"Successful Approach ({municipality}): {element.get('aspect')}"
            if element.get('reason'):
                content += f" | Why: {element.get('reason')}"

            # Calculate dynamic confidence for successful elements
            base_confidence, breakdown = self.confidence_scorer.calculate_approval_pattern_confidence(
                approval_data=approval_data,
                municipality=municipality,
                pattern_type="successful_element"
            )

            # Adjust for replicability
            replicable = element.get('replicable', True)
            confidence = base_confidence if replicable else base_confidence * 0.85

            # Update breakdown if non-replicable
            if not replicable:
                breakdown["replicability_penalty"] = round(base_confidence * 0.15, 2)
                breakdown["calculation"] = f"{breakdown['calculation'].split('=')[0]}× 0.85 (non-replicable) = {confidence:.2f}"

            chunk = KnowledgeChunk(
                chunk_id=f"success_{municipality}_{idx}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                source_type="feedback",
                source_reference=approval_data.get('source_pdf', 'unknown'),
                municipality=municipality,
                document_type=None,
                content=content,
                metadata={
                    "approval_status": "approved",
                    "confidence_score": round(confidence, 2),  # Round to 2 decimals
                    "confidence_breakdown": breakdown,  # Store calculation details
                    "response_type": "approval",
                    "replicable": replicable
                }
            )
            chunks.append(chunk)

        print(f"✅ Created {len(chunks)} golden record chunks from approval")
        return chunks

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
            return {"error": f"Failed to parse JSON: {e}", "raw_response": response_text}


# Example usage
if __name__ == "__main__":
    parser = MunicipalResponseParser()

    # Example: Parse a rejection
    # rejection_data = parser.parse_rejection("path/to/afslag.pdf")
    # chunks = parser.create_knowledge_chunks_from_rejection(rejection_data)

    # Example: Parse an approval
    # approval_data = parser.parse_approval("path/to/godkendelse.pdf")
    # chunks = parser.create_knowledge_chunks_from_approval(approval_data)

    print("Municipal Response Parser initialized")
    print("Use parse_rejection() or parse_approval() methods")
