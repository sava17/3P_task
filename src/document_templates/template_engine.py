from google import genai
from google.genai import types
from typing import List, Dict, Optional
from config.settings import GEMINI_API_KEY, GEMINI_MODEL, TEMPERATURE, MAX_TOKENS
from src.models import BuildingProject, DocumentType, GeneratedDocument
from datetime import datetime
import uuid

class DocumentTemplateEngine:
    """Generate BR18 documents using templates and RAG context"""

    def __init__(self, vector_store=None):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.vector_store = vector_store  # Optional vector store for enhanced retrieval

    def _retrieve_enhanced_context(
        self,
        query: str,
        municipality: Optional[str] = None,
        document_type: Optional[str] = None,
        include_br18: bool = True
    ) -> List[str]:
        """
        Retrieve context from both example documents AND BR18 regulations

        Args:
            query: Search query
            municipality: Filter by municipality for examples
            document_type: Filter by document type for examples
            include_br18: Whether to include BR18 regulation context

        Returns:
            List of context strings (examples + regulations)
        """
        if not self.vector_store:
            return []

        context_parts = []

        # 1. Retrieve example documents (for structure/style)
        example_chunks = self.vector_store.search(
            query=query,
            top_k=3,  # Get top 3 examples
            municipality=municipality,
            document_type=document_type
        )
        for chunk in example_chunks:
            context_parts.append(f"[EXAMPLE from {chunk.source_reference}]\n{chunk.content}")

        # 2. Retrieve BR18 regulations (for accurate § citations)
        if include_br18:
            # Search specifically for regulation chunks
            from src.rag_system.vector_store import VectorStore
            # Create a custom query for BR18 regulations
            regulation_query = f"BR18 fire safety regulations {query}"

            # Fetch regulation chunks - need to query directly with where filter
            # Since we can't filter by source_type in search(), we'll use a workaround
            all_results = self.vector_store.search(query=regulation_query, top_k=10)

            # Filter to only regulation chunks
            regulation_chunks = [chunk for chunk in all_results if chunk.source_type == "regulation"][:3]

            for chunk in regulation_chunks:
                context_parts.append(f"[BR18 REGULATION]\n{chunk.content}")

        return context_parts

    def generate_start_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """
        Generate START (Starterklæring) document

        Args:
            project: Building project details
            rag_context: Retrieved knowledge from RAG system (optional, will use enhanced retrieval if available)

        Returns:
            Generated document
        """
        # Use enhanced retrieval if vector_store is available and no context provided
        if rag_context is None and self.vector_store:
            query = f"START declaration {project.fire_classification.value} {project.municipality}"
            rag_context = self._retrieve_enhanced_context(
                query=query,
                municipality=project.municipality,
                document_type="START"
            )

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
            rag_context: Retrieved knowledge from RAG system (optional, will use enhanced retrieval if available)

        Returns:
            Generated document
        """
        # Use enhanced retrieval if vector_store is available and no context provided
        if rag_context is None and self.vector_store:
            query = f"DBK fire classification {project.fire_classification.value} evacuation fire strategy"
            rag_context = self._retrieve_enhanced_context(
                query=query,
                municipality=project.municipality,
                document_type="DBK"
            )

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

    def generate_itt_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """Generate ITT (Indsatstaktisk Tegning - Rescue Service Tactical Conditions) document"""
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate an ITT (Redningsberedskabets indsatsforhold - Rescue Service Tactical Conditions) document for BR18 submission.

PROJECT DETAILS:
- Project: {project.project_name}
- Address: {project.address}
- Municipality: {project.municipality}
- Building Type: {project.building_type}
- Total Area: {project.total_area_m2} m²
- Floors: {project.floors}
- Fire Classification: {project.fire_classification.value}

REFERENCE EXAMPLES:
{context_str}

Generate a complete ITT document in Danish covering:
1. Building access for rescue services
2. Water supply locations and capacity
3. Rescue operation areas and limitations
4. Special hazards or conditions
5. Emergency contact information
6. BR18 §§126-133 compliance

Output in Danish following BR18 requirements for rescue service conditions."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL, contents=[prompt],
            config=types.GenerateContentConfig(temperature=TEMPERATURE, max_output_tokens=MAX_TOKENS)
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()), project=project,
            document_type=DocumentType.ITT, content=response.text,
            rag_context_used=rag_context or []
        )

    def generate_bsr_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """Generate BSR (Brandstrategirapport - Fire Strategy Report) document"""
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate a BSR (Brandstrategirapport - Fire Strategy Report) for BR18 submission.

PROJECT DETAILS:
- Project: {project.project_name}
- Building Type: {project.building_type}
- Total Area: {project.total_area_m2} m²
- Floors: {project.floors}
- Fire Classification: {project.fire_classification.value}
- Occupancy: {project.occupancy} persons

REFERENCE EXAMPLES:
{context_str}

Generate a comprehensive BSR document in Danish covering:
1. Overall fire safety strategy and principles
2. Fire compartmentalization strategy
3. Evacuation strategy and routes
4. Active fire protection systems
5. Passive fire protection measures
6. Integration with building systems
7. BR18 compliance documentation

Output in Danish with proper technical terminology."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL, contents=[prompt],
            config=types.GenerateContentConfig(temperature=TEMPERATURE, max_output_tokens=MAX_TOKENS)
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()), project=project,
            document_type=DocumentType.BSR, content=response.text,
            rag_context_used=rag_context or []
        )

    def generate_bplan_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """Generate BPLAN (Brandplaner og situationsplan - Fire Plans and Site Plan) document"""
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate BPLAN (Brandplaner og situationsplan - Fire Plans and Site Plan) for BR18 submission.

PROJECT DETAILS:
- Project: {project.project_name}
- Address: {project.address}
- Total Area: {project.total_area_m2} m²
- Floors: {project.floors}

REFERENCE EXAMPLES:
{context_str}

Generate a BPLAN document in Danish describing:
1. Site plan with fire safety elements
2. Floor plans showing:
   - Fire compartments and barriers
   - Evacuation routes and exits
   - Fire equipment locations
   - Fire-rated walls and doors
3. Technical drawings references
4. Legend and symbols explanation

Output in Danish following BR18 technical drawing requirements."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL, contents=[prompt],
            config=types.GenerateContentConfig(temperature=TEMPERATURE, max_output_tokens=MAX_TOKENS)
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()), project=project,
            document_type=DocumentType.BPLAN, content=response.text,
            rag_context_used=rag_context or []
        )

    def generate_pfp_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """Generate PFP (Pladsfordelingsplaner - Occupancy Distribution Plans) document"""
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate PFP (Pladsfordelingsplaner - Occupancy Distribution Plans) for BR18 submission.

PROJECT DETAILS:
- Project: {project.project_name}
- Building Type: {project.building_type}
- Total Area: {project.total_area_m2} m²
- Occupancy: {project.occupancy} persons

REFERENCE EXAMPLES:
{context_str}

Generate a PFP document in Danish covering:
1. Occupancy calculations per floor/area
2. Person density per room/zone
3. Maximum permitted occupancy
4. Evacuation capacity verification
5. BR18 occupancy requirements compliance

Output in Danish with calculations and justifications."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL, contents=[prompt],
            config=types.GenerateContentConfig(temperature=TEMPERATURE, max_output_tokens=MAX_TOKENS)
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()), project=project,
            document_type=DocumentType.PFP, content=response.text,
            rag_context_used=rag_context or []
        )

    def generate_dim_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """Generate DIM (Brandteknisk dimensionering - Fire Engineering Calculations) document"""
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate DIM (Brandteknisk dimensionering - Fire Engineering Calculations) for BR18 submission.

PROJECT DETAILS:
- Project: {project.project_name}
- Building Type: {project.building_type}
- Fire Classification: {project.fire_classification.value}
- Fire Load: {project.fire_load_mj_m2 or 'To be determined'} MJ/m²

REFERENCE EXAMPLES:
{context_str}

Generate a DIM document in Danish with calculations for:
1. Fire load calculations
2. Evacuation time calculations
3. Smoke control dimensioning
4. Fire resistance requirements
5. Sprinkler/suppression system design (if applicable)
6. Heat release rate calculations
7. BR18 calculation methods and references

Required for BK3-4 classifications. Output in Danish with detailed calculations."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL, contents=[prompt],
            config=types.GenerateContentConfig(temperature=TEMPERATURE, max_output_tokens=MAX_TOKENS)
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()), project=project,
            document_type=DocumentType.DIM, content=response.text,
            rag_context_used=rag_context or []
        )

    def generate_funk_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """Generate FUNK (Funktionsbeskrivelse - Functional Description of Fire Safety Systems) document"""
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate FUNK (Funktionsbeskrivelse - Functional Description) for fire safety systems in BR18 submission.

PROJECT DETAILS:
- Project: {project.project_name}
- Building Type: {project.building_type}
- Fire Classification: {project.fire_classification.value}

REFERENCE EXAMPLES:
{context_str}

Generate a FUNK document in Danish describing:
1. Fire alarm system functionality
2. Smoke detection and alarm
3. Sprinkler/suppression systems (if applicable)
4. Smoke exhaust systems
5. Fire doors and barriers operation
6. Emergency lighting and signage
7. Integration between systems
8. Testing and maintenance requirements
9. BR18 compliance for each system

Output in Danish with detailed functional descriptions."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL, contents=[prompt],
            config=types.GenerateContentConfig(temperature=TEMPERATURE, max_output_tokens=MAX_TOKENS)
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()), project=project,
            document_type=DocumentType.FUNK, content=response.text,
            rag_context_used=rag_context or []
        )

    def generate_krap_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """Generate KRAP (Kontrolrapporter - Control Reports) document"""
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate KRAP (Kontrolrapporter - Control Reports) template for BR18 submission.

PROJECT DETAILS:
- Project: {project.project_name}
- Fire Classification: {project.fire_classification.value}

REFERENCE EXAMPLES:
{context_str}

Generate a KRAP document template in Danish for recording:
1. Control point inspections during construction
2. Fire door installation verification
3. Fire barrier inspections
4. Fire safety system testing results
5. Material certification verification
6. Deviations and corrective actions
7. Sign-off by responsible parties
8. BR18 compliance verification

Output in Danish as a template for documentation during construction."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL, contents=[prompt],
            config=types.GenerateContentConfig(temperature=TEMPERATURE, max_output_tokens=MAX_TOKENS)
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()), project=project,
            document_type=DocumentType.KRAP, content=response.text,
            rag_context_used=rag_context or []
        )

    def generate_dkv_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """Generate DKV (Drift-, kontrol- og vedligeholdelse - Operation, Control and Maintenance) document"""
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate DKV (Drift-, kontrol- og vedligeholdelse - Operation, Control and Maintenance) for BR18 submission.

PROJECT DETAILS:
- Project: {project.project_name}
- Building Type: {project.building_type}

REFERENCE EXAMPLES:
{context_str}

Generate a DKV document in Danish with instructions for:
1. Fire safety system operation procedures
2. Regular inspection schedules and checklists
3. Maintenance requirements and intervals
4. Testing procedures for fire safety equipment
5. Documentation and record keeping
6. Responsible parties and contacts
7. Emergency procedures
8. BR18 compliance maintenance

Output in Danish as operational instructions for building management."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL, contents=[prompt],
            config=types.GenerateContentConfig(temperature=TEMPERATURE, max_output_tokens=MAX_TOKENS)
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()), project=project,
            document_type=DocumentType.DKV, content=response.text,
            rag_context_used=rag_context or []
        )

    def generate_slut_document(
        self,
        project: BuildingProject,
        rag_context: Optional[List[str]] = None
    ) -> GeneratedDocument:
        """Generate SLUT (Sluterklæring - Final Declaration) document"""
        context_str = "\n\n".join(rag_context) if rag_context else ""

        prompt = f"""Generate SLUT (Sluterklæring - Final Declaration) for BR18 submission.

