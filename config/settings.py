import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EXAMPLE_PDFS_DIR = DATA_DIR / "example_pdfs"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
FEEDBACK_DIR = DATA_DIR / "feedback"
GENERATED_DOCS_DIR = DATA_DIR / "generated_docs"

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model settings
GEMINI_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 768  # Recommended dimension for Gemini embeddings (768, 1536, or 3072)

# RAG settings
VECTOR_INDEX_PATH = KNOWLEDGE_BASE_DIR / "embeddings.ann"
CHUNKS_PATH = KNOWLEDGE_BASE_DIR / "chunks.json"
TOP_K_RETRIEVAL = 5

# Document generation settings
TEMPERATURE = 0.3  # Lower for more consistent document generation
MAX_TOKENS = 8192

# Fire classification document requirements (BR18)
DOCUMENT_REQUIREMENTS = {
    "BK1": ["START", "ITT"],
    "BK2": ["START", "ITT", "DBK", "BSR", "BPLAN", "PFP", "DIM", "FUNK"],
    "BK3": ["START", "ITT", "DBK", "BSR", "BPLAN", "PFP", "DIM", "FUNK", "KPLA", "KRAP", "DKV"],
    "BK4": ["START", "ITT", "DBK", "BSR", "BPLAN", "PFP", "DIM", "FUNC", "KPLA", "KRAP", "DKV", "SLUT"]
}

# Learning settings
FEEDBACK_BATCH_SIZE = 10
LEARNING_INTERVAL_HOURS = 24
MIN_FEEDBACK_FOR_LEARNING = 5
