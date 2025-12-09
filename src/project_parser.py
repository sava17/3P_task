"""
Project Input Parser - Extracts building data from project specification PDFs

This module handles Del 1: Intelligent Template System med Projektdata Integration
- Parses project specification documents (architectural plans, building specs)
- Extracts building parameters automatically using Gemini
- Determines required document types based on fire classification
"""

import os
from google import genai
from google.genai import types
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import re

from src.models import (
    BuildingProject,
    FireClassification,
    ApplicationCategory,
    RiskClass,
    DocumentType
)
from config.settings import GEMINI_API_KEY, GEMINI_MODEL


class ProjectInputParser:
    """Extracts building project data from specification documents"""

    def __init__(self):
        """Initialize the parser with Gemini API"""
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = GEMINI_MODEL

    def parse_project_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse a project specification PDF and extract building data.

        Args:
            pdf_path: Path to project specification PDF

        Returns:
            Dictionary with extracted project data
        """
        print(f"\n📄 Parsing project specification: {Path(pdf_path).name}")
        print("=" * 80)

        # Read PDF file
        print("📖 Reading PDF file...")
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        # Create extraction prompt
        prompt = self._create_extraction_prompt()

        # Extract data using Gemini
        print("\n🤖 Extracting building data with Gemini...")
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(
                    data=pdf_data,
                    mime_type='application/pdf',
                ),
                prompt
            ]
        )

        # Parse JSON response
        try:
            extracted_data = self._parse_gemini_response(response.text)
            print("\n✅ Extraction complete!")
            self._print_extracted_data(extracted_data)
            return extracted_data
        except Exception as e:
            print(f"\n❌ Error parsing Gemini response: {e}")
            print(f"Raw response: {response.text}")
            raise

    def _create_extraction_prompt(self) -> str:
        """Create prompt for Gemini to extract project data"""
        return """
Extract building project information from this document and return it as JSON.

Required fields:
1. project_name: Name of the building project
2. address: Full address of the building
3. municipality: Which Danish municipality (e.g., Aarhus, København, Aalborg)
4. building_type: Type of building (e.g., "Office Building", "Shopping Center", "Residential")
5. total_area_m2: Total area in square meters (number)
6. floors: Number of floors (number)
7. occupancy: Maximum number of people (number)
8. fire_load_mj_m2: Fire load in MJ/m² (number, estimate if not explicitly stated)
9. application_category: Building usage category 1-6 (number):
   - 1: Single-family residential (enfamiliehuse)
   - 2: Multi-family residential (etageboliger)
   - 3: Commercial/Office buildings
   - 4: Industrial buildings (fabrikker, lagerhaller)
   - 5: Assembly buildings (forsamlingslokaler, hoteller, institutioner)
   - 6: Special buildings (hospitals, prisons, etc.)
10. risk_class: Fire risk class 1-4 (number):
   - 1: Low risk (residential, small offices)
   - 2: Medium risk (larger offices, schools)
   - 3: High risk (hospitals, large public buildings)
   - 4: Very high risk (special facilities)
11. fire_classification: BR18 fire classification (string: "BK1", "BK2", "BK3", or "BK4")
12. consultant_name: Fire safety consultant name (if mentioned, otherwise "TBD")
13. consultant_certificate: Consultant certificate number (if mentioned, otherwise "TBD")
14. client_name: Client/owner name (if mentioned, otherwise "TBD")

IMPORTANT:
- Return ONLY valid JSON, no markdown or explanation
- Use null for unknown numeric values
- Make reasonable estimates based on building type if exact values not stated
- For fire_classification, use:
  * BK1: Simple buildings, low rise residential
  * BK2: Standard commercial/office buildings
  * BK3: Large buildings, high rise
  * BK4: Special buildings requiring extra safety

Example JSON format:
{
  "project_name": "Kontorhus Aarhus C",
  "address": "Åboulevarden 23, 8000 Aarhus C",
  "municipality": "Aarhus",
  "building_type": "Office Building",
  "total_area_m2": 2500,
  "floors": 5,
  "occupancy": 150,
  "fire_load_mj_m2": 420,
  "application_category": 3,
  "risk_class": 2,
  "fire_classification": "BK2",
  "consultant_name": "TBD",
  "consultant_certificate": "TBD",
  "client_name": "TBD"
}

