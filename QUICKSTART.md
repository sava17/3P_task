# Quick Start Guide

## Getting Started in 5 Minutes

### 1. Install Dependencies

**Using Anaconda Environment (Recommended):**

```bash
# Activate your environment
conda activate 3P

# Install dependencies
cd "D:\Jobsøgning\3P Opgave\br18_automation"
pip install -r requirements.txt
```

**Or using regular Python:**

```bash
cd "D:\Jobsøgning\3P Opgave\br18_automation"
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create a `.env` file in the project root:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

**Get API Key:**
- Gemini: https://aistudio.google.com/apikey
  - Free tier includes embeddings and generation

### 3. Run the Demo

**Option A: GUI Demo (Recommended for Presentations)** 🖥️

```bash
# Windows - Auto-activates Anaconda environment
run_demo_gui.bat

# Or manually with Anaconda
conda activate 3P
python demo_gui.py
```

**Option B: Command Line Demo**

```bash
# Windows - Auto-activates Anaconda environment
run_demo.bat

# Or manually with Anaconda
conda activate 3P
python demo.py
```

**Note:** The `.bat` files automatically activate the `E:\Anaconda_envs\3P` environment.

The demo will:
1. Extract knowledge from the example BR18 PDFs
2. Generate initial documents (40% approval rate)
3. Simulate municipality feedback
4. Learn patterns using Gemini
5. Generate improved documents (75% approval rate)
6. Show improvement metrics

**Total runtime:** ~3-5 minutes (depends on API response times)

### 4. What to Watch For

The demo has **6 interactive steps**. Press Enter to advance between steps.

**Key Moments:**

1. **Step 1:** Watch it extract START and DBK documents
   - See structured metadata extraction
   - Observe chunking for RAG

2. **Step 4:** ⭐ **MOST IMPORTANT** - The Learning Step
   - Gemini analyzes municipality feedback
   - Extracts 5-10 specific patterns
   - Shows confidence scores
   - Examples: "København requires explicit §508 references" (85% confidence)

3. **Step 6:** See the improvement metrics
   - Approval rate: 40% → 75%
   - Knowledge base growth
   - Municipality-specific learning

## Understanding the Output

### Step 1 Output Example
```
Processing: START - Starterklæring.pdf
  - Extracted 12450 characters
  - Created 25 chunks
  - Metadata: START

Adding 50 chunks to vector database...
Built vector index with 50 chunks

Vector Store Statistics:
  Total chunks: 50
  By source: {'approved_doc': 50}
  By municipality: {'København': 25, 'Ishøj': 25}
```

### Step 4 Output Example (The Learning!)
```
Analyzing 5 feedback items...
Using Gemini 2.5 Flash to extract patterns...

✨ Extracted 8 Learning Insights:

1. København requires explicit reference to BR18 §508 in declaration
   Confidence: 85%
   Municipality: København

2. Evacuation distances must be specified in meters, not just "adequate"
   Confidence: 78%
   Municipality: København

3. Fire resistance classes must use exact format (R60, not "60 minutes")
   Confidence: 92%
   Municipality: Aarhus

...

Converting insights to knowledge chunks for RAG system...
Added 8 new knowledge chunks from learning

Updated Vector Store:
  Total chunks: 58
  By source: {'approved_doc': 50, 'insight': 8}
```

### Step 6 Output Example (Metrics)
```
📊 PERFORMANCE METRICS:
  Initial Approval Rate:   40%
  After Learning:          75%
  Improvement:             +35%

📈 KNOWLEDGE BASE GROWTH:
  Total Knowledge Chunks:  58
  From Approved Docs:      50
  From Learned Insights:   8

🎯 MUNICIPALITY-SPECIFIC LEARNING:
  København: 30 knowledge chunks
  Aarhus: 18 knowledge chunks
  Aalborg: 10 knowledge chunks
```

## Troubleshooting

### API Key Errors

**Error:** `google.genai.types.GenerateContentError: API key not valid`

**Fix:**
1. Check your `.env` file exists in `br18_automation/` folder
2. Verify API key is correct (no quotes around the key)
3. Make sure you have Gemini API access enabled

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'google.genai'`

**Fix:**
```bash
pip install --upgrade google-genai annoy pydantic pypdf2
```

### Path Errors

**Error:** `FileNotFoundError: example_pdfs/`

**Fix:** The example PDFs should be in `data/example_pdfs/`. They were copied from your original folder during setup.

## Project Structure

```
br18_automation/
├── demo.py                    ← Run this file
├── .env                       ← Your API keys (create this)
├── requirements.txt
├── src/                       ← Core code
├── config/                    ← Settings
└── data/
    ├── example_pdfs/         ← BR18 examples (already there)
    ├── knowledge_base/       ← Created during demo
    ├── feedback/             ← Created during demo
    └── generated_docs/       ← Created during demo
```

## Next Steps

After running the demo:

1. **Review Generated Documents**
   - Check `data/generated_docs/` folder
   - See actual START documents created

2. **Inspect Knowledge Base**
   - `data/knowledge_base/chunks.json` - All knowledge chunks
   - See both original examples and learned insights

3. **Review Feedback**
   - `data/feedback/feedback_batch_*.json` - Simulated feedback

4. **Explore the Code**
   - `src/learning_engine/feedback_analyzer.py` - The learning magic ⭐
   - `src/rag_system/vector_store.py` - RAG implementation
   - `src/document_templates/template_engine.py` - Document generation

## Customization

### Change Number of Test Projects

Edit `demo.py` line 337:
```python
initial_docs = self.step2_generate_initial_documents(num_projects=5)  # Change this number
```

### Adjust Initial Approval Rate

Edit `demo.py` line 341:
```python
feedbacks = self.step3_simulate_municipality_feedback(initial_docs, initial_approval_rate=0.4)  # Change 0.4
```

### Add Your Own BR18 PDFs

1. Copy your PDFs to `data/example_pdfs/`
2. Run demo - they'll be automatically processed

## API Costs Estimate

**Per Demo Run:**
- Gemini API calls: ~15-20 requests (generation + analysis)
- Gemini embedding calls: ~50-100 requests (for vector database)
- **FREE with Gemini free tier!** ✨

The Gemini free tier includes both embeddings and generation, making this demo completely free to run!

## For Presentation

**Before your presentation:**
1. Run the demo once to verify it works
2. Delete `data/knowledge_base/` and `data/generated_docs/` to start fresh
3. Run it live during presentation, or
4. Have a completed run ready and walk through the output

**Presentation flow:**
1. Show the code structure (2 min)
2. Run the demo (3-5 min)
3. Explain the learning step in detail (5 min)
4. Show the metrics and improvement (2 min)
5. Q&A

## Support

If you encounter issues:

1. Check API keys are valid
2. Verify all dependencies installed
3. Make sure example PDFs are in `data/example_pdfs/`
4. Check Python version (3.8+ required)

## Key Files to Review

**Most Important:**
- `src/learning_engine/feedback_analyzer.py` - How learning works
- `demo.py` - Full demonstration flow
- `README.md` - Complete documentation

**Supporting:**
- `src/rag_system/vector_store.py` - Vector database
- `src/document_templates/template_engine.py` - Generation
- `PRESENTATION.md` - Presentation slides

---

**You're ready to go! Run `python demo.py` and watch the learning happen.** 🚀
