from google import genai
from google.genai import types
from typing import List, Dict, Optional
from config.settings import GEMINI_API_KEY, GEMINI_MODEL, TEMPERATURE, MAX_TOKENS
from src.models import BuildingProject, DocumentType, GeneratedDocument
from datetime import datetime
import uuid

class DocumentTemplateEngine:
    """Generate BR18 documents using templates and RAG context"""

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate_start_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """
        Generate START (Starterklæring) document

        Args:
            project: Building project details
            rag_context: Retrieved knowledge from RAG system

        Returns:
            Generated document
        """
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate a START (Starterklæring - Declaration) document for a BR18 fire safety submission.

PROJECT DETAILS:
- Project Name: {project.project_name}
- Address: {project.address}
- Municipality: {project.municipality}
- Building Type: {project.building_type}
- Total Area: {project.total_area_m2} m²
- Floors: {project.floors}
- Occupancy: {project.occupancy}
- Fire Classification: {project.fire_classification.value}
- Application Category: {project.application_category.value}
- Risk Class: {project.risk_class.value}
- Consultant: {project.consultant_name}
- Certificate: {project.consultant_certificate}
- Client: {project.client_name}

REFERENCE EXAMPLES AND REQUIREMENTS:
{context_str}

IMPORTANT REQUIREMENTS FOR {project.municipality}:
- Follow the exact structure from approved examples
- Include all required BR18 paragraph references (especially §508)
- List all required documents for {project.fire_classification.value} classification
- Use proper Danish terminology and formatting
- Include signature section for certified consultant

Generate a complete START document following the standard structure:
1. Document title and project information
2. Certified fire consultant declaration
3. Fire classification checkbox (mark {project.fire_classification.value})
4. Required documents checklist
5. Rescue service conditions
6. Control plan requirements
7. Signature section

Output in Danish, following BR18 regulations."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=TEMPERATURE,
                max_output_tokens=MAX_TOKENS,
            )
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()),
            project=project,
            document_type=DocumentType.START,
            content=response.text,
            rag_context_used=rag_context or []
        )

    def generate_dbk_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """
        Generate DBK (Documentation for fire classification) document

        Args:
            project: Building project details
            rag_context: Retrieved knowledge from RAG system

        Returns:
            Generated document
        """
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate a DBK (Dokumentation for Brandteknisk Klassificering) document for BR18 submission.

PROJECT DETAILS:
- Project Name: {project.project_name}
- Address: {project.address}
- Municipality: {project.municipality}
- Building Type: {project.building_type}
- Total Area: {project.total_area_m2} m²
- Floors: {project.floors}
- Fire Classification: {project.fire_classification.value}
- Fire Load: {project.fire_load_mj_m2 or 'Not specified'} MJ/m²

REFERENCE EXAMPLES AND REQUIREMENTS:
{context_str}

IMPORTANT REQUIREMENTS FOR {project.municipality}:
- Follow approved DBK document structure
- Include building description with all specifications
- Detail fire strategy principles (evacuation, construction protection, smoke/fire spread prevention)
- Reference specific BR18 paragraphs for each requirement
- Include rescue service conditions and access routes

Generate a complete DBK document following the standard structure:
1. Project information header
2. Building description (type, area, floors, usage)
3. Fire classification placement ({project.fire_classification.value})
4. Fire strategy principles:
   - Evacuation strategy (max distances, escape routes)
   - Construction protection (fire resistance classes R60, material classifications)
   - Prevention of smoke and fire spread
   - Rescue service conditions
5. BR18 paragraph references throughout
6. Consultant signature section

Output in Danish with proper technical terminology."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=TEMPERATURE,
                max_output_tokens=MAX_TOKENS,
            )
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()),
            project=project,
            document_type=DocumentType.DBK,
            content=response.text,
            rag_context_used=rag_context or []
        )

    def generate_kpla_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """
        Generate KPLA (Kontrolplan - Control Plan) document

        Args:
            project: Building project details
            rag_context: Retrieved knowledge from RAG system

        Returns:
            Generated document
        """
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate a KPLA (Kontrolplan - Control Plan) document for BR18 submission.

PROJECT DETAILS:
- Project Name: {project.project_name}
- Address: {project.address}
- Municipality: {project.municipality}
- Building Type: {project.building_type}
- Fire Classification: {project.fire_classification.value}

REFERENCE EXAMPLES AND REQUIREMENTS:
{context_str}

The control plan must specify:
1. Quality assurance procedures during construction
2. Inspection points for fire safety installations
3. Testing requirements for fire doors, barriers, and protection
4. Documentation requirements
5. Responsible parties for each control point
6. BR18 compliance verification procedures

Generate a comprehensive KPLA document in Danish following BR18 requirements."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=TEMPERATURE,
                max_output_tokens=MAX_TOKENS,
            )
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()),
            project=project,
            document_type=DocumentType.KPLA,
            content=response.text,
            rag_context_used=rag_context or []
        )

    def generate_document(
        self,
        project: BuildingProject,
        document_type: DocumentType,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """
        Generate any BR18 document type

        Args:
            project: Building project details
            document_type: Type of document to generate
            rag_context: Retrieved knowledge from RAG system

        Returns:
            Generated document
        """
        generators = {
            DocumentType.START: self.generate_start_document,
            DocumentType.DBK: self.generate_dbk_document,
            DocumentType.KPLA: self.generate_kpla_document,
        }

        generator = generators.get(document_type)
        if generator:
            return generator(project, rag_context)
        else:
            raise NotImplementedError(f"Generator for {document_type} not yet implemented")

    def generate_all_required_documents(
        self,
        project: BuildingProject,
        rag_retriever=None
    ) -> List[GeneratedDocument]:
        """
        Generate all required documents for a project based on fire classification

        Args:
            project: Building project details
            rag_retriever: RAG retrieval system (optional)

        Returns:
            List of generated documents
        """
        required_docs = project.get_required_documents()
        generated = []

        for doc_type_str in required_docs:
            try:
                doc_type = DocumentType(doc_type_str)

                # Retrieve relevant context if RAG system available
                rag_context = None
                if rag_retriever:
                    query = f"{project.municipality} {doc_type_str} requirements for {project.fire_classification.value}"
                    rag_context = rag_retriever.retrieve(query, top_k=5)

                # Generate document
                doc = self.generate_document(project, doc_type, rag_context)
                generated.append(doc)
                print(f"Generated {doc_type_str} document")

            except (NotImplementedError, ValueError) as e:
                print(f"Skipping {doc_type_str}: {e}")
                continue

        return generated