PROJECT DETAILS:
- Project: {project.project_name}
- Address: {project.address}
- Fire Classification: {project.fire_classification.value}
- Consultant: {project.consultant_name}

REFERENCE EXAMPLES:
{context_str}

Generate a SLUT document in Danish with:
1. Certified fire consultant's final declaration
2. Confirmation that construction matches approved plans
3. Verification of all fire safety installations
4. Statement of BR18 compliance
5. Control report references
6. Any deviations and approved solutions
7. Signature and certification
8. Date of final inspection

Output in Danish following official declaration format."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL, contents=[prompt],
            config=types.GenerateContentConfig(temperature=TEMPERATURE, max_output_tokens=MAX_TOKENS)
        )

        return GeneratedDocument(
            document_id=str(uuid.uuid4()), project=project,
            document_type=DocumentType.SLUT, content=response.text,
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
            DocumentType.ITT: self.generate_itt_document,
            DocumentType.DBK: self.generate_dbk_document,
            DocumentType.BSR: self.generate_bsr_document,
            DocumentType.BPLAN: self.generate_bplan_document,
            DocumentType.PFP: self.generate_pfp_document,
            DocumentType.DIM: self.generate_dim_document,
            DocumentType.FUNK: self.generate_funk_document,
            DocumentType.KPLA: self.generate_kpla_document,
            DocumentType.KRAP: self.generate_krap_document,
            DocumentType.DKV: self.generate_dkv_document,
            DocumentType.SLUT: self.generate_slut_document,
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
