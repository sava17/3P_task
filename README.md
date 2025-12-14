# BR18 Document Automation System

**Automated generation of fire safety documentation for building projects in Denmark**

## 📋 Overview

This system automates the creation of BR18 (Danish Building Regulations 2018) fire safety documents using AI-powered document generation with RAG (Retrieval-Augmented Generation). The system learns from approved example documents and BR18 regulations to generate accurate, compliant documentation.

### Key Features

✅ **Automatic Project Data Extraction** (Del 1)

- Parse project specification PDFs
- Extract building details, fire classification, and requirements
- Automatically determine required document types

✅ **Knowledge Base & RAG System** (Del 2)

- Upload and process approved BR18 example documents
- **Extract document-type-specific insights** (approved phrasings, fire strategies, certifications)
- **Save insights to vector database** for future document generation
- Embed BR18 regulations for accurate paragraph citations
- Vector database (ChromaDB) for intelligent retrieval
- Municipal response parsing (approvals/rejections) → golden records & negative constraints

✅ **Intelligent Document Generation**

- Generate START, ITT, DBK, and other BR18 documents
- Context-aware generation using RAG
- Accurate BR18 § paragraph references
- Comparison mode (with/without knowledge)

✅ **BR18 Regulation Integration**

- Upload BR18.pdf for regulation embedding
- Automatic paragraph citation (§508, §93, etc.)
- Update handling when BR18 changes
- Validation against current regulations

---

## 🎯 Assignment Requirements Coverage

### Del 1: Automatic Project Input Processing

- [x] Parse project specification PDFs
- [x] Extract building parameters automatically
- [x] Determine required document types based on fire classification
- [x] Intelligent form filling with correct paragraph references

### Del 2: Knowledge Base & Learning

- [x] Process approved example documents
- [x] RAG system with vector embeddings
- [x] Municipal response parsing (Afslag/Godkendelse)
- [x] BR18 regulation embedding and update handling
- [x] Confidence scoring and golden record extraction

### Del 3: Validation & Quality

- [x] **Validation through RAG context** - BR18 § citations verified during generation
- [x] **BR18 update handling** - Re-upload BR18.pdf → automatic citation updates
- [x] Confidence-based knowledge ranking
- [x] Comparison between documents with/without knowledge
- [x] Knowledge base browser and statistics

**Note on Quality Control:** The system validates during generation rather than post-generation. By embedding BR18 regulations in the vector database and retrieving relevant § paragraphs during document generation, the AI model produces accurate citations from the start. This eliminates the need for post-hoc validation and ensures compliance with the latest BR18 version.

---

## 🏗️ Architecture

```
br18_automation/
├── src/
│   ├── pdf_processing/         # PDF extraction with Gemini Vision
│   │   └── pdf_extractor.py
│   ├── rag_system/             # Vector database & retrieval
│   │   └── vector_store.py
│   ├── document_templates/      # Document generation
│   │   └── template_engine.py
│   ├── learning_engine/         # Confidence scoring
│   │   └── confidence_scorer.py
│   ├── parsers/                # Municipal response & project parsing
│   │   ├── municipal_response_parser.py
│   │   └── project_input_parser.py
│   └── models.py               # Data models
├── config/
│   └── settings.py             # Configuration
├── data/
│   ├── BR18.pdf               # Building regulations
│   ├── example_pdfs/          # Approved examples
│   ├── knowledge_base/        # ChromaDB vector store
│   └── generated_docs/        # Output documents
│       ├── without_knowledge/  # Baseline documents
│       └── with_knowledge/     # RAG-enhanced documents
├── prototype_gui.py           # Main GUI application
├── demo.py                    # CLI demo system
└── README.md
```

---

## 🚀 Installation & Setup

### Prerequisites

- **Python 3.10+**
- **Anaconda** (recommended)
- **Gemini API Key** (Google AI Studio)

### Step 1: Create Environment

```bash
conda create -n 3P python=3.10
conda activate 3P
```

### Step 2: Install Dependencies

```bash
pip install customtkinter
pip install google-generativeai
pip install chromadb
pip install pypdf
pip install python-dotenv
```

### Step 3: Configure API Key

Create `.env` file in project root:

```env
GEMINI_API_KEY=your_api_key_here
```

