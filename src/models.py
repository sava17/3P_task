from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
from enum import Enum

class FireClassification(str, Enum):
    """BR18 Fire classification levels"""
    BK1 = "BK1"
    BK2 = "BK2"
    BK3 = "BK3"
    BK4 = "BK4"

class ApplicationCategory(str, Enum):
    """BR18 Application categories (1-6)"""
    CAT_1 = "1"  # Single-family dwellings
    CAT_2 = "2"  # Multi-family dwellings
    CAT_3 = "3"  # Commercial/office
    CAT_4 = "4"  # Industrial/warehouse
    CAT_5 = "5"  # Places of assembly
    CAT_6 = "6"  # Special buildings

class RiskClass(str, Enum):
    """BR18 Risk classification (1-4)"""
    RISK_1 = "1"
    RISK_2 = "2"
    RISK_3 = "3"
    RISK_4 = "4"

class BuildingProject(BaseModel):
    """Represents a building project with fire safety requirements"""
    project_name: str
    address: str
    municipality: str
    building_type: str
    total_area_m2: float
    floors: int
    occupancy: int
    fire_load_mj_m2: Optional[float] = None
    application_category: ApplicationCategory
    risk_class: RiskClass
    fire_classification: FireClassification
    consultant_name: str
    consultant_certificate: str
    client_name: str

    def get_required_documents(self) -> List[str]:
        """Get list of required document types based on fire classification"""
        from config.settings import DOCUMENT_REQUIREMENTS
        return DOCUMENT_REQUIREMENTS.get(self.fire_classification.value, [])

class DocumentType(str, Enum):
    """BR18 Document types"""
    START = "START"  # Starterklæring (Declaration)
    ITT = "ITT"      # Indsatstaktisk Tegning (Tactical drawing)
    DBK = "DBK"      # Dokumentation for Brandteknisk Klassificering
    BSR = "BSR"      # Brandstrategi Rapport
    BPLAN = "BPLAN"  # Brandteknisk Plan
    PFP = "PFP"      # Passive Fire Protection
    DIM = "DIM"      # Dimensionering
    FUNK = "FUNK"    # Funktionskrav
    KPLA = "KPLA"    # Kontrolplan
    KRAP = "KRAP"    # Kontrolrapport
    DKV = "DKV"      # Dokumentation af kvalitetssikring
    SLUT = "SLUT"    # Sluterklæring

class GeneratedDocument(BaseModel):
    """Represents a generated BR18 document"""
    document_id: str
    project: BuildingProject
    document_type: DocumentType
    content: str
    generated_at: datetime = Field(default_factory=datetime.now)
    template_version: str = "1.0"
    rag_context_used: List[str] = Field(default_factory=list)

class MunicipalityFeedback(BaseModel):
    """Feedback from municipality on submitted document"""
    document_id: str
    municipality: str
    approved: bool
    feedback_text: Optional[str] = None
    rejection_reasons: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    received_at: datetime = Field(default_factory=datetime.now)

class LearningInsight(BaseModel):
    """Insights extracted from feedback analysis"""
    insight_id: str
    municipality: str
    document_type: DocumentType
    pattern_description: str
    examples: List[str]
    confidence_score: float
    extracted_at: datetime = Field(default_factory=datetime.now)
    applied_count: int = 0
    success_rate: float = 0.0

class KnowledgeChunk(BaseModel):
    """A chunk of knowledge for RAG system"""
    chunk_id: str
    source_type: Literal["regulation", "approved_doc", "feedback", "insight"]
    source_reference: str
    municipality: Optional[str] = None
    document_type: Optional[DocumentType] = None
    content: str
    metadata: Dict = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.now)