Return only the JSON object.
"""

    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini's JSON response"""
        # Remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Parse JSON
        return json.loads(text)

    def _print_extracted_data(self, data: Dict[str, Any]):
        """Pretty print extracted data"""
        print("\n📊 Extracted Project Data:")
        print("-" * 80)
        print(f"  Project: {data.get('project_name')}")
        print(f"  Address: {data.get('address')}")
        print(f"  Municipality: {data.get('municipality')}")
        print(f"  Building Type: {data.get('building_type')}")
        print(f"  Total Area: {data.get('total_area_m2')} m²")
        print(f"  Floors: {data.get('floors')}")
        print(f"  Max Occupancy: {data.get('occupancy')} people")
        print(f"  Fire Load: {data.get('fire_load_mj_m2')} MJ/m²")
        print(f"  Application Category: {data.get('application_category')}")
        print(f"  Risk Class: {data.get('risk_class')}")
        print(f"  Fire Classification: {data.get('fire_classification')}")
        print(f"  Consultant: {data.get('consultant_name')}")
        print(f"  Client: {data.get('client_name')}")
        print("-" * 80)

    def create_building_project(self, extracted_data: Dict[str, Any]) -> BuildingProject:
        """
        Convert extracted data to BuildingProject model.

        Args:
            extracted_data: Dictionary from parse_project_pdf()

        Returns:
            BuildingProject instance
        """
        # Map numeric values to enums (convert to strings for ApplicationCategory and RiskClass)
        fire_class = FireClassification[extracted_data['fire_classification']]
        app_category = ApplicationCategory(str(extracted_data['application_category']))
        risk_class = RiskClass(str(extracted_data['risk_class']))

        return BuildingProject(
            project_name=extracted_data['project_name'],
            address=extracted_data['address'],
            municipality=extracted_data['municipality'],
            building_type=extracted_data['building_type'],
            total_area_m2=float(extracted_data['total_area_m2']),
            floors=int(extracted_data['floors']),
            occupancy=int(extracted_data['occupancy']),
            fire_load_mj_m2=extracted_data.get('fire_load_mj_m2'),
            application_category=app_category,
            risk_class=risk_class,
            fire_classification=fire_class,
            consultant_name=extracted_data.get('consultant_name', 'TBD'),
            consultant_certificate=extracted_data.get('consultant_certificate', 'TBD'),
            client_name=extracted_data.get('client_name', 'TBD')
        )

    def determine_required_documents(self, fire_classification: FireClassification) -> List[DocumentType]:
        """
        Automatically determine which documents are required based on fire classification.

        This implements the "Automatisk dokumentselektion" requirement from Del 1:
        - BK1: Only START and ITT
        - BK2: 8 document types
        - BK3-4: All 11 document types

        Args:
            fire_classification: The building's fire classification

        Returns:
            List of required DocumentType enums
        """
        print(f"\n📋 Determining required documents for {fire_classification.value}...")

        if fire_classification == FireClassification.BK1:
            # Simple buildings: Only starter declaration and installation technical report
            required = [DocumentType.START, DocumentType.ITT]
            print(f"  ✅ BK1: Requires {len(required)} documents (START, ITT)")

        elif fire_classification == FireClassification.BK2:
            # Standard commercial: 8 core documents
            required = [
                DocumentType.START,
                DocumentType.ITT,
                DocumentType.DBK,
                DocumentType.BSR,
                DocumentType.BPLAN,
                DocumentType.PFP,
                DocumentType.DIM,
                DocumentType.FUNK
            ]
            print(f"  ✅ BK2: Requires {len(required)} documents")

        else:  # BK3 or BK4
            # Large/complex buildings: All document types
            required = [
                DocumentType.START,
                DocumentType.ITT,
                DocumentType.DBK,
                DocumentType.BSR,
                DocumentType.BPLAN,
                DocumentType.PFP,
                DocumentType.DIM,
                DocumentType.FUNK,
                DocumentType.KPLA,
                DocumentType.KRAP,
                DocumentType.DKV,
                DocumentType.SLUT
            ]
            print(f"  ✅ {fire_classification.value}: Requires {len(required)} documents (all types)")

        # Print document list
        print("\n  Required document types:")
        for doc_type in required:
            print(f"    • {doc_type.value}: {self._get_document_description(doc_type)}")

        return required

    def _get_document_description(self, doc_type: DocumentType) -> str:
        """Get human-readable description of document type"""
        descriptions = {
            DocumentType.START: "Starterklæring (Start declaration)",
            DocumentType.ITT: "Installationsteknisk tilsyn (Installation technical report)",
            DocumentType.DBK: "Dokumentation for brandtekniske installationer (Fire system documentation)",
            DocumentType.BSR: "Brandsikringsredegørelse (Fire safety statement)",
            DocumentType.BPLAN: "Brandstrategi (Fire strategy plan)",
            DocumentType.PFP: "Plan for periodisk funktionsafprøvning (Periodic function testing plan)",
            DocumentType.DIM: "Dimensioneringsrapport (Dimensioning report)",
            DocumentType.FUNK: "Funktionsbeskrivelse (Function description)",
            DocumentType.KPLA: "Kontrolplan (Control plan)",
            DocumentType.KRAP: "Kontrolrapport (Control report)",
            DocumentType.DKV: "Drifts- og vedligeholdelsesplan (Operations & maintenance plan)",
            DocumentType.SLUT: "Sluterklæring (Final declaration)"
        }
        return descriptions.get(doc_type, "Unknown document type")


# Example usage
if __name__ == "__main__":
    parser = ProjectInputParser()

    # Example: Parse a project specification PDF
    # extracted_data = parser.parse_project_pdf("example_project_spec.pdf")
    # project = parser.create_building_project(extracted_data)
    # required_docs = parser.determine_required_documents(project.fire_classification)

    # For testing without actual PDF:
    test_data = {
        "project_name": "Kontorhus Aarhus C",
        "address": "Åboulevarden 23, 8000 Aarhus C",
        "municipality": "Aarhus",
        "building_type": "Office Building",
        "total_area_m2": 2500,
        "floors": 5,
        "occupancy": 150,
        "fire_load_mj_m2": 420,
        "application_category": 3,
        "risk_class": 2,
        "fire_classification": "BK2",
        "consultant_name": "Lars Nielsen",
        "consultant_certificate": "BRT-12345",
        "client_name": "Aarhus Properties A/S"
    }

    project = parser.create_building_project(test_data)
    required_docs = parser.determine_required_documents(project.fire_classification)

    print(f"\n✅ Project created: {project.project_name}")
    print(f"✅ Required documents: {len(required_docs)}")