Get your API key from (the one in the project is my IP restricted one): [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### Step 4: Run the Application

**Windows:**

```bash
run_prototype_gui.bat
```

**Manual:**

```bash
python prototype_gui.py
```

---

## 📖 User Guide

### Tab 1: Parse Project Input (Del 1)

**Purpose:** Automatically extract building project data from PDFs

**Steps:**

1. Click "📁 Select Project PDF"
2. Choose your project specification PDF
3. Click "⚙️ Parse Project PDF"
4. Review extracted data (name, address, fire classification, etc.)
5. Optionally edit data before proceeding

**Output:** Automatically populated project form with required document types

---

### Tab 2: Knowledge Base Setup (Del 2)

**Purpose:** Build the RAG knowledge base from approved documents and BR18

#### 2A: Upload Example Documents

**Steps:**

1. Click "📁 Add PDF Files"
2. Select approved START/DBK example documents
3. Click "⚙️ Extract & Build Knowledge Base"
4. Wait for extraction and embedding (~1-2 min per document)

**What Happens:**

- Extracts text content from PDFs using Gemini Vision
- Chunks documents into ~500-word segments
- Extracts general metadata (project name, municipality, fire class, etc.)
- **Extracts document-type-specific insights:**
  - DBK: Approved phrasings for fire classification
  - START: Typical certification conditions
  - BSR: Successful fire strategies
- **Saves both chunks AND insights** to vector database with metadata

**Output:** Vector database populated with example document chunks + insights

#### 2B: Upload BR18 Regulation

**Steps:**

1. Click "📤 Upload BR18.pdf"
2. Select `data/BR18.pdf`
3. Wait for regulation extraction (~1-2 minutes)
4. Status shows: "✅ Loaded (X chunks)"

**Output:** BR18 paragraphs embedded for citation in generated documents

**Updating BR18 (when new regulation version is released):**

1. Replace `data/BR18.pdf` with new version
2. Click "📤 Upload BR18.pdf" again
3. System automatically:
   - ✅ Detects existing BR18 chunks
   - 🗑️ Deletes old BR18 version
   - 📝 Adds new BR18 version
4. Future documents now use updated regulations

#### 2C: Parse Municipal Response (Optional)

**Steps:**

1. Upload municipal Afslag (rejection) or Godkendelse (approval)
2. Click "⚙️ Parse Municipal Response"
3. System extracts patterns and adds to knowledge base

**Output:**

- Rejections → Negative constraints (patterns to avoid)
- Approvals → Golden records (patterns to follow)

---

### Tab 3: Generate Documents

**Purpose:** Generate BR18 fire safety documents

**Steps:**

1. Enter project details (or use parsed data from Tab 1)
2. Click "💾 Save Project"
3. Select document types to generate
4. **Choose mode:**
   - ✅ **WITHOUT knowledge** - Baseline documents for comparison
   - ⬜ **WITH knowledge** - Enhanced documents using RAG
5. Click "📝 Generate BR18 Documents"
6. Documents saved to:
   - `data/generated_docs/without_knowledge/` (baseline)
   - `data/generated_docs/with_knowledge/` (enhanced)

**Template Projects:**

- Office Building BK2 (commercial)
- Garage BK1 (simple)

**Output:** Generated .txt files with full BR18 documentation

---

### Tab 4: View Knowledge Base

**Purpose:** Browse and query the knowledge base

**Features:**

- **Statistics Dashboard:** Total chunks, golden records, negative constraints
- **Search:** Query knowledge base with filters
- **Quick Views:**
  - 📊 View All Stats
  - ✅ Golden Records (approved patterns)
  - ⚠️ Negative Constraints (rejected patterns)

---

## 🧠 Metadata vs Insights: Dual Extraction Strategy

### Why Extract BOTH Metadata AND Insights?

The system performs **two types of extraction** from each example document, each serving a distinct purpose in the RAG system:

#### 📊 Metadata Extraction (Who, What, Where)

**Extracted fields:**

- Project name, address, municipality
- Building type, area (m²), floors, occupancy
- Fire classification (BK1-4), application category, risk class
- Consultant name and certificate number
- BR18 paragraph references

**Purpose:** Enable precise filtering and retrieval

**Example use case:**

```
Query: "Generate DBK for 1500m² warehouse in København, BK2"

With metadata filtering:
✅ Retrieves: 3 DBK documents, all warehouses, all BK2, 2 from København
❌ Without: Random mix of START, residential buildings, BK1 projects
```

**Benefits:**

- 🎯 Municipality-specific learning ("How does København format DBK?")
- 📏 Size-appropriate examples (similar m² projects)
- 🔥 Fire class matching (BK2 examples for BK2 generation)
- 📊 Statistics dashboard ("10 examples from 5 municipalities")
- 🔍 Advanced search ("Show all warehouse DBK documents")

---

#### 🧠 Insights Extraction (How to Write)

**Document-type-specific insights:**

**DBK Insights:**

- Approved phrasing: "Byggeriet kan indplaceres i Brandklasse 2"
- Technical specs: Material classes (K1 10/B-s1,d0), fire resistance (R 60)
- Structural patterns: Section ordering, how to reference ITT
- Distance specifications: "30 m til nærmeste udgang"

**START Insights:**

- Certification patterns: How to present consultant credentials
- Declaration phrases: "Det angives hermed: At dokumentationen..."
- Compliance language: "byggeriet vil overholde bygningsreglementets brandkrav"
- Document structure: Checkbox format, certificate copy as final page

**BSR Insights:**

- Fire strategy approaches: Risk analysis methodology
- Justification language: How design choices are explained to authorities
- Technical solutions: Fire protection systems, evacuation strategies
- Scenario analysis: How fire scenarios are presented

**Purpose:** Enable quality content generation

**Benefits:**

- ✍️ Professional writing style matching approved examples
- 📝 Correct technical terminology and material classifications
- 🏗️ Proper document structure and section ordering
- ⚖️ Compliance-focused language patterns
- 🔗 Accurate BR18 paragraph citation formats

---

#### 💡 Why Both Together?

| Aspect                    | Metadata Only | Insights Only | Both (Current) |
| ------------------------- | ------------- | ------------- | -------------- |
| **Filtering precision**   | ✅ Excellent   | ❌ None        | ✅ Excellent    |
| **Content quality**       | ❌ Generic     | ✅ Good        | ✅ Excellent    |
| **Municipality learning** | ✅ Yes         | ❌ No          | ✅ Yes          |
| **Approved phrasing**     | ❌ No          | ✅ Yes         | ✅ Yes          |
| **Search capability**     | ✅ Yes         | ❌ No          | ✅ Yes          |
| **Statistics**            | ✅ Yes         | ❌ No          | ✅ Yes          |
| **Cost per document**     | ~$0.05        | ~$0.05        | ~$0.10         |

**Verdict:** The ~$0.05 extra cost per document for dual extraction pays off with:

- More relevant RAG retrieval (metadata filtering)
- Higher quality output (insights-informed generation)
- Production-ready features (search, statistics, municipality patterns)

**Example in practice:**

```python
# User generates DBK for København warehouse, BK2
query = "Generate DBK document"
project = BuildingProject(municipality="København", fire_class="BK2", type="warehouse")

# Step 1: Metadata filters retrieval
filtered_chunks = vector_store.retrieve(
    query=query,
    filters={
        "document_type": "DBK",
        "municipality": "København",  # Metadata
        "fire_classification": "BK2"   # Metadata
    }
)

# Step 2: Insights inform generation
context = [
    chunk.content +  # Actual text
    chunk.metadata['insights']['approved_phrasing'] +  # How to write
    chunk.metadata['insights']['technical_specs']      # What to include
    for chunk in filtered_chunks
]

# Result: Document that matches København's style AND includes correct technical specs
```

---

## 🧠 How RAG Works

### Without Knowledge (Baseline)

```
User Input → Gemini 2.5 Flash → Basic Document
```

**Result:** Generic document without specific examples or BR18 citations

### With Knowledge (RAG)

```
User Input → Query Vector DB → Retrieve:
  • 3x Example Documents (structure/style)
  • 3x BR18 Paragraphs (regulations)
    ↓
  Combined Context → Gemini 2.5 Flash → Enhanced Document
```

**Result:** Professional document with accurate BR18 § references

---

## 📊 Technologies Used

| Component           | Technology           | Purpose                              |
| ------------------- | -------------------- | ------------------------------------ |
| **AI Model**        | Gemini 2.5 Flash     | PDF extraction & document generation |
| **Vector Database** | ChromaDB             | Embedding storage & retrieval        |
| **Embeddings**      | Gemini Embedding 001 | Text embeddings (768 dimensions)     |
| **PDF Processing**  | Gemini Vision        | Extract text from PDFs               |
| **GUI Framework**   | CustomTkinter        | Modern dark theme UI                 |
| **Language**        | Python 3.10          | Core implementation                  |

---

## 🎓 Key Innovations

### 1. Dual-Source RAG Retrieval

- Retrieves **both** example documents (style) AND BR18 regulations (content)
- Ensures accurate citations while maintaining professional structure

### 2. Confidence-Based Learning

- Scores knowledge chunks based on:
  - Approval status (approved > neutral > rejected)
  - Source quality (golden records > examples > synthetic)
  - Pattern strength (explicit > implicit)
- Prioritizes high-confidence patterns during retrieval

### 3. Comparison Mode

- Generate documents **without** knowledge (baseline)
- Generate documents **with** knowledge (enhanced with insights + BR18)
- Side-by-side comparison demonstrates RAG learning effectiveness

### 4. Validation Through RAG Context

- Quality control happens **during generation**, not after
- BR18 § paragraphs retrieved from vector database as context
- AI model generates accurate citations from authoritative source
- Re-upload BR18.pdf → all future documents use updated regulations
- No post-hoc validation needed when source is always current

---

## 📁 Output Example

**Filename:** `Garage_ved_Villa_Hansen_START_with_knowledge_20251210_143025.txt`

**Structure:**

```
================================================================================
BR18 DOCUMENT - START
================================================================================

Project: Garage ved Villa Hansen
Address: Møllevej 12, 8000 Aarhus C
Municipality: Aarhus
Fire Classification: BK1
Building Type: Garage
Total Area: 50 m²
Floors: 1
Max Occupancy: 2

Consultant: Lars Nielsen
Certificate: BRC-2341
Client: Jensen Familie

Generated: 2025-12-10 14:30:25
Document ID: abc123...

================================================================================
DOCUMENT CONTENT
================================================================================

[Generated BR18 documentation with accurate § references]
```

---

## 🔧 Configuration

Edit `config/settings.py`:

```python
# RAG settings
TOP_K_RETRIEVAL = 5  # Number of chunks retrieved

# Model settings
GEMINI_MODEL = "gemini-2.5-flash"
TEMPERATURE = 0.3  # Lower = more consistent
MAX_TOKENS = 8192

# Document requirements by fire class
DOCUMENT_REQUIREMENTS = {
    "BK1": ["START", "ITT"],
    "BK2": ["START", "ITT", "DBK", "BSR", "BPLAN", "PFP", "DIM", "FUNK"],
    ...
}
```

---

## 🐛 Troubleshooting

### "Failed to extract PDF"

- Ensure Gemini API key is valid in `.env`
- Check PDF is not corrupted
- Try smaller PDF (<5MB)

### "No chunks retrieved from knowledge base"

- Upload example documents first (Tab 2)
- Upload BR18.pdf for regulations
- Check vector database has data (Tab 4 → View All Stats)

### "Generated document missing BR18 references"

- Ensure BR18.pdf is uploaded (Tab 2)
- Check status shows "✅ Loaded"
- Regenerate with knowledge base populated

---

## 📈 Performance

| Operation                             | Time    | Cost (approx)    |
| ------------------------------------- | ------- | ---------------- |
| Parse project PDF                     | 10-30s  | $0.02            |
| Extract example document              | 30-60s  | $0.10            |
| Upload BR18 regulation                | 1-2 min | $0.15 (one-time) |
| Generate document (without knowledge) | 15-30s  | $0.03            |
| Generate document (with knowledge)    | 20-40s  | $0.05            |

**Total setup cost:** ~$0.50-1.00 (one-time)
**Per document cost:** ~$0.03-0.05

---

## 🔐 Data Privacy

- All processing done via Google Gemini API
- No data stored on external servers beyond API calls
- Vector database stored locally in `data/knowledge_base/`
- Generated documents saved locally

---

## 👤 Author

**Samuel A.V. Andersen**

- Assignment: BR18 Document Automation
- Date: December 2025

---

## 🚀 Future Development

With real operational data across 100+ projects, the system can be extended with:

### Advanced Quality Validation

- LLM-based section completeness checking

---

## 📺 Demo Video

[Watch Demo Video](./Final_demo.mp4)
